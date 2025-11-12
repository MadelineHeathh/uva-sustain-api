"""
Convert UVA Energy Tracker template data to sustainability_metrics.csv format.

This script reads the template CSV (uva_energy_data_template.csv) and converts it
to the format used by the API (sustainability_metrics.csv).

Column mapping:
- energy_kw -> energy_consumption_kwh (convert kW to kWh if needed)
- water_gallons -> water_consumption_gallons
- primary_use -> metric_type
- waste_diverted_lbs -> calculated or default (0)
- co2_emissions_tons -> calculated from energy or default (0)
"""

import csv
import os
from pathlib import Path

# File paths
TEMPLATE_FILE = Path(__file__).parent.parent / 'assets' / 'uva_energy_data_template.csv'
OUTPUT_FILE = Path(__file__).parent.parent / 'assets' / 'sustainability_metrics.csv'

def convert_kw_to_kwh(kw_value, hours_per_year=8760):
    """
    Convert kW to kWh (assuming annual usage).
    For year data, multiply by hours in a year.
    """
    if not kw_value or kw_value == '':
        return None
    try:
        # If it's already in kWh, return as is
        # If it's in kW, multiply by hours (for annual data)
        kw = float(kw_value)
        # Assume if value is very large (>100000), it's already in kWh
        if kw > 100000:
            return int(kw)
        # Otherwise convert kW to kWh (annual)
        return int(kw * hours_per_year)
    except (ValueError, TypeError):
        return None

def calculate_co2_from_energy(energy_kwh):
    """
    Calculate CO2 emissions from energy consumption.
    Rough estimate: 0.0004 tons CO2 per kWh (varies by region)
    """
    if not energy_kwh:
        return 0.0
    try:
        # US average: ~0.0004 tons CO2 per kWh
        co2_tons = float(energy_kwh) * 0.0004
        return round(co2_tons, 1)
    except (ValueError, TypeError):
        return 0.0

def estimate_waste_from_energy(energy_kwh):
    """
    Estimate waste diverted from energy consumption.
    This is a rough estimate - actual values would come from waste data.
    """
    if not energy_kwh:
        return 0
    try:
        # Rough estimate: 1 lb waste per 30 kWh
        waste_lbs = int(float(energy_kwh) / 30)
        return waste_lbs
    except (ValueError, TypeError):
        return 0

def map_primary_use_to_metric_type(primary_use):
    """
    Map primary_use to metric_type.
    """
    if not primary_use or primary_use == '':
        return 'other'
    
    primary_use_lower = primary_use.lower()
    
    mapping = {
        'office': 'administrative',
        'academic': 'academic',
        'library': 'academic',
        'residential': 'student_life',
        'dining': 'student_life',
        'recreation': 'athletic',
        'athletic': 'athletic',
        'healthcare': 'healthcare',
        'historic': 'historic',
        'administrative': 'administrative'
    }
    
    for key, value in mapping.items():
        if key in primary_use_lower:
            return value
    
    return 'other'

def convert_template_to_metrics():
    """
    Read template CSV and convert to sustainability_metrics.csv format.
    """
    if not TEMPLATE_FILE.exists():
        print(f"Error: Template file not found: {TEMPLATE_FILE}")
        return False
    
    rows = []
    
    # Read template CSV
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Skip empty rows
            if not row.get('building') or not row.get('year'):
                continue
            
            building = row['building'].strip()
            year = row['year'].strip()
            
            # Convert energy (kW to kWh)
            energy_kw = row.get('energy_kw', '').strip()
            energy_kwh = convert_kw_to_kwh(energy_kw)
            
            # If no total energy, try summing electricity + heating + cooling
            if not energy_kwh:
                elec_kw = row.get('electricity_kw', '').strip()
                heat_kw = row.get('heating_kw', '').strip()
                cool_kw = row.get('cooling_kw', '').strip()
                
                elec_kwh = convert_kw_to_kwh(elec_kw)
                heat_kwh = convert_kw_to_kwh(heat_kw)
                cool_kwh = convert_kw_to_kwh(cool_kw)
                
                # Sum if available
                if elec_kwh or heat_kwh or cool_kwh:
                    energy_kwh = (elec_kwh or 0) + (heat_kwh or 0) + (cool_kwh or 0)
            
            # Water
            water_gallons = row.get('water_gallons', '').strip()
            if water_gallons:
                try:
                    water_gallons = int(float(water_gallons))
                except (ValueError, TypeError):
                    water_gallons = 0
            else:
                water_gallons = 0
            
            # Calculate derived values
            waste_diverted_lbs = estimate_waste_from_energy(energy_kwh) if energy_kwh else 0
            co2_emissions_tons = calculate_co2_from_energy(energy_kwh) if energy_kwh else 0.0
            
            # Map primary_use to metric_type
            primary_use = row.get('primary_use', '').strip()
            metric_type = map_primary_use_to_metric_type(primary_use)
            
            # Only add row if we have at least energy or water data
            if energy_kwh or water_gallons:
                rows.append({
                    'building': building,
                    'year': int(year),
                    'energy_consumption_kwh': energy_kwh or 0,
                    'water_consumption_gallons': water_gallons,
                    'waste_diverted_lbs': waste_diverted_lbs,
                    'co2_emissions_tons': co2_emissions_tons,
                    'metric_type': metric_type
                })
    
    if not rows:
        print("No data found in template. Please fill in the template CSV first.")
        return False
    
    # Write to output CSV
    fieldnames = [
        'building', 'year', 'energy_consumption_kwh', 'water_consumption_gallons',
        'waste_diverted_lbs', 'co2_emissions_tons', 'metric_type'
    ]
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Successfully converted {len(rows)} rows from template to sustainability_metrics.csv")
    print(f"📁 Output file: {OUTPUT_FILE}")
    return True

if __name__ == "__main__":
    print("Converting UVA Energy Tracker template to sustainability_metrics.csv...")
    print("=" * 60)
    
    if convert_template_to_metrics():
        print("\n✅ Conversion complete!")
        print("\nNext steps:")
        print("1. Rebuild Docker image: docker build -t madelineheathh/uva-sustain-api:latest .")
        print("2. Push to Docker Hub: docker push madelineheathh/uva-sustain-api:latest")
        print("3. Restart Azure Web App")
    else:
        print("\n❌ Conversion failed. Please check the template file and try again.")

