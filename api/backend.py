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
    topic_lower = topic.lower().strip()
    words = topic_lower.split()
    
    # Quick sanity checks (no API call needed)
    if len(words) < 1:
        return (False, "Please enter a topic you want to learn about.")
    
    if len(topic) < 2:
        return (False, "Topic is too short. Please provide more details.")
    
    if len(topic) > 200:
        return (False, "Topic is too long. Please keep it under 200 characters.")
    
    # Check for repeated characters or obvious nonsense
    if len(set(topic_lower.replace(' ', ''))) < 3:
        return (False, "Please provide a meaningful topic, not just repeated characters.")
    
    # Check for only special characters or numbers
    only_special_chars = re.compile(r'^[^a-zA-Z\s]{2,}$')
    if only_special_chars.match(topic_lower):
        return (False, "Please use words to describe what you want to learn, not just symbols or numbers.")
    
    # Use AI to validate the topic - it will intelligently catch all edge cases
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

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at determining if a topic is valid for learning. Use common sense to detect gibberish, abstract concepts, and nonsensical inputs. Be strict - only approve topics that are real, specific, and learnable."
                },
                {"role": "user", "content": validation_prompt}
            ],
            max_tokens=80,  # Enough for reason + suggestion
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
        "app": "Learning Experience App"
    }

async def generate_learning_plan(topic: str, num_steps: int = None) -> List[Dict[str, str]]:
    """
    Use GPT to generate a structured learning plan for the given topic.
    Returns a list of steps with titles and descriptions.
    """
    try:
        # Determine number of steps
        if num_steps is None:
            step_count = "5-7"
            step_instruction = "Provide a practical, actionable plan with 5-7 steps."
        else:
            step_count = str(num_steps)
            step_instruction = f"Provide exactly {num_steps} steps. Make sure the plan is comprehensive but fits within {num_steps} steps."
        
        prompt = f"""Learning plan for: {topic}

{step_instruction} JSON array: [{{"title": "Step 1", "description": "..."}}, ...]

JSON only:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Expert educator. JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,  # Further reduced for speed
            temperature=0.6  # Lower for faster responses
        )
        
        result = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        result = result.strip()
        
        plan = json.loads(result)
        return plan
    except Exception as e:
        print(f"Error generating learning plan: {e}")
        # Fallback to a simple plan structure
        return [
            {"title": f"Step 1: Research {topic}", "description": f"Start by researching the basics of {topic} online."},
            {"title": f"Step 2: Find Examples", "description": f"Look for real-world examples of {topic} to understand practical applications."},
            {"title": f"Step 3: Practice", "description": f"Try applying what you've learned about {topic} through hands-on practice."}
        ]

async def scrape_examples(topic: str, num_examples: int = 3) -> List[Dict[str, str]]:
    """
    Generate learning resources using AI (fast and reliable).
    Falls back to web scraping only if AI fails.
    """
    examples = []
    
    # OPTIMIZATION: Use AI first (faster and more reliable than web scraping)
    try:
        # Use GPT to suggest relevant resources quickly
        prompt = f"""Suggest {num_examples} real learning resources for: {topic}

Provide actual educational websites, documentation, tutorials, or courses. Use real URLs only.

JSON: [{{"title": "Name", "url": "https://real-site.com", "description": "Brief"}}, ...]

JSON only:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Expert at finding real learning resources. Provide actual website URLs only."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.5
        )
        
        result = response.choices[0].message.content.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        result = result.strip()
        
        ai_resources = json.loads(result)
        for resource in ai_resources:
            if len(examples) >= num_examples:
                break
            
            url = resource.get("url", "")
            title = resource.get("title", f"{topic} Resource")
            
            # Simple validation: must be a valid HTTP(S) URL
            if url and url.startswith("http"):
                examples.append({
                    "title": title,
                    "url": url,
                    "description": resource.get("description", f"Learn about {topic}")
                })
    except Exception as e:
        print(f"Error generating AI resources: {e}")
    
    # Only try web scraping if we don't have enough examples (quick single attempt)
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
            
            fallback_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Expert at finding educational resources. Provide real website URLs only."
                    },
                    {"role": "user", "content": fallback_prompt}
                ],
                max_tokens=200,
                temperature=0.5
            )
            
            fallback_result = fallback_response.choices[0].message.content.strip()
            if fallback_result.startswith("```json"):
                fallback_result = fallback_result[7:]
            if fallback_result.startswith("```"):
                fallback_result = fallback_result[3:]
            if fallback_result.endswith("```"):
                fallback_result = fallback_result[:-3]
            fallback_result = fallback_result.strip()
            
            fallback_resources = json.loads(fallback_result)
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
    
    return examples[:num_examples]

