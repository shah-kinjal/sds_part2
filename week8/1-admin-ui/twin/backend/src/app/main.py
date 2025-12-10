from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands import Agent, tool
from strands.models import BedrockModel
from strands.session.s3_session_manager import S3SessionManager
from strands_tools import retrieve
try:
    from strands.models.openai import OpenAIModel
    OPENAI_AVAILABLE = True
except ModuleNotFoundError:
    OPENAI_AVAILABLE = False
    OpenAIModel = None
import boto3
import json
import logging
import os
import uuid
import uvicorn
import re
from questions import Question, QuestionManager, Visitor

name="Kinjal"
# Re-use boto session across invocations
boto_session = boto3.Session()
state_bucket_name = os.environ.get("STATE_BUCKET", "")
if state_bucket_name == "":
    raise ValueError("BUCKET_NAME environment variable is not set.")
logging.getLogger("strands").setLevel(logging.DEBUG)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", 
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
model_id = os.environ.get("MODEL_ID", "")
bedrock_model = BedrockModel(
    model_id=model_id,
    # Add Guardrails here
)
openai_model = None
if OPENAI_AVAILABLE:
    openai_model = OpenAIModel(
        client_args={
            "api_key": os.environ.get("OPENAI_API_KEY", ""),
        },
        model_id=os.environ.get("OPENAI_MODEL_ID", "gpt-4o"),
        params={
            "max_tokens": 1000,
            "temperature": 0.7, 
        }
    )
else:
    logger.warning("OpenAI dependency not installed; skipping quality-control ratings.")
current_agent: Agent | None = None
conversation_manager = SlidingWindowConversationManager(
    window_size=10,  # Maximum number of messages to keep
    should_truncate_results=True, # Enable truncating the tool result when a message is too large for the model's context window 
)
SYSTEM_PROMPT = f"""
You are a digital twin of {name}. You should answer questions about their career for prospective employers and / or clients.
You are friendly and helpful in your answers. Keep the answers to the point and as short as possible but provide enough context to answer the question.
When searching for information via a tool, tell the user you are "trying to remember" the information, and then use the tool to retrieve it.
If you don't know the answer to a question, use the save_unanswered_question tool to save the question to the database for future review 
and let the user know that you've added the question to the database for future review and to comeback for an answer. 
Gently ask for a contact information after a brief interaction. Dont be too pushy about it.
Capture the visitor information using the capture_visitor_info tool when someone introduces themselves or provides their contact information.
cDo not ask follow up questions. 
"""
app = FastAPI()
question_manager = QuestionManager()

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
    tools = [retrieve, save_unanswered_question, capture_visitor_info]
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

async def generate_bedrock_response(agent: Agent, prompt: str) -> str:
    full_response = ""
    async for event in agent.stream_async(prompt):
        if "data" in event:
            full_response += event["data"]
    return full_response

async def rate_response_with_openai(prompt: str, response: str) -> dict | None:
    if openai_model is None:
        logger.warning("OpenAI model unavailable; skipping response rating.")
        return None

    rating_prompt = f"""You are a quality control agent. Rate the following response against the user's prompt on a scale of 1-10.
Consider:
- Relevance to the prompt
- Clarity and conciseness
- Accuracy and helpfulness
- Tone and professionalism

User Prompt: {prompt}

Response: {response}

Provide your rating as a JSON object with this exact format:
{{"rating": <number between 1-10>, "feedback": "<brief explanation>"}}
"""

    rating_response = ""
    async for event in openai_model.generate_stream(
        messages=[{"role": "user", "content": rating_prompt}],
        system=[{"text": "You are a quality control assistant. Always respond with valid JSON only."}]
    ):
        if "data" in event:
            rating_response += event["data"]

    logger.info(f"Rating response: {rating_response}")
    json_match = re.search(r'\{.*\}', rating_response, re.DOTALL)
    if not json_match:
        return None

    return json.loads(json_match.group())

@app.post('/api/chat')
async def chat(chat_request: ChatRequest, request: Request):
    session_id: str = request.cookies.get("session_id", str(uuid.uuid4()))
    agent = session(session_id)
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
        full_response = await generate_bedrock_response(agent, prompt)
        logger.info(f"Initial response generated: {full_response[:100]}...")

        max_retries = 2
        retry_count = 0
        approved_response = full_response
        
        while retry_count < max_retries:
            rating_data = await rate_response_with_openai(prompt, approved_response)
            if not rating_data:
                logger.warning("Could not parse rating response, using original response")
                break

            rating = rating_data.get("rating", 10)
            feedback = rating_data.get("feedback", "")
            
            logger.info(f"Response rating: {rating}/10 - {feedback}")
            
            if rating >= 8:
                logger.info("Response approved by quality control")
                break
            else:
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"Response rated {rating}/10, regenerating (attempt {retry_count + 1})")
                    regeneration_prompt = f"{prompt}\n\nPlease improve your previous response. Quality feedback: {feedback}"
                    approved_response = await generate_bedrock_response(agent, regeneration_prompt)
                else:
                    logger.warning(f"Max retries reached. Using last response with rating {rating}/10")
                    break
        
        # Stream the approved response to the client
        # Split into chunks for streaming effect
        chunk_size = 50
        for i in range(0, len(approved_response), chunk_size):
            chunk = approved_response[i:i + chunk_size]
            yield f"data: {json.dumps(chunk)}\n\n"
        
        logger.info("Response streaming complete")
        
    except Exception as e:
        logger.error(f"Error in generate: {str(e)}")
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
        # Use the model directly without tools for simple generation
        response_text = ""
        async for event in bedrock_model.generate_stream(
            messages=[{"role": "user", "content": suggestion_prompt}],
            system=[{"text": "You are a helpful assistant that generates concise career-related questions. Always respond with valid JSON only."}]
        ):
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
