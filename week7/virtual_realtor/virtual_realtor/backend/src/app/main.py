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
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import hashlib
from botocore.exceptions import ClientError

# Load environment variables from .env file
load_dotenv()

# Re-use boto session across invocations
boto_session = boto3.Session()
realtor_team_name="Monika Realty Team"
realtor_name="Monika Trivedi"
realtor_email="monika@monikarealty.com"
realtor_phone="510-468-2232"
realltor_dre_number="206536433"
realter_website="https://www.monikarealty.com"
state_bucket_name = os.environ.get("STATE_BUCKET", "")
if state_bucket_name == "":
    raise ValueError("BUCKET_NAME environment variable is not set.")

# S3 client for Q&A storage
s3_client = boto3.client('s3')
qa_prefix = "qa/"
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

if You can not find the information you need, you can say you don't have knowledge of the properties.
You can only answer questions about the properties based on the information you get from the tools.

You should answer questions about {realtor_name}'s services for current or perspective clients.
You are humorous in your answers when appropriate. Keep the asnwer to the point and concise. No need to provide the whole story.


When searching for information via a tool, tell the user you are "trying to get the information", and then use the tool to retrieve it.
"""
app = FastAPI()

@tool

def search_properties(
    city: str, #optional city to search for properties in case of zip code is not provided
    state: str, #optional state to search for properties in case of zip code is not provided
    status: str = "Active",
    limit: int = 10, # optional limit to search for properties
    zipCode: str = None, # optional zip code to search for properties
) -> str:
    logger.info(f"search_properties called for city: {city}, state: {state}, status: {status}, limit: {limit}")
    """
    tool to search for properties for sale using the RentCast API.
    atleast one of city or state or zipCode must be provided.
    Args:
        city: The city name (optional)
        state: The state abbreviation (optional)
        status: Property status (default: "Active")
        limit: Maximum number of results to return (default: 5)
        zipCode: The zip code to search for properties (optional)
    Returns:
        JSON string containing property listings or error message
    """
    try:
        api_key = os.environ.get("RENTCAST_API_KEY")
        if not api_key:
            error_msg = "RENTCAST_API_KEY environment variable is not set. Please set it in your .env file."
            logger.error(error_msg)
            return json.dumps({"error": error_msg})
        
        api_url = os.environ.get("RENTCAST_API_URL", "https://api.rentcast.io/v1/listings/sale")
        url = api_url
        
        params = {
            "city": city,
            "state": state,
            "status": status,
            "limit": limit,
            "zipCode": zipCode
        }
        
        headers = {
            "accept": "application/json",
            "X-Api-Key": api_key
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        return json.dumps(data, indent=2)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling RentCast API: {e}")
        return json.dumps({"error": f"Failed to retrieve properties: {str(e)}"})
    except Exception as e:
        logger.error(f"Unexpected error in search_properties: {e}")
        return json.dumps({"error": f"An unexpected error occurred: {str(e)}"})

@tool
def store_qa(search_query: str, answer: str) -> str:
    logger.info(f"store_qa called for search_query: {search_query}")
    logger.info(f"answer: {answer}")
    """
    tool to store search query and answer  in S3 with a 24-hour TTL.
    
    Args:
        question: The question asked by the user
        answer: The answer provided
    
    Returns:
        JSON string indicating success or error
    """
    try:
        # Create a hash of the question for the key
        question_hash = hashlib.md5(search_query.lower().strip().encode()).hexdigest()
        
        # Calculate expiration time (24 hours from now)
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(hours=24)
        
        # Create the Q&A document
        qa_document = {
            "property_address": search_query,
            "property_details": answer,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "ttl_hours": 24
        }
        
        # Store in S3
        key = f"{qa_prefix}{question_hash}.json"
        s3_client.put_object(
            Bucket=state_bucket_name,
            Key=key,
            Body=json.dumps(qa_document),
            ContentType='application/json'
        )
        
        logger.info(f"Stored Q&A pair with key: {key}")
        return json.dumps({
            "status": "success",
            "message": "Question and answer stored successfully",
            "expires_at": expires_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error storing Q&A: {e}")
        return json.dumps({"error": f"Failed to store Q&A: {str(e)}"})

@tool
def search_qa(question: str) -> str:
    logger.info(f"search_qa called for search_query: {question}")
    """
    tool to Search for an answer to a question in the stored Q&A pairs.
    Only returns answers that haven't expired (within 24 hours).
    
    Args:
        question: The question to search for
    
    Returns:
        JSON string containing matching answers or empty if not found
    """
    try:
        # Create hash of the question to find exact match
        question_hash = hashlib.md5(question.lower().strip().encode()).hexdigest()
        key = f"{qa_prefix}{question_hash}.json"
        
        # Try to get the exact match first
        try:
            response = s3_client.get_object(Bucket=state_bucket_name, Key=key)
            qa_document = json.loads(response['Body'].read().decode('utf-8'))
            
            # Check if expired
            expires_at = datetime.fromisoformat(qa_document['expires_at'])
            if datetime.utcnow() < expires_at:
                return json.dumps({
                    "found": True,
                    "question": qa_document['question'],
                    "answer": qa_document['answer'],
                    "created_at": qa_document['created_at'],
                    "expires_at": qa_document['expires_at']
                })
            else:
                # Entry expired, delete it
                s3_client.delete_object(Bucket=state_bucket_name, Key=key)
                logger.info(f"Deleted expired Q&A entry: {key}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                pass  # Key doesn't exist, continue to search
            else:
                raise
        
        # If exact match not found, search all Q&A entries
        matching_answers = []
        
        try:
            # List all objects with the qa prefix
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=state_bucket_name, Prefix=qa_prefix)
            
            for page in pages:
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    try:
                        # Get the object
                        response = s3_client.get_object(Bucket=state_bucket_name, Key=obj['Key'])
                        qa_document = json.loads(response['Body'].read().decode('utf-8'))
                        
                        # Check if expired
                        expires_at = datetime.fromisoformat(qa_document['expires_at'])
                        if datetime.utcnow() >= expires_at:
                            # Delete expired entry
                            s3_client.delete_object(Bucket=state_bucket_name, Key=obj['Key'])
                            continue
                        
                        # Simple text matching - check if question keywords match
                        question_lower = question.lower()
                        stored_question_lower = qa_document['question'].lower()
                        
                        # Check for keyword overlap (simple matching)
                        question_words = set(question_lower.split())
                        stored_words = set(stored_question_lower.split())
                        
                        # If significant overlap (at least 50% of words match)
                        if len(question_words) > 0:
                            overlap = len(question_words.intersection(stored_words)) / len(question_words)
                            if overlap >= 0.5:
                                matching_answers.append({
                                    "question": qa_document['question'],
                                    "answer": qa_document['answer'],
                                    "created_at": qa_document['created_at'],
                                    "expires_at": qa_document['expires_at'],
                                    "match_score": overlap
                                })
                    except Exception as e:
                        logger.warning(f"Error processing Q&A entry {obj['Key']}: {e}")
                        continue
            
            if matching_answers:
                # Sort by match score (highest first)
                matching_answers.sort(key=lambda x: x['match_score'], reverse=True)
                return json.dumps({
                    "found": True,
                    "matches": matching_answers
                })
            else:
                return json.dumps({
                    "found": False,
                    "message": "No matching answers found"
                })
                
        except Exception as e:
            logger.error(f"Error searching Q&A: {e}")
            return json.dumps({
                "found": False,
                "error": f"Error during search: {str(e)}"
            })
            
    except Exception as e:
        logger.error(f"Unexpected error in search_qa: {e}")
        return json.dumps({"error": f"An unexpected error occurred: {str(e)}"})

def session(id: str) -> Agent:
    tools = [retrieve]
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


# Called by the Lambda Adapter to check liveness
@app.get("/")
async def root():
    return Response(
        content=json.dumps({"message": "OK"}),
        media_type="application/json",
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
