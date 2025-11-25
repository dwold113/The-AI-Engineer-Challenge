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
                {"role": "system", "content": "You are a supportive helper."},
                {"role": "developer", "content": "You are an expert on AI and pixelated backgrounds. You have a good taste of design and can build impressive pixelated backgrounds."},
                {"role": "user", "content": user_message}
            ]
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling OpenAI API: {str(e)}")

@app.post("/api/generate-image")
def generate_image(request: ImageRequest):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=request.prompt,
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
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")
