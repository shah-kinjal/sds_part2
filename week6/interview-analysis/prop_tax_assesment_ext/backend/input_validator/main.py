import json
import boto3
import os
from strands import Agent

model_id = os.environ.get("MODEL_ID", "")
s3_client = boto3.client('s3')

agent = Agent(model=model_id, callback_handler=None)

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

def validate_tax_assessment_image(document: bytes, image_format: str = 'png') -> bool:
    print("Input validator: Validating tax assessment image...")
    
    # Ensure document is actually bytes
    if not isinstance(document, bytes):
        raise TypeError(f"document must be bytes, got {type(document)}")

    validator_prompt = """
        Does this image represent a property tax assessment? Please respond with "yes" or "no" only.
        """
    print(f"Validator prompt: {validator_prompt}")  # TODO: Remove this

    # Build the message content
    image_content = {
        "image": {
            "format": image_format,
            "source": {
                "bytes": document,
            },
        },
    }
    
   
    response = agent([
        {"text": validator_prompt},
        image_content,
    ])
    output = str(response)
    print(f"Output: {output}")
    if output.strip().lower() == "yes":
        return True
    else:
        return False

def handler(event, context):
    """
    Lambda handler for Step Functions triggered by S3 PutObject events.
    
    Args:
        event: Step Functions event containing S3 object information
        context: Lambda context object
    
    Returns:
        dict: Contains the binary content of the uploaded document as bytes
    """
    print("Handler:Validating tax assessment image...")
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

        validation_result = validate_tax_assessment_image(file_content, image_format)
        print("Handler: Validation result: ", validation_result)
        return {
            'bucket': bucket,
            'key': key,
            'valid': validation_result
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'error': str(e)
        }


if __name__ == "__main__":
    # For local testing
    test_event = {
        'bucket': 'test-bucket',
        'key': 'test-document.png'
    }
    result = handler(test_event, None)
    print(json.dumps(result, default=str))
