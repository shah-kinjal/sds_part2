from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands import Agent, tool
from strands.models import BedrockModel
from strands.session.s3_session_manager import S3SessionManager
from strands_tools import retrieve as original_retrieve

import boto3
import json
import logging
import os
import uuid
import uvicorn
import re
from questions import Question, QuestionManager, Visitor
from rag_enhancements import RAGEnhancer

name="Kinjal Shah"
# Re-use boto session across invocations
boto_session = boto3.Session()
state_bucket_name = os.environ.get("STATE_BUCKET", "")
if state_bucket_name == "":
    raise ValueError("BUCKET_NAME environment variable is not set.")
logging.getLogger("strands").setLevel(logging.INFO)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
model_id = os.environ.get("MODEL_ID", "")
bedrock_model = BedrockModel(
    model_id=model_id,
    cache_prompt="default",
    # Add Guardrails here
)

# Initialize RAG Enhancer with configurable settings
rag_enhancer = RAGEnhancer(
    enable_query_rewrite=os.environ.get("ENABLE_QUERY_REWRITE", "true").lower() == "true",
    enable_reranking=os.environ.get("ENABLE_RERANKING", "true").lower() == "true",
    query_rewrite_model_id=os.environ.get("QUERY_REWRITE_MODEL_ID", None),
    rerank_model_id=os.environ.get("RERANK_MODEL_ID", None),
    rerank_method=os.environ.get("RERANK_METHOD", "bedrock"),
    rerank_top_k=int(os.environ.get("RERANK_TOP_K", "10"))
)

current_agent: Agent | None = None
conversation_manager = SlidingWindowConversationManager(
    window_size=5,  # Reduced from 10 to improve performance
    should_truncate_results=True, # Enable truncating the tool result when a message is too large for the model's context window
)
SYSTEM_PROMPT = f"""
Digital Twin System Prompt – {name}

Core Identity

You are {name}, a senior software engineering leader, speaking to prospective employers and clients.

Prime directive: Credibility over helpfulness. Never invent facts. If you don't know, say so plainly.

Knowledge Base

You have: LinkedIn profile, resume, interview prep notes (projects, metrics, CAR stories)

You don't have: Salary history, performance reviews, proprietary code/IP, personal opinions on former employers

Boundaries: Don't discuss compensation, confidential tech, or legal matters. Redirect without apology.

Retrieval Rules

Before answering any question about experience, projects, or outcomes:

1. Query knowledge base with key entities (company, role, tech, timeframe)
2. If confidence < 0.7 OR results conflict → acknowledge gap
3. If no data → "I don't have verified details on that"
4. Retrieve silently; never narrate tool usage

Partial data: "I led teams up to [X]; exact peak headcount isn't in my records."

Missing data: "I don't have that verified. I can flag it for {name} to follow up."

Response Framework

Leadership Lens (Required)

Every answer must include:
1. Team/org context – size, constraints
2. Decision rationale – why this over alternatives
3. Outcome at scale – team/system level, not personal output

❌ "I built a caching layer that reduced latency by 40%."  
✅ "I directed the platform team to prioritize caching over features, reducing P95 latency by 40% and unblocking 3 product teams."

CAR Format

Context → The problem/constraint  
Action → What {name} specifically did  
Result → Measurable impact with metrics

Metrics Rules

- Only cite numbers from retrieved data (verbatim)
- Use ranges if given ("10-15%", not "~12%")
- Never round aggressively (47% ≠ "nearly 50%")
- Distinguish team vs. system vs. org metrics

Hypotheticals & Judgment Questions

If analog exists: "Based on [verified situation], I'd approach this by [principle], optimizing for [tradeoff]."

If no analog: "I don't have a direct parallel. Generally I'd [principle], but specifics depend on [constraint]."

Never: Give step-by-step playbooks for unverified scenarios or commit to timelines/guarantees.

Tone & Length

Tone: Confident, concise, grounded. Never self-deprecating, salesy, or defensive.
Length: 
  - Factual questions: ≤3 sentences
  - Architecture/process: 4-6 sentences if needed
No: Generic follow-ups, buzzwords, apologies for knowledge gaps

Optional (sparingly): "Want to go deeper into how we scaled the platform team?"

Audience Calibration

Employer signals (job title, "we're hiring") → Emphasize: scope, people leadership, decision quality, accountability

Client signals (project needs, "help with") → Emphasize: outcomes, delivery, risk management, tradeoffs

Visitor Engagement

High-Intent (1st Message)
If they mention a role, urgency ("hiring for"), or technical requirements:  
[Answer question] + "If you'd like to discuss this with {name} directly, feel free to share your contact info."

Standard (After 2-3 Exchanges)
"If you'd like {name} to share more context directly, happy to connect you."  
Only ask once.

Contact Capture
When shared: "Thanks—{name}'s team will be in touch."  
→ Call `save_visitor_contact`

Failure Handling

After 3 "I don't know" responses:  
"I'm hitting the limits of my records. Want me to flag these for {name} to follow up?"  
→ Call `save_unanswered_question` for each

Conflicting sources:  
"My records show variation—[range]. I can have {name} clarify."

Off-topic persistence:  
"I'm here to discuss {name}'s professional background. Happy to refocus on [topic]."

---

## Critical Guardrails

❌ Never fabricate metrics, timelines, team sizes  
❌ Never commit to deliverables or guarantees  
❌ Never share compensation or proprietary info  
❌ Never answer leadership questions with IC contributions  

✅ Always anchor in verified outcomes  
✅ Always distinguish fact from judgment  
✅ Always prioritize credibility over perceived helpfulness

After 15 messages or 3 knowledge gaps → suggest direct contact with {name}
"""
app = FastAPI()
question_manager = QuestionManager()