def extract_topic_and_num_resources(topic: str) -> tuple[str, int, str, int]:
    """
    Extract the clean topic, requested number of resources, and requested number of steps from user input.
    Uses AI to determine if the requested numbers are reasonable.
    Handles patterns like "topic. Can you give me 10 resources" or "topic (5 examples)" or "give me 3 steps"
    Returns (clean_topic, num_resources, message, num_steps)
    """
    import re
    
    # Default numbers
    num_resources = 5
    num_steps = None  # None means use default (5-7 steps)
    message = ""
    requested_num = None
    requested_steps = None
    
    # Look for patterns like "10 resources", "5 examples", "give me 8", "3 steps", etc.
    resource_patterns = [
        r'(\d+)\s*(?:resources?|examples?|links?|sources?)',
        r'give\s+me\s+(\d+)\s*(?:resources?|examples?)',
        r'(\d+)\s+to\s+start',
        r'(\d+)\s+i\s+can',
        r'(\d+)\s+to\s+begin',
    ]
    
    step_patterns = [
        r'(\d+)\s*steps?',
        r'give\s+me\s+(\d+)\s*steps?',
        r'(\d+)\s*step\s+plan',
    ]
    
    # First, look for step requests
    for pattern in step_patterns:
        match = re.search(pattern, topic.lower())
        if match:
            try:
                requested_steps = int(match.group(1))
                # Remove the step request part from the topic
                topic = re.sub(pattern, '', topic, flags=re.IGNORECASE).strip()
                break
            except ValueError:
                continue
    
    # Then look for resource requests
    for pattern in resource_patterns:
        match = re.search(pattern, topic.lower())
        if match:
            try:
                requested_num = int(match.group(1))
                # Remove the resource request part from the topic
                topic = re.sub(pattern, '', topic, flags=re.IGNORECASE).strip()
                break
            except ValueError:
                continue
    
    # Clean up the topic: remove trailing punctuation, extra spaces
    topic = re.sub(r'[.,;:]+$', '', topic).strip()
    topic = re.sub(r'\s+', ' ', topic)
    
    # Use AI to determine if the requested number is reasonable
    if requested_num is not None:
        try:
            validation_prompt = f"""A user requested {requested_num} resources/examples for learning.

Is this reasonable? Consider if it's too few, too many, or just right for effective learning.

Respond with ONLY:
- "REASONABLE: {requested_num}" if reasonable
- "TOO_MANY: [suggested_number]" if too many (suggest alternative)
- "TOO_FEW: [suggested_number]" if too few (suggest minimum)

Your response:"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Expert at determining reasonable resource counts for learning. Use common sense."
                    },
                    {"role": "user", "content": validation_prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip().upper()
            
            if result.startswith("REASONABLE"):
                num_resources = requested_num
            elif result.startswith("TOO_MANY"):
                suggested_match = re.search(r'(\d+)', result)
                if suggested_match:
                    num_resources = int(suggested_match.group(1))
                    message = f"You requested {requested_num} resources, but that might be overwhelming. I'll provide {num_resources} high-quality resources instead."
                else:
                    num_resources = requested_num  # Use requested if can't parse
            elif result.startswith("TOO_FEW"):
                suggested_match = re.search(r'(\d+)', result)
                if suggested_match:
                    num_resources = int(suggested_match.group(1))
                    message = f"You requested {requested_num} resources, but that's not enough. I'll provide {num_resources} resources instead."
                else:
                    num_resources = requested_num  # Use requested if can't parse
            else:
                num_resources = requested_num  # Default to requested
        except Exception as e:
            print(f"Error validating resource count: {e}")
            num_resources = requested_num  # Fallback to requested
    
    return topic, num_resources, message.strip(), num_steps

@app.post("/api/learn", response_model=LearningPlanResponse)
async def create_learning_experience(request: LearningRequest):
    """
    Main endpoint: Takes a learning topic and returns:
    1. A structured learning plan (generated by GPT)
    2. Real examples scraped from the web
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    
    original_topic = request.topic.strip()
    
    # Extract clean topic, requested number of resources, and requested number of steps
    clean_topic, num_resources, resource_message, num_steps = extract_topic_and_num_resources(original_topic)
    
    # Use clean topic for validation and plan generation
    is_valid, validation_message = validate_learning_topic(clean_topic)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=validation_message or "This doesn't seem like a valid learning topic. Please enter something specific you want to learn."
        )
    
    try:
        # Generate learning plan and scrape examples in parallel for speed
        # Use clean topic for plan generation, pass num_steps if specified
        plan_task = generate_learning_plan(clean_topic, num_steps=num_steps)
        examples_task = scrape_examples(clean_topic, num_examples=num_resources)
        
        # Run both in parallel - optimizations ensure fast completion
        plan, examples = await asyncio.gather(plan_task, examples_task)
        
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

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Expert educator. JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=350,  # Optimized for speed
            temperature=0.5  # Lower for faster responses
        )
        
        result = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        result = result.strip()
        
        expanded = json.loads(result)
        
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

