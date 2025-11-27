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

async def validate_url(resource: dict, topic: str) -> dict | None:
    """Validate a single URL and return resource dict if valid, None if invalid.
    Checks both HTTP status and page content to ensure it's a working page with actual content."""
    url = resource.get("url", "")
    if not url or not url.startswith("http"):
        return None
    
    # Verify URL exists and has valid content
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as http_client:
            # Get the page content to verify it's not an error page
            response = await http_client.get(url)
            
            # First check: HTTP status code must be 2xx or 3xx
            status = response.status_code
            if status >= 400:
                # 4xx or 5xx - URL is broken, reject it
                return None
            
            # Second check: Use AI to verify page content is not an error page (only for HTML pages)
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" in content_type:
                # Only check content for HTML pages
                try:
                    # Get a sample of the page content
                    content_sample = response.text[:10000]
                    content_lower = content_sample.lower()
                    
                    # Intelligent check for YouTube videos (no hardcoded patterns)
                    is_youtube = "youtube.com" in url.lower() or "youtu.be" in url.lower()
                    if is_youtube:
                        # Use intelligent heuristics to determine if video is available
                        content_size = len(content_sample)
                        
                        # Heuristic 1: Content size analysis
                        # Available YouTube videos have substantial HTML (player, description, comments, metadata)
                        # Unavailable videos typically have minimal HTML (just footer/navigation)
                        # Typical available video pages are 100KB+ with full content
                        # Unavailable videos are usually < 50KB with mostly footer/navigation
                        
                        # Heuristic 2: Content structure analysis
                        # Available videos have video-related elements (player, metadata, description, comments)
                        # Count potential video-related elements vs generic page elements
                        # Look for structural indicators of a video page vs error page
                        
                        # Heuristic 3: Content density
                        # Available videos have rich content (descriptions, comments, related videos)
                        # Unavailable videos have sparse content (mostly navigation/footer)
                        # Calculate ratio of meaningful content vs boilerplate
                        
                        # Quick size-based rejection for obviously unavailable videos
                        if content_size < 20000:
                            # Extremely small page - definitely unavailable (even error pages are usually larger)
                            return None
                        
                        # For larger pages, use AI to analyze content structure and determine if video is available
                        # This is more reliable than pattern matching and handles all edge cases
                        youtube_analysis_prompt = f"""Analyze this YouTube page to determine if the video is available and playable.

URL: {url}
Page size: {content_size} bytes
Content sample (first 8000 chars): {content_sample[:8000]}

Determine if this YouTube video page contains:
1. A playable video player
2. Video metadata (title, description, etc.)
3. Video content structure (not just navigation/footer)

A page with ONLY navigation, footer, or error messages (even if HTML loads successfully) means the video is UNAVAILABLE.

Respond with ONLY:
- "AVAILABLE" if the video appears to be playable and accessible
- "UNAVAILABLE" if the video is removed, private, deleted, or the page only shows navigation/footer

Response:"""

                        youtube_analysis = call_ai(
                            youtube_analysis_prompt,
                            "Expert at analyzing YouTube pages. Understand that a page can load HTML successfully but the video itself might be unavailable. Check for actual video player and content, not just page structure.",
                            max_tokens=10,
                            temperature=0.1
                        )
                        
                        if youtube_analysis.upper().strip().startswith("UNAVAILABLE"):
                            # AI determined video is unavailable
                            return None
                        
                        # If AI says available or response is unclear, continue with normal validation
                    
                    # Use AI to determine if this page's primary resource is accessible and usable
                    validation_prompt = f"""Analyze this webpage:

URL: {url}
Content sample: {content_sample[:8000]}

Determine if this page's PRIMARY RESOURCE is accessible and usable.

CRITICAL DISTINCTION (understand this concept):
- A page can have HTML content (navigation, headers, layout) but the PRIMARY RESOURCE might be unavailable
- For video pages: The page HTML might load, but the VIDEO itself might be unavailable
- For document pages: The page might load, but the DOCUMENT content might be unavailable
- For course pages: The page might load, but the COURSE content might be unavailable
- For general pages: The page content itself is the resource

IMPORTANT RULES (follow these):
- For video pages (like YouTube): Check if the VIDEO is playable, not just if the page HTML loads. If the video is unavailable, removed, private, or says "not available anymore", respond "INVALID". If the video appears to be available and playable, respond "VALID"
- For document/course pages: Check if the actual content is accessible, not just if the page loads
- If the page says the primary resource is unavailable, removed, private, deleted, or not accessible, respond "INVALID"
- A page with navigation/headers but an unavailable primary resource is INVALID
- Only respond "VALID" if the primary resource is actually accessible and usable
- Be lenient for general content pages - when in doubt, choose "VALID"
- For video pages: Be strict about detecting errors (unavailable, removed, private), but if the video appears available, approve it

Respond with ONLY:
- "VALID" if the primary resource is accessible and usable
- "INVALID" if the primary resource is unavailable, removed, private, or not accessible

Response:"""

                    ai_result = call_ai(
                        validation_prompt,
                        "Expert at analyzing web pages. Understand the distinction between page HTML content and the actual resource availability. For video pages (like YouTube), be STRICT - check if the actual video is playable, not just if the page HTML loads. A page with navigation but an unavailable resource is invalid. For general pages, be lenient - approve when in doubt.",
                        max_tokens=20,
                        temperature=0.1
                    )
                    ai_result_upper = ai_result.upper().strip()
                    
                    # Check for explicit INVALID
                    if ai_result_upper.startswith("INVALID") and len(ai_result_upper) > 5:
                        # AI explicitly determined it's an error page
                        return None
                    # If response is unclear, include it anyway (lenient mode)
                except Exception:
                    # If AI check fails, but status is good, include it (better to show than block)
                    pass
            
            # URL passed all checks - it's valid
            return {
                "title": resource.get("title", f"{topic} Resource"),
                "url": url,
                "description": resource.get("description", f"Learn about {topic}")
            }
                
    except httpx.HTTPStatusError as e:
        # httpx may raise this for some 4xx/5xx responses
        if hasattr(e, 'response'):
            status = e.response.status_code
            if 200 <= status < 400:
                return {
                    "title": resource.get("title", f"{topic} Resource"),
                    "url": url,
                    "description": resource.get("description", f"Learn about {topic}")
                }
        # 4xx or 5xx - broken URL, reject it
        return None
    except (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError):
        # Network errors - can't verify, but might work for users
        return {
            "title": resource.get("title", f"{topic} Resource"),
            "url": url,
            "description": resource.get("description", f"Learn about {topic}")
        }
    except Exception:
        # Other unexpected errors - can't verify, skip it
        return None

