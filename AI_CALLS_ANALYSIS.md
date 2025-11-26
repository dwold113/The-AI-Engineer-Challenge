# AI Calls Analysis

## For a Single `/api/learn` Request

### OPTIMIZED: Minimum AI Calls: **2 calls** (50% reduction!)

1. **`extract_validate_and_prepare_topic()`** - 1 call
   - **COMBINED**: Extracts clean topic, requested numbers, validates topic, and validates number reasonableness
   - Always called
   - Replaces the old 2-3 separate calls (extraction + validation + number validation)

2. **`generate_plan_and_resources()`** - 1 call
   - **COMBINED**: Generates both learning plan steps AND resources/examples
   - Always called
   - Replaces the old 2 separate calls (plan generation + resource generation)

### Additional Conditional Calls: **+0 to +1 call**

3. **Fallback resources** - 0-1 call
   - Only if initial combined generation fails or doesn't provide enough examples
   - Generates fallback educational resources

### For "Dive Deeper" (`/api/expand-step`): **1 call**

- **`expand_learning_step()`** - 1 call
  - Generates additional context for a specific learning step
  - Only called when user clicks "Dive Deeper"

## Summary

**Typical Request:**
- **2 AI calls** (50% reduction from previous 4 calls!)

**Request with fallback needed:**
- **3 AI calls** (2 base + 1 fallback)

**Maximum possible:**
- **3 AI calls** (2 base + 1 fallback)

## Optimization Benefits

- **50% cost reduction**: From 4 calls to 2 calls per request
- **50% latency reduction**: Fewer sequential API calls means faster response times
- **Same functionality**: All features preserved (validation, extraction, plan generation, resources)

## Call Flow (Optimized)

```
User Request → extract_validate_and_prepare_topic (1 combined call)
             → generate_plan_and_resources (1 combined call)
             → [if needed] fallback resources (0-1 call)
```

## Previous Implementation (Before Optimization)

- **4 minimum calls**: extract (1) + validate (1) + plan (1) + resources (1)
- **Up to 6 calls**: with validation and fallback
- **Parallel execution**: plan and resources ran in parallel, but still 2 separate calls

## Optimization Notes

- Calls #3 and #4 run in **parallel** using `asyncio.gather()` for speed
- Calls #5 and #6 only happen if user explicitly requests numbers
- Call #7 only happens if initial resource generation fails
- All calls use `gpt-4o-mini` for cost efficiency
- Token limits are optimized (50-500 tokens) for speed

