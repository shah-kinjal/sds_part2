import sys
import os
import logging
import json
import boto3

# Ensure we can import from app and its submodules
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), 'app'))

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

def test_tools():
    table_name = find_table_name()
    if not table_name:
        print("Could not find DynamoDB table")
        return

    print(f"Using table: {table_name}")
    os.environ['DDB_TABLE'] = table_name
    
    # Import tools AFTER setting env var because they initialize managers at module level
    from app.tools import (
        add_property_to_favorites,
        add_property_to_visit_list,
        get_user_saved_properties,
        remove_property_from_favorites,
        remove_property_from_visit_list,
        get_property_info_from_db
    )

    
    # Initialize manager to clean up if needed
    manager = FavoritesManager()
    user_id = "test-tool-user-456"
    property_id = "prop-tool-001"
    
    # Pre-populate property info in DB using the manager logic so tools can find it?
    # Actually, the tools assume the property exists in our DB (using get_property_info_from_db).
    # search_properties returns data but doesn't save to DB unless we call add_property_info_to_db?
    # Wait, get_property_info_from_db checks DynamoDB PROPERTY_INFO item.
    # I need to insert a fake property info into dynamo first so tool can find it.
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    # Insert mock property
    table.put_item(Item={
        'PK': f'PROPERTY_INFO',
        'SK': property_id,
        'id': property_id,
        'formattedAddress': '456 Tool Ln, Tool City, TX 78701',
        'price': 500000,
        'ttl': 1735689600 # Some future timestamp
    })
    print("Inserted mock property info")

    print("\n--- Test 1: Add to Favorites Tool ---")
    res = add_property_to_favorites(user_id=user_id, property_id=property_id)
    print(res)
    assert "Added" in res
    
    print("\n--- Test 2: Get Saved Properties Tool ---")
    res = get_user_saved_properties(user_id=user_id)
    print(res)
    data = json.loads(res)
    assert len(data) >= 1
    assert data[0]['property_id'] == property_id
    
    print("\n--- Test 3: Add to Visit List Tool ---")
    res = add_property_to_visit_list(user_id=user_id, property_id=property_id)
    print(res)
    assert "visit list" in res
    
    print("\n--- Test 4: Get Saved Properties (Visit Only) ---")
    res = get_user_saved_properties(user_id=user_id, visit_only=True)
    print(res)
    data = json.loads(res)
    assert len(data) >= 1
    
    print("\n--- Test 5: Remove from Visit List Tool ---")
    res = remove_property_from_visit_list(user_id=user_id, property_id=property_id)
    print(res)
    assert "removed from visit list" in res
    
    print("\n--- Test 6: Remove from Favorites Tool ---")
    res = remove_property_from_favorites(user_id=user_id, property_id=property_id)
    print(res)
    assert "removed" in res

    print("\n✅ All tool tests passed!")

if __name__ == "__main__":
    test_tools()
