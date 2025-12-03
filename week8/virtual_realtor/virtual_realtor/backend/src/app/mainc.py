from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands import Agent
from strands.models import BedrockModel
from strands.session.s3_session_manager import S3SessionManager
import boto3
import json
import logging
import os
import uuid
import uvicorn
import re
try:
    from strands.models.openai import OpenAIModel
    OPENAI_AVAILABLE = True
except ModuleNotFoundError:
    OPENAI_AVAILABLE = False
    OpenAIModel = None

# Import all tools from the tools module
from tools import ALL_TOOLS

realtor_team_name="Monika Realty Team"
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
if model_id == "":
    raise ValueError("MODEL_ID environment variable is not set.")
llm_as_a_judge_model_id = os.environ.get("LLM_AS_A_JUDGE_MODEL_ID", "us.amazon.nova-pro-v1:0")

bedrock_model = BedrockModel(
    model_id=model_id,
    # Add Guardrails here
)
llm_as_a_judge_model = None


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

def session(id: str) -> Agent:
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
        tools=ALL_TOOLS,
    )

class ChatRequest(BaseModel):
    prompt: str



async def rate_response_with_llm_as_a_judge(prompt: str, response: str, session_id: str) -> dict | None:
    if llm_as_a_judge_model is None:
        logger.warning("LLM as a judge model unavailable; skipping response rating.")
        return None
    judge_system_prompt = f"""You are a quality control agent. Rate the following response against the user's prompt on a scale of 1-10.
    Consider:
    - Relevance to the prompt
    - Clarity and conciseness
    - Accuracy and helpfulness
    - Tone and professionalism
    Provide your rating as a JSON object with this exact format:
    {{"rating": <number between 1-10>, "feedback": "<brief explanation>"}}
    """
    # Don't use a session manager for the judge agent - it's a one-off rating and doesn't need conversation history
    # This avoids inheriting tool use/result blocks from the main conversation
    judge_agent = Agent(
        model=llm_as_a_judge_model,
        system_prompt=judge_system_prompt,
        tools=[],  # Explicitly set empty tools list to avoid tool-related errors
    )
    rating_response = ""
    async for event in judge_agent.stream_async(f"{prompt}\n\nResponse: {response}"):
        if "data" in event:
            rating_response += event["data"]
    
    logger.info(f"Rating response: {rating_response}")
    json_match = re.search(r'\{.*\}', rating_response, re.DOTALL)
    if not json_match:
        return None
    return json.loads(json_match.group())

async def generate_bedrock_response(agent: Agent, prompt: str) -> str:
    """
    Generate a complete response from the agent for the given prompt.
    This function collects all streaming chunks into a single response.
    """
    full_response = ""
    async for event in agent.stream_async(prompt):
        if "data" in event:
            full_response += event["data"]
    return full_response

@app.post('/api/chat')
async def chat(chat_request: ChatRequest, request: Request):
    session_id: str = request.cookies.get("session_id", str(uuid.uuid4()))
    logger.debug(f"Session ID: {session_id}")    
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
            rating_data = await rate_response_with_llm_as_a_judge(prompt, approved_response, session_id)
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

Generate exactly 4 relevant follow-up questions that the user might want to ask about properties for sale. 
These should be natural questions a potential home buyer would ask.
Return ONLY the 3 questions as a JSON array, nothing else. Format: ["question 1", "question 2", "question 3"]"""
    else:
        suggestion_prompt = """Generate exactly 4 common questions that someone looking for properties might ask a realtor.
Return ONLY the 3 questions as a JSON array, nothing else. Format: ["question 1", "question 2", "question 3"]"""
    
    try:
        # Use an Agent with the model for simple generation
        suggestion_agent = Agent(
            model=bedrock_model,
            system_prompt="You are a helpful assistant that generates relevant real estate questions. Always respond with valid JSON only."
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
