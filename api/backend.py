from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
import httpx
import asyncio
import re
from urllib.parse import unquote, parse_qs, urlparse
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from typing import List, Dict
import json

load_dotenv()

app = FastAPI()

# ===== HELPER FUNCTIONS =====

def clean_json_response(text: str) -> str:
    """
    Clean AI response by removing markdown code blocks.
    Handles ```json, ```, and trailing ``` patterns.
    """
    result = text.strip()
    if result.startswith("```json"):
        result = result[7:]
    if result.startswith("```"):
        result = result[3:]
    if result.endswith("```"):
        result = result[:-3]
    return result.strip()

def call_ai(prompt: str, system_message: str, max_tokens: int = 500, temperature: float = 0.5) -> str:
    """
    Common function to call OpenAI API and return cleaned response.
    """
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
    """
    Clean and parse JSON from AI response.
    """
    cleaned = clean_json_response(text)
    return json.loads(cleaned)

# CORS so the frontend can talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class LearningRequest(BaseModel):
    topic: str

class LearningPlanResponse(BaseModel):
    plan: List[Dict[str, str]]
    examples: List[Dict[str, str]]
    message: str = ""  # Optional message about resource count adjustments

class ExpandStepRequest(BaseModel):
    topic: str
    step_title: str
    step_description: str

def validate_learning_topic(topic: str) -> tuple[bool, str]:
    """
    Use AI to determine if a topic is valid for learning.
    Uses common sense to check if the topic makes sense and can be learned.
    Returns (is_valid, message)
    """
    # Basic check: topic must exist
    if not topic or not topic.strip():
        return (False, "Please enter a topic you want to learn about.")
    
    # Use AI to validate the topic - it intelligently handles all edge cases
    try:
        validation_prompt = f"""Analyze this learning topic: "{topic}"

Determine if this is a valid, learnable topic. Check for:
- Real, meaningful content (not gibberish or random characters)
- Learnable subject matter (not abstract philosophical concepts)
- Sufficient specificity (not too vague)
- Logical coherence

Respond ONLY:
- "VALID" if it's a real, learnable topic
- "INVALID: [specific reason and helpful suggestion]" if it's not valid

Response:"""

        result = call_ai(
            validation_prompt,
            "You are an expert at determining if a topic is valid for learning. Use common sense to detect gibberish, abstract concepts, and nonsensical inputs. Be strict - only approve topics that are real, specific, and learnable.",
            max_tokens=80,
            temperature=0.1
        ).upper()
        
        if result.startswith("VALID"):
            return (True, "")
        elif result.startswith("INVALID"):
            # Extract the explanation
            explanation = result.replace("INVALID", "").strip()
            if explanation.startswith(":"):
                explanation = explanation[1:].strip()
            return (False, explanation if explanation else "This doesn't seem like a valid learning topic. Please enter something specific you want to learn.")
        else:
            # If response format is unexpected, be conservative and allow it
            # Better to let the system try than to block valid topics
            return (True, "")
            
    except Exception as e:
        # If AI validation fails, be lenient and allow the topic
        # Better to let the system try than to block valid topics
        print(f"Validation error: {e}")
        return (True, "")

@app.get("/")
def root():
    # Debug endpoint to check if environment variable is set
    api_key_set = bool(os.getenv("OPENAI_API_KEY"))
    return {
        "status": "ok",
        "openai_api_key_configured": api_key_set,
        "app": "AI Learning Experience App"
    }

async def generate_plan_and_resources(topic: str, num_steps: int = None, num_examples: int = 5) -> tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    OPTIMIZED: Combined function that generates both learning plan and resources in a single AI call.
    This reduces latency and cost by 50% compared to separate calls.
    Returns (plan, examples)
    """
    try:
        # Determine number of steps
        if num_steps is None:
            step_instruction = "Provide a practical, actionable plan with 5-7 steps."
        else:
            step_instruction = f"Provide exactly {num_steps} steps. Make sure the plan is comprehensive but fits within {num_steps} steps."
        
        # Single AI call that generates both plan and resources
        combined_prompt = f"""Learning topic: {topic}

