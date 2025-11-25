#!/usr/bin/env python3
"""
Simple example of using the RentCast API property search tool.
This is a minimal example showing the basic usage.
"""

import os
import json
from dotenv import load_dotenv
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'app'))

from questions import QuestionManager

# Load environment variables
load_dotenv()

# Initialize the question manager
qm = QuestionManager()

# Example 1: Simple search by city and state
print("Searching for properties in Austin, TX...")
result = qm.search_properties(city="Austin", state="TX", limit=3)
properties = json.loads(result)

if "error" in properties:
    print(f"Error: {properties['error']}")
else:
    print(f"\nFound {len(properties)} properties:")
    for prop in properties:
        print(f"\n  Address: {prop.get('formattedAddress')}")
        print(f"  Price: ${prop.get('price'):,}")
        print(f"  Bedrooms: {prop.get('bedrooms')}")
        print(f"  Bathrooms: {prop.get('bathrooms')}")
        print(f"  Square Footage: {prop.get('squareFootage')} sq ft")
        print(f"  Property Type: {prop.get('propertyType')}")
        print(f"  Status: {prop.get('status')}")

# Example 2: Advanced search with filters
print("\n" + "="*80)
print("Searching for Single Family homes with 3+ bedrooms, 2+ baths, under $600k...")
result = qm.search_properties(
    city="Austin",
    state="TX",
    propertyType="Single Family",
    bedrooms="3-5",
    bathrooms="2-4",
    price="0-600000",
    limit=3
)
properties = json.loads(result)

if "error" in properties:
    print(f"Error: {properties['error']}")
else:
    print(f"\nFound {len(properties)} matching properties:")
    for prop in properties:
        print(f"\n  {prop.get('formattedAddress')}")
        print(f"  ${prop.get('price'):,} | {prop.get('bedrooms')} bed | {prop.get('bathrooms')} bath | {prop.get('squareFootage')} sq ft")
