from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands import Agent, tool
from strands.models import BedrockModel
from strands.session.s3_session_manager import S3SessionManager
from strands_tools import retrieve
import boto3
import json
import logging
import os
import uuid
import uvicorn
from questions import Question, QuestionManager, Visitor
import re
try:
    from strands.models.openai import OpenAIModel
    OPENAI_AVAILABLE = True
except ModuleNotFoundError:
    OPENAI_AVAILABLE = False
    OpenAIModel = None
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
if model_id == "":
    raise ValueError("MODEL_ID environment variable is not set.")
llm_as_a_judge_model_id = os.environ.get("LLM_AS_A_JUDGE_MODEL_ID", "")
if llm_as_a_judge_model_id == "":
    raise ValueError("LLM_AS_A_JUDGE_MODEL_ID environment variable is not set.")
bedrock_model = BedrockModel(
    model_id=model_id,
    # Add Guardrails here
)
llm_as_a_judge_model = BedrockModel(
    model_id=llm_as_a_judge_model_id,
    # Add Guardrails here
)

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

@tool
def search_properties(
    city: str = None,
    state: str = None,
    status: str = "Active",
    limit: int = 10,
    zipCode: str = None,
    address: str = None,
    latitude: float = None,
    longitude: float = None,
    radius: float = None,
    propertyType: str = None,
    bedrooms: str = None,
    bathrooms: str = None,
    squareFootage: str = None,
    lotSize: str = None,
    yearBuilt: str = None,
    price: str = None,
    daysOld: str = None,
    offset: int = None,
    includeTotalCount: bool = False
) -> str:
    """
    Search for properties for sale using the RentCast API.
    At least one of city, state, zipCode, or address must be provided.
    
    Args:
        address: Full address of the property (Street, City, State, Zip)
        city: The city name (case-sensitive, defaults to Austin)
        state: The 2-character state abbreviation (case-sensitive, defaults to TX)
        zipCode: The 5-digit zip code
        latitude: Latitude for circular area search
        longitude: Longitude for circular area search
        radius: Search radius in miles (max 100), use with lat/long or address
        propertyType: Type of property (Single Family, Condo, Townhouse, Manufactured, Multi-Family, Apartment, Land)
        bedrooms: Number of bedrooms (supports ranges and multiple values, e.g., "3", "3-4", "3,4,5")
        bathrooms: Number of bathrooms (supports fractions, ranges, and multiple values, e.g., "2", "2.5", "2-3")
        squareFootage: Total living area in sq ft (supports ranges and multiple values, e.g., "1500-2000")
        lotSize: Total lot size in sq ft (supports ranges and multiple values)
        yearBuilt: Year of construction (supports ranges and multiple values, e.g., "2000-2020")
        status: Property status (Active or Inactive, default: "Active")
        price: Listed price (supports ranges and multiple values, e.g., "300000-500000")
        daysOld: Days since listing (minimum 1, supports ranges)
        limit: Maximum number of results (1-500, default: 10)
        offset: Index of first record for pagination (default: 0)
        includeTotalCount: Include total count in X-Total-Count header (default: False)
        
    Returns:
        JSON string containing property listings with details like address, price, bedrooms, bathrooms, etc.
    """
    return question_manager.search_properties(
        city=city,
        state=state,
        status=status,
        limit=limit,
        zipCode=zipCode,
        address=address,
        latitude=latitude,
        longitude=longitude,
        radius=radius,
        propertyType=propertyType,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        squareFootage=squareFootage,
        lotSize=lotSize,
        yearBuilt=yearBuilt,
        price=price,
        daysOld=daysOld,
        offset=offset,
        includeTotalCount=includeTotalCount
    )

@tool
def add_property_info(property_data: dict, ttl_hours: int = None) -> str:
    """
    Add or update property information in the database with configurable TTL (time-to-live).
    The property will be automatically removed from the database after the TTL expires.
    
    Args:
        property_data: Dictionary containing property information. Must include either 'id' or 'formattedAddress'.
                      Example: {"id": "123", "formattedAddress": "123 Main St, Austin, TX 78701", 
                               "price": 500000, "bedrooms": 3, "bathrooms": 2, "city": "Austin", "zipCode": "78701"}
        ttl_hours: Time-to-live in hours (default: 12 hours, configurable via PROPERTY_TTL_HOURS env var)
        
    Returns:
        JSON string with success status, property ID, and expiration time
    """
    result = question_manager.add_property_info(property_data=property_data, ttl_hours=ttl_hours)
    return json.dumps(result, indent=2)

@tool
def get_property_info(property_id: str = None, property_address: str = None) -> str:
    """
    Retrieve property information from the database by property ID or address.
    
    Args:
        property_id: The unique property ID (e.g., "3821-Hargis-St-Austin-TX-78723")
        property_address: The formatted property address (e.g., "3821 Hargis St, Austin, TX 78723")
        
    Note: Either property_id or property_address must be provided.
    
    Returns:
        JSON string containing property information or None if not found
    """
    result = question_manager.get_property_info(property_id=property_id, property_address=property_address)
    if result is None:
        return json.dumps({"message": "Property not found"})
    return json.dumps(result, indent=2)

@tool
def search_properties_by_location(zipCode: str = None, city: str = None, limit: int = 50) -> str:
    """
    Search for cached properties in the database by zip code or city name.
    This searches the local database cache, not the external API.
    
    Args:
        zipCode: The 5-digit zip code to search for
        city: The city name to search for (case-sensitive)
        limit: Maximum number of results to return (default: 50)
        
    Note: Either zipCode or city must be provided.
    
    Returns:
        JSON string containing list of properties matching the search criteria
    """
    result = question_manager.search_properties_by_location(zipCode=zipCode, city=city, limit=limit)
    return json.dumps(result, indent=2)

def session(id: str) -> Agent:
    tools = [
        retrieve, 
        save_unanswered_question, 
        capture_visitor_info, 
        search_properties,
        add_property_info,
        get_property_info,
        search_properties_by_location
    ]
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
        # Stream the response as it's being generated for better UX
        full_response = ""
        async for event in agent.stream_async(prompt):
            if "data" in event:
                chunk = event["data"]
                full_response += chunk
                # Stream each chunk immediately to the client
                yield f"data: {json.dumps(chunk)}\n\n"
        
        logger.info(f"Response generated: {full_response[:100]}...")
        
        # Do quality control in the background (non-blocking for now)
        # TODO: Consider making this optional or async
        try:
            rating_data = await rate_response_with_llm_as_a_judge(prompt, full_response, session_id)
            if rating_data:
                rating = rating_data.get("rating", 10)
                feedback = rating_data.get("feedback", "")
                logger.info(f"Response rating: {rating}/10 - {feedback}")
        except Exception as rating_error:
            logger.warning(f"Quality control rating failed: {str(rating_error)}")
        
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