async def generate_plan_and_resources(topic: str, num_steps: int = None, num_examples: int = 3) -> tuple[List[Dict[str, str]], List[Dict[str, str]]]:
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
        
        # Request more resources upfront to account for validation failures
        # Request 2x the needed amount to ensure we get enough valid ones
        resources_to_generate = max(num_examples * 2, 8)  # At least 8, or 2x requested
        
        # Single AI call that generates both plan and resources
        combined_prompt = f"""Learning topic: {topic}

Generate both:
1. A structured learning plan: {step_instruction}
2. {resources_to_generate} diverse learning resources from DIFFERENT platforms (mix of videos, articles, courses, documentation)

IMPORTANT - DIVERSITY REQUIRED:
- Include a VARIETY of resource types: YouTube videos, articles, courses, documentation, tutorials
- Use DIFFERENT platforms - don't repeat the same platform multiple times
- Include YouTube videos when relevant (they're great for learning!)
- Mix of formats: videos, written guides, interactive courses, documentation

Platforms to consider (use variety, not just one):
- YouTube: https://www.youtube.com/watch?v=... (include relevant videos!)
- Khan Academy, Coursera, edX (courses)
- Wikipedia, Medium, personal blogs (articles)
- GitHub (code examples, projects)
- MDN Web Docs, official documentation sites
- Reddit, forums (community discussions)
- Other educational sites specific to the topic

CRITICAL: Only provide URLs that you KNOW exist and are accessible. Do NOT make up URLs or guess URL structures.

Respond in JSON format:
{{
  "plan": [{{"title": "Step 1", "description": "..."}}, ...],
  "resources": [{{"title": "Name", "url": "https://real-site.com", "description": "Brief"}}, ...]
}}

JSON only:"""

        result = call_ai(
            combined_prompt,
            "Expert educator and resource finder. Generate diverse learning resources from different platforms. Include a mix of YouTube videos, articles, courses, and documentation. Prioritize variety - use different platforms and resource types. Only provide URLs that you KNOW exist and are accessible. Do NOT make up URLs or guess URL structures.",
            max_tokens=800,
            temperature=0.7
        )
        data = parse_json_response(result)
        
        plan = data.get("plan", [])
        resources = data.get("resources", [])
        
        print(f"[DEBUG] Topic: {topic}")
        print(f"[DEBUG] Requested num_examples: {num_examples}")
        print(f"[DEBUG] AI generated {len(resources)} resources")
        for i, res in enumerate(resources, 1):
            print(f"[DEBUG] Resource {i}: {res.get('title', 'No title')} - {res.get('url', 'No URL')}")
        
        # Process resources - validate URLs actually exist (in parallel for speed)
        validation_tasks = [validate_url(resource, topic) for resource in resources[:num_examples]]
        validation_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        # Collect valid results
        examples = []
        for i, result in enumerate(validation_results, 1):
            if isinstance(result, Exception):
                print(f"[DEBUG] Validation {i} raised exception: {type(result).__name__}")
            elif result and isinstance(result, dict):
                examples.append(result)
                print(f"[DEBUG] Validation {i} PASSED: {result.get('title', 'Unknown')}")
            else:
                print(f"[DEBUG] Validation {i} FAILED: Resource rejected")
        
        print(f"[DEBUG] After validation: {len(examples)} valid resources out of {len(resources[:num_examples])} checked")
        
        # Determine minimum resources needed (at least 3, or user's request if less)
        min_resources = min(3, num_examples) if num_examples < 3 else 3
        
        # Fallback if plan is empty
        if not plan:
            plan = [
                {"title": f"Step 1: Research {topic}", "description": f"Start by researching the basics of {topic} online."},
                {"title": f"Step 2: Find Examples", "description": f"Look for real-world examples of {topic} to understand practical applications."},
                {"title": f"Step 3: Practice", "description": f"Try applying what you've learned about {topic} through hands-on practice."}
            ]
        
        # If we don't have enough valid resources, try once more with a larger batch
        if len(examples) < min_resources:
            print(f"[DEBUG] Only {len(examples)} valid resources, need at least {min_resources}. Trying one more time with larger batch...")
            
            try:
                # Generate a larger batch (enough to get min_resources even with 50% failure rate)
                needed = (min_resources - len(examples)) * 3  # Request 3x to account for failures
                fallback_prompt = f"""Suggest {needed} diverse educational resources for learning about: {topic}

Provide a VARIETY of resources from DIFFERENT platforms:
- YouTube videos (include relevant videos!)
- Articles (Wikipedia, Medium, blogs)
- Courses (Coursera, edX, Khan Academy)
- Documentation (official docs, MDN, etc.)
- Community resources (Reddit, forums)

Use DIFFERENT platforms - don't repeat the same one. Avoid URLs already suggested.

JSON: [{{"title": "Resource Name", "url": "https://real-site.com", "description": "Brief"}}, ...]

JSON only:"""
                
                fallback_result = call_ai(fallback_prompt, "Expert at finding diverse educational resources. Include a mix of YouTube videos, articles, courses, and documentation from different platforms. Prioritize variety.", max_tokens=600, temperature=0.7)
                fallback_resources = parse_json_response(fallback_result)
                
                print(f"[DEBUG] Fallback generated {len(fallback_resources)} resources")
                
                # Skip resources we already have
                existing_urls = {ex.get('url') for ex in examples}
                new_resources = [r for r in fallback_resources if r.get('url') and r.get('url').startswith('http') and r.get('url') not in existing_urls]
                
                # Validate new URLs in parallel
                validation_tasks = [validate_url(resource, topic) for resource in new_resources]
                validation_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
                
                for i, result in enumerate(validation_results, 1):
                    if isinstance(result, Exception):
                        print(f"[DEBUG] Fallback validation {i} raised exception: {type(result).__name__}")
                    elif result and isinstance(result, dict):
                        examples.append(result)
                        print(f"[DEBUG] Fallback validation {i} PASSED: {result.get('title', 'Unknown')}")
                    else:
                        print(f"[DEBUG] Fallback validation {i} FAILED: Resource rejected")
                
                print(f"[DEBUG] After fallback: {len(examples)} valid resources")
                
                # If still not enough, include unvalidated resources to reach minimum
                if len(examples) < min_resources:
                    print(f"[DEBUG] Still below minimum - including unvalidated resources")
                    for resource in new_resources:
                        if len(examples) >= min_resources:
                            break
                        if resource.get("url") and resource.get("url").startswith("http") and resource.get('url') not in existing_urls:
                            examples.append({
                                "title": resource.get("title", f"{topic} Resource"),
                                "url": resource.get("url"),
                                "description": resource.get("description", f"Learn about {topic}")
                            })
                            existing_urls.add(resource.get('url'))
            except Exception as e:
                print(f"[DEBUG] Fallback failed with exception: {type(e).__name__}: {e}")
                pass
        
        return plan, examples
        
    except Exception as e:
        # Fallback
        plan = [
            {"title": f"Step 1: Research {topic}", "description": f"Start by researching the basics of {topic} online."},
            {"title": f"Step 2: Find Examples", "description": f"Look for real-world examples of {topic} to understand practical applications."},
            {"title": f"Step 3: Practice", "description": f"Try applying what you've learned about {topic} through hands-on practice."}
        ]
        examples = []
        
        # Determine minimum resources needed (at least 3, or user's request if less)
        min_resources = min(3, num_examples) if num_examples < 3 else 3
        
        # Try web scraping as fallback for resources only if we don't have enough
        if len(examples) < min_resources:
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
                    results = soup.find_all('a', class_='result__a', limit=min_resources - len(examples) + 2)
                    
                    for result in results:
                        if len(examples) >= min_resources:
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
        
        # If we don't have enough, try once more with a larger batch
        if len(examples) < min_resources:
            print(f"[DEBUG] Exception handler - Only {len(examples)} valid resources, need {min_resources}. Trying once more...")
            
            try:
                # Generate a larger batch (enough to get min_resources even with 50% failure rate)
                needed = (min_resources - len(examples)) * 3  # Request 3x to account for failures
                fallback_prompt = f"""Suggest {needed} diverse educational resources for learning about: {topic}

Provide a VARIETY of resources from DIFFERENT platforms:
- YouTube videos (include relevant videos!)
- Articles (Wikipedia, Medium, blogs)
- Courses (Coursera, edX, Khan Academy)
- Documentation (official docs, MDN, etc.)
- Community resources (Reddit, forums)

Use DIFFERENT platforms - don't repeat the same one.

JSON: [{{"title": "Resource Name", "url": "https://real-site.com", "description": "Brief"}}, ...]

JSON only:"""
                
                fallback_result = call_ai(fallback_prompt, "Expert at finding diverse educational resources. Include a mix of YouTube videos, articles, courses, and documentation from different platforms. Prioritize variety.", max_tokens=600, temperature=0.7)
                fallback_resources = parse_json_response(fallback_result)
                
                print(f"[DEBUG] Exception handler - Fallback generated {len(fallback_resources)} resources")
                
                # Skip resources we already have
                existing_urls = {ex.get('url') for ex in examples}
                new_resources = [r for r in fallback_resources if r.get('url') and r.get('url').startswith('http') and r.get('url') not in existing_urls]
                
                # Validate new URLs in parallel
                validation_tasks = [validate_url(resource, topic) for resource in new_resources]
                validation_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
                
                for i, result in enumerate(validation_results, 1):
                    if isinstance(result, Exception):
                        print(f"[DEBUG] Exception handler - Fallback validation {i} raised exception: {type(result).__name__}")
                    elif result and isinstance(result, dict):
                        examples.append(result)
                        print(f"[DEBUG] Exception handler - Fallback validation {i} PASSED: {result.get('title', 'Unknown')}")
                    else:
                        print(f"[DEBUG] Exception handler - Fallback validation {i} FAILED: Resource rejected")
                
                print(f"[DEBUG] Exception handler - After fallback: {len(examples)} valid resources")
                
                # If still not enough, include unvalidated resources to reach minimum
                if len(examples) < min_resources:
                    print(f"[DEBUG] Exception handler - Still below minimum - including unvalidated resources")
                    for resource in new_resources:
                        if len(examples) >= min_resources:
                            break
                        if resource.get("url") and resource.get("url").startswith("http") and resource.get('url') not in existing_urls:
                            examples.append({
                                "title": resource.get("title", f"{topic} Resource"),
                                "url": resource.get("url"),
                                "description": resource.get("description", f"Learn about {topic}")
                            })
                            existing_urls.add(resource.get('url'))
            except Exception as e:
                print(f"[DEBUG] Exception handler - Fallback failed with exception: {type(e).__name__}: {e}")
                pass
        
        final_count = len(examples[:num_examples])
        print(f"[DEBUG] Final result: Returning {final_count} resources (requested: {num_examples})")
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
4. Validate if the topic is learnable. REJECT if it fails ANY of these checks:
   - NOT gibberish, random characters, or nonsensical text
     → Examples to REJECT: "fgnrjk gnsogfd", "asdfgh", "xyz abc", "qwerty", any random letter combinations
     → If the input has no meaning, is just random characters, or doesn't form real words, set is_valid to false
   - NOT random words put together that make no sense or have no coherent meaning
     → Examples to REJECT: "time space coffee", "car tree music", "water fire sky", "book phone table"
     → If words are unrelated and don't form a coherent learning topic, set is_valid to false
     → The topic must be a REAL, MEANINGFUL subject that can actually be learned
   - NOT abstract philosophical concepts that can't be practically learned
   - NOT too vague (must be specific enough to create a learning plan)
   - NOT about a specific real person (politicians, celebrities, public figures, historical figures, etc.)
     → Examples to REJECT: "donald trump", "barack obama", "barak obama", "elon musk", "taylor swift", "albert einstein", "steve jobs"
     → Learning plans should be for SKILLS, SUBJECTS, or CONCEPTS, not personal biographies or people
     → If the input is a person's name (even with typos), set is_valid to false
     → If about a person, suggest learning about their field/domain instead (e.g., "business strategy" instead of "donald trump", "public speaking" instead of "barack obama")
