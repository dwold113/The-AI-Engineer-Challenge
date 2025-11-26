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
    
    # Check if user is requesting a GIF/animated image
    # DALL-E 3 only generates static images, not animated GIFs
    gif_keywords = ['gif', 'animated', 'animation', 'moving', 'video']
    if any(keyword in prompt_lower for keyword in gif_keywords):
        return (False, "DALL-E can only generate static images, not animated GIFs. Try describing the scene instead, like 'a boy dancing' or 'a dancing boy in motion'. You can upload your own GIF files using the 'Upload Image' option.")
    
    # Quick heuristic check for obviously valid prompts (skip AI validation for speed)
    # If prompt contains visual keywords, it's likely valid - skip expensive AI call
    visual_keywords = ['at', 'with', 'of', 'in', 'on', 'over', 'under', 'through', 'across', 'sunset', 'sunrise', 'night', 'day', 'city', 'mountain', 'ocean', 'forest', 'beach', 'sky', 'cloud', 'star', 'light', 'dark', 'color', 'abstract', 'pattern', 'scene', 'landscape', 'portrait', 'view']
    has_visual_keywords = any(keyword in prompt_lower for keyword in visual_keywords)
    
    # Only use AI validation for potentially problematic prompts
    # Skip AI validation for obviously visual prompts to save time
    if has_visual_keywords and len(words) >= 2:
        # Quick check for specific person names (common names that might be in prompts)
        # This is a fast heuristic - if it passes, skip expensive AI validation
        common_names = ['elon', 'musk', 'taylor', 'swift', 'obama', 'trump', 'biden', 'gates', 'bezos', 'zuckerberg']
        has_name = any(name in prompt_lower for name in common_names)
        if not has_name:
            # Looks like a valid visual prompt - skip AI validation for speed
            return (True, "")
    
    # Use fast AI validation only for edge cases
    try:
        validation_prompt = f"""Is this a valid image prompt? "{prompt}"

Respond ONLY:
- "VALID" if it describes a visual scene/object (not abstract concepts or specific real people)
- "INVALID: [reason]" if it's abstract, philosophical, or requests a specific real person

Response:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Validate image prompts. Only approve visual scenes/objects. Reject abstract concepts or specific real people."},
                {"role": "user", "content": validation_prompt}
            ],
            max_tokens=30,  # Minimal tokens for fastest response
            temperature=0.1  # Very low temperature for speed
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
