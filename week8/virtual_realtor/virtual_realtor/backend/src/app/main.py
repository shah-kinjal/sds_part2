from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands import Agent, tool
from strands.models import BedrockModel, OpenAIModel
from strands.session.s3_session_manager import S3SessionManager
from strands_tools import retrieve
import boto3
import json
import logging
import os
import uuid
import uvicorn
from questions import Question, QuestionManager, Visitor

ealtor_team_name="Monika Realty Team"
realtor_name="Monika Trivedi"
realtor_email="monika@monikarealty.com"
realtor_phone="510-468-2232"
realltor_dre_number="206536433"
realter_website="https://www.monikarealty.com"
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
current_agent: Agent | None = None
conversation_manager = SlidingWindowConversationManager(
    window_size=10,  # Maximum number of messages to keep
    should_truncate_results=True, # Enable truncating the tool result when a message is too large for the model's context window 
)
SYSTEM_PROMPT = f"""
You are a digital avatar representative of {realtor_name} their dre id is{realltor_dre_number}
and their website is {realter_website}, and their email is {realtor_email} and their phone is {realtor_phone}.
Answering quesions as a realtor in California.
You answer questions about properoties available for sale in a given area.
by  looking up the information about the properties in the knowledge base.
 
if You cannot find the information you need, you can say you don't have knowledge of the properties
and add the question to the database for future reference using the save_unanswered_question tool.
Let the user know that you've added the question to the database for future review and to comeback for an answer and 
ask for a contact information and capture the information using the capture_visitor_info tool.
After a brief interaction, gently ask for a contact information and capture the information using the capture_visitor_info tool.
Only answer questions about the properties based on the information you get from the tools. Do not make up information.

You should answer questions about {realtor_name}'s services for current or perspective clients.
You are humorous in your answers when appropriate. Keep the asnwer as brief as possible and concise.
No need to provide the whole story. Do not be verbose. Be brief and to the point.

When searching for information via a tool, tell the user you are "trying to get the information", and then use the tool to retrieve it.
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
        async for event in agent.stream_async(prompt):
            if "complete" in event:
                logger.info("Response generation complete")
            if "data" in event:
                yield f"data: {json.dumps(event['data'])}\n\n"
    except Exception as e:
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

@app.delete('/api/chat')
def chat_delete(request: Request):
    session_id = request.cookies.get("session_id", str(uuid.uuid4()))
    # Create a new agent with empty session
    agent = session(session_id)
    # Clear the session by deleting it
    try:
        agent.session_manager.delete_session()
    except Exception as e:
        logger.warning(f"Failed to delete session: {str(e)}")
    
    response = Response(
        content=json.dumps({"message": "Chat cleared"}),
        media_type="application/json",
    )
    # Generate a new session ID
    new_session_id = str(uuid.uuid4())
    response.set_cookie(key="session_id", value=new_session_id)
    return response

@app.get('/api/suggestions')
async def get_suggestions(request: Request):
    """
    Generate 3 contextually relevant question suggestions based on the conversation history.
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

Generate exactly 3 relevant follow-up questions that the user might want to ask about properties for sale. 
These should be natural questions a potential home buyer would ask.
Return ONLY the 3 questions as a JSON array, nothing else. Format: ["question 1", "question 2", "question 3"]"""
    else:
        suggestion_prompt = """Generate exactly 3 common questions that someone looking for properties might ask a realtor.
Return ONLY the 3 questions as a JSON array, nothing else. Format: ["question 1", "question 2", "question 3"]"""
    
    try:
        # Use the model directly without tools for simple generation
        response_text = ""
        async for event in bedrock_model.generate_stream(
            messages=[{"role": "user", "content": suggestion_prompt}],
            system=[{"text": "You are a helpful assistant that generates relevant real estate questions. Always respond with valid JSON only."}]
        ):
            if "data" in event:
                response_text += event["data"]
        
        # Parse the JSON response
        import re
        # Extract JSON array from response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            suggestions = json.loads(json_match.group())
            # Ensure we have exactly 3 suggestions
            suggestions = suggestions[:3]
        else:
            # Fallback suggestions if parsing fails
            suggestions = [
                "What properties are currently available in the area?",
                "Can you tell me about the price range of homes?",
                "What are the features of properties in this neighborhood?"
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
            "What properties are currently available?",
            "Can you tell me about pricing in the area?",
            "What amenities do the properties have?"
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
