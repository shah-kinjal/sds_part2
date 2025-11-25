# RentCast API Property Search Tool

This tool integrates the RentCast API to search for property listings for sale. It's been integrated into the virtual realtor chatbot as a tool that the AI agent can use to answer questions about available properties.

## Features

The `search_properties` tool supports all RentCast API query parameters:

### Location Parameters
- **address**: Full address of the property (Street, City, State, Zip)
- **city**: City name (case-sensitive, defaults to Austin)
- **state**: 2-character state abbreviation (case-sensitive, defaults to TX)
- **zipCode**: 5-digit zip code
- **latitude/longitude**: Coordinates for circular area search
- **radius**: Search radius in miles (max 100), use with lat/long or address

### Property Filters
- **propertyType**: Single Family, Condo, Townhouse, Manufactured, Multi-Family, Apartment, Land
- **bedrooms**: Number of bedrooms (supports ranges and multiple values, e.g., "3", "3-4", "3,4,5")
- **bathrooms**: Number of bathrooms (supports fractions, ranges, and multiple values, e.g., "2", "2.5", "2-3")
- **squareFootage**: Total living area in sq ft (supports ranges and multiple values, e.g., "1500-2000")
- **lotSize**: Total lot size in sq ft (supports ranges and multiple values)
- **yearBuilt**: Year of construction (supports ranges and multiple values, e.g., "2000-2020")

### Listing Filters
- **status**: Property status (Active or Inactive, default: "Active")
- **price**: Listed price (supports ranges and multiple values, e.g., "300000-500000")
- **daysOld**: Days since listing (minimum 1, supports ranges)

### Pagination
- **limit**: Maximum number of results (1-500, default: 10)
- **offset**: Index of first record for pagination (default: 0)
- **includeTotalCount**: Include total count in X-Total-Count header (default: False)

## Setup

### Environment Variables

You need to set the following environment variables in your `.env` file:

```bash
# Required
RENTCAST_API_KEY=your_api_key_here

# Optional (defaults shown)
RENTCAST_API_URL=https://api.rentcast.io/v1/listings/sale
```

### Dependencies

The tool requires the `requests` library, which should already be in your `requirements.txt`:

```bash
pip install requests
```

## Usage

### As an AI Agent Tool

The tool is automatically available to the AI agent. Users can ask questions like:

- "What properties are available in Austin, TX?"
- "Show me 3-bedroom homes in zip code 78723"
- "Find single family homes under $500k in Austin"
- "What properties are available with 2+ bathrooms and built after 2010?"

### Direct Python Usage

You can also use the tool directly in Python:

```python
from questions import QuestionManager

qm = QuestionManager()

# Basic search
result = qm.search_properties(city="Austin", state="TX", limit=5)

# Advanced search with filters
result = qm.search_properties(
    city="Austin",
    state="TX",
    propertyType="Single Family",
    bedrooms="3-4",
    bathrooms="2-3",
    price="300000-500000",
    yearBuilt="2010-2024",
    limit=10
)

print(result)  # Returns JSON string with property listings
```

### Testing

Run the test script to see examples of various search queries:

```bash
cd /Users/kinjal/projects/sds_part2/week8/virtual_realtor/virtual_realtor/backend
python test_rentcast_api.py
```

## API Response Format

The API returns an array of property objects with the following structure:

```json
[
  {
    "id": "3821-Hargis-St,-Austin,-TX-78723",
    "formattedAddress": "3821 Hargis St, Austin, TX 78723",
    "addressLine1": "3821 Hargis St",
    "city": "Austin",
    "state": "TX",
    "zipCode": "78723",
    "county": "Travis",
    "latitude": 30.290643,
    "longitude": -97.701547,
    "propertyType": "Single Family",
    "bedrooms": 4,
    "bathrooms": 2.5,
    "squareFootage": 2345,
    "lotSize": 3284,
    "yearBuilt": 2008,
    "hoa": {
      "fee": 65
    },
    "status": "Active",
    "price": 899000,
    "listingType": "Standard",
    "listedDate": "2024-06-24T00:00:00.000Z",
    "daysOnMarket": 99,
    "mlsName": "UnlockMLS",
    "mlsNumber": "5519228",
    "listingAgent": {
      "name": "Jennifer Welch",
      "phone": "5124313110",
      "email": "jennifer@gottesmanresidential.com"
    },
    "listingOffice": {
      "name": "Gottesman Residential R.E.",
      "phone": "5124512422"
    }
  }
]
```

## Implementation Details

### Files Modified

1. **`src/app/main.py`**:
   - Added `search_properties` as a tool decorator
   - Registered the tool with the AI agent
   - Comprehensive parameter documentation

2. **`src/app/questions.py`**:
   - Enhanced `search_properties` method in `QuestionManager` class
   - Added support for all RentCast API parameters
   - Improved error handling and logging
   - Only includes non-None parameters in API requests

### Key Features

- **Flexible Search**: Supports all RentCast API query parameters
- **Range Support**: Many parameters support ranges (e.g., "3-4" bedrooms, "300000-500000" price)
- **Multiple Values**: Some parameters support comma-separated values
- **Error Handling**: Graceful error handling with informative error messages
- **Logging**: Comprehensive logging for debugging
- **Type Safety**: Proper type hints for all parameters

## Notes

- At least one location parameter (city, state, zipCode, or address) must be provided
- The API is case-sensitive for city and state parameters
- Radius parameter requires either latitude/longitude or address to be specified
- The limit parameter has a maximum value of 500
- Range values should be formatted as "min-max" (e.g., "300000-500000")
- Multiple values should be comma-separated (e.g., "3,4,5")

## Error Handling

The tool handles various error scenarios:

- **Missing API Key**: Raises ValueError at initialization
- **API Request Errors**: Returns JSON error message
- **Invalid Parameters**: API will return appropriate error response
- **Network Issues**: Caught and logged with error details

All errors are logged and returned as JSON objects with an "error" field for easy parsing.
