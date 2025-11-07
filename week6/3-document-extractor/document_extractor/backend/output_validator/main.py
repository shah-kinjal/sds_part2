import json

def handler(event, context):
    """
    Validates the output from the extractor function.
    Checks for presence and basic validity of required fields based on document type.
    """
    print("Validating extracted output...")
    print(f"Event: {json.dumps(event)}")
    
    extracted_data = event.get('extracted_data', {})
    document_type = event.get('document_type', '')
    
    # Determine required fields based on document type
    if document_type == 'bank_stmt':
        # Fields for bank statement validation
        # Field names match the aliases from BankStatementData model
        required_fields = [
            "BankName",
            "AccountNumber",
            "ClosingBalance",
            "StartDate",
            "EndDate"
        ]
    elif document_type == 'tax_asmt':
        # Fields for property tax assessment validation
        # Field names match the aliases from PropertyTaxAssessmentData model
        required_fields = [
            "PropertyValueLand",
            "PropertyValueBuilding",
            "PropertyValueTotal",
            "TaxYear",
            "CurrentTaxAmount",
            "CurrentTaxRate",
            "PreviousTaxYear",
            "PreviousTaxAmount"
        ]
    else:
        print(f"Unknown document type: {document_type}")
        result = event.copy()
        result['valid'] = False
        return result
    
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
        print(f"Validation successful for {document_type}.")
    else:
        print(f"Validation failed for {document_type}.")
        
    return result
