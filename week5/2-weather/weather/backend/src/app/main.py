from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from strands import Agent, tool
from strands.session.s3_session_manager import S3SessionManager
import boto3
import json
import logging
import os
import uuid
import uvicorn
import requests
from strands.models import BedrockModel
from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp import MCPClient

model_id = os.environ.get("MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0")
bedrock_model = BedrockModel(
        model_id=model_id,
        cache_prompt="default" # Enable prompt caching
    )
serper_api_key = os.environ.get("SERPER_API_KEY", "7299f48d35af30dedb94d6986f5c93c8d02bf5d3")
serper_url = os.environ.get("SERPER_URL", "https://google.serper.dev/search")
brave_api_key = os.environ.get("BRAVE_API_KEY", "")
firecrawl_api_key = os.environ.get("FIRECRAWL_API_KEY", "")
state_bucket = os.environ.get("STATE_BUCKET", "")
state_prefix = os.environ.get("STATE_PREFIX", "sessions/")
logging.getLogger("strands").setLevel(logging.WARNING)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", 
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Logger initialized")

if not state_bucket:
    raise RuntimeError("STATE_BUCKET environment variable must be set")

if state_prefix and not state_prefix.endswith("/"):
    state_prefix = f"{state_prefix}/"

boto_session = boto3.Session()


class ChatRequest(BaseModel):
    prompt: str

