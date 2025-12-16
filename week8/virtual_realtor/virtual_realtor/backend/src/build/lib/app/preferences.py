import os
import boto3
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class PriceRange(BaseModel):
    """Price range for property search"""
    min: Optional[int] = None
    max: Optional[int] = None

    @model_validator(mode='after')
    def validate_range(self):
        if self.min is not None and self.max is not None:
            if self.max < self.min:
                raise ValueError("max must be greater than or equal to min")
        if self.min is not None and self.min < 0:
            raise ValueError("min must be positive")
        if self.max is not None and self.max < 0:
            raise ValueError("max must be positive")
        return self


class BedroomRange(BaseModel):
    """Bedroom count range"""
    min: Optional[int] = None
    max: Optional[int] = None

    @model_validator(mode='after')
    def validate_range(self):
        if self.min is not None and self.max is not None:
            if self.max < self.min:
                raise ValueError("max must be greater than or equal to min")
        if self.min is not None and self.min < 0:
            raise ValueError("min must be non-negative")
        if self.max is not None and self.max < 0:
            raise ValueError("max must be non-negative")
        return self


class BathroomRange(BaseModel):
    """Bathroom count range (supports fractions)"""
    min: Optional[float] = None
    max: Optional[float] = None

    @model_validator(mode='after')
    def validate_range(self):
        if self.min is not None and self.max is not None:
            if self.max < self.min:
                raise ValueError("max must be greater than or equal to min")
        if self.min is not None and self.min < 0:
            raise ValueError("min must be non-negative")
        if self.max is not None and self.max < 0:
            raise ValueError("max must be non-negative")
        return self


class SqftRange(BaseModel):
    """Square footage range"""
    min: Optional[int] = None
    max: Optional[int] = None

    @model_validator(mode='after')
    def validate_range(self):
        if self.min is not None and self.max is not None:
            if self.max < self.min:
                raise ValueError("max must be greater than or equal to min")
        if self.min is not None and self.min < 0:
            raise ValueError("min must be positive")
        if self.max is not None and self.max < 0:
            raise ValueError("max must be positive")
        return self


class UserPreferences(BaseModel):
    """User property search preferences"""
    userId: str
    email: Optional[str] = None
    priceRange: Optional[PriceRange] = None
    zipCodes: List[str] = Field(default_factory=list)
    bedrooms: Optional[BedroomRange] = None
    bathrooms: Optional[BathroomRange] = None
    sqft: Optional[SqftRange] = None
    propertyType: Optional[str] = None
    updatedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v:
            # Basic email validation
            if '@' not in v or '.' not in v.split('@')[1]:
                raise ValueError("Invalid email format")
        return v

    @field_validator('zipCodes')
    @classmethod
    def validate_zipcodes(cls, v: List[str]) -> List[str]:
        if len(v) > 3:
            raise ValueError("Maximum 3 zip codes allowed")
        for zipcode in v:
            if not zipcode.isdigit() or len(zipcode) != 5:
                raise ValueError(f"Invalid zip code format: {zipcode}. Must be 5 digits.")
        return v

    @field_validator('propertyType')
    @classmethod
    def validate_property_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v:
            valid_types = [
                "Single Family",
                "Condo",
                "Townhouse",
                "Manufactured",
                "Multi-Family",
                "Apartment",
                "Land"
            ]
            if v not in valid_types:
                raise ValueError(f"Invalid property type. Must be one of: {', '.join(valid_types)}")
        return v


