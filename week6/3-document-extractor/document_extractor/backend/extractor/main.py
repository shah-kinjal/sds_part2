import json
import boto3
import os
from strands import Agent
import uuid
from pydantic import BaseModel, Field, ConfigDict

model_id = os.environ.get("MODEL_ID", "")
s3_client = boto3.client('s3')

agent = Agent(model=model_id, callback_handler=None)

class BankStatementData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    bank_name: str = Field(description="Bank name from the statement", alias="BankName")
    account_number: str = Field(description="Account number from the statement", alias="AccountNumber")
    opening_balance: float = Field(description="Opening balance from the statement", alias="OpeningBalance")
    closing_balance: float = Field(description="Closing balance from the statement", alias="ClosingBalance")
    start_date: str = Field(description="Start date from the statement", alias="StartDate")
    end_date: str = Field(description="End date from the statement", alias="EndDate")

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

def detect_file_format(key: str, content_type: str = None) -> tuple[str, str]:
    """
    Detect file format from file extension or ContentType.
    Returns tuple of (format, media_type) where:
    - format: 'pdf', 'png', 'jpeg', etc.
    - media_type: 'document' for PDF, 'image' for images
    """
    # Try ContentType first
    if content_type:
        if 'application/pdf' in content_type or 'pdf' in content_type:
            return ('pdf', 'document')
        elif 'image/png' in content_type:
            return ('png', 'image')
        elif 'image/jpeg' in content_type or 'image/jpg' in content_type:
            return ('jpeg', 'image')
        elif 'image/gif' in content_type:
            return ('gif', 'image')
        elif 'image/webp' in content_type:
            return ('webp', 'image')
    
    # Fall back to file extension
    key_lower = key.lower()
    if key_lower.endswith('.pdf'):
        return ('pdf', 'document')
    elif key_lower.endswith('.png'):
        return ('png', 'image')
    elif key_lower.endswith(('.jpg', '.jpeg')):
        return ('jpeg', 'image')
    elif key_lower.endswith('.gif'):
        return ('gif', 'image')
    elif key_lower.endswith('.webp'):
        return ('webp', 'image')
    
    # Default to pdf/document if unable to detect
    return ('pdf', 'document')

def extract_bank_statement_data(document: bytes, file_format: str, media_type: str) -> dict:
    """
    Extracts structured data from a bank statement document.
    """
    extractor_prompt = """
        Please extract information from this bank statement and return it as a BankStatementData object:
        """

    response = agent.structured_output(
        BankStatementData,
        [{"text": extractor_prompt}, 
        {
            media_type: {
                "format": file_format,
                "name": f"bank_statement-{uuid.uuid4()}",
                "source": {
                    "bytes": document,
                },
            },
        },
    ])

    # Return dict with PascalCase keys to match output_validator expectations
    return response.model_dump(by_alias=True)

def extract_property_tax_assessment_data(document: bytes, file_format: str, media_type: str) -> dict:
    """
    Extracts structured data from a property tax assessment document/image.
    """
    # Ensure document is actually bytes
    if not isinstance(document, bytes):
        raise TypeError(f"document must be bytes, got {type(document)}")
    
    print(f"Document type: {type(document)}, size: {len(document)} bytes")
    
    extractor_prompt = """
        Please extract information from this property tax assessment image and return it as a PropertyTaxAssessmentData object:
        """
    
    # Build the content structure based on media type
    content = {
        media_type: {
            "format": file_format,
            "source": {
                "bytes": document,
            },
        },
    }
    
    print(f"Content structure: {list(content[media_type].keys())}")
    print(f"Source keys: {list(content[media_type]['source'].keys())}")
    print(f"Bytes type: {type(content[media_type]['source']['bytes'])}")

    response = agent.structured_output(
        PropertyTaxAssessmentData,
        [{"text": extractor_prompt}, 
        content,
    ])
    # Return dict with PascalCase keys to match output_validator expectations
    return response.model_dump(by_alias=True)


def handler(event, context):
    """
    Lambda handler for document extraction.
    Extracts either bank statement data or property tax assessment data
    depending on document_type from event.
    """
    print("Extracting document data...")
    print(f"Event: {json.dumps(event)}")
    
    bucket = event['bucket']
    key = event['key']
    document_type = event.get('document_type', '')
    
    # Get the object from S3
    response = s3_client.get_object(Bucket=bucket, Key=key)
    
    # Detect file format and media type from ContentType or file extension
    content_type = response.get('ContentType', '')
    file_format, media_type = detect_file_format(key, content_type)
    print(f"Detected file format: {file_format}, media type: {media_type}")
    
    # Read the binary content
    file_content = response['Body'].read()
    
    # Extract data based on document type
    if document_type == 'bank_stmt':
        print("Extracting bank statement data...")
        extracted_data = extract_bank_statement_data(file_content, file_format, media_type)
    elif document_type == 'tax_asmt':
        print("Extracting property tax assessment data...")
        extracted_data = extract_property_tax_assessment_data(file_content, file_format, media_type)
    else:
        print(f"Unknown document type: {document_type}")
        raise ValueError(f"Unsupported document_type: {document_type}. Expected 'bank_stmt' or 'tax_asmt'")

    is_valid = bool(extracted_data)

    return {
        'bucket': bucket,
        'key': key,
        'valid': is_valid,
        'extracted_data': extracted_data,
        'document_type': document_type,
        'retry_count': event.get('retry_count', 0) + 1
    }
