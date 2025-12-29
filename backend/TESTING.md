# Testing the Chat API

## Quick Start

1. **Start the server:**

   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **In another terminal, test the queries:**

   **Test 1: AI Experience**

   ```bash
   curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "what experience does Tae have with AI",
       "top_k": 6
     }'
   ```

   **Test 2: Backend Frameworks**

   ```bash
   curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "what backend frameworks has Tae used",
       "top_k": 6
     }'
   ```

   Or use the test script:

   ```bash
   ./test_chat_debug.sh
   ```

## What to Check

When you make requests, check the **server console output** for:

### 1. System Prompt

- Should contain instructions for synthesis
- Should mention "Tae Kim" and resume context

### 2. User Prompt (first 1500 chars)

- Should include the user's question
- Should contain chunk IDs like `[chunk_001]`
- Should show Section and Entity metadata
- Should include full text from retrieved chunks

### 3. Evidence Summary

- Should show multiple entities (projects + experience)
- Should show chunk IDs, sections, entities, and scores
- Should show relevant keywords

### 4. Citations

- Should match the evidence chunk IDs
- Should show section and entity for each citation

### 5. Response JSON

- `evidence` array should have multiple items
- `citations` array should match evidence IDs
- `answer` field should be present (currently placeholder)

## Expected Behavior

For "what experience does Tae have with AI":

- Should retrieve chunks mentioning AI, LLM, RAG, OpenAI, etc.
- Should include multiple entities (different projects/companies)
- Citations should reference the chunk IDs used

For "what backend frameworks has Tae used":

- Should retrieve chunks mentioning FastAPI, Socket.IO, etc.
- Should synthesize across multiple experience entries
- Should show different companies/projects where frameworks were used

## Removing Debug Prints

When ready for production, remove or comment out the debug print statements in `app/chat/routes.py` (lines with `print(...)`).