class PreferencesManager:
    """Manages user preferences in DynamoDB"""

    def __init__(self):
        """Initialize the PreferencesManager with DynamoDB connection"""
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = os.environ.get('DDB_TABLE')
        if not self.table_name:
            logger.error("DDB_TABLE environment variable is not set")
            raise ValueError("DDB_TABLE environment variable is required.")
        self.table = self.dynamodb.Table(self.table_name)
        logger.info(f"PreferencesManager initialized with table: {self.table_name}")

    def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user preferences from DynamoDB.

        Args:
            user_id: Cognito sub (user ID)

        Returns:
            Dictionary containing user preferences or None if not found
        """
        try:
            # Mask user ID in logs (show only first 8 chars)
            masked_user_id = f"{user_id[:8]}..." if len(user_id) > 8 else user_id
            logger.info(f"Retrieving preferences for user: {masked_user_id}")

            response = self.table.get_item(
                Key={
                    'PK': f'USER_PREF#{user_id}',
                    'SK': 'PROFILE'
                }
            )

            if 'Item' in response:
                item = response['Item']
                # Remove DynamoDB-specific fields
                item.pop('PK', None)
                item.pop('SK', None)
                
                # Convert Decimals back to floats for JSON serialization
                item = self._convert_decimals_to_float(item)

                logger.info(f"Retrieved preferences for user: {masked_user_id}")
                return item
            else:
                logger.info(f"No preferences found for user: {masked_user_id}")
                return None

        except ClientError as e:
            logger.error(f"DynamoDB error retrieving preferences: {e.response['Error']['Message']}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving preferences: {str(e)}", exc_info=True)
            raise

    def _convert_decimals_to_float(self, obj: Any) -> Any:
        """
        Recursively convert Decimal values to float for JSON serialization.
        
        Args:
            obj: Object to convert (can be dict, list, Decimal, or other types)
            
        Returns:
            Converted object with Decimals replaced by floats
        """
        if isinstance(obj, dict):
            return {k: self._convert_decimals_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals_to_float(item) for item in obj]
        elif isinstance(obj, Decimal):
            # Convert Decimal to float for JSON
            return float(obj)
        else:
            return obj

    def save_preferences(self, preferences: UserPreferences) -> Dict[str, Any]:
        """
        Save or update user preferences in DynamoDB.

        Args:
            preferences: UserPreferences object to save

        Returns:
            Dictionary with success status and updated timestamp
        """
        try:
            # Mask user ID and email in logs
            masked_user_id = f"{preferences.userId[:8]}..." if len(preferences.userId) > 8 else preferences.userId
            masked_email = "<masked-email>" if preferences.email else None
            logger.info(f"Saving preferences for user: {masked_user_id}, email: {masked_email}")

            # Convert to dict and prepare for DynamoDB
            prefs_dict = preferences.model_dump(exclude_none=True)
            
            # Convert floats to Decimal for DynamoDB compatibility
            prefs_dict = self._convert_floats_to_decimal(prefs_dict)
            
            # Add DynamoDB keys
            item_data = {
                'PK': f'USER_PREF#{preferences.userId}',
                'SK': 'PROFILE',
                **prefs_dict
            }

            # Save to DynamoDB
            self.table.put_item(Item=item_data)

            logger.info(f"Successfully saved preferences for user: {masked_user_id}")

            return {
                'success': True,
                'userId': preferences.userId,
                'updatedAt': preferences.updatedAt
            }

        except ClientError as e:
            logger.error(f"DynamoDB error saving preferences: {e.response['Error']['Message']}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving preferences: {str(e)}", exc_info=True)
            raise

    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """
        Recursively convert float values to Decimal for DynamoDB compatibility.
        
        Args:
            obj: Object to convert (can be dict, list, float, or other types)
            
        Returns:
            Converted object with floats replaced by Decimals
        """
        if isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        elif isinstance(obj, float):
            # Convert float to Decimal
            return Decimal(str(obj))
        else:
            return obj

    def delete_preferences(self, user_id: str) -> bool:
        """
        Delete user preferences from DynamoDB.

        Args:
            user_id: Cognito sub (user ID)

        Returns:
            True if deleted successfully
        """
        try:
            masked_user_id = f"{user_id[:8]}..." if len(user_id) > 8 else user_id
            logger.info(f"Deleting preferences for user: {masked_user_id}")

            self.table.delete_item(
                Key={
                    'PK': f'USER_PREF#{user_id}',
                    'SK': 'PROFILE'
                }
            )

            logger.info(f"Successfully deleted preferences for user: {masked_user_id}")
            return True

        except ClientError as e:
            logger.error(f"DynamoDB error deleting preferences: {e.response['Error']['Message']}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting preferences: {str(e)}", exc_info=True)
            raise

