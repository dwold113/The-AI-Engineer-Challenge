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
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        raise

# ===== CORS =====

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== MODELS =====

class LearningRequest(BaseModel):
    topic: str

class LearningPlanResponse(BaseModel):
    plan: List[Dict[str, str]]
    message: str = ""  # Optional message about step count adjustments

class ExpandStepRequest(BaseModel):
    topic: str
    step_title: str
    step_description: str

# ===== VALIDATION =====

def extract_validate_and_prepare_topic(topic: str) -> tuple[str, str, int, bool, str]:
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

# ===== EXPAND LEARNING STEP =====

async def expand_learning_step(topic: str, step_title: str, step_description: str) -> Dict[str, any]:
    """
    Generate additional clarity and context for a learning step without repeating existing information.
    Focuses on gaps, nuances, and practical details that weren't covered in the main step.
    """
    try:
        prompt = f"""Topic: {topic}
Step: {step_title} - {step_description}

Generate SPECIFIC, UNIQUE details for THIS PARTICULAR STEP. Do NOT provide generic advice that could apply to any step.

Focus on:
- What makes THIS step unique compared to other steps in learning {topic}
- Step-specific techniques, methods, or approaches
- Concrete examples relevant to THIS step
- Challenges that are PARTICULAR to THIS step
- Practical details that help with THIS specific step

The content must be tailored to "{step_title}" and "{step_description}" - not generic learning advice.

JSON format:
{{
  "additionalContext": "Step-specific context about why this step matters and how it fits into learning {topic}",
  "practicalDetails": ["Specific actionable detail for THIS step", "Another specific detail for THIS step"],
  "importantConsiderations": ["Consideration specific to THIS step"],
  "realWorldExamples": ["Example specific to THIS step"],
  "potentialChallenges": ["Challenge specific to THIS step: Solution for THIS step", "Another challenge for THIS step: Solution"]
}}

CRITICAL: All content must be SPECIFIC to "{step_title}" - {step_description}. Do NOT repeat generic learning advice.
All fields must be arrays of STRINGS only. potentialChallenges should be strings like "Challenge: Solution", not objects.

JSON only:"""

        result = call_ai(
            prompt,
            "Expert educator who provides step-specific, tailored guidance. Generate unique content for each step that directly relates to the step title and description. Avoid generic advice.",
            max_tokens=400,
            temperature=0.6
        )
        expanded = parse_json_response(result)
        
        # Ensure all array fields are arrays of strings (not objects)
        # Fix potentialChallenges if AI returned objects instead of strings
        if "potentialChallenges" in expanded and expanded["potentialChallenges"]:
            fixed_challenges = []
            for item in expanded["potentialChallenges"]:
                if isinstance(item, str):
                    fixed_challenges.append(item)
                elif isinstance(item, dict):
                    # Convert object to string format
                    challenge = item.get('challenge', 'Challenge')
                    solution = item.get('solution', 'Solution')
                    fixed_challenges.append(f"{challenge}: {solution}")
                else:
                    fixed_challenges.append(str(item))
            expanded["potentialChallenges"] = fixed_challenges
        
        # Ensure all other array fields are strings
        for field in ["practicalDetails", "importantConsiderations", "realWorldExamples"]:
            if field in expanded and expanded[field]:
                expanded[field] = [
                    item if isinstance(item, str) else str(item)
                    for item in expanded[field]
                ]
        
        return expanded
    except Exception as e:
        print(f"Error expanding learning step: {e}")
        # Fallback response
        return {
            "additionalContext": f"While working on {step_title}, keep in mind that this step builds on foundational concepts. Understanding the 'why' behind each action will help you apply this knowledge more effectively.",
            "practicalDetails": [
                "Break down complex tasks into smaller, manageable pieces",
                "Set aside dedicated time for focused practice",
                "Document your progress and questions as you go"
            ],
            "importantConsiderations": [
                "Make sure you have the necessary prerequisites before starting",
                "Don't rush - quality understanding is more important than speed"
            ],
            "realWorldExamples": [
                "Many successful learners use spaced repetition to reinforce concepts",
                "Building projects helps solidify theoretical knowledge"
            ],
            "potentialChallenges": [
                "Information overload - focus on one concept at a time",
                "Lack of immediate feedback - seek out communities or mentors for guidance"
            ]
        }

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

@app.post("/api/expand-step")
async def expand_step(request: ExpandStepRequest):
    """
    Endpoint to get expanded, detailed information for a specific learning step.
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    
    try:
        expanded = await expand_learning_step(
            request.topic,
            request.step_title,
            request.step_description
        )
        return expanded
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error expanding learning step: {str(e)}")
