"""
Tool definitions for the Virtual Realtor Agent.

This module contains all the tool functions that the agent can use to interact with
the property database, knowledge base, and visitor management system.
"""

from strands import tool
from strands_tools import retrieve
import json
import logging
from questions import QuestionManager
from preferences import PreferencesManager

logger = logging.getLogger(__name__)

# Initialize the question manager
question_manager = QuestionManager()

# Initialize the preferences manager
preferences_manager = PreferencesManager()


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
def add_property_info_to_db(property_data: dict, ttl_hours: int = None) -> str:
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
def get_property_info_from_db(property_id: str = None, property_address: str = None) -> str:
    """
    Retrieve property information from the database by property ID or address.
    
    Args:
        property_id: The unique property ID (e.g., "3821-Hargis-St-Austin-TX-78723")
        property_address: The formatted property address (e.g., "3821 Hargis St, Austin, TX 78723")
        
    Note: Either property_id or property_address must be provided.
    
    Returns:
        JSON string containing property information or None if not found
    """
    result = question_manager.get_property_info_from_db(property_id=property_id, property_address=property_address)
    if result is None:
        return json.dumps({"message": "Property not found"})
    return json.dumps(result, indent=2)


@tool
def search_properties_by_location_from_db(zipCode: str = None, city: str = None, limit: int = 50) -> str:
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
    result = question_manager.search_properties_by_location_from_db(zipCode=zipCode, city=city, limit=limit)
    return json.dumps(result, indent=2)


@tool
def search_web(query: str, num_results: int = 5) -> str:
    """
    Search the web using Google via the Serper API.
    Use this tool to find current information about neighborhoods, market trends,
    local amenities, schools, crime rates, or any other real-time information
    that might help answer questions about properties and locations.
    
    Args:
        query: The search query string (e.g., "best schools in Austin TX", "crime rate in San Francisco")
        num_results: Number of search results to return (default: 5, max: 10)
        
    Returns:
        JSON string containing search results with titles, links, and snippets
    """
    return question_manager.search_web(query=query, num_results=num_results)


@tool
def get_user_preferences(user_id: str) -> str:
    """
    Retrieve user's property search preferences from the database.
    Use this when generating personalized property suggestions for the user.
    
    Args:
        user_id: The user's Cognito sub (user ID)
        
    Returns:
        JSON string containing user preferences (price range, zip codes, bedrooms, bathrooms, sqft, property type)
        or a message if no preferences are found
    """
    try:
        preferences = preferences_manager.get_preferences(user_id)
        if preferences:
            return json.dumps(preferences, indent=2)
        else:
            return json.dumps({"message": "No preferences found for this user"})
    except Exception as e:
        logger.error(f"Error retrieving user preferences: {str(e)}")
        return json.dumps({"error": f"Failed to retrieve preferences: {str(e)}"})


# Export all tools as a list for easy import
ALL_TOOLS = [
    retrieve,
    save_unanswered_question,
    capture_visitor_info,
    search_properties,
    add_property_info_to_db,
    get_property_info_from_db,
    search_properties_by_location_from_db,
    search_web,
    get_user_preferences
]
