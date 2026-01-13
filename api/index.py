from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
import sys
import json
# #region agent log
try:
    with open('/Users/dannywold/ai/The-AI-Engineer-Challenge/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"A","location":"api/index.py:6","message":"Before dotenv import - checking Python path","data":{"pythonPath":sys.path[:3],"pythonVersion":sys.version},"timestamp":int(__import__('time').time()*1000)}) + '\n')
except: pass
# #endregion
try:
    from dotenv import load_dotenv
    # #region agent log
    with open('/Users/dannywold/ai/The-AI-Engineer-Challenge/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"A","location":"api/index.py:10","message":"dotenv import successful","data":{},"timestamp":int(__import__('time').time()*1000)}) + '\n')
    # #endregion
except ImportError as e:
    # #region agent log
    with open('/Users/dannywold/ai/The-AI-Engineer-Challenge/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"A","location":"api/index.py:13","message":"dotenv import failed","data":{"error":str(e),"errorType":type(e).__name__},"timestamp":int(__import__('time').time()*1000)}) + '\n')
    # #endregion
    raise

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
                {"role": "system", "content": "You are a subject matter expert in anything related to outerspace. Your goal is to answer only space related questions. Answers should be short and concise. Any nonsense questions or gibberish will be met with a redirect to the user to ask a space related question. If you dont know the answer say I dont know"},
                {"role": "user", "content": user_message}
            ]
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling OpenAI API: {str(e)}")