@tool
def search_jobs_google(query: str, location: str = "") -> str:
    """Search for job openings using Google Search via Serper API.

    Args:
        query: The job search query (e.g., "Software Engineer jobs", "Data Scientist careers")
        location: Optional location filter (e.g., "San Francisco", "Remote", "New York")

    Returns:
        JSON string containing search results with company career pages
    """
    logger.info(f"Searching jobs: query={query}, location={location}")

    # Construct search query optimized for company career pages
    search_query = f"{query} {location} site:careers OR inurl:careers OR inurl:jobs -site:linkedin.com -site:indeed.com -site:glassdoor.com"

    payload = json.dumps({
        "q": search_query,
        "num": 20  # Request more results to filter down
    })
    headers = {
        "X-API-KEY": serper_api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(serper_url, headers=headers, data=payload)
        logger.info(f"Serper API response status: {response.status_code}")
        return response.text
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        return json.dumps({"error": str(e)})

def create_mcp_clients():
    """Create MCP clients for Brave Search and Firecrawl if API keys are available"""
    mcp_tools = []

    # Add Brave Search MCP client if API key is available
    if brave_api_key:
        try:
            brave_client = MCPClient(lambda: stdio_client(
                StdioServerParameters(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-brave-search"],
                    env={"BRAVE_API_KEY": brave_api_key}
                )
            ))
            mcp_tools.append(brave_client)
            logger.info("Brave Search MCP client created")
        except Exception as e:
            logger.warning(f"Failed to create Brave Search client: {e}")

    # Add Firecrawl MCP client if API key is available
    if firecrawl_api_key:
        try:
            firecrawl_client = MCPClient(lambda: stdio_client(
                StdioServerParameters(
                    command="npx",
                    args=["-y", "firecrawl-mcp-server"],
                    env={"FIRECRAWL_API_KEY": firecrawl_api_key}
                )
            ))
            mcp_tools.append(firecrawl_client)
            logger.info("Firecrawl MCP client created")
        except Exception as e:
            logger.warning(f"Failed to create Firecrawl client: {e}")

    return mcp_tools

def create_agent(session_id: str) -> Agent:
    session_manager_kwargs = {
        "session_id": session_id,
        "bucket": state_bucket,
        "boto_session": boto_session,
    }

    if state_prefix:
        session_manager_kwargs["prefix"] = state_prefix

    system_prompt = """You are a job search assistant that finds job postings directly on company career pages.

**Core Mission**: Find actual job postings on company websites, NOT links to general career pages or job aggregators.

1. **Initial Questions** (if info missing):
- Exact job title or type of role?
- Location preference? (city, state, country, remote)
- Experience level? (entry, mid, senior)
- Any specific companies or industries?

2. **Search Requirements**:
- Search for jobs on company career sites (careers.company.com, jobs.company.com, company.com/careers)
- Find ACTUAL job postings with specific titles, not just career page homepages
- Match exact title OR similar/related titles
- Skip job aggregators: LinkedIn, Indeed, Glassdoor, Dice, ZipRecruiter, Monster, JobVite

3. **Search Strategy**: Use search_jobs_google tool to find company career pages:
   - Focus on company career pages (careers.company.com, jobs.company.com, company.com/careers)
   - Avoid job aggregators (LinkedIn, Indeed, Glassdoor)
   - Use location filters when specified

4. **Fetch Details**: If Brave Search or Firecrawl tools are available, use them to:
   - Get detailed job descriptions from career pages
   - Extract company information
   - Verify job posting links are active

5. **Output Format**: Present results as a clean, numbered list (max 10 jobs):

---
**Job 1: [Job Title]**
Company: [Company Name]
Link: [Direct URL]
Description: [Brief 2-3 sentence summary]

---
**Job 2: [Job Title]**
...

6. **Be Concise**:
   - Don't explain your search process
   - Don't mention which tools you're using
   - Just present the job listings
   - If you find fewer than 10 jobs, that's okay - show what you found

7. **Rules**:
- Show only jobs with direct posting URLs, not general career pages
- Be concise - no process explanations, just results
- If <10 jobs found, show what you found
- If no results, suggest broader search terms
"""

    # Combine custom tools with MCP tools
    tools = [search_jobs_google]

    # Add MCP clients if available
    mcp_tools = create_mcp_clients()
    if mcp_tools:
        tools.extend(mcp_tools)

    session_manager = S3SessionManager(**session_manager_kwargs)
    agent = Agent(
        model=bedrock_model,
        session_manager=session_manager,
        tools=tools,
        system_prompt=system_prompt
    )
    logger.info("Job search agent initialized for session %s with %d tools", session_id, len(tools))
    return agent

app = FastAPI()

# Called by the Lambda Adapter to check liveness
@app.get("/")
async def root():
    return {"message": "Job Search Agent is running"}

@app.get('/chat')
def chat_history(request: Request):
    session_id = request.cookies.get("session_id", str(uuid.uuid4()))
    agent = create_agent(session_id)

    # Filter messages to only include first text content
    filtered_messages = []
    for message in agent.messages:
        if (message.get("content") and 
            len(message["content"]) > 0 and 
            "text" in message["content"][0]):
            filtered_messages.append({
                "role": message["role"],
                "content": [{
                    "text": message["content"][0]["text"]
                }]
            })
 
    response = Response(
        content = json.dumps({
            "messages": filtered_messages,
        }),
        media_type="application/json",
    )
    response.set_cookie(key="session_id", value=session_id)
    return response

@app.post('/chat')
async def chat(chat_request: ChatRequest, request: Request):
    session_id = request.cookies.get("session_id", str(uuid.uuid4()))
    agent = create_agent(session_id)
    response = StreamingResponse(
        generate(agent, session_id, chat_request.prompt, request),
        media_type="text/event-stream"
    )
    response.set_cookie(key="session_id", value=session_id)
    return response

async def generate(agent: Agent, session_id: str, prompt: str, request: Request):
    try:
        async for event in agent.stream_async(prompt):
            if await request.is_disconnected():
                logger.info("Client disconnected before completion for session %s", session_id)
                break
            if "complete" in event:
                logger.info("Response generation complete")
            if "data" in event:
                yield f"data: {json.dumps(event['data'])}\n\n"
 
    except Exception as e:
        error_message = json.dumps({"error": str(e)})
        yield f"event: error\ndata: {error_message}\n\n"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
