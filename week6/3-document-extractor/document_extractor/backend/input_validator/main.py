import json
import boto3
import os
from strands import Agent
import uuid

model_id = os.environ.get("MODEL_ID", "")
s3_client = boto3.client('s3')

agent = Agent(model=model_id, callback_handler=None)

def detect_file_format(key: str) -> str:
    """
    Detect file format from S3 key extension.
    
    Args:
        key: S3 object key (filename)
    
    Returns:
        str: File format (pdf, png, jpg, jpeg, gif, bmp, webp)
    """
    key_lower = key.lower()
    
    # Check for PDF
    if key_lower.endswith('.pdf'):
        return 'pdf'
    
    # Check for image formats
    image_extensions = {
        '.png': 'png',
        '.jpg': 'jpg',
        '.jpeg': 'jpeg',
        '.gif': 'gif',
        '.bmp': 'bmp',
        '.webp': 'webp'
    }
    
    for ext, format_name in image_extensions.items():
        if key_lower.endswith(ext):
            return format_name
    
    # Default to PDF if format cannot be determined
    print(f"Warning: Could not determine file format for key '{key}', defaulting to 'pdf'")
    return 'pdf'

def validate_document(document: bytes, file_format: str) -> str:
    """
    Validate and identify the document type.
    
    
    """
    validator_prompt = """
        What type of document is this? Please respond with exactly one of the following:
        - "bank_stmt" if this is a bank statement
        - "tax_asmt" if this is a property tax assessment
        - "none" if this is neither a bank statement nor a property tax assessment
    """

    # Determine the media type based on file format
    media_type = "document" if file_format == "pdf" else "image"
    print(f"Media type: {media_type}")
    print(f"File format: {file_format}")

    response = agent([
        {"text": validator_prompt},
        {
            media_type: {
                "format": file_format,
                "source": {
                    "bytes": document,
                },
            },
        },
    ])
    print(f"Got response from agent")
    print(f"Response: {response}")
    output = str(response).strip().lower()
    print(f"Output: {output}")
    
    # Parse the response to determine document type
    if "bank_stmt" in output or "bank statement" in output:
        return "bank_stmt"
    elif "tax_asmt" in output or "property tax" in output or "tax assessment" in output:
        return "tax_asmt"
    else:
        return ""

def handler(event, context):
    """
    Lambda handler for Step Functions triggered by S3 PutObject events.
    
    """
    try:
        # Extract S3 bucket and key from the event
        # The event structure will contain S3 event information
        if 'Records' in event:
            # Direct S3 event trigger
            s3_event = event['Records'][0]
            bucket = s3_event['s3']['bucket']['name']
            key = s3_event['s3']['object']['key']
        else:
            # Step Functions input format
            bucket = event.get('bucket')
            key = event.get('key')
        
        if not bucket or not key:
            raise ValueError("Missing bucket or key in event")

        print(f"Validating document in bucket: {bucket} with key: {key}")
        # Get the object from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        
        
        # Read the binary content
        file_content = response['Body'].read()
        
        # Detect file format from key
        file_format = detect_file_format(key)
        print(f"Detected file format: {file_format} for key: {key}")

        document_type = validate_document(file_content, file_format)
        
        # Document is valid if it's one of the supported types
        is_valid = document_type in ["bank_stmt", "tax_asmt"]
        
        return {
            'bucket': bucket,
            'key': key,
            'valid': is_valid,
            'document_type': document_type,
            'file_format': file_format
        }
        
    except Exception as e:
        return {
            'print(f"Error validating document in bucket: {bucket} with key: {key}")': e,
            'statusCode': 500,
            'error': str(e)
        }


if __name__ == "__main__":
    # For local testing
    test_event = {
        'bucket': 'test-bucket',
        'key': 'test-document.pdf'
    }
    result = handler(test_event, None)
    print(json.dumps(result, default=str))
