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
    Validate if a prompt makes sense for image generation by checking if it describes visual elements.
    Returns (is_valid, message)
    """
    prompt_lower = prompt.lower().strip()
    words = prompt_lower.split()
    
    # Quick checks for obvious invalid prompts
    test_words = ['test', 'dummy', 'placeholder', 'example', 'sample', 'asdf', 'qwerty']
    if len(words) <= 2 and any(word in test_words for word in words):
        return (False, "This doesn't describe a visual scene. Please describe what you want to see, like 'a sunset over mountains' or 'a cozy coffee shop'.")
    
    # Check for repeated characters or nonsense
    if len(set(prompt_lower.replace(' ', ''))) < 3:
        return (False, "Please provide a meaningful description of a visual scene, not just repeated characters.")
    
    # Check if prompt contains visual/descriptive words that indicate it can be turned into an image
    visual_keywords = [
        # Objects and things
        'image', 'picture', 'photo', 'scene', 'view', 'landscape', 'portrait', 'art', 'artwork', 'design',
        # Places and locations
        'city', 'forest', 'beach', 'mountain', 'ocean', 'desert', 'valley', 'island', 'room', 'house', 'building',
        # Nature
        'sunset', 'sunrise', 'sky', 'cloud', 'tree', 'flower', 'water', 'river', 'lake', 'sea',
        # Time and atmosphere
        'night', 'day', 'morning', 'evening', 'foggy', 'sunny', 'rainy', 'snowy',
        # Colors and styles
        'color', 'colour', 'bright', 'dark', 'vibrant', 'abstract', 'geometric', 'pattern',
        # Actions and concepts that can be visualized
        'flying', 'floating', 'glowing', 'shining', 'reflection', 'shadow', 'light', 'space',
        # Descriptive adjectives
        'serene', 'peaceful', 'dramatic', 'majestic', 'beautiful', 'stunning', 'epic', 'vast',
        # Visual concepts
        'horizon', 'perspective', 'depth', 'texture', 'gradient', 'silhouette'
    ]
    
    # Check if prompt contains visual keywords
    has_visual_keywords = any(keyword in prompt_lower for keyword in visual_keywords)
    
    # Check for abstract/philosophical phrases that don't describe visuals
    abstract_phrases = [
        'infinite possibilities', 'freedom to', 'open weights', 'philosophy', 'concept', 'idea',
        'meaning of', 'purpose of', 'essence of', 'nature of', 'truth about'
    ]
    
    has_abstract_phrase = any(phrase in prompt_lower for phrase in abstract_phrases)
    
    # If it has abstract phrases but no visual keywords, it's probably not suitable for image generation
    if has_abstract_phrase and not has_visual_keywords:
        return (False, "This prompt is too abstract or philosophical. Please describe a visual scene you want to see, like 'a futuristic city at night' or 'abstract geometric patterns in blue and purple'.")
    
    # If it has visual keywords, allow it
    if has_visual_keywords:
        return (True, "")
    
    # If it's very short (less than 3 words), require more detail
    if len(words) < 3:
        return (False, "Please provide more details about the visual scene you want to see.")
    
    # For longer prompts without obvious visual keywords, be lenient but warn
    # Let DALL-E try to interpret it, but suggest improvement
    if len(words) >= 5:
        return (True, "")  # Allow longer prompts even without obvious keywords
    
    # For medium-length prompts without visual keywords, suggest improvement
    return (False, "This doesn't clearly describe a visual scene. Try describing what you want to see, like 'a cyberpunk cityscape' or 'a serene mountain landscape at sunset'.")

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
        # Use smallest HD size for fastest generation while maintaining highest quality
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",  # Smallest size for fastest generation
            quality="hd",  # HD quality for highest image clarity
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