Generate both:
1. A structured learning plan: {step_instruction}
2. {num_examples} real learning resources (actual educational websites, documentation, tutorials, or courses with real URLs)

Respond in JSON format:
{{
  "plan": [{{"title": "Step 1", "description": "..."}}, ...],
  "resources": [{{"title": "Name", "url": "https://real-site.com", "description": "Brief"}}, ...]
}}

JSON only:"""

        result = call_ai(
            combined_prompt,
            "Expert educator and resource finder. Generate learning plans and find real educational resources. Provide actual website URLs only.",
            max_tokens=800,
            temperature=0.5
        )
        data = parse_json_response(result)
        
        plan = data.get("plan", [])
        resources = data.get("resources", [])
        
        # Process resources - validate URLs and format
        examples = []
        for resource in resources[:num_examples]:
            url = resource.get("url", "")
            title = resource.get("title", f"{topic} Resource")
            
            # Simple validation: must be a valid HTTP(S) URL
            if url and url.startswith("http"):
                examples.append({
                    "title": title,
                    "url": url,
                    "description": resource.get("description", f"Learn about {topic}")
                })
        
        # Fallback if plan is empty
        if not plan:
            plan = [
                {"title": f"Step 1: Research {topic}", "description": f"Start by researching the basics of {topic} online."},
                {"title": f"Step 2: Find Examples", "description": f"Look for real-world examples of {topic} to understand practical applications."},
                {"title": f"Step 3: Practice", "description": f"Try applying what you've learned about {topic} through hands-on practice."}
            ]
        
        return plan, examples
        
    except Exception as e:
        print(f"Error generating combined plan and resources: {e}")
        # Fallback
        plan = [
            {"title": f"Step 1: Research {topic}", "description": f"Start by researching the basics of {topic} online."},
            {"title": f"Step 2: Find Examples", "description": f"Look for real-world examples of {topic} to understand practical applications."},
            {"title": f"Step 3: Practice", "description": f"Try applying what you've learned about {topic} through hands-on practice."}
        ]
        examples = []
        
        # Try web scraping as fallback for resources only if we don't have enough
        if len(examples) < num_examples:
            try:
                # Single quick web scraping attempt (2 second timeout max - very aggressive)
                async with httpx.AsyncClient(timeout=2.0, follow_redirects=True) as http_client:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    }
                    
                    search_url = f"https://html.duckduckgo.com/html/?q={topic.replace(' ', '+')}+tutorial"
                    response = await http_client.get(search_url, headers=headers)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'lxml')
                    results = soup.find_all('a', class_='result__a', limit=num_examples - len(examples))
                    
                    for result in results:
                        if len(examples) >= num_examples:
                            break
                        
                        title = result.get_text(strip=True)
                        url = result.get('href', '')
                        
                        if not title or not url:
                            continue
                        
                        # Clean up DuckDuckGo redirect URLs
                        if url.startswith('/l/?') or 'uddg=' in url:
                            try:
                                if 'uddg=' in url:
                                    parts = url.split('uddg=')
                                    if len(parts) > 1:
                                        encoded_url = parts[1].split('&')[0]
                                        url = unquote(encoded_url)
                                        if not url.startswith('http'):
                                            continue
                                    else:
                                        continue
                                else:
                                    parsed = urlparse(url)
                                    params = parse_qs(parsed.query)
                                    if 'uddg' in params:
                                        url = unquote(params['uddg'][0])
                                    else:
                                        continue
                            except:
                                continue
                        
                        if url.startswith('http') and not any(ex['url'] == url for ex in examples):
                            examples.append({
                                "title": title[:100],
                                "url": url,
                                "description": f"Learn more about {topic} with this resource"
                            })
            except Exception as e:
                print(f"Error in web scraping (non-critical): {e}")
        
        # Final fallback if we still don't have enough - use AI to generate fallback resources
        if len(examples) == 0:
            try:
                # Use AI to suggest fallback educational resources
                fallback_prompt = f"""Suggest 3 general educational resources for learning about: {topic}

