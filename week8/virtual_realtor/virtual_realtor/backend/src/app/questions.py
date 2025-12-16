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

# Configuration: Use mock API for testing
USE_MOCK_API = os.environ.get("USE_MOCK_RENTCAST_API", "true").lower() == "true"

if USE_MOCK_API:
    logger.warning("⚠️ USING MOCK RENTCAST API - Set USE_MOCK_RENTCAST_API=false to use real API")
    api_key = "mock-api-key"
    api_url = "mock://rentcast.io/v1/listings/sale"
else:
    api_key = os.environ.get("RENTCAST_API_KEY") or os.environ.get("RENTAL_CAST_API_KEY")
    if not api_key:
        error_msg = "RENTCAST_API_KEY environment variable is not set. Please set it in your .env file."
        logger.error(error_msg)
        raise ValueError(error_msg)
    logger.info(f"API Key: {api_key[:10]}...")
    api_url = os.environ.get("RENTCAST_API_URL", "https://api.rentcast.io/v1/listings/sale")
    
url = api_url 
logger.info(f"API URL: {url}")


def generate_mock_properties(
    city: str = None,
    state: str = "CA",
    zipCode: str = None,
    limit: int = 10,
    bedrooms: str = None,
    bathrooms: str = None,
    price: str = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Generate mock property data for testing.
    Returns realistic property listings based on search criteria.
    """
    # Sample California cities and zip codes
    mock_locations = {
        "94539": {"city": "Fremont", "state": "CA"},
        "94102": {"city": "San Francisco", "state": "CA"},
        "94301": {"city": "Palo Alto", "state": "CA"},
        "94025": {"city": "Menlo Park", "state": "CA"},
        "94041": {"city": "Mountain View", "state": "CA"},
    }
    
    # Determine location
    if zipCode and zipCode in mock_locations:
        location = mock_locations[zipCode]
    elif city:
        location = {"city": city, "state": state or "CA"}
    else:
        location = {"city": "Fremont", "state": "CA"}
        zipCode = "94539"
    
    # Parse search criteria
    min_price, max_price = 500000, 2000000
    if price:
        if '-' in price:
            parts = price.split('-')
            min_price, max_price = int(parts[0]), int(parts[1])
    
    min_beds, max_beds = 2, 5
    if bedrooms:
        if '-' in bedrooms:
            parts = bedrooms.split('-')
            min_beds, max_beds = int(parts[0]), int(parts[1])
    
    # Sample street names
    streets = [
        "Mohave Cmn", "Mission Blvd", "Hackamore Ln", "Corte Verde", "Zacate Ave",
        "Mill Creek Rd", "Highland Ter", "Pinion St", "Oak St", "Maple Ave"
    ]
    
    # Property types and their typical characteristics
    property_types = [
        {"type": "Single Family", "sqft_range": (1500, 3000), "lot_mult": 5},
        {"type": "Condo", "sqft_range": (800, 1500), "lot_mult": 0},
        {"type": "Townhouse", "sqft_range": (1200, 2000), "lot_mult": 0.1},
    ]
    
    properties = []
    import random
    random.seed(hash(zipCode or city or "default"))  # Consistent results for same search
    
    for i in range(min(limit, 10)):
        prop_type = random.choice(property_types)
        beds = random.randint(max(min_beds, 1), min(max_beds, 6))
        baths = random.choice([1.5, 2, 2.5, 3, 3.5, 4]) if beds >= 3 else random.choice([1, 1.5, 2])
        sqft = random.randint(*prop_type["sqft_range"])
        lot_size = int(sqft * prop_type["lot_mult"]) if prop_type["lot_mult"] > 0 else sqft
        
        base_price = random.randint(min_price, max_price)
        year_built = random.randint(1970, 2020)
        days_on_market = random.randint(1, 180)
        
        street_num = random.randint(100, 9999)
        street = random.choice(streets)
        address = f"{street_num} {street}, {location['city']}, {location['state']} {zipCode}"
        property_id = address.replace(" ", "-").replace(",", "")
        
        property_data = {
            "id": property_id,
            "formattedAddress": address,
            "addressLine1": f"{street_num} {street}",
            "addressLine2": None,
            "city": location["city"],
            "state": location["state"],
            "zipCode": zipCode or "94539",
            "county": "Alameda",
            "latitude": round(37.5 + random.uniform(-0.1, 0.1), 6),
            "longitude": round(-121.9 + random.uniform(-0.1, 0.1), 6),
            "propertyType": prop_type["type"],
            "bedrooms": beds,
            "bathrooms": baths,
            "squareFootage": sqft,
            "lotSize": lot_size if lot_size > 0 else None,
            "yearBuilt": year_built,
            "status": "Active",
            "price": base_price,
            "listingType": "Standard",
            "listedDate": f"{2024 - (days_on_market // 365)}-{str((days_on_market % 365) // 30 + 1).zfill(2)}-01T00:00:00.000Z",
            "daysOnMarket": days_on_market,
            "mlsName": random.choice(["BayEast", "MLSListings", "BAREIS"]),
            "mlsNumber": f"{random.randint(40000000, 42000000)}",
            "listingAgent": {
                "name": random.choice(["John Smith", "Jane Doe", "Mike Johnson", "Sarah Williams"]),
                "phone": f"510{random.randint(1000000, 9999999)}"
            }
        }
        
        # Add HOA fee for condos and townhouses
        if prop_type["type"] in ["Condo", "Townhouse"]:
            property_data["hoa"] = {"fee": random.randint(300, 600)}
        
        properties.append(property_data)
    
    logger.info(f"🎭 Generated {len(properties)} mock properties for {location['city']}, {zipCode}")
    return properties


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
        Search for properties for sale using the RentCast API (or mock API if enabled).
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
        
        # Use mock API if enabled
        if USE_MOCK_API:
            logger.info("Using MOCK RentCast API")
            try:
                mock_properties = generate_mock_properties(
                    city=city,
                    state=state,
                    zipCode=zipCode,
                    limit=limit,
                    bedrooms=bedrooms,
                    bathrooms=bathrooms,
                    price=price,
                    propertyType=propertyType
                )
                return json.dumps(mock_properties, indent=2)
            except Exception as e:
                error_msg = f"Error generating mock properties: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return json.dumps({"error": error_msg})
        
        # Use real RentCast API
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

    def add_property_info_to_db(
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

    def get_property_info_from_db(
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

    def search_properties_by_location_from_db(
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