@tool
def rag_retrieve(query: str) -> str:
    """
    Search for information about Kinjal Shah's career, experience, projects, and background.
    This tool uses enhanced RAG with query rewriting and reranking for better results.

    Args:
        query: The search query or question to find relevant information

    Returns:
        Relevant information retrieved from the knowledge base
    """
    try:
        # Step 1: Enhance the query through rewriting
        conversation_history = []
        if current_agent and hasattr(current_agent, 'messages'):
            conversation_history = current_agent.messages

        enhanced_query = rag_enhancer.enhance_query(query, conversation_history)
        logger.info(f"Query enhancement: '{query}' -> '{enhanced_query}'")

        # Step 2: Retrieve documents using the enhanced query
        # The original_retrieve function returns a formatted string
        retrieval_result = original_retrieve(enhanced_query)

        # Step 3: Parse the retrieval result if it contains structured data
        # For now, we'll work with the string result as-is since strands_tools
        # returns formatted text. If you need reranking on individual documents,
        # you would need to access the raw retrieval results differently.

        # Log the retrieval for debugging
        logger.info(f"Retrieved {len(retrieval_result)} characters for query: {enhanced_query}")

        return retrieval_result

    except Exception as e:
        logger.error(f"Error in enhanced retrieve: {str(e)}", exc_info=True)
        # Fall back to original retrieve on error
        return original_retrieve(query)

@tool
def save_unanswered_question(question: str) -> str:
    """
    Saves an unanswered question to the database for future review.
    Use this when you don't know the answer to a question or when you need
    more information to provide a proper response.
    
    Args:
        question: The question that you couldn't answer
        
    Returns:
        A confirmation message with the question ID
    """
    try:
        saved_question = question_manager.add_question(question=question)
        logger.info(f"Saved unanswered question with ID: {saved_question.question_id}")
        return f"Successfully saved the unanswered question to the database with ID: {saved_question.question_id}"
    except Exception as e:
        logger.error(f"Failed to save question: {str(e)}")
        return f"Failed to save the question to the database: {str(e)}"

@tool
def capture_visitor_info(name: str, email: str) -> str:
    """
    Captures visitor information (name and email) and saves it to the visitor log.
    Use this when someone introduces themselves or provides their contact information.
    
    Args:
        name: The visitor's name
        email: The visitor's email address
        
    Returns:
        A confirmation message with the visitor ID
    """
    try:
        visitor = question_manager.add_visitor(name=name, email=email)
        logger.info(f"Captured visitor info for {name} ({email}) with ID: {visitor.visitor_id}")
        return f"Successfully captured visitor information for {name} with ID: {visitor.visitor_id}"
    except Exception as e:
        logger.error(f"Failed to capture visitor info: {str(e)}")
        return f"Failed to capture visitor information: {str(e)}"

def session(id: str) -> Agent:
    # Use the enhanced retrieve tool with query rewriting and reranking
    tools = [rag_retrieve, save_unanswered_question, capture_visitor_info]
    session_manager = S3SessionManager(
        boto_session=boto_session,
        bucket=state_bucket_name,
        session_id=id,
    )
    return Agent(
        conversation_manager=conversation_manager,
        model=bedrock_model,
        session_manager=session_manager,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
    )

class ChatRequest(BaseModel):
    prompt: str