Provide real educational websites, documentation, or learning platforms.

JSON: [{{"title": "Resource Name", "url": "https://real-site.com", "description": "Brief"}}, ...]

JSON only:"""
                
                fallback_result = call_ai(fallback_prompt, "Expert at finding educational resources. Provide real website URLs only.", max_tokens=200, temperature=0.5)
                fallback_resources = parse_json_response(fallback_result)
                for resource in fallback_resources:
                    url = resource.get("url", "")
                    if url and url.startswith("http"):
                        examples.append({
                            "title": resource.get("title", f"{topic} Resource"),
                            "url": url,
                            "description": resource.get("description", f"Learn about {topic}")
                        })
            except Exception as e:
                print(f"Error generating fallback resources: {e}")
        
        return plan, examples[:num_examples]

def extract_validate_and_prepare_topic(topic: str) -> tuple[str, int, str, int, bool, str]:
    """
    OPTIMIZED: Combined extraction, validation, and number validation in a single AI call.
    Extracts clean topic, requested numbers, validates topic, and validates number reasonableness.
    Returns (clean_topic, num_resources, message, num_steps, is_valid, validation_message)
    """
    import re
    
    # Default values
    num_resources = 5
    num_steps = None
    message = ""
    is_valid = True
    validation_message = ""
    
    try:
        # Single AI call that does everything: extract, validate topic, validate numbers
        combined_prompt = f"""User input: "{topic}"

Perform these tasks in one response:
1. Extract the clean learning topic (remove number requests)
2. Extract any requested number of resources/examples (if mentioned)
3. Extract any requested number of steps (if mentioned)
4. Validate if the topic is learnable:
   - NOT gibberish, random characters, or nonsensical text
     → Examples to REJECT: "fgnrjk gnsogfd", "asdfgh", "xyz abc", "qwerty", any random letter combinations
     → If the input has no meaning, is just random characters, or doesn't form real words, set is_valid to false
   - NOT abstract philosophical concepts
   - NOT too vague
   - NOT about a specific real person (politicians, celebrities, public figures, historical figures, etc.)
     → Examples to REJECT: "donald trump", "barack obama", "barak obama", "elon musk", "taylor swift", "albert einstein", "steve jobs"
     → Learning plans should be for SKILLS, SUBJECTS, or CONCEPTS, not personal biographies or people
     → If the input is a person's name (even with typos), set is_valid to false
     → If about a person, suggest learning about their field/domain instead (e.g., "business strategy" instead of "donald trump", "public speaking" instead of "barack obama")
5. If a resource number was requested, determine if it's reasonable (3-15 is reasonable)

All validation checks are equally important. Reject the topic if it fails any check:
- If the input is gibberish/random characters (like "fgnrjk gnsogfd"), reject it and set is_valid to false
- If the input appears to be a person's name (first name + last name pattern, or a well-known single name), reject it and provide a helpful alternative suggestion
- If the input is too abstract, vague, or not learnable, reject it
- Only approve topics that are real, meaningful, learnable subjects, skills, or concepts

Respond in JSON format:
{{
  "topic": "clean topic",
  "num_resources": number or null,
  "num_steps": number or null,
  "is_valid": true/false,
  "validation_message": "error message if invalid, empty if valid. If gibberish, say 'This appears to be random characters or gibberish. Please enter a real learning topic.' If about a person, suggest learning the skill/domain instead.",
  "resource_message": "message if resource count was adjusted, empty otherwise"
}}

