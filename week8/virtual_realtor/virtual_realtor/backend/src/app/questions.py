import uuid
import os
import boto3
import logging
import json
import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from botocore.exceptions import ClientError
from datetime import datetime
from typing import Dict, Any, Optional, List
import time


logger = logging.getLogger(__name__)
load_dotenv()
api_key = os.environ.get("RENTCAST_API_KEY") or os.environ.get("RENTAL_CAST_API_KEY")
if not api_key:
    error_msg = "RENTCAST_API_KEY environment variable is not set. Please set it in your .env file."
    logger.error(error_msg)
    raise ValueError(error_msg)
logger.info(f"API Key: {api_key}")
api_url = os.environ.get("RENTCAST_API_URL", "https://api.rentcast.io/v1/listings/sale")
url = api_url 
logger.info(f"API URL: {url}")


class Question(BaseModel):
    """
    Represents a question to be stored and managed.
    """
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    answer: str | None = None
    processed: bool = False


class Visitor(BaseModel):
    """
    Represents a visitor to be logged.
    """
    visitor_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class QuestionManager:
    """
    Manages questions in DynamoDB.
    """
    def __init__(self):
        """
        Initialises the QuestionManager.
        - Sets up DynamoDB client.
        - Gets table name from environment variables.
        """
        logger.info("Initialising QuestionManager")
        self.dynamodb = boto3.resource('dynamodb')
        self.sns_client = boto3.client('sns')

        self.table_name = os.environ.get('DDB_TABLE')
        if not self.table_name:
            logger.error("DDB_TABLE environment variable is not set")
            raise ValueError("DDB_TABLE environment variable is required.")
        self.table = self.dynamodb.Table(self.table_name)
        logger.info(f"DynamoDB table name: {self.table_name}")

        self.notification_topic_arn = os.environ.get('NOTIFICATION_TOPIC_ARN')
        if self.notification_topic_arn:
            logger.info(f"SNS notification topic ARN: {self.notification_topic_arn}")
        else:
            logger.warning("NOTIFICATION_TOPIC_ARN environment variable is not set. SNS notifications will be disabled.")

    def add_question(self, question: str, answer: str | None = None) -> Question:
        """
        Adds a new question to DynamoDB. The processed flag is set to False.

        :param question: The question text.
        :param answer: The optional answer to the question.
        :return: The created Question object.
        """
        new_question = Question(
            question=question,
            answer=answer
        )

        item_data = new_question.model_dump(exclude_none=True)
        item_data['PK'] = 'QUESTIONS'
        item_data['SK'] = new_question.question_id

        self.table.put_item(
            Item=item_data
        )

        if self.notification_topic_arn:
            try:
                message = f"A new question has been added:\n\n{question}"
                self.sns_client.publish(
                    TopicArn=self.notification_topic_arn,
                    Message=message,
                    Subject="New Question Added"
                )
                logger.info(f"Published new question notification to SNS topic {self.notification_topic_arn}")
            except Exception as e:
                # Do not fail the request if SNS notification fails
                logger.error(f"Failed to publish to SNS topic {self.notification_topic_arn}: {e}", exc_info=True)

        return new_question

    def add_visitor(self, name: str, email: str) -> Visitor:
        """
        Adds a new visitor to the visitor log in DynamoDB.

        :param name: The visitor's name.
        :param email: The visitor's email address.
        :return: The created Visitor object.
        """
        new_visitor = Visitor(
            name=name,
            email=email
        )

        item_data = new_visitor.model_dump()
        item_data['PK'] = 'VISITOR_LOG'
        item_data['SK'] = new_visitor.visitor_id

        self.table.put_item(
            Item=item_data
        )
        if self.notification_topic_arn:
            try:
                message = f"A new visitor has been added:\n\n{name} ({email})"
                self.sns_client.publish(
                    TopicArn=self.notification_topic_arn,
                    Message=message,
                    Subject="New Visitor Added"
                )
                logger.info(f"Published new visitor notification to SNS topic {self.notification_topic_arn}")
            except Exception as e:
                # Do not fail the request if SNS notification fails
                logger.error(f"Failed to publish to SNS topic {self.notification_topic_arn}: {e}", exc_info=True)

        logger.info(f"Added visitor to log: {name} ({email}) with ID: {new_visitor.visitor_id}")

        return new_visitor


    def search_properties(
        self,
        city: str = None,
        state: str = "CA",
        status: str = "Active",
        limit: int = 30,
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
            city: The city name (case-sensitive)
            state: The 2-character state abbreviation (case-sensitive)
            zipCode: The 5-digit zip code
            latitude: Latitude for circular area search
            longitude: Longitude for circular area search
            radius: Search radius in miles (max 100), use with lat/long or address
            propertyType: Type of property (Single Family, Condo, Townhouse, Manufactured, Multi-Family, Apartment, Land)
            bedrooms: Number of bedrooms (supports ranges and multiple values)
            bathrooms: Number of bathrooms (supports fractions, ranges, and multiple values)
            squareFootage: Total living area in sq ft (supports ranges and multiple values)
            lotSize: Total lot size in sq ft (supports ranges and multiple values)
            yearBuilt: Year of construction (supports ranges and multiple values)
            status: Property status (Active or Inactive, default: "Active")
            price: Listed price (supports ranges and multiple values)
            daysOld: Days since listing (minimum 1, supports ranges)
            limit: Maximum number of results (1-500, default: 10)
            offset: Index of first record for pagination (default: 0)
            includeTotalCount: Include total count in X-Total-Count header (default: False)
            
        Returns:
            JSON string containing property listings or error message
        """
        logger.info(f"search_properties called with params - city: {city}, state: {state}, zipCode: {zipCode}, address: {address}")
        try:    
            # Build params dict, only including non-None values
            params = {}
            
            if address:
                params["address"] = address
            if city:
                params["city"] = city
            if state:
                params["state"] = state
            if zipCode:
                params["zipCode"] = zipCode
            if latitude is not None:
                params["latitude"] = latitude
            if longitude is not None:
                params["longitude"] = longitude
            if radius is not None:
                params["radius"] = radius
            if propertyType:
                params["propertyType"] = propertyType
            if bedrooms:
                params["bedrooms"] = bedrooms
            if bathrooms:
                params["bathrooms"] = bathrooms
            if squareFootage:
                params["squareFootage"] = squareFootage
            if lotSize:
                params["lotSize"] = lotSize
            if yearBuilt:
                params["yearBuilt"] = yearBuilt
            if status:
                params["status"] = status
            if price:
                params["price"] = price
            if daysOld:
                params["daysOld"] = daysOld
            if limit:
                params["limit"] = limit
            if offset is not None:
                params["offset"] = offset
            if includeTotalCount:
                params["includeTotalCount"] = includeTotalCount
            
            headers = {
                "accept": "application/json",
                "X-Api-Key": api_key
            }
            
            logger.info(f"Making request to {url} with params: {params}")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully retrieved {len(data) if isinstance(data, list) else 'unknown'} properties")
            return json.dumps(data, indent=2)
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching properties from RentCast API: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return json.dumps({"error": error_msg})
        except Exception as e:
            error_msg = f"Unexpected error in search_properties: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return json.dumps({"error": error_msg})

    def add_property_info(
        self,
        property_data: Dict[str, Any],
        ttl_hours: int = None
    ) -> Dict[str, Any]:
        """
        Add or update property information in DynamoDB with optional TTL.
        
        Args:
            property_data: Dictionary containing property information.
                          Must include either 'id' or 'formattedAddress'.
            ttl_hours: Time-to-live in hours (default from env var PROPERTY_TTL_HOURS or 12)
            
        Returns:
            Dictionary with success status and property ID
        """
        try:
            # Get TTL from parameter, environment, or default to 12 hours
            if ttl_hours is None:
                ttl_hours = int(os.environ.get('PROPERTY_TTL_HOURS', '12'))
            
            # Calculate TTL timestamp (current time + ttl_hours)
            ttl_timestamp = int(time.time()) + (ttl_hours * 3600)
            
            # Extract property ID or generate from address
            property_id = property_data.get('id')
            if not property_id:
                # Generate ID from formatted address if not provided
                formatted_address = property_data.get('formattedAddress')
                if not formatted_address:
                    raise ValueError("Property data must include 'id' or 'formattedAddress'")
                # Create ID from address (replace spaces and commas)
                property_id = formatted_address.replace(' ', '-').replace(',', '')
            
            # Prepare item for DynamoDB
            item_data = {
                'PK': 'PROPERTY_INFO',
                'SK': property_id,
                'property_id': property_id,
                'ttl': ttl_timestamp,
                'created_at': datetime.utcnow().isoformat(),
                **property_data  # Include all property data
            }
            
            # Add indexes for searching
            if 'zipCode' in property_data:
                item_data['zipCode'] = property_data['zipCode']
            if 'city' in property_data:
                item_data['city'] = property_data['city']
            if 'formattedAddress' in property_data:
                item_data['formattedAddress'] = property_data['formattedAddress']
            
            # Store in DynamoDB
            self.table.put_item(Item=item_data)
            
            logger.info(f"Added property info for {property_id} with TTL of {ttl_hours} hours")
            
            return {
                'success': True,
                'property_id': property_id,
                'ttl_hours': ttl_hours,
                'expires_at': datetime.fromtimestamp(ttl_timestamp).isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error adding property info: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg
            }

    def get_property_info(
        self,
        property_id: str = None,
        property_address: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve property information by property ID or address.
        
        Args:
            property_id: The unique property ID
            property_address: The formatted property address
            
        Returns:
            Dictionary containing property information or None if not found
        """
        try:
            if not property_id and not property_address:
                raise ValueError("Either property_id or property_address must be provided")
            
            # If address is provided but not ID, generate ID from address
            if not property_id and property_address:
                property_id = property_address.replace(' ', '-').replace(',', '')
            
            # Query DynamoDB
            response = self.table.get_item(
                Key={
                    'PK': 'PROPERTY_INFO',
                    'SK': property_id
                }
            )
            
            if 'Item' in response:
                item = response['Item']
                # Remove DynamoDB-specific fields
                item.pop('PK', None)
                item.pop('SK', None)
                
                logger.info(f"Retrieved property info for {property_id}")
                return item
            else:
                logger.info(f"No property info found for {property_id}")
                return None
                
        except Exception as e:
            error_msg = f"Error retrieving property info: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg}

    def search_properties_by_location(
        self,
        zipCode: str = None,
        city: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for properties in DynamoDB by zipCode or city name.
        
        Args:
            zipCode: The 5-digit zip code to search for
            city: The city name to search for
            limit: Maximum number of results to return (default: 50)
            
        Returns:
            List of property dictionaries matching the search criteria
        """
        try:
            if not zipCode and not city:
                raise ValueError("Either zipCode or city must be provided")
            
            # Use scan with filter expression (Note: For production, consider using GSI)
            filter_expressions = []
            expression_attribute_values = {}
            expression_attribute_names = {}
            
            if zipCode:
                filter_expressions.append('#zipCode = :zipCode')
                expression_attribute_values[':zipCode'] = zipCode
                expression_attribute_names['#zipCode'] = 'zipCode'
            
            if city:
                filter_expressions.append('#city = :city')
                expression_attribute_values[':city'] = city
                expression_attribute_names['#city'] = 'city'
            
            # Combine filter expressions
            filter_expression = ' AND '.join(filter_expressions)
            
            # Query parameters
            scan_kwargs = {
                'FilterExpression': filter_expression,
                'ExpressionAttributeValues': expression_attribute_values,
                'ExpressionAttributeNames': expression_attribute_names,
                'Limit': limit
            }
            
            # Add condition to only get PROPERTY_INFO items
            scan_kwargs['FilterExpression'] = f'PK = :pk AND ({filter_expression})'
            scan_kwargs['ExpressionAttributeValues'][':pk'] = 'PROPERTY_INFO'
            
            response = self.table.scan(**scan_kwargs)
            
            items = response.get('Items', [])
            
            # Clean up DynamoDB-specific fields
            cleaned_items = []
            for item in items:
                item.pop('PK', None)
                item.pop('SK', None)
                cleaned_items.append(item)
            
            logger.info(f"Found {len(cleaned_items)} properties for zipCode={zipCode}, city={city}")
            
            return cleaned_items
            
        except Exception as e:
            error_msg = f"Error searching properties by location: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return [{'error': error_msg}]

    def search_web(
        self,
        query: str,
        num_results: int = 5
    ) -> str:
        """
        Search the web using Google via the Serper API.
        
        Args:
            query: The search query string
            num_results: Number of search results to return (default: 5, max: 10)
            
        Returns:
            JSON string containing search results with titles, links, and snippets
        """
        serper_api_key = os.environ.get("SERPER_API_KEY", "")
        serper_url = os.environ.get("SERPER_URL", "https://google.serper.dev/search")
        
        if not serper_api_key:
            logger.error("SERPER_API_KEY environment variable is not set")
            return json.dumps({
                "error": "Web search is not configured. Please contact support.",
                "results": []
            })
        
        try:
            headers = {
                "X-API-KEY": serper_api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": min(num_results, 10)  # Cap at 10 results
            }
            
            logger.info(f"Searching web for: {query}")
            response = requests.post(serper_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract relevant information
            results = {
                "query": query,
                "organic_results": []
            }
            
            # Add organic search results
            if "organic" in data:
                for item in data["organic"][:num_results]:
                    results["organic_results"].append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    })
            
            # Add knowledge graph if available
            if "knowledgeGraph" in data:
                kg = data["knowledgeGraph"]
                results["knowledge_graph"] = {
                    "title": kg.get("title", ""),
                    "description": kg.get("description", ""),
                    "attributes": kg.get("attributes", {})
                }
            
            # Add answer box if available
            if "answerBox" in data:
                ab = data["answerBox"]
                results["answer_box"] = {
                    "answer": ab.get("answer", ""),
                    "snippet": ab.get("snippet", "")
                }
            
            logger.info(f"Web search completed successfully with {len(results['organic_results'])} results")
            return json.dumps(results, indent=2)
            
        except requests.exceptions.Timeout:
            logger.error(f"Web search timed out for query: {query}")
            return json.dumps({
                "error": "Search request timed out. Please try again.",
                "results": []
            })
        except requests.exceptions.RequestException as e:
            logger.error(f"Web search failed for query '{query}': {str(e)}")
            return json.dumps({
                "error": f"Search failed: {str(e)}",
                "results": []
            })
        except Exception as e:
            logger.error(f"Unexpected error during web search: {str(e)}")
            return json.dumps({
                "error": f"An unexpected error occurred: {str(e)}",
                "results": []
            })
