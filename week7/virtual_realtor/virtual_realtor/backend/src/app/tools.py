"""
Agent Tools for Virtual Realtor
Contains property search and Q&A storage/retrieval tools
"""
from strands import tool
import boto3
import json
import logging
import os
import hashlib
import requests
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Set up logger
logger = logging.getLogger(__name__)

# DynamoDB setup for Q&A storage
dynamodb = boto3.resource('dynamodb')
qa_table_name = os.environ.get("QA_TABLE_NAME", "")
if qa_table_name == "":
    raise ValueError("QA_TABLE_NAME environment variable is not set.")
qa_table = dynamodb.Table(qa_table_name)


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
    tool to store search query and answer in DynamoDB with a 24-hour TTL.
    
    Args:
        search_query: The question asked by the user
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
        
        # DynamoDB TTL expects epoch time in seconds
        ttl_timestamp = int(expires_at.timestamp())
        
        # Create the Q&A document
        qa_document = {
            "question_hash": question_hash,
            "property_address": search_query,
            "property_details": answer,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "ttl": ttl_timestamp  # DynamoDB TTL attribute
        }
        
        # Store in DynamoDB
        qa_table.put_item(Item=qa_document)
        
        logger.info(f"Stored Q&A pair with hash: {question_hash}")
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
        
        # Try to get the exact match first
        try:
            response = qa_table.get_item(Key={'question_hash': question_hash})
            
            if 'Item' in response:
                qa_document = response['Item']
                
                # Check if expired (DynamoDB TTL may not have deleted it yet)
                expires_at = datetime.fromisoformat(qa_document['expires_at'])
                if datetime.utcnow() < expires_at:
                    return json.dumps({
                        "found": True,
                        "property_address": qa_document['property_address'],
                        "property_details": qa_document['property_details'],
                        "created_at": qa_document['created_at'],
                        "expires_at": qa_document['expires_at']
                    })
                else:
                    # Entry expired, delete it
                    qa_table.delete_item(Key={'question_hash': question_hash})
                    logger.info(f"Deleted expired Q&A entry: {question_hash}")
        except ClientError as e:
            logger.warning(f"Error getting exact match: {e}")
            pass  # Continue to fuzzy search
        
        # If exact match not found, search all Q&A entries for fuzzy matching
        matching_answers = []
        
        try:
            # Scan all items in the table
            response = qa_table.scan()
            items = response.get('Items', [])
            
            # Handle pagination if there are many items
            while 'LastEvaluatedKey' in response:
                response = qa_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response.get('Items', []))
            
            for qa_document in items:
                try:
                    # Check if expired (DynamoDB TTL may not have deleted it yet)
                    expires_at = datetime.fromisoformat(qa_document['expires_at'])
                    if datetime.utcnow() >= expires_at:
                        # Delete expired entry
                        qa_table.delete_item(Key={'question_hash': qa_document['question_hash']})
                        continue
                    
                    # Simple text matching - check if question keywords match
                    question_lower = question.lower()
                    stored_question_lower = qa_document['property_address'].lower()
                    
                    # Check for keyword overlap (simple matching)
                    question_words = set(question_lower.split())
                    stored_words = set(stored_question_lower.split())
                    
                    # If significant overlap (at least 50% of words match)
                    if len(question_words) > 0:
                        overlap = len(question_words.intersection(stored_words)) / len(question_words)
                        if overlap >= 0.5:
                            matching_answers.append({
                                "property_address": qa_document['property_address'],
                                "property_details": qa_document['property_details'],
                                "created_at": qa_document['created_at'],
                                "expires_at": qa_document['expires_at'],
                                "match_score": overlap
                            })
                except Exception as e:
                    logger.warning(f"Error processing Q&A entry: {e}")
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