@app.post('/api/chat')
async def chat(chat_request: ChatRequest, request: Request):
    import time
    start_time = time.time()
    
    session_id: str = request.cookies.get("session_id", str(uuid.uuid4()))
    logger.info(f"Chat request for session {session_id}")
    
    agent = session(session_id)
    logger.info(f"Agent created in {time.time() - start_time:.2f}s")
    
    global current_agent
    current_agent = agent  # Store the current agent for use in tools
    response = StreamingResponse(
        generate(agent, session_id, chat_request.prompt, request),
        media_type="text/event-stream"
    )
    response.set_cookie(key="session_id", value=session_id)
    return response


async def generate(agent: Agent, session_id: str, prompt: str, request: Request):
    try:
        logger.info(f"Starting generation for session {session_id}")
        
        # Stream the response directly from the agent
        has_data = False
        async for event in agent.stream_async(prompt):
            if "data" in event:
                has_data = True
                yield f"data: {json.dumps(event['data'])}\n\n"
        
        if not has_data:
            logger.warning("No data was streamed from agent")
            
        logger.info("Response streaming complete")
        
    except Exception as e:
        logger.error(f"Error in generate: {str(e)}", exc_info=True)
        error_message = json.dumps({"error": str(e)})
        yield f"event: error\ndata: {error_message}\n\n"

@app.get('/api/chat')
def chat_get(request: Request):
    session_id = request.cookies.get("session_id", str(uuid.uuid4()))
    agent = session(session_id)

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
        content=json.dumps({
            "messages": filtered_messages,
        }),
        media_type="application/json",
    )
    response.set_cookie(key="session_id", value=session_id)
    return response

@app.get('/api/suggestions')
async def get_suggestions(request: Request):
    """
    Generate 4 contextually relevant question suggestions based on the conversation history.
    """
    session_id = request.cookies.get("session_id", str(uuid.uuid4()))
    agent = session(session_id)
    
    # Build context from conversation history
    conversation_context = ""
    if agent.messages:
        # Get last few messages for context
        recent_messages = agent.messages[-4:] if len(agent.messages) > 4 else agent.messages
        for msg in recent_messages:
            role = msg.get("role", "")
            if msg.get("content") and len(msg["content"]) > 0 and "text" in msg["content"][0]:
                text = msg["content"][0]["text"]
                conversation_context += f"{role}: {text}\n"
    
    # Create a prompt to generate suggestions
    if conversation_context:
        suggestion_prompt = f"""Based on this conversation history:

{conversation_context}

Generate exactly 4 relevant follow-up questions that the user might ask to learn more about Kinjal's background, experience, or projects.
These should feel natural for a recruiter or hiring manager.
Return ONLY the 4 questions as a JSON array, nothing else. Format: ["question 1", "question 2", "question 3", "question 4"]"""
    else:
        suggestion_prompt = """Generate exactly 4 common questions that someone evaluating Kinjal's fit for a role might ask.
Return ONLY the 4 questions as a JSON array, nothing else. Format: ["question 1", "question 2", "question 3", "question 4"]"""
    
    try:
        # Create a temporary agent for generating suggestions
        suggestion_agent = Agent(
            model=bedrock_model,
            cache_prompt="default",
            system_prompt = "You are a helpful assistant that generates concise career-related questions. Always respond with valid JSON only.",
            tools=[]
        )
        
        response_text = ""
        async for event in suggestion_agent.stream_async(suggestion_prompt):
            if "data" in event:
                response_text += event["data"]
        
        # Parse the JSON response
        import re
        # Extract JSON array from response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            suggestions = json.loads(json_match.group())
            # Ensure we have exactly 4 suggestions
            suggestions = suggestions[:4]
        else:
            # Fallback suggestions if parsing fails
            suggestions = [
                "What roles are you focusing on right now?",
                "Can you summarize your recent leadership achievements?",
                "What are your core technical specializations?",
                "Do you have experience scaling engineering teams?"
            ]
        
        response = Response(
            content=json.dumps({"suggestions": suggestions}),
            media_type="application/json",
        )
        response.set_cookie(key="session_id", value=session_id)
        return response
        
    except Exception as e:
        logger.error(f"Error generating suggestions: {str(e)}")
        # Return default suggestions on error
        default_suggestions = [
            "What roles are you focusing on right now?",
            "Can you summarize your recent leadership achievements?",
            "What are your core technical specializations?",
            "Do you have experience scaling engineering teams?"
        ]
        response = Response(
            content=json.dumps({"suggestions": default_suggestions}),
            media_type="application/json",
        )
        response.set_cookie(key="session_id", value=session_id)
        return response


# Called by the Lambda Adapter to check liveness
@app.get("/")
async def root():
    return Response(
        content=json.dumps({"message": "OK"}),
        media_type="application/json",
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
