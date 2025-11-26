from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
import httpx
import asyncio
import re
from urllib.parse import unquote
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

Check if this is a valid topic someone can learn about:

1. Is it a real, meaningful topic? (not gibberish like "gfdnjlg nfgdsgdnjklgfnjs")
2. Can someone actually learn about this? (not abstract concepts like "the meaning of life" or "what is love")
3. Is it specific enough to create a learning plan? (not too vague like "stuff" or "things")
4. Does it make sense as a learning subject? (not nonsensical combinations)

Examples of VALID topics:
- "Python programming" ✅
- "Machine Learning" ✅
- "Cooking Italian food" ✅
- "Web Development" ✅
- "Spanish language" ✅
- "Photography" ✅

Examples of INVALID topics:
- "gfdnjlg nfgdsgdnjklgfnjs" ❌ (gibberish/nonsense)
- "the meaning of life" ❌ (too abstract/philosophical)
- "asdfghjkl" ❌ (random keyboard mashing)
- "123456" ❌ (just numbers)
- "what is love" ❌ (abstract concept, not a learnable skill)
- "stuff" ❌ (too vague)

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
            return (False, explanation if explanation else "This doesn't seem like a valid learning topic. Please enter something specific you want to learn, like 'Python programming' or 'Cooking Italian food'.")
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
        
        prompt = f"""Create a step-by-step learning plan for someone who wants to learn about: {topic}

{step_instruction} For each step, include:
- A clear title
- A detailed description of what to do
- Why this step is important

Format your response as a JSON array of objects, each with "title" and "description" fields.
Example format:
[
  {{"title": "Step 1: Understand the Basics", "description": "Start by learning the fundamental concepts..."}},
  {{"title": "Step 2: Practice with Examples", "description": "Find real-world examples and try them yourself..."}}
]

Your response (JSON only, no markdown):"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educator who creates clear, practical learning plans. Always respond with valid JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
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
    Scrape the web to find real examples related to the learning topic.
    Uses multiple strategies to find relevant articles, tutorials, or resources.
    """
    examples = []
    
    # Try multiple search strategies
    search_strategies = [
        # Strategy 1: DuckDuckGo HTML search
        {
            "query": f"{topic} tutorial guide examples",
            "url": f"https://html.duckduckgo.com/html/?q={topic.replace(' ', '+')}+tutorial+guide",
            "selectors": [
                ('a', {'class': 'result__a'}),
                ('a', {'class': 'result-link'}),
                ('a', {'class': 'web-result'}),
                ('a', {'href': lambda x: x and x.startswith('/l/?')}),
            ]
        },
        # Strategy 2: GitHub search
        {
            "query": f"{topic} site:github.com",
            "url": f"https://html.duckduckgo.com/html/?q={topic.replace(' ', '+')}+site%3Agithub.com",
            "selectors": [
                ('a', {'class': 'result__a'}),
                ('a', {'href': lambda x: x and 'github.com' in x}),
            ]
        },
        # Strategy 3: General web search
        {
            "query": f"{topic} examples",
            "url": f"https://html.duckduckgo.com/html/?q={topic.replace(' ', '+')}+examples",
            "selectors": [
                ('a', {'class': 'result__a'}),
                ('a', {'class': 'result-link'}),
            ]
        }
    ]
    
    for strategy in search_strategies:
        if len(examples) >= num_examples:
            break
            
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as http_client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
                
                response = await http_client.get(strategy["url"], headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Try different selectors
                results = []
                for selector, attrs in strategy["selectors"]:
                    found = soup.find_all(selector, attrs, limit=num_examples * 2)
                    if found:
                        results = found
                        break
                
                # If no results with class selectors, try finding links in result containers
                if not results:
                    # Look for result containers and find links within them
                    result_containers = soup.find_all(['div', 'article', 'section'], class_=lambda x: x and ('result' in str(x).lower() or 'web' in str(x).lower()))
                    for container in result_containers[:num_examples * 2]:
                        link = container.find('a', href=True)
                        if link:
                            results.append(link)
                
                for result in results:
                    if len(examples) >= num_examples:
                        break
                    
                    title = result.get_text(strip=True)
                    url = result.get('href', '')
                    
                    if not title or not url:
                        continue
                    
                    # Skip internal DuckDuckGo links
                    if url.startswith('/') and not url.startswith('/l/?'):
                        continue
                    
                    # Clean up DuckDuckGo redirect URLs
                    if url.startswith('/l/?') or 'uddg=' in url:
                        try:
                            if 'uddg=' in url:
                                parts = url.split('uddg=')
                                if len(parts) > 1:
                                    encoded_url = parts[1].split('&')[0]
                                    actual_url = unquote(encoded_url)
                                    # Validate it's a real URL
                                    if actual_url.startswith('http'):
                                        url = actual_url
                                    else:
                                        continue
                                else:
                                    continue
                            else:
                                # Try to extract from query params
                                from urllib.parse import parse_qs, urlparse
                                parsed = urlparse(url)
                                params = parse_qs(parsed.query)
                                if 'uddg' in params:
                                    url = unquote(params['uddg'][0])
                                else:
                                    continue
                        except Exception as e:
                            print(f"Error parsing redirect URL: {e}")
                            continue
                    
                    # Validate URL
                    if not url.startswith('http'):
                        continue
                    
                    # Avoid duplicates
                    if any(ex['url'] == url for ex in examples):
                        continue
                    
                    examples.append({
                        "title": title[:100],  # Limit title length
                        "url": url,
                        "description": f"Learn more about {topic} with this resource"
                    })
                    
        except Exception as e:
            print(f"Error in search strategy: {e}")
            continue
    
    # If we still don't have enough examples, generate some using AI
    if len(examples) < num_examples:
        try:
            # Use GPT to suggest relevant resources
            prompt = f"""Suggest {num_examples - len(examples)} specific, real online resources (websites, tutorials, courses, documentation) for learning about: {topic}

For each resource, provide:
- A specific website/tool name
- A realistic URL (can be a search URL if specific URL unknown)
- A brief description

Format as JSON array:
[
  {{"title": "Resource Name", "url": "https://example.com", "description": "Brief description"}},
  ...
]

Your response (JSON only, no markdown):"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at finding learning resources. Suggest real, specific websites, tutorials, courses, or documentation that exist online."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
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
                # Avoid duplicates
                if not any(ex['url'] == resource.get('url', '') for ex in examples):
                    examples.append({
                        "title": resource.get("title", f"{topic} Resource"),
                        "url": resource.get("url", f"https://www.google.com/search?q={topic.replace(' ', '+')}"),
                        "description": resource.get("description", f"Learn about {topic}")
                    })
        except Exception as e:
            print(f"Error generating AI resources: {e}")
    
    # Final fallback if we still don't have enough
    if len(examples) == 0:
        examples = [
            {
                "title": f"{topic} - Search Results",
                "url": f"https://www.google.com/search?q={topic.replace(' ', '+')}+tutorial",
                "description": f"Find tutorials and resources about {topic}"
            },
            {
                "title": f"{topic} - Wikipedia",
                "url": f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}",
                "description": f"Learn the basics of {topic} on Wikipedia"
            },
            {
                "title": f"{topic} - YouTube Tutorials",
                "url": f"https://www.youtube.com/results?search_query={topic.replace(' ', '+')}+tutorial",
                "description": f"Watch video tutorials about {topic}"
            }
        ]
    
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
            validation_prompt = f"""A user requested {requested_num} resources/examples for learning about a topic.

Is this a reasonable number? Consider:
- Too few (1-2): Not enough variety
- Reasonable (3-15): Good for learning, manageable to review
- Many (16-30): Still reasonable but might be overwhelming
- Too many (31+): Likely too overwhelming, hard to process, may not be useful

Respond with ONLY:
- "REASONABLE: {requested_num}" if it's reasonable
- "TOO_MANY: [suggested_number]" if it's too many (suggest a reasonable alternative like 15 or 20)
- "TOO_FEW: [suggested_number]" if it's too few (suggest at least 3)

Your response:"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at determining reasonable resource counts for learning. Use common sense - too many resources can be overwhelming and counterproductive."
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
                # Extract suggested number
                suggested_match = re.search(r'(\d+)', result)
                if suggested_match:
                    num_resources = int(suggested_match.group(1))
                    message = f"You requested {requested_num} resources, but that might be overwhelming. I'll provide {num_resources} high-quality resources instead."
                else:
                    num_resources = 20  # Default cap
                    message = f"You requested {requested_num} resources, but that's too many to be useful. I'll provide {num_resources} high-quality resources instead."
            elif result.startswith("TOO_FEW"):
                suggested_match = re.search(r'(\d+)', result)
                if suggested_match:
                    num_resources = int(suggested_match.group(1))
                    message = f"You requested {requested_num} resources, but that's not enough. I'll provide {num_resources} resources instead."
                else:
                    num_resources = 5
            else:
                # Fallback: use requested number but cap at 30
                num_resources = min(requested_num, 30)
                if requested_num > 30:
                    message = f"You requested {requested_num} resources. I'll provide {num_resources} high-quality resources to keep it manageable."
        except Exception as e:
            print(f"Error validating resource count: {e}")
            # Fallback: use requested number but cap at 30
            if requested_num:
                num_resources = min(requested_num, 30)
                if requested_num > 30:
                    message += f"You requested {requested_num} resources. I'll provide {num_resources} high-quality resources to keep it manageable."
    
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
            detail=validation_message or "This doesn't seem like a valid learning topic. Please enter something specific you want to learn, like 'Python programming' or 'Cooking Italian food'."
        )
    
    try:
        # Generate learning plan and scrape examples in parallel for speed
        # Use clean topic for plan generation, pass num_steps if specified
        plan_task = generate_learning_plan(clean_topic, num_steps=num_steps)
        examples_task = scrape_examples(clean_topic, num_examples=num_resources)
        
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
        prompt = f"""The user is learning about: {topic}

They want additional clarity on this step:
Title: {step_title}
Description: {step_description}

IMPORTANT: Do NOT repeat information already in the step title or description. Instead, provide:
1. Additional context and nuances that weren't mentioned
2. Practical implementation details and how-to specifics
3. Important considerations or prerequisites they should know
4. Real-world applications or examples specific to this step
5. Potential challenges and how to overcome them

Focus on filling gaps and providing clarity that complements (not repeats) the existing step.

Format your response as JSON with this structure:
{{
  "additionalContext": "Important context, nuances, or background information not covered in the main step...",
  "practicalDetails": ["Specific how-to detail 1", "Specific how-to detail 2", "Specific how-to detail 3"],
  "importantConsiderations": ["Consideration 1", "Consideration 2"],
  "realWorldExamples": ["Example 1", "Example 2"],
  "potentialChallenges": ["Challenge 1 with solution", "Challenge 2 with solution"]
}}

Your response (JSON only, no markdown):"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educator who provides detailed, actionable learning guidance. Always respond with valid JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
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

