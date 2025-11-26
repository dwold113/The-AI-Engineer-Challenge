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
    # Debug endpoint to check if environment variable is set (remove in production)
    api_key_set = bool(os.getenv("OPENAI_API_KEY"))
    return {
        "status": "ok",
        "openai_api_key_configured": api_key_set,
        "note": "Remove this debug info in production"
    }

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
                {"role": "developer", "content": "You are able to use common sense and determine if the prompt should be generated"},
                {"role": "user", "content": user_message}
            ]
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling OpenAI API: {str(e)}")

def validate_prompt_makes_sense(prompt: str) -> tuple[bool, str]:
    """
    Use AI to determine if a prompt can be visualized as an image.
    Uses common sense to check if the phrase describes something that can be pictured.
    Returns (is_valid, message)
    """
    prompt_lower = prompt.lower().strip()
    words = prompt_lower.split()
    
    # Quick sanity checks (no API call needed)
    if len(words) < 2:
        return (False, "Please provide more details about what you want to see.")
    
    # Check for repeated characters or obvious nonsense
    if len(set(prompt_lower.replace(' ', ''))) < 3:
        return (False, "Please provide a meaningful description, not just repeated characters.")
    
    # Use AI to validate the prompt - it will intelligently catch all edge cases
    # No hardcoded keyword lists - AI handles copyrighted content, GIF requests, specific people, etc.
    try:
        validation_prompt = f"""Analyze this image generation prompt: "{prompt}"

Check for these issues:
1. Abstract/philosophical concepts (e.g., "freedom", "the meaning of life")
2. Specific real people (e.g., "jaxson dart", "elon musk", "taylor swift")
3. Copyrighted/trademarked content (e.g., "marvel", "disney", "star wars", specific superhero names)
4. Animated/GIF requests (e.g., "gif of", "animated", "moving video")

Respond ONLY:
- "VALID" if it's a visual scene/object without the above issues
- "INVALID: [specific reason and helpful suggestion]" if it has any of the above issues

Response:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert at validating image generation prompts. Check for abstract concepts, specific real people, copyrighted content, and animation requests. Provide helpful suggestions when rejecting prompts."
                },
                {"role": "user", "content": validation_prompt}
            ],
            max_tokens=50,  # Enough for reason + suggestion
            temperature=0.1  # Low temperature for consistent validation
        )
        
        result = response.choices[0].message.content.strip().upper()
        
        if result.startswith("VALID"):
            return (True, "")
        elif result.startswith("INVALID"):
            # Extract the explanation
            explanation = result.replace("INVALID", "").strip()
            if explanation.startswith(":"):
                explanation = explanation[1:].strip()
            return (False, explanation if explanation else "This doesn't describe a visual scene. Please describe what you want to see, like 'a sunset over mountains' or 'abstract geometric patterns'.")
        else:
            # If response format is unexpected, be conservative and allow it
            # Let DALL-E decide if it can generate it
            return (True, "")
            
    except Exception as e:
        # If AI validation fails, be lenient and allow the prompt
        # Better to let DALL-E try than to block valid prompts
        print(f"Validation error: {e}")
        return (True, "")

@app.post("/api/generate-image")
async def generate_image(request: ImageRequest):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    
    # Basic prompt validation
    prompt = request.prompt.strip()
    if len(prompt) < 3:
        raise HTTPException(status_code=400, detail="Prompt is too short. Please provide more details.")
    if len(prompt) > 1000:
        raise HTTPException(status_code=400, detail="Prompt is too long. Please keep it under 1000 characters.")
    
    # Fast validation to check if prompt makes sense
    is_valid, validation_message = validate_prompt_makes_sense(prompt)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=validation_message or "This prompt doesn't clearly describe a visual scene. Please provide more details about what background you want to see."
        )
    
    try:
        # Use standard quality for fastest generation (under 10 seconds)
        # Standard quality is still high quality but generates much faster than HD
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",  # Smallest size for fastest generation
            quality="standard",  # Standard quality for speed (still high quality)
            n=1,
        )
        image_url = response.data[0].url
        
        # Fetch the image asynchronously and convert to base64 to avoid CORS issues
        # Use shorter timeout for faster failure if image isn't ready
        async with httpx.AsyncClient(timeout=5.0) as http_client:
            img_response = await http_client.get(image_url)
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
        # Note: DALL-E may generate images for prompts with specific people, but they won't be accurate
        # The validation step should catch these, but if it gets through, we let DALL-E try
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")
