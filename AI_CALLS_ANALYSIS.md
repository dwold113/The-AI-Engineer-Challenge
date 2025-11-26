# AI Calls Analysis

## For a Single `/api/learn` Request

### Minimum AI Calls: **4 calls**

1. **`extract_topic_and_num_resources()`** - 1 call
   - Extracts clean topic and requested numbers from user input
   - Always called

2. **`validate_learning_topic()`** - 1 call
   - Validates if topic is learnable (not gibberish, abstract, etc.)
   - Always called

3. **`generate_learning_plan()`** - 1 call
   - Generates the learning plan steps
   - Always called (runs in parallel with #4)

4. **`scrape_examples()`** - 1 call
   - Generates learning resources/examples
   - Always called (runs in parallel with #3)

### Additional Conditional Calls: **+0 to +2 calls**

5. **Resource count validation** - 0-1 call
   - Only if user requests specific number of resources (e.g., "give me 10 resources")
   - Validates if the requested number is reasonable

6. **Fallback resources** - 0-1 call
   - Only if initial resource generation fails or doesn't provide enough examples
   - Generates fallback educational resources

### For "Dive Deeper" (`/api/expand-step`): **1 call**

- **`expand_learning_step()`** - 1 call
  - Generates additional context for a specific learning step
  - Only called when user clicks "Dive Deeper"

## Summary

**Typical Request (no number requests):**
- **4 AI calls** (all run in parallel where possible)

**Request with resource number specification:**
- **5 AI calls** (4 base + 1 validation call)

**Request with fallback needed:**
- **5 AI calls** (4 base + 1 fallback)

**Maximum possible:**
- **6 AI calls** (4 base + 1 validation + 1 fallback)

## Call Flow

```
User Request → extract_topic_and_num_resources (1 call)
             → validate_learning_topic (1 call)
             → generate_learning_plan (1 call) ─┐
             → scrape_examples (1 call) ────────┼─ Parallel execution
             → [if needed] resource validation (0-1 call)
             → [if needed] fallback resources (0-1 call)
```

## Optimization Notes

- Calls #3 and #4 run in **parallel** using `asyncio.gather()` for speed
- Calls #5 and #6 only happen if user explicitly requests numbers
- Call #7 only happens if initial resource generation fails
- All calls use `gpt-4o-mini` for cost efficiency
- Token limits are optimized (50-500 tokens) for speed

