from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from strands import Agent, tool
from strands.session.s3_session_manager import S3SessionManager
from strands.agent.conversation_manager import SummarizingConversationManager
import boto3
from botocore.exceptions import ClientError
import json
import logging
import os
import uuid
import uvicorn
import requests
import db_tools
from strands.models import BedrockModel
from datetime import datetime, timedelta

model_id = os.environ.get("MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0")
bedrock_model = BedrockModel(
        model_id=model_id,
        cache_prompt="default" # Enable prompt caching
    )
serper_api_key = os.environ.get("SERPER_API_KEY", "7299f48d35af30dedb94d6986f5c93c8d02bf5d3")
serper_url = os.environ.get("SERPER_URL", "https://google.serper.dev/search")
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

def search_web(web_query):
    """Search the web using Serper API"""
    print(f"Searching web: {web_query}")
    payload = json.dumps({"q": web_query})
    headers = {
        "X-API-KEY": serper_api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(serper_url, headers=headers, data=payload)
        print(response.text)
        return response.text
    except Exception as e:
        print(f"Error searching web: {e}")
        return f"Error: {str(e)}"


def weather_forecast_with_google_search(city: str, days: int = 3):
    logger.info("Calling weather_forecast via google search tool for city: %s and days: %s", city, days)
    f"""Search the internet for the latest weather info for a given city and days.

    Args:
        city: The name of the city
        days: Number of days for the forecast
    Returns:
        A string containing the weather forecast for the {city} for the next {days} days in json format.
    """
    query = f"Find the weather now and forecast for {city} for the next {days} days."
    return search_web(query)

@tool
def weather_forecast(city: str, days: int = 3) -> str:
    
    """Get the latest weather info for a given city and days from the internet.

    Args:
        city: The name of the city
        days: Number of days for the forecast
    """
    logger.info(" weather_forecast tool called for city: %s and days: %s", city, days)
    weather_forecast = requests.get(f"https://wttr.in/{city}?format=j1").json()
    #weather_forecast = res
    logger.info("Weather forecast for %s is %s", city, weather_forecast)
    return weather_forecast

@tool
def get_weater_info_from_cache (city: str) -> Optional[str]:
    """
    Retrieve forecast data from  cache for a given city.
   
    Args:
        city: The name of the city to retrieve forecast data for
    
    Returns:
        JSON string containing the forecast data, or None if not found
    """
    logger.info(f"get_weater_info_from_cache called for city: {city}")
    if forecast := db_tools.fetch_forecast_from_cache(city):
        return forecast
    return f"No forecast found in the cache for {city}. " 

@tool
def cache_weather_info(city: str, forecast_json: str) -> str:
    """
    Store forecast data in  cache using city as key.
    The forecast data is cached for 30 minutes.
    Args:
        city: The name of the city (used as S3 key)
        forecast_json: The forecast data in JSON format (as string or dict that will be converted to JSON)
    
    Returns:
        A string indicating success or failure
    """
    logger.info(f"cache_weather_info called for city: {city}")
    db_tools.cache_forecast(city, forcast)
    return f"Forecast cached successfully for {city}."

@tool
def store_forecast_in_s3(city: str, forecast_json: str) -> str:
    """
    Store forecast data in  cache using city as key.
    The forecast data is cached for 30 minutes.
    Args:
        city: The name of the city (used as S3 key)
        forecast_json: The forecast data in JSON format (as string or dict that will be converted to JSON)
    
    Returns:
        A string indicating success or failure
    """
    logger.info(f"store_forecast_in_s3 called for city: {city}")
    try:
        s3_client = boto_session.client('s3')
        cache_prefix = f"forecast-cache/{city.lower().replace(' ', '_')}.json"
        
        # Convert to JSON string if it's a dict
        if isinstance(forecast_json, dict):
            forecast_json = json.dumps(forecast_json)
        elif not isinstance(forecast_json, str):
            forecast_json = json.dumps(forecast_json)
        
        # Calculate expiry time (30 minutes from now)
        cached_at = datetime.utcnow()
        expires_at = cached_at + timedelta(minutes=30)
        
        # Store JSON with metadata including TTL
        s3_client.put_object(
            Bucket=state_bucket,
            Key=cache_prefix,
            Body=forecast_json.encode('utf-8'),
            ContentType='application/json',
            Metadata={
                'city': city,
                'cached_at': cached_at.isoformat(),
                'expires_at': expires_at.isoformat()
            }
        )
        logger.info(f"Forecast cached in S3 for city: {city} (expires at {expires_at.isoformat()})")
        return f"Forecast stored in S3 cache for {city} (valid for 30 minutes)."
    except Exception as e:
        logger.error(f"Error storing forecast in S3: {e}")
        return f"Error storing forecast in S3: {str(e)}"

@tool
def get_forecast_from_s3(city: str) -> Optional[str]:
    """
    Retrieve forecast data from  cache for a given city.
   
    Args:
        city: The name of the city to retrieve forecast for
    
    Returns:
        JSON string containing the forecast data, or None if not found
    """
    logger.info(f" get_forecast_from_s3 called for city: {city}")
    try:
        s3_client = boto_session.client('s3')
        cache_prefix = f"forecast-cache/{city.lower().replace(' ', '_')}.json"
        
        response = s3_client.get_object(
            Bucket=state_bucket,
            Key=cache_prefix
        )
        
        # Check expiry from metadata
        metadata = response.get('Metadata', {})
        expires_at_str = metadata.get('expires_at')
        
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str)
                now = datetime.utcnow()
                
                # If expired, delete and return None
                if now > expires_at:
                    logger.info(f"Forecast expired for city: {city} (expired at {expires_at.isoformat()})")
                    s3_client.delete_object(Bucket=state_bucket, Key=cache_prefix)
                    return None
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse expiry date for {city}: {e}")
                # Continue to return data if we can't parse expiry
        
        # Read and return the JSON content
        forecast_json = response['Body'].read().decode('utf-8')
        logger.info(f"Forecast retrieved from S3 for city: {city}")
        return forecast_json
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'NoSuchKey':
            logger.info(f"No forecast found in S3 for city: {city}")
            return None
        logger.error(f"Error retrieving forecast from S3: {e}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving forecast from S3: {e}")
        return None

