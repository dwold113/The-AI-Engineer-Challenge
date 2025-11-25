from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from openai import OpenAI
import os
import httpx
import base64
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS so the frontend can talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatRequest(BaseModel):
    message: str

class ImageRequest(BaseModel):
    prompt: str

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/api/chat")
def chat(request: ChatRequest):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    
    try:
        user_message = request.message
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a supportive helper"},
                {"role": "developer", "content": "You are able to use common sense and determine if the promt should be generated"},
                {"role": "user", "content": user_message}
            ]
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling OpenAI API: {str(e)}")

def validate_prompt_makes_sense(prompt: str) -> tuple[bool, str]:
    """
    Use AI to validate if a prompt makes sense for image generation.
    Returns (is_valid, message)
    """
    try:
        validation_prompt = f"""Analyze this image generation prompt and determine if it makes sense for creating a background image. 

Prompt: "{prompt}"

Respond with ONLY one of these two options:
1. If the prompt makes sense and describes a visual scene/background: "VALID"
2. If the prompt is vague, nonsensical, or doesn't describe a visual scene: "INVALID: [brief explanation of why it doesn't make sense and what the user should provide instead]"

Examples:
- "dummy prompt" -> "INVALID: This doesn't describe a visual scene. Please describe what you want to see, like 'a sunset over mountains' or 'a cozy coffee shop'."
- "test" -> "INVALID: This is too vague. Please describe a specific scene or background you'd like to see."
- "a serene mountain landscape at sunset" -> "VALID"
- "cyberpunk city at night" -> "VALID"

Your response:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use cheaper model for validation
            messages=[
                {"role": "system", "content": "You are a prompt validator. You determine if image generation prompts make sense. Be strict - only approve prompts that clearly describe visual scenes or backgrounds."},
                {"role": "user", "content": validation_prompt}
            ],
            max_tokens=150,
            temperature=0.3
        )
        
        result = response.choices[0].message.content.strip().upper()
        
        if result.startswith("VALID"):
            return (True, "")
        elif result.startswith("INVALID"):
            # Extract the explanation
            explanation = result.replace("INVALID", "").strip()
            if explanation.startswith(":"):
                explanation = explanation[1:].strip()
            return (False, explanation if explanation else "This prompt doesn't clearly describe a visual scene. Please provide more details about what background you want to see.")
        else:
            # If response format is unexpected, default to checking manually
            if len(prompt.split()) < 3 or any(word in prompt.lower() for word in ['test', 'dummy', 'placeholder', 'example', 'sample']):
                return (False, "Please provide a clear description of the background you want to see, not a test or placeholder text.")
            return (True, "")
    except Exception as e:
        # If validation fails, do basic checks and allow generation
        print(f"Validation error: {e}")
        return (True, "")

@app.post("/api/generate-image")
def generate_image(request: ImageRequest):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    
    # Basic prompt validation
    prompt = request.prompt.strip()
    if len(prompt) < 3:
        raise HTTPException(status_code=400, detail="Prompt is too short. Please provide more details.")
    if len(prompt) > 1000:
        raise HTTPException(status_code=400, detail="Prompt is too long. Please keep it under 1000 characters.")
    
    # AI-based validation to check if prompt makes sense
    is_valid, validation_message = validate_prompt_makes_sense(prompt)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=validation_message or "This prompt doesn't clearly describe a visual scene. Please provide more details about what background you want to see."
        )
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        
        # Fetch the image and convert to base64 to avoid CORS issues
        with httpx.Client() as http_client:
            img_response = http_client.get(image_url, timeout=30.0)
            img_response.raise_for_status()
            image_data = img_response.content
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            image_data_url = f"data:image/png;base64,{image_base64}"
        
        return {"image_url": image_data_url}
    except Exception as e:
        error_str = str(e).lower()
        # Check for content policy violations
        if 'content_policy' in error_str or 'safety' in error_str or 'policy' in error_str:
            raise HTTPException(
                status_code=400, 
                detail="This prompt may violate content policies. Please try a different, more appropriate description."
            )
        # Check for invalid prompts
        if 'invalid' in error_str or 'malformed' in error_str:
            raise HTTPException(
                status_code=400,
                detail="The prompt doesn't make sense or is invalid. Please provide a clearer description of the background you want."
            )
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")