5. If a resource number was requested, determine if it's reasonable (3-15 is reasonable)

All validation checks are equally important. Reject the topic if it fails ANY check:
- If the input is gibberish/random characters (like "fgnrjk gnsogfd"), reject it and set is_valid to false
- If the input is random words put together with no coherent meaning (like "time space coffee", "car tree music"), reject it and set is_valid to false
- If the input appears to be a person's name (first name + last name pattern, or a well-known single name), reject it and provide a helpful alternative suggestion
- If the input is too abstract, vague, or not learnable, reject it
- Only approve topics that are REAL, MEANINGFUL, COHERENT, learnable subjects, skills, or concepts
- The topic must make logical sense as something someone can actually learn about

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
            "Expert at extracting and validating learning topics. You MUST REJECT: (1) Gibberish/random characters - if input has no meaning or is just random letters, reject it. (2) Random word combinations with no coherent meaning - if words are unrelated and don't form a real learning topic (like 'time space coffee'), reject it. (3) Specific real person names - learning plans are for skills, subjects, and concepts only, never for people. (4) Abstract, vague, or unlearnable topics. Be EXTREMELY STRICT. Only approve topics that are REAL, MEANINGFUL, COHERENT, and actually learnable. When in doubt, REJECT the topic.",
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
        
        # Handle validation - default to False if not explicitly set to True
        # Be strict: only allow if AI explicitly says it's valid
        is_valid = data.get("is_valid", False)  # Changed default from True to False
        validation_message = data.get("validation_message", "").strip()
        
        # If validation message exists but is_valid is True, that's suspicious - be more strict
        if validation_message and is_valid:
            # If there's a validation message, it usually means there's an issue
            # Only allow if message is empty or clearly indicates it's valid
            if validation_message.lower() not in ["", "valid", "ok"]:
                is_valid = False
        
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

        result = call_ai(prompt, "Expert educator who provides step-specific, tailored guidance. Generate unique content for each step that directly relates to the step title and description. Avoid generic advice.", max_tokens=400, temperature=0.6)
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

