import os
import boto3
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger(__name__)

class FavoriteProperty(BaseModel):
    """Model for a favorite property record"""
    user_id: str
    property_id: str
    is_visit_candidate: bool = False
    favorited_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    last_refreshed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Property Snapshot Fields
    formattedAddress: str
    price: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    squareFootage: Optional[int] = None
    propertyType: Optional[str] = None
    city: Optional[str] = None
    zipCode: Optional[str] = None
    daysOnMarket: Optional[int] = None
    source: Optional[str] = None
    sourceUrl: Optional[str] = None
    listingDate: Optional[str] = None
    imageUrl: Optional[str] = None
    
    # Snapshot Metadata
    snapshot_price: Optional[int] = None
    snapshot_timestamp: Optional[str] = None

    @model_validator(mode='after')
    def set_snapshot_metadata(self):
        if self.snapshot_price is None and self.price is not None:
            self.snapshot_price = self.price
        if self.snapshot_timestamp is None:
            self.snapshot_timestamp = datetime.utcnow().isoformat()
        return self

class FavoritesManager:
    """Manages user favorites and visit list in DynamoDB"""

    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = os.environ.get('DDB_TABLE')
        if not self.table_name:
            logger.error("DDB_TABLE environment variable is not set")
            raise ValueError("DDB_TABLE environment variable is required.")
        self.table = self.dynamodb.Table(self.table_name)
        logger.info(f"FavoritesManager initialized with table: {self.table_name}")

    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """Recursively convert float values to Decimal for DynamoDB compatibility."""
        if isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        elif isinstance(obj, float):
            return Decimal(str(obj))
        return obj

    def _convert_decimals_to_float(self, obj: Any) -> Any:
        """Recursively convert Decimal values to float for JSON serialization."""
        if isinstance(obj, dict):
            return {k: self._convert_decimals_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals_to_float(item) for item in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        return obj

    def _extract_property_snapshot(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts relevant fields from property API response"""
        fields = [
            'formattedAddress', 'price', 'bedrooms', 'bathrooms', 
            'squareFootage', 'propertyType', 'city', 'zipCode', 
            'daysOnMarket', 'source', 'sourceUrl', 'listingDate', 'imageUrl'
        ]
        snapshot = {}
        for field in fields:
            if field in property_data:
                snapshot[field] = property_data[field]
        return snapshot

    def _create_favorite_record(self, user_id: str, property_data: Dict[str, Any], is_visit: bool = False) -> Dict[str, Any]:
        """Creates DynamoDB item structure with PK/SK"""
        property_id = property_data.get('id') or property_data.get('property_id')
        if not property_id:
            raise ValueError("Property data must contain 'id' or 'property_id'")

        snapshot = self._extract_property_snapshot(property_data)
        
        favorite = FavoriteProperty(
            user_id=user_id,
            property_id=property_id,
            is_visit_candidate=is_visit,
            **snapshot
        )
        
        item_dict = favorite.model_dump(exclude_none=True)
        item_dict = self._convert_floats_to_decimal(item_dict)
        
        return {
            'PK': f'USER#{user_id}',
            'SK': f'FAVORITE#{property_id}',
            **item_dict
        }

    def _should_refresh(self, last_refreshed_at: str) -> bool:
        """Check if >24 hours since last refresh"""
        if not last_refreshed_at:
            return True
        last_refresh = datetime.fromisoformat(last_refreshed_at)
        return datetime.utcnow() - last_refresh > timedelta(hours=24)

    def add_to_favorites(self, user_id: str, property_data: Dict[str, Any], is_visit: bool = False) -> Dict[str, Any]:
        """Add a property to favorites"""
        try:
            item = self._create_favorite_record(user_id, property_data, is_visit)
            property_id = property_data.get('id') or property_data.get('property_id')
            
            logger.info(f"Adding property {property_id} to favorites for user {user_id}")
            
            self.table.put_item(Item=item)
            
            return self._convert_decimals_to_float(item)
        except ClientError as e:
            logger.error(f"DynamoDB error adding favorite: {e.response['Error']['Message']}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error adding favorite: {str(e)}", exc_info=True)
            raise

    def get_user_favorites(self, user_id: str, visit_only: bool = False) -> List[Dict[str, Any]]:
        """Retrieve user's favorite properties"""
        try:
            key_condition = Key('PK').eq(f'USER#{user_id}') & Key('SK').begins_with('FAVORITE#')
            
            if visit_only:
                response = self.table.query(
                    KeyConditionExpression=key_condition,
                    FilterExpression=Attr('is_visit_candidate').eq(True)
                )
            else:
                response = self.table.query(
                    KeyConditionExpression=key_condition
                )
                
            items = response.get('Items', [])
            items = [self._convert_decimals_to_float(item) for item in items]
            
            # Sort by favorited_at desc
            items.sort(key=lambda x: x.get('favorited_at', ''), reverse=True)
            
            return items
        except Exception as e:
            logger.error(f"Error getting favorites for user {user_id}: {str(e)}", exc_info=True)
            raise

    def get_favorite_by_id(self, user_id: str, property_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific favorite property"""
        try:
            response = self.table.get_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': f'FAVORITE#{property_id}'
                }
            )
            item = response.get('Item')
            if item:
                return self._convert_decimals_to_float(item)
            return None
        except Exception as e:
            logger.error(f"Error getting favorite {property_id} for user {user_id}: {str(e)}")
            raise

    def remove_from_favorites(self, user_id: str, property_id: str) -> bool:
        """Remove property from favorites"""
        try:
            logger.info(f"Removing property {property_id} from favorites for user {user_id}")
            self.table.delete_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': f'FAVORITE#{property_id}'
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error removing favorite {property_id}: {str(e)}")
            raise

    def add_to_visit_list(self, user_id: str, property_id: str, property_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add property to visit list (and favorites if not present)"""
        try:
            # Check if exists
            existing = self.get_favorite_by_id(user_id, property_id)
            if existing:
                logger.info(f"Updating property {property_id} to visit list for user {user_id}")
                self.table.update_item(
                    Key={
                        'PK': f'USER#{user_id}',
                        'SK': f'FAVORITE#{property_id}'
                    },
                    UpdateExpression="SET is_visit_candidate = :val",
                    ExpressionAttributeValues={':val': True}
                )
                existing['is_visit_candidate'] = True
                return existing
            else:
                if not property_data:
                    raise ValueError("Property data required for new favorite")
                return self.add_to_favorites(user_id, property_data, is_visit=True)
        except Exception as e:
            logger.error(f"Error adding to visit list: {str(e)}")
            raise

    def remove_from_visit_list(self, user_id: str, property_id: str) -> bool:
        """Remove from visit list but keep in favorites"""
        try:
            logger.info(f"Removing property {property_id} from visit list for user {user_id}")
            self.table.update_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': f'FAVORITE#{property_id}'
                },
                UpdateExpression="SET is_visit_candidate = :val",
                ExpressionAttributeValues={':val': False},
                ConditionExpression="attribute_exists(PK)" 
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return False
            raise
        except Exception as e:
             logger.error(f"Error removing from visit list: {str(e)}")
             raise

    def get_favorites_count(self, user_id: str) -> Dict[str, int]:
        """Get counts of favorites and visit candidates"""
        favorites = self.get_user_favorites(user_id, visit_only=False)
        visit_count = sum(1 for f in favorites if f.get('is_visit_candidate'))
        return {
            "total": len(favorites),
            "favorites": len(favorites),
            "visit": visit_count
        }

    def merge_session_favorites(self, from_session_id: str, to_user_id: str) -> int:
        """Merge anonymous session favorites to user account"""
        try:
            session_favorites = self.get_user_favorites(from_session_id)
            merged_count = 0
            
            for item in session_favorites:
                property_id = item['property_id']
                # Check if user already has this favorite
                if not self.get_favorite_by_id(to_user_id, property_id):
                    # Create new record for user
                    new_item = item.copy()
                    new_item['PK'] = f'USER#{to_user_id}'
                    new_item['user_id'] = to_user_id
                    
                    # Store as new item
                    new_item_decimal = self._convert_floats_to_decimal(new_item)
                    self.table.put_item(Item=new_item_decimal)
                    merged_count += 1
                
                # Delete old session record
                self.remove_from_favorites(from_session_id, property_id)
                
            logger.info(f"Merged {merged_count} favorites from session {from_session_id} to user {to_user_id}")
            return merged_count
        except Exception as e:
            logger.error(f"Error merging session favorites: {str(e)}")
            raise

    def refresh_property_data(self, user_id: str, property_id: str, updated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Refresh property data if stale"""
        try:
            existing = self.get_favorite_by_id(user_id, property_id)
            if not existing:
                raise ValueError(f"Favorite {property_id} not found")

            if self._should_refresh(existing.get('last_refreshed_at')):
                logger.info(f"Refreshing data for property {property_id}")
                
                # Update snapshot
                snapshot = self._extract_property_snapshot(updated_data)
                
                # Prepare update expression (simplified for readability, in production we might dynamic build)
                # Here we'll just put the whole item again with updated fields to be safe and simple with Pydantic
                
                # Merge existing with new snapshot
                existing.update(snapshot)
                existing['last_refreshed_at'] = datetime.utcnow().isoformat()
                
                # Validate with model
                updated_model = FavoriteProperty(**existing)
                
                item_dict = updated_model.model_dump(exclude_none=True)
                item_dict = self._convert_floats_to_decimal(item_dict)
                
                item = {
                    'PK': f'USER#{user_id}',
                    'SK': f'FAVORITE#{property_id}',
                    **item_dict
                }
                
                self.table.put_item(Item=item)
                return self._convert_decimals_to_float(item)
            
            return existing
        except Exception as e:
            logger.error(f"Error refreshing property {property_id}: {str(e)}")
            raise