def create_agent(session_id: str) -> Agent:
    session_manager_kwargs = {
        "session_id": session_id,
        "bucket": state_bucket,
        "boto_session": boto_session,
    }
   

    if state_prefix:
        session_manager_kwargs["prefix"] = state_prefix
    system_prompt = """
    You are an advisor who is very good at giving advice based on weather conditions. 
    You answer users specific questions based o the weather in a given city or multiple cities in a region or 
    country. 
    
    When you are asked to answer a specific question based on the wather, keep the answer to the point and concise. No need to provide the whole forcast. 
    As much as possible, keep the answer to the point and concise. No need to provide the whole forcast when asnwering a specific question.
    
    Only provide full forcast when asked to do so specifically. 
    Otherwise, keep the answer to the point and concise to max 2 lines.
    
    Please answer the questions the in the local language of the city or region or country user is inquiring about.
    
    If you asked to create weather report or a script, Be witty and slighlty humorous
    in your answers when appropriate in your responses. 

    You can use tools to get the current weather as well as the forecast for the next n days and answer the question.
    tools available to you are: 
    - get_forecast_from_s3: get the forecast from the cache by city name.
    - weather_forecast: get the current weather as well as the forecast for the next n days from the internet. 
    - store_forecast_in_s3: add forecast for a given city by city name to th.  

    When you need weather forecast for a given city or cities
    look in the cache for the information first. If the information is not found in the cache, 
    Search the internet for the latest information and immedialte cache the information in the cache.
    NOTE: No need to let the user know that you are using the cache or internet. Just use the cache if it is available. 
    Be less verbose regarding the tools you are using.
  
    """
    
    tools = [weather_forecast, store_forecast_in_s3, get_forecast_from_s3]
    #tools = [weather_forecast, get_weater_info_from_cache, cache_weather_info]

    session_manager = S3SessionManager(**session_manager_kwargs)
    agent = Agent(model=bedrock_model, session_manager=session_manager, tools=tools, system_prompt=system_prompt)
    logger.info("Agent initialized for session %s", session_id)
    return agent

app = FastAPI()

# Called by the Lambda Adapter to check liveness
@app.get("/")
async def root():
    return {"message": "OK"}

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
