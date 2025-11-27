# SIMPLIFIED VERSION - WITHOUT "Real Examples & Resources"
# This shows what the code would look like if we removed all resource/examples logic

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
import re
import json
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

app = FastAPI()

# ===== HELPER FUNCTIONS =====

def clean_json_response(text: str) -> str:
    """Clean AI response by removing markdown code blocks."""
    result = text.strip()
    if result.startswith("```json"):
        result = result[7:]
    if result.startswith("```"):
        result = result[3:]
    if result.endswith("```"):
        result = result[:-3]
    return result.strip()

def call_ai(prompt: str, system_message: str, max_tokens: int = 500, temperature: float = 0.5) -> str:
    """Common function to call OpenAI API and return cleaned response."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=temperature
    )
    return clean_json_response(response.choices[0].message.content)

def parse_json_response(text: str) -> any:
    """Parse JSON response from AI, handling common formatting issues."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from text
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        raise

# ===== MODELS =====

class LearningRequest(BaseModel):
    topic: str

class LearningPlanResponse(BaseModel):
    plan: List[Dict[str, str]]
    message: str = ""  # Optional message about step count adjustments

# ===== VALIDATION =====

def extract_validate_and_prepare_topic(topic: str) -> tuple[str, str, int, bool]:
    """
    Combined function: Extract, validate topic, and extract number of steps.
    Returns (clean_topic, message, num_steps, is_valid, validation_message)
    """
    try:
        prompt = f"""Analyze this learning topic request: "{topic}"

Extract and validate:
1. Clean topic (remove "how to", "learn", "learning", "teach me", etc. - just the core topic)
2. Extract any requested number of steps (if mentioned, like "give me 3 steps")
3. Validate if this is a valid learning topic

APPROVE these types of topics:
- Languages (e.g., "amharic", "spanish", "japanese", "swahili", "learning amharic", "how to learn amharic")
- Skills (e.g., "cooking", "programming", "painting", "photography")
- Subjects (e.g., "mathematics", "history", "biology", "philosophy")
- Concepts (e.g., "machine learning", "quantum physics", "music theory")
- Practical topics (e.g., "how to run a marathon", "how to start a business")

REJECT only these:
- Gibberish/random characters (e.g., "fgnrjk gnsogfd", "asdfgh")
- Random unrelated words (e.g., "time space coffee", "car tree music")
- Specific real person names (e.g., "donald trump", "barack obama", "elon musk")
- Too vague or abstract to create a learning plan

Respond in JSON:
{{
  "clean_topic": "cleaned topic",
  "num_steps": number or null,
  "is_valid": true/false,
  "validation_message": "message if invalid, empty if valid"
}}

JSON only:"""

        result = call_ai(
            prompt,
            "Expert at extracting and validating learning topics. Be balanced - approve valid learning topics (languages, skills, subjects, concepts) but reject gibberish, person names, and nonsensical combinations. Languages like 'amharic', 'spanish', 'japanese' are always valid.",
            max_tokens=200,
            temperature=0.1
        )
        
        data = parse_json_response(result)
        clean_topic = data.get("clean_topic", "").strip()
        num_steps = data.get("num_steps")
        is_valid = data.get("is_valid", False)
        validation_message = data.get("validation_message", "").strip()
        
        # Extract num_steps from topic if not in AI response
        if num_steps is None:
            step_match = re.search(r'(\d+)\s*steps?', topic.lower())
            if step_match:
                num_steps = int(step_match.group(1))
            else:
                num_steps = None
        
        message = ""
        if validation_message:
            message = validation_message
        
    except Exception as e:
        print(f"Error in validation: {e}")
        clean_topic = re.sub(r'[.,;:]+$', '', topic).strip()
        clean_topic = re.sub(r'\s+', ' ', clean_topic)
        # Remove common prefixes to get core topic
        clean_topic = re.sub(r'^(learn|learning|how to|teach me|i want to learn)\s+', '', clean_topic, flags=re.IGNORECASE).strip()
        
        # If we can extract a reasonable topic, default to valid (be lenient)
        # Only reject if topic is clearly gibberish or empty
        if len(clean_topic) < 2 or not clean_topic.replace(' ', '').isalnum():
            is_valid = False
            validation_message = "Unable to validate this topic. Please enter a clear, learnable subject, skill, or concept."
        else:
            # Default to valid if we extracted something reasonable
            is_valid = True
            validation_message = ""
        
        num_steps = None
        message = validation_message
    
    return clean_topic, message, num_steps, is_valid, validation_message

# ===== LEARNING PLAN GENERATION =====

def generate_learning_plan(topic: str, num_steps: int = None) -> List[Dict[str, str]]:
    """
    Generate a structured learning plan for the topic.
    Returns list of steps with title and description.
    """
    try:
        if num_steps is None:
            step_instruction = "Provide a practical, actionable plan with 5-7 steps."
        else:
            step_instruction = f"Provide exactly {num_steps} steps. Make sure the plan is comprehensive but fits within {num_steps} steps."
        
        prompt = f"""Learning topic: {topic}

Generate a structured learning plan: {step_instruction}

Each step should be practical and actionable. Focus on what the learner should actually DO.

Respond in JSON format:
{{
  "plan": [{{"title": "Step 1: ...", "description": "..."}}, ...]
}}

JSON only:"""

        result = call_ai(
            prompt,
            "Expert educator who creates practical, actionable learning plans.",
            max_tokens=600,
            temperature=0.7
        )
        
        data = parse_json_response(result)
        plan = data.get("plan", [])
        
        # Fallback if plan is empty
        if not plan:
            plan = [
                {"title": f"Step 1: Research {topic}", "description": f"Start by researching the basics of {topic} online."},
                {"title": f"Step 2: Practice", "description": f"Try applying what you've learned about {topic} through hands-on practice."},
                {"title": f"Step 3: Build Projects", "description": f"Create projects to solidify your understanding of {topic}."}
            ]
        
        return plan
        
    except Exception as e:
        print(f"Error generating learning plan: {e}")
        # Fallback plan
        return [
            {"title": f"Step 1: Research {topic}", "description": f"Start by researching the basics of {topic} online."},
            {"title": f"Step 2: Practice", "description": f"Try applying what you've learned about {topic} through hands-on practice."},
            {"title": f"Step 3: Build Projects", "description": f"Create projects to solidify your understanding of {topic}."}
        ]

# ===== ENDPOINTS =====

@app.get("/")
def root():
    api_key_set = bool(os.getenv("OPENAI_API_KEY"))
    return {
        "status": "ok",
        "openai_api_key_configured": api_key_set,
        "app": "AI Learning Experience App"
    }

@app.post("/api/learn", response_model=LearningPlanResponse)
async def create_learning_experience(request: LearningRequest):
    """
    Takes a learning topic and returns a structured learning plan.
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    
    original_topic = request.topic.strip()
    
    # Extract, validate topic, and get number of steps
    clean_topic, message, num_steps, is_valid, validation_message = extract_validate_and_prepare_topic(original_topic)
    
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=validation_message or "This doesn't seem like a valid learning topic. Please enter something specific you want to learn."
        )
    
    try:
        # Generate learning plan
        plan = generate_learning_plan(clean_topic, num_steps=num_steps)
        
        return LearningPlanResponse(
            plan=plan,
            message=message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating learning experience: {str(e)}")

# ===== CORS =====

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

