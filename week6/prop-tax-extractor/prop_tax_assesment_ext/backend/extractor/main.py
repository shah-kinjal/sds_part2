import json
import boto3
import os
from strands import Agent
from pydantic import BaseModel, Field, ConfigDict

model_id = os.environ.get("MODEL_ID", "")
s3_client = boto3.client('s3')

agent = Agent(model=model_id, callback_handler=None)

class PropertyTaxAssessmentData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    assesed_property_value_land: float = Field(description="Property value land from the statement", alias="PropertyValueLand")
    assesed_property_value_building: float = Field(description="Property value building from the statement", alias="PropertyValueBuilding")
    assesed_property_value_total: float = Field(description="Property value total from the statement", alias="PropertyValueTotal")
    current_tax_year: str = Field(description="Tax year from the statement", alias="TaxYear")
    current_total_tax_amount: float = Field(description="Current tax amount from the statement", alias="CurrentTaxAmount")
    current_tax_rate: float = Field(description="Current tax rate from the statement", alias="CurrentTaxRate")
    previous_tax_year: str = Field(description="Previous tax year from the statement", alias="PreviousTaxYear")
    previous_total_tax_amount: float = Field(description="Previous tax amount from the statement", alias="PreviousTaxAmount")


def detect_image_format(key: str, content_type: str = None) -> str:
    """
    Detect image format from file extension or ContentType.
    Defaults to 'png' if unable to detect.
    """
    # Try ContentType first
    if content_type:
        if 'image/png' in content_type:
            return 'png'
        elif 'image/jpeg' in content_type or 'image/jpg' in content_type:
            return 'jpeg'
        elif 'image/gif' in content_type:
            return 'gif'
        elif 'image/webp' in content_type:
            return 'webp'
    
    # Fall back to file extension
    key_lower = key.lower()
    if key_lower.endswith('.png'):
        return 'png'
    elif key_lower.endswith(('.jpg', '.jpeg')):
        return 'jpeg'
    elif key_lower.endswith('.gif'):
        return 'gif'
    elif key_lower.endswith('.webp'):
        return 'webp'
    
    # Default to png if unable to detect
    return 'png'

def extract_property_tax_assessment_data(document: bytes, image_format: str = 'png') -> dict:
    """
    Extracts structured data from a property tax assessment Image.
    """
    # Ensure document is actually bytes
    if not isinstance(document, bytes):
        raise TypeError(f"document must be bytes, got {type(document)}")
    
    print(f"Document type: {type(document)}, size: {len(document)} bytes")
    
    extractor_prompt = """
        Please extract information from this property tax assessment image and return it as a PropertyTaxAssessmentData object:
        """

    # Build the image content
    image_content = {
        "image": {
            "format": image_format,
            "source": {
                "bytes": document,
            },
        },
    }
    
  
    response = agent.structured_output(
        PropertyTaxAssessmentData,
        [{"text": extractor_prompt}, 
        image_content,
    ])
    # Return dict with PascalCase keys to match output_validator expectations
    return response.model_dump(by_alias=True)


def handler(event, context):
    """
    Lambda handler for document extraction.
    """
    print("Extracting document data...")
    print(f"Event: {json.dumps(event)}")
    
    bucket = event['bucket']
    key = event['key']
    
    # Get the object from S3
    response = s3_client.get_object(Bucket=bucket, Key=key)
    
    # Detect image format from ContentType or file extension
    content_type = response.get('ContentType', '')
    image_format = detect_image_format(key, content_type)
    
    # Read the binary content
    file_content = response['Body'].read()
    
    # Ensure we have actual bytes, not the bytes type
    if not isinstance(file_content, bytes):
        raise TypeError(f"Expected bytes, got {type(file_content)}")
    
    print(f"File content type: {type(file_content)}, size: {len(file_content)} bytes")

    extracted_data = extract_property_tax_assessment_data(file_content, image_format)

    is_valid = bool(extracted_data)

    return {
        'bucket': bucket,
        'key': key,
        'valid': is_valid,
        'extracted_data': extracted_data,
        'retry_count': event.get('retry_count', 0) + 1
    }
