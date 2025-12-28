import json
from pydantic import BaseModel, Field, ConfigDict, ValidationError



def handler(event, context):
    """
    Validates the output from the extractor function.
    Checks for presence and basic validity of required fields.
    """
    print("Validating extracted output...")
    print(f"Event: {json.dumps(event)}")
    
    extracted_data = event.get('extracted_data', {})
    
    # These fields are required and should not be empty
    # Field names match the aliases from PropertyTaxAssessmentData model
    required_fields = [
        "PropertyValueLand",           # alias for assesed_property_value_land
        "PropertyValueBuilding",       # alias for assesed_property_value_building
        "PropertyValueTotal",          # alias for assesed_property_value_total
        "TaxYear",                     # alias for current_tax_year
        "CurrentTaxAmount",            # alias for current_total_tax_amount
        "CurrentTaxRate",              # alias for current_tax_rate
        "PreviousTaxYear",             # alias for previous_tax_year
        "PreviousTaxAmount"            # alias for previous_total_tax_amount
    ]
    
    is_valid = True
    if not extracted_data:
        is_valid = False
    else:
        for field in required_fields:
            value = extracted_data.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                is_valid = False
                print(f"Validation failed for field '{field}'")
                break

    result = event.copy()
    result['valid'] = is_valid
    
    if is_valid:
        print("Validation successful.")
    else:
        print("Validation failed.")
        
    return result
