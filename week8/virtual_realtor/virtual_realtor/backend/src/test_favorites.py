import sys
import os
import logging
import boto3



from app.favorites import FavoritesManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_table_name():
    dynamodb = boto3.client('dynamodb')
    tables = dynamodb.list_tables()['TableNames']
    for name in tables:
        if 'AdminTable' in name:
             return name
    return None

def test_manager():
    table_name = find_table_name()
    if not table_name:
        print("Could not find DynamoDB table")
        return

    print(f"Using table: {table_name}")
    os.environ['DDB_TABLE'] = table_name
    
    manager = FavoritesManager()
    user_id = "test-user-123"
    
    # Mock property data
    prop_data = {
        "id": "prop-001",
        "formattedAddress": "123 Test St, Test City, CA 90210",
        "price": 1000000,
        "bedrooms": 3,
        "bathrooms": 2.5,
        "squareFootage": 2000,
        "propertyType": "Single Family"
    }

    print("\n--- Testing Add to Favorites ---")
    try:
        fav = manager.add_to_favorites(user_id, prop_data)
        print(f"Added: {fav['property_id']} - {fav['formattedAddress']}")
    except Exception as e:
        print(f"Error adding favorite: {e}")
        return

    print("\n--- Testing Get User Favorites ---")
    favorites = manager.get_user_favorites(user_id)
    print(f"Found {len(favorites)} favorites")
    assert any(f['property_id'] == 'prop-001' for f in favorites)
    
    print("\n--- Testing Visit List (Add) ---")
    visit = manager.add_to_visit_list(user_id, "prop-001")
    print(f"Visit candidate: {visit['is_visit_candidate']}")
    assert visit['is_visit_candidate'] == True
    
    print("\n--- Testing Get Count ---")
    counts = manager.get_favorites_count(user_id)
    print(f"Counts: {counts}")
    assert counts['visit'] >= 1
    
    print("\n--- Testing Visit List (Remove) ---")
    manager.remove_from_visit_list(user_id, "prop-001")
    fav = manager.get_favorite_by_id(user_id, "prop-001")
    print(f"Visit candidate after remove: {fav.get('is_visit_candidate')}")
    assert fav.get('is_visit_candidate') == False

    print("\n--- Testing Remove from Favorites ---")
    manager.remove_from_favorites(user_id, "prop-001")
    fav = manager.get_favorite_by_id(user_id, "prop-001")
    print(f"Exists after delete: {fav is not None}")
    assert fav is None
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_manager()
