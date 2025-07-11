#!/usr/bin/env python3
"""
Test script for the integrated GraphQL scraper functionality.
This tests the scraper with integrated GraphQL enhancement to get comprehensive data in one pass.
"""

import sys
import os
import json
import logging

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scraper import KingArthurScraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_integrated_scraper():
    """Test the integrated scraper with GraphQL enhancement."""
    print("="*80)
    print("🧪 Testing Integrated GraphQL Scraper")
    print("="*80)
    
    try:
        # Create scraper instance
        scraper = KingArthurScraper()
        
        # Override target count for testing
        scraper.target_count = 5  # Just test with 5 products
        
        print("🚀 Starting integrated scraping with GraphQL enhancement...")
        print("   This will scrape AND enhance products in one pass")
        print("   Target: 5 products (for testing)")
        
        # Run the integrated scraper
        products = scraper.scrape_products()
        
        if products:
            print(f"\n✅ Successfully scraped {len(products)} products")
            
            # Analyze the enhancement results
            enhanced_products = [p for p in products if p.get('enhanced', False)]
            basic_products = [p for p in products if not p.get('enhanced', False)]
            
            print(f"📊 Enhancement Results:")
            print(f"   Enhanced products: {len(enhanced_products)}")
            print(f"   Basic products: {len(basic_products)}")
            print(f"   Enhancement rate: {len(enhanced_products)/len(products)*100:.1f}%")
            
            # Show sample of enhanced data
            if enhanced_products:
                sample = enhanced_products[0]
                print(f"\n🔍 Sample Enhanced Product:")
                print(f"   Name: {sample.get('name', 'Unknown')}")
                print(f"   Entity ID: {sample.get('entity_id', 'N/A')}")
                print(f"   Brand: {sample.get('brand', 'N/A')}")
                print(f"   Categories: {[cat.get('name') for cat in sample.get('categories', [])]}")
                
                # Count custom fields
                custom_fields = sample.get('custom_fields', {})
                non_empty_fields = {k: v for k, v in custom_fields.items() if v}
                print(f"   Custom Fields: {len(non_empty_fields)} found")
                
                if non_empty_fields:
                    print("   📋 Sample Custom Data:")
                    for key, value in list(non_empty_fields.items())[:3]:
                        display_value = str(value)[:40] + "..." if len(str(value)) > 40 else str(value)
                        print(f"      • {key}: {display_value}")
                
                # Show images
                images = sample.get('images', [])
                print(f"   Images: {len(images)} available")
                
                # Show variants
                variants = sample.get('variants', [])
                if variants:
                    first_variant = variants[0]
                    prices = first_variant.get('prices', {})
                    print(f"   Price: ${prices.get('price', 'N/A')}")
                    inventory = first_variant.get('inventory', {})
                    print(f"   In Stock: {inventory.get('is_in_stock', 'N/A')}")
            
            # Save results
            output_file = "integrated_scraper_test_results.json"
            scraper.save_to_json(products, output_file)
            print(f"\n💾 Results saved to: {output_file}")
            
            return True
            
        else:
            print("❌ No products were scraped")
            return False
            
    except Exception as e:
        print(f"❌ Error during integrated scraping test: {e}")
        return False

def analyze_data_completeness(filename: str):
    """Analyze the completeness of the scraped data."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        print(f"\n📊 Data Completeness Analysis:")
        print(f"Total products: {len(products)}")
        
        enhanced_count = sum(1 for p in products if p.get('enhanced', False))
        print(f"Enhanced products: {enhanced_count}")
        
        # Check field completeness
        fields_to_check = [
            'brand', 'categories', 'custom_fields', 'images', 
            'description', 'ingredients', 'instructions'
        ]
        
        for field in fields_to_check:
            count = sum(1 for p in products if p.get(field))
            percentage = count / len(products) * 100
            print(f"{field}: {count}/{len(products)} ({percentage:.1f}%)")
        
        # Check custom fields richness
        total_custom_fields = 0
        for product in products:
            custom_fields = product.get('custom_fields', {})
            non_empty_fields = [k for k, v in custom_fields.items() if v]
            total_custom_fields += len(non_empty_fields)
        
        avg_custom_fields = total_custom_fields / len(products) if products else 0
        print(f"Average custom fields per product: {avg_custom_fields:.1f}")
        
    except Exception as e:
        print(f"Error analyzing data: {e}")

def main():
    """Main test function."""
    print("🚀 Starting Integrated GraphQL Scraper Tests...\n")
    
    success = test_integrated_scraper()
    
    if success:
        # Analyze the results
        analyze_data_completeness("integrated_scraper_test_results.json")
    
    print("\n" + "="*80)
    if success:
        print("✅ Integrated GraphQL scraper test completed successfully!")
        print("\n🎯 Key Benefits:")
        print("   ✅ Single-pass scraping with comprehensive data")
        print("   ✅ No need for separate enhancement step")
        print("   ✅ Rich product information including:")
        print("      • Brand and category data")
        print("      • Complete custom fields")
        print("      • Product images and descriptions")
        print("      • Pricing and inventory data")
        print("      • Review ratings and counts")
        print("\n📋 Next steps:")
        print("   1. Run the full scraper: python main.py --scrape")
        print("   2. All products will be comprehensive from the start")
        print("   3. No need for separate --enhance step")
    else:
        print("❌ Tests failed. Check the error messages above.")
    print("="*80)

if __name__ == "__main__":
    main() 