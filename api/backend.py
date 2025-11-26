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
    
    # Use AI to determine if the prompt can be visualized
    try:
        validation_prompt = f"""Analyze this image generation prompt step by step:

Prompt: "{prompt}"

Step 1: Does this describe something that can be visualized as an image?
- Can you picture this in your mind?
- Does it describe visual elements (objects, scenes, colors, shapes, landscapes, etc.)?
- Or is it abstract/philosophical (concepts, ideas, emotions without visual representation)?

Step 2: IMPORTANT - Check if prompt requests a specific real person:
- Does the prompt contain a specific person's name (like "jaxson dart", "elon musk", "taylor swift")?
- If yes, this is a problem because AI image generators cannot accurately create images of specific real people
- Instead, suggest describing the scene without the person's name (e.g., "a quarterback running" instead of "jaxson dart running")

Step 3: Examples of what CAN be visualized:
- "a sunset over mountains" ✅ (clear visual scene)
- "abstract geometric patterns" ✅ (visual design)
- "a cyberpunk city at night" ✅ (describes a scene)
- "serene forest with glowing mushrooms" ✅ (visual elements)
- "a quarterback running on a field" ✅ (describes a scene without specific person)

Step 4: Examples of what CANNOT be visualized:
- "Open weights. Infinite possibilities" ❌ (abstract concept, no visual elements)
- "the meaning of life" ❌ (philosophical, not visual)
- "freedom to run anywhere" ❌ (abstract concept, not a scene)
- "jaxson dart running" ❌ (requests specific real person - AI cannot accurately generate this)

Step 5: Your analysis:
Respond with ONLY one of these:
- "VALID" if it can be visualized as an image AND doesn't request a specific real person
- "INVALID: [brief explanation]" if it cannot be visualized or requests a specific real person, with a helpful suggestion

Your response:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cheap for validation
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert at determining if text can be visualized as an image. Use common sense and think step by step. Be strict - only approve prompts that clearly describe visual scenes, objects, or designs that can be rendered as images."
                },
                {"role": "user", "content": validation_prompt}
            ],
            max_tokens=100,  # Reduced for faster response
            temperature=0.2  # Low temperature for consistent validation
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
        async with httpx.AsyncClient(timeout=10.0) as http_client:
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
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")
