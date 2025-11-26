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

async def generate_learning_plan(topic: str) -> List[Dict[str, str]]:
    """
    Use GPT to generate a structured learning plan for the given topic.
    Returns a list of steps with titles and descriptions.
    """
    try:
        prompt = f"""Create a step-by-step learning plan for someone who wants to learn about: {topic}

Provide a practical, actionable plan with 5-7 steps. For each step, include:
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
    Uses DuckDuckGo search to find relevant articles, tutorials, or resources.
    """
    examples = []
    
    try:
        # Use DuckDuckGo HTML search (no API key needed)
        search_query = f"{topic} examples tutorial guide"
        search_url = f"https://html.duckduckgo.com/html/?q={search_query.replace(' ', '+')}"
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as http_client:
            # Set headers to appear as a browser
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = await http_client.get(search_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find search result links
            results = soup.find_all('a', class_='result__a', limit=num_examples)
            
            for result in results:
                title = result.get_text(strip=True)
                url = result.get('href', '')
                
                # Clean up DuckDuckGo redirect URLs
                if url.startswith('/l/?kh=') or 'uddg=' in url:
                    # Extract actual URL from DuckDuckGo redirect
                    try:
                        if 'uddg=' in url:
                            # Parse the redirect URL to get the actual destination
                            parts = url.split('uddg=')
                            if len(parts) > 1:
                                encoded_url = parts[1].split('&')[0]
                                actual_url = unquote(encoded_url)
                            else:
                                actual_url = url
                        else:
                            actual_url = url
                    except Exception as e:
                        print(f"Error parsing URL: {e}")
                        actual_url = url
                else:
                    actual_url = url
                
                if title and actual_url:
                    examples.append({
                        "title": title,
                        "url": actual_url,
                        "description": f"Learn more about {topic} with this resource"
                    })
        
        # If we didn't get enough examples, try a different approach
        if len(examples) < num_examples:
            # Use a simpler search approach
            try:
                # Try searching for GitHub examples, tutorials, etc.
                github_query = f"{topic} examples site:github.com"
                github_url = f"https://html.duckduckgo.com/html/?q={github_query.replace(' ', '+')}"
                
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as http_client:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                    response = await http_client.get(github_url, headers=headers)
                    soup = BeautifulSoup(response.text, 'lxml')
                    results = soup.find_all('a', class_='result__a', limit=num_examples - len(examples))
                    
                    for result in results:
                        title = result.get_text(strip=True)
                        url = result.get('href', '')
                        if title and url and len(examples) < num_examples:
                            examples.append({
                                "title": title,
                                "url": url,
                                "description": f"Real-world example of {topic}"
                            })
            except Exception as e:
                print(f"Error in secondary search: {e}")
        
    except Exception as e:
        print(f"Error scraping examples: {e}")
        # Return fallback examples
        examples = [
            {
                "title": f"{topic} - Wikipedia",
                "url": f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}",
                "description": f"Learn the basics of {topic} on Wikipedia"
            },
            {
                "title": f"{topic} Tutorial",
                "url": f"https://www.google.com/search?q={topic.replace(' ', '+')}+tutorial",
                "description": f"Find tutorials about {topic}"
            }
        ]
    
    return examples[:num_examples]

@app.post("/api/learn", response_model=LearningPlanResponse)
async def create_learning_experience(request: LearningRequest):
    """
    Main endpoint: Takes a learning topic and returns:
    1. A structured learning plan (generated by GPT)
    2. Real examples scraped from the web
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    
    topic = request.topic.strip()
    
    # Validate the topic using AI to catch all edge cases
    is_valid, validation_message = validate_learning_topic(topic)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=validation_message or "This doesn't seem like a valid learning topic. Please enter something specific you want to learn, like 'Python programming' or 'Cooking Italian food'."
        )
    
    try:
        # Generate learning plan and scrape examples in parallel for speed
        plan_task = generate_learning_plan(topic)
        examples_task = scrape_examples(topic, num_examples=5)
        
        plan, examples = await asyncio.gather(plan_task, examples_task)
        
        return LearningPlanResponse(
            plan=plan,
            examples=examples
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating learning experience: {str(e)}")

# Keep old endpoints for backward compatibility (can remove later)
class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
def chat(request: ChatRequest):
    """Legacy chat endpoint - kept for compatibility"""
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    
    try:
        user_message = request.message
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful learning assistant"},
                {"role": "user", "content": user_message}
            ]
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling OpenAI API: {str(e)}")