JSON only:"""

        result = call_ai(
            combined_prompt,
            "Expert at extracting and validating learning topics. You MUST reject: (1) Gibberish/random characters/nonsensical text - if input has no meaning or is just random letters, reject it. (2) Specific real person names - learning plans are for skills, subjects, and concepts only, never for people. Be very strict about detecting gibberish and person names. Only approve real, meaningful, learnable topics.",
            max_tokens=200,
            temperature=0.1
        )
        data = parse_json_response(result)
        
        # Extract values - handle None safely
        extracted_topic = data.get("topic")
        if extracted_topic:
            clean_topic = str(extracted_topic).strip()
        else:
            # Fallback to original topic if extraction failed
            clean_topic = re.sub(r'[.,;:]+$', '', topic).strip()
            clean_topic = re.sub(r'\s+', ' ', clean_topic)
        
        if not clean_topic:
            clean_topic = topic.strip()
        
        # Handle resource count
        if data.get("num_resources"):
            requested_num = int(data["num_resources"])
            # Check if AI adjusted it
            resource_msg = data.get("resource_message", "").strip()
            if resource_msg:
                message = resource_msg
                # Try to extract the adjusted number from the message or use requested
                match = re.search(r'(\d+)', resource_msg)
                if match:
                    num_resources = int(match.group(1))
                else:
                    num_resources = requested_num
            else:
                num_resources = requested_num
        else:
            num_resources = 5  # Default
        
        # Handle step count
        if data.get("num_steps"):
            num_steps = int(data["num_steps"])
        
        # Handle validation
        is_valid = data.get("is_valid", True)
        validation_message = data.get("validation_message", "").strip()
        
    except Exception as e:
        print(f"Error in combined extraction/validation: {e}")
        # If validation fails, be strict and reject the topic
        # Better to reject potentially invalid topics than to allow gibberish/person names
        clean_topic = re.sub(r'[.,;:]+$', '', topic).strip()
        clean_topic = re.sub(r'\s+', ' ', clean_topic)
        is_valid = False
        validation_message = "Unable to validate this topic. Please enter a clear, learnable subject, skill, or concept."
    
    return clean_topic, num_resources, message.strip(), num_steps, is_valid, validation_message

@app.post("/api/learn", response_model=LearningPlanResponse)
async def create_learning_experience(request: LearningRequest):
    """
    OPTIMIZED endpoint: Uses combined AI calls to reduce latency and cost by 50%.
    Takes a learning topic and returns:
    1. A structured learning plan (generated by GPT)
    2. Real examples scraped from the web
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    
    original_topic = request.topic.strip()
    
    # OPTIMIZATION: Combined extraction, validation, and number validation in one call
    clean_topic, num_resources, resource_message, num_steps, is_valid, validation_message = extract_validate_and_prepare_topic(original_topic)
    
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=validation_message or "This doesn't seem like a valid learning topic. Please enter something specific you want to learn."
        )
    
    try:
        # OPTIMIZATION: Combined plan and resource generation in one call (reduces from 2 calls to 1)
        plan, examples = await generate_plan_and_resources(clean_topic, num_steps=num_steps, num_examples=num_resources)
        
        return LearningPlanResponse(
            plan=plan,
            examples=examples,
            message=resource_message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating learning experience: {str(e)}")

async def expand_learning_step(topic: str, step_title: str, step_description: str) -> Dict[str, any]:
    """
    Generate additional clarity and context for a learning step without repeating existing information.
    Focuses on gaps, nuances, and practical details that weren't covered in the main step.
    """
    try:
        prompt = f"""Topic: {topic}
Step: {step_title} - {step_description}

Complementary details. JSON:
{{
  "additionalContext": "Brief context...",
  "practicalDetails": ["Detail 1", "Detail 2"],
  "importantConsiderations": ["Consideration 1"],
  "realWorldExamples": ["Example 1"],
  "potentialChallenges": ["Challenge 1: Solution description", "Challenge 2: Solution description"]
}}

IMPORTANT: All fields must be arrays of STRINGS only. potentialChallenges should be strings like "Challenge: Solution", not objects.

JSON only:"""

        result = call_ai(prompt, "Expert educator. JSON only.", max_tokens=350, temperature=0.5)
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

