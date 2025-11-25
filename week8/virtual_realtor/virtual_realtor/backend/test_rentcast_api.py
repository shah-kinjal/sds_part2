#!/usr/bin/env python3
"""
Test script for RentCast API property search functionality.
This demonstrates how to use the search_properties function with various parameters.
"""

import os
import sys
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'app'))

from questions import QuestionManager

def main():
    """Run various test searches against the RentCast API."""
    
    # Load environment variables
    load_dotenv()
    
    # Initialize the question manager
    qm = QuestionManager()
    
    print("=" * 80)
    print("RentCast API Property Search Tests")
    print("=" * 80)
    
    # Test 1: Basic city/state search
    print("\n1. Basic Search - Austin, TX (Active listings, limit 5)")
    print("-" * 80)
    result = qm.search_properties(city="Austin", state="TX", status="Active", limit=5)
    print(result)
    
    # Test 2: Search with property type filter
    print("\n2. Search with Property Type - Single Family homes in Austin, TX")
    print("-" * 80)
    result = qm.search_properties(
        city="Austin",
        state="TX",
        propertyType="Single Family",
        limit=3
    )
    print(result)
    
    # Test 3: Search with bedroom/bathroom filters
    print("\n3. Search with Bedrooms/Bathrooms - 3+ bed, 2+ bath in Austin, TX")
    print("-" * 80)
    result = qm.search_properties(
        city="Austin",
        state="TX",
        bedrooms="3-5",
        bathrooms="2-4",
        limit=3
    )
    print(result)
    
    # Test 4: Search with price range
    print("\n4. Search with Price Range - $300k-$500k in Austin, TX")
    print("-" * 80)
    result = qm.search_properties(
        city="Austin",
        state="TX",
        price="300000-500000",
        limit=3
    )
    print(result)
    
    # Test 5: Search by zip code
    print("\n5. Search by Zip Code - 78723")
    print("-" * 80)
    result = qm.search_properties(
        zipCode="78723",
        status="Active",
        limit=3
    )
    print(result)
    
    # Test 6: Search with square footage
    print("\n6. Search with Square Footage - 1500-2500 sq ft in Austin, TX")
    print("-" * 80)
    result = qm.search_properties(
        city="Austin",
        state="TX",
        squareFootage="1500-2500",
        limit=3
    )
    print(result)
    
    # Test 7: Search with year built
    print("\n7. Search with Year Built - Built 2010 or later in Austin, TX")
    print("-" * 80)
    result = qm.search_properties(
        city="Austin",
        state="TX",
        yearBuilt="2010-2024",
        limit=3
    )
    print(result)
    
    print("\n" + "=" * 80)
    print("Tests Complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
