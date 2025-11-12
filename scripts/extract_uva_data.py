"""
Script to help extract data from UVA Energy Tracker website.

Note: This is a helper script. The UVA Energy Tracker website is interactive
and may require manual data collection or API access (if available).

For the assignment, you can:
1. Use this script structure to manually collect data
2. Contact UVA Facilities Management for data access
3. Use the sample data provided for demonstration
"""

import csv
import requests
from bs4 import BeautifulSoup
import json

# UVA Energy Tracker URL
ENERGY_TRACKER_URL = "https://energytracker.fm.virginia.edu/#building"

def get_building_list():
    """
    Attempt to get list of buildings from UVA Energy Tracker.
    Note: This may not work if the site requires JavaScript or authentication.
    """
    try:
        response = requests.get(ENERGY_TRACKER_URL)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # The site likely uses JavaScript to load data dynamically
            # You may need to use Selenium or check for an API endpoint
            print("Website accessible, but data may be loaded via JavaScript")
            print("You may need to manually collect data or use browser automation")
            return []
    except Exception as e:
        print(f"Error accessing website: {e}")
        return []

def create_csv_template():
    """
    Create a CSV template matching the UVA Energy Tracker structure.
    Based on the website, buildings have:
    - Energy (total)
    - Electricity
    - Heating
    - Cooling
    - Water
    - Data by Day/Week/Month/Year
    """
    headers = [
        'building',
        'year',
        'energy_kw',
        'electricity_kw',
        'heating_kw',
        'cooling_kw',
        'water_gallons',
        'gross_square_feet',
        'occupancy',
        'primary_use'
    ]
    
    # Create template CSV
    with open('../assets/uva_energy_data_template.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        print("Template CSV created: assets/uva_energy_data_template.csv")
        print("Fill in the data manually from the UVA Energy Tracker website")

def manual_data_collection_guide():
    """
    Print instructions for manually collecting data from the website.
    """
    print("\n" + "="*60)
    print("MANUAL DATA COLLECTION GUIDE")
    print("="*60)
    print("\n1. Go to: https://energytracker.fm.virginia.edu/#building")
    print("2. Select a building from the dropdown")
    print("3. View data by 'Year'")
    print("4. Note the following metrics:")
    print("   - Energy (total in kW)")
    print("   - Electricity (kW)")
    print("   - Heating (kW)")
    print("   - Cooling (kW)")
    print("   - Water (gallons)")
    print("5. Record building details:")
    print("   - Gross square feet")
    print("   - Occupancy")
    print("   - Primary use")
    print("\n6. Repeat for multiple buildings and years")
    print("7. Fill in the template CSV file")
    print("\n" + "="*60)

if __name__ == "__main__":
    print("UVA Energy Tracker Data Extraction Helper")
    print("="*60)
    print("\nNote: The UVA Energy Tracker is an interactive dashboard.")
    print("Data may need to be collected manually or via API (if available).")
    print("\nOptions:")
    print("1. Create CSV template for manual data entry")
    print("2. Show manual collection guide")
    print("3. Attempt to access website (may not work due to JavaScript)")
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == "1":
        create_csv_template()
    elif choice == "2":
        manual_data_collection_guide()
    elif choice == "3":
        buildings = get_building_list()
        if not buildings:
            print("\nWebsite requires JavaScript. Consider using:")
            print("- Selenium for browser automation")
            print("- Contacting UVA Facilities Management for data access")
            print("- Using the sample data provided for the assignment")
    else:
        print("Invalid choice")

