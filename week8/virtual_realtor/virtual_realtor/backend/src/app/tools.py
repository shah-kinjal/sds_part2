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
from favorites import FavoritesManager

logger = logging.getLogger(__name__)

# Initialize the question manager
question_manager = QuestionManager()

# Initialize the preferences manager
preferences_manager = PreferencesManager()

# Initialize the favorites manager
favorites_manager = FavoritesManager()


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


@tool
def add_property_to_favorites(user_id: str, property_id: str, property_address: str = None) -> str:
    """
    Add a property to the user's favorites list.
    Use when user asks to save, favorite, or bookmark a property.
    
    Args:
        user_id: The user's Cognito sub (user ID)
        property_id: The unique ID of the property
        property_address: The address of the property (optional, for validation/fallback)
        
    Returns:
        A confirmation message
    """
    try:
        if not user_id:
            return "You must be logged in to save properties."

        # Fetch full property data
        # Try retrieving from DB first
        property_data = question_manager.get_property_info_from_db(property_id=property_id)
        
        # If not found in DB, try to fetch from API if address is provided
        if not property_data and property_address:
            logger.info(f"Property {property_id} not in DB, searching API for address: {property_address}")
            # Search by address
            search_results_json = question_manager.search_properties(address=property_address, limit=1)
            try:
                search_results = json.loads(search_results_json)
                if isinstance(search_results, list) and len(search_results) > 0:
                    property_data = search_results[0]
                    # Save context to DB so we have it next time
                    question_manager.add_property_info_to_db(property_data)
                    logger.info(f"Fetched and cached property data for {property_address}")
            except Exception as search_error:
                logger.error(f"Error fetching property details: {search_error}")

        if not property_data:
             return "Property not found in our database. Please ensure you have searched for this property first or provide the full address."

        favorites_manager.add_to_favorites(user_id, property_data, is_visit=False)
        address = property_data.get('formattedAddress', property_address or 'the property')
        return f"Added {address} to your favorites!"
    except Exception as e:
        logger.error(f"Error adding to favorites: {str(e)}")
        return f"Failed to add to favorites: {str(e)}"



@tool
def add_property_to_visit_list(user_id: str, property_id: str) -> str:
    """
    Add a property to the visit list (and favorites if not already saved).
    Use when user wants to schedule a visit or mark property as high priority.
    
    Args:
        user_id: The user's Cognito sub (user ID)
        property_id: The unique ID of the property
        
    Returns:
        A confirmation message
    """
    try:
        if not user_id:
             return "You must be logged in to use the visit list."

        # Check if already in favorites to skip fetch if permissible, 
        # but manager needs data if new.
        property_data = question_manager.get_property_info_from_db(property_id=property_id)
        
        # If in favorites but not in cache? FavoritesManager usually handles basic data.
        # But if completely new, fetch it.
        # We don't have property_address here in arguments! 
        # But maybe we can try to extract address from ID if it follows our convention?
        # Or rely on the agent calling add_property_to_favorites with address first?
        # Let's try to infer address or update the tool signature in a future step if needed.
        # For now, if property_data is None, we might fail unless we can guess address.
        
        # NOTE: Tool signature update requires agent prompt update. 
        # Let's try to parse ID if it looks like an address slug.
        if not property_data and property_id and "-" in property_id:
             # Best effort: convert ID back to probable address string for search
             probable_address = property_id.replace("-", " ")
             # This is a bit risky but better than failing
             logger.info(f"Property {property_id} not in DB, trying to search by inferred address: {probable_address}")
             search_results_json = question_manager.search_properties(address=probable_address, limit=1)
             try:
                search_results = json.loads(search_results_json)
                if isinstance(search_results, list) and len(search_results) > 0:
                    property_data = search_results[0]
                    question_manager.add_property_info_to_db(property_data)
             except:
                pass

        if not property_data:
            # Maybe it is already in favorites but expired from cache? 
            # favorites_manager checks existing favorite first.
            # But add_to_visit_list needs data if it's inserting a new record.
            # If it's already a favorite, favorites_manager might handle it.
            pass

        result = favorites_manager.add_to_visit_list(user_id, property_id, property_data)
        
        address = result.get('formattedAddress', 'the property')
        return f"Added {address} to your visit list!"
    except Exception as e:
        logger.error(f"Error adding to visit list: {str(e)}")
        return f"Failed to add to visit list: {str(e)}"


@tool
def get_user_saved_properties(user_id: str, visit_only: bool = False) -> str:
    """
    Retrieve user's saved properties or visit list.
    
    Args:
        user_id: The user's Cognito sub (user ID)
        visit_only: If True, returns only properties in visit list. If False, returns all favorites.
        
    Returns:
        JSON string containing list of properties
    """
    try:
        if not user_id:
            return json.dumps({"message": "User not authenticated"})
            
        items = favorites_manager.get_user_favorites(user_id, visit_only)
        if not items:
            msg = "You haven't saved any properties yet." if not visit_only else "Your visit list is empty."
            return json.dumps({"message": msg, "items": []})
            
        return json.dumps(items, indent=2)
    except Exception as e:
        logger.error(f"Error getting saved properties: {str(e)}")
        return json.dumps({"error": str(e)})


@tool
def remove_property_from_favorites(user_id: str, property_id: str) -> str:
    """
    Remove a property completely from favorites and visit list.
    
    Args:
        user_id: The user's Cognito sub (user ID)
        property_id: The unique ID of the property
        
    Returns:
        Confirmation message
    """
    try:
        if not user_id:
            return "Unauthorized"
        
        favorites_manager.remove_from_favorites(user_id, property_id)
        return "Property removed from favorites."
    except Exception as e:
        logger.error(f"Error removing from favorites: {str(e)}")
        return f"Error removing property: {str(e)}"


@tool
def remove_property_from_visit_list(user_id: str, property_id: str) -> str:
    """
    Remove a property from the visit list but keep it in favorites.
    
    Args:
        user_id: The user's Cognito sub (user ID)
        property_id: The unique ID of the property
        
    Returns:
        Confirmation message
    """
    try:
        if not user_id:
             return "Unauthorized"

        success = favorites_manager.remove_from_visit_list(user_id, property_id)
        if success:
            return "Property removed from visit list (still in favorites)."
        else:
            return "Property was not in your visit list."
    except Exception as e:
        logger.error(f"Error removing from visit list: {str(e)}")
        return f"Error updating list: {str(e)}"


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
    get_user_preferences,
    add_property_to_favorites,
    add_property_to_visit_list,
    get_user_saved_properties,
    remove_property_from_favorites,
    remove_property_from_visit_list
]
