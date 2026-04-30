# Python AI Agents with LangChain + FastAPI

Here's what I've learned building production AI agents in Python:

**LangChain Patterns (2026):**
- `create_openai_functions_agent` for structured tools
- `create_openai_tools_agent` for tool calling
- `ConversationBufferMemory` + Redis for production memory
- `@tool` decorator for custom functions

**FastAPI Integration:**
- Pydantic models for request/response validation
- Async/await with `ainvoke()` for concurrency
- SSE (Server-Sent Events) for streaming responses
- Error handling with fallback chains

**Production Hardening:**
- `max_iterations=5` to prevent infinite loops
- Cost tracking via token usage monitoring
- Prompt injection protection via guardrails
- Model fallback (OpenAI → Anthropic) for reliability

**Architecture I use now:**
```
Client → FastAPI Endpoint → LangChain Agent → Tools → LLM
                          ↓
                     LangSmith (tracing)
```

**Example flow:**
1. User POSTs to `/api/agent` with message
2. FastAPI validates with Pydantic schema
3. LangChain agent runs with memory context
4. Tools execute (search, database, API calls)
5. Response streams via SSE to frontend

**Tools I've built:**
- Agent that queries BigQuery and returns results as HTML tables
- Support agent that creates Linear tickets from natural language
- Data analysis agent that generates plots and shares to Slack

The tutorials from AI Agents Plus and Bitcot are good starting points. The real learning comes from debugging why agents fail in production.

#Python #LangChain #FastAPI #AI
