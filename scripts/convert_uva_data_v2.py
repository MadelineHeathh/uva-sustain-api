"""
Convert UVA Energy Tracker data to sustainability_metrics.csv format.

Handles format: building,month,year,energy_MMBtu,gross_square_feet,occupancy,primary_use
"""

import csv
from pathlib import Path
from collections import defaultdict

# File paths
TEMPLATE_FILE = Path(__file__).parent.parent / 'assets' / 'uva_energy_data_template.csv'
OUTPUT_FILE = Path(__file__).parent.parent / 'assets' / 'sustainability_metrics.csv'

# Conversion factor: 1 MMBtu = 293.071 kWh
MMBTU_TO_KWH = 293.071

def safe_get(row, key, default=''):
    """Safely get value from row, handling None."""
    val = row.get(key)
    if val is None:
        return default
    return str(val).strip()

def convert_mmbtu_to_kwh(mmbtu):
    """Convert MMBtu to kWh."""
    if not mmbtu or mmbtu == '' or mmbtu == '...':
        return None
    try:
        return int(float(mmbtu) * MMBTU_TO_KWH)
    except (ValueError, TypeError):
        return None

def calculate_co2_from_energy(energy_kwh):
    """Calculate CO2 emissions from energy consumption."""
    if not energy_kwh:
        return 0.0
    try:
        co2_tons = float(energy_kwh) * 0.0004
        return round(co2_tons, 1)
    except (ValueError, TypeError):
        return 0.0

def estimate_water_from_energy(energy_kwh):
    """Estimate water consumption from energy."""
    if not energy_kwh:
        return 0
    try:
        water_gallons = int(float(energy_kwh) * 0.5)
        return water_gallons
    except (ValueError, TypeError):
        return 0

def estimate_waste_from_energy(energy_kwh):
    """Estimate waste diverted from energy consumption."""
    if not energy_kwh:
        return 0
    try:
        waste_lbs = int(float(energy_kwh) / 30)
        return waste_lbs
    except (ValueError, TypeError):
        return 0

def map_primary_use_to_metric_type(primary_use):
    """Map primary_use to metric_type."""
    if not primary_use or primary_use == '' or primary_use == '...':
        return 'other'
    
    primary_use_lower = primary_use.lower()
    
    mapping = {
        'academic': 'academic',
        'multi-use': 'student_life',
        'multi-purpose': 'student_life',
        'fitness': 'athletic',
        'medical': 'healthcare',
        'dining': 'student_life',
        'office': 'administrative',
        'administrative': 'administrative',
        'historic': 'historic'
    }
    
    for key, value in mapping.items():
        if key in primary_use_lower:
            return value
    
    return 'other'

def convert_template_to_metrics():
    """Read template CSV, aggregate monthly data to yearly, and convert format."""
    if not TEMPLATE_FILE.exists():
        print(f"Error: Template file not found: {TEMPLATE_FILE}")
        return False
    
    # Dictionary to aggregate data by building and year
    aggregated = defaultdict(lambda: {
        'energy_kwh': 0,
        'primary_use': '',
        'gross_square_feet': 0,
        'occupancy': 0
    })
    
    # Read template CSV
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Check what columns we have
        print(f"Columns found: {reader.fieldnames}")
        
        for row in reader:
            # Try different possible column names
            building = safe_get(row, 'building')
            month = safe_get(row, 'month')
            year = safe_get(row, 'year')
            
            # Try different energy column names
            energy_mmbtu = safe_get(row, 'energy_MMBtu') or safe_get(row, 'energy_kw') or safe_get(row, 'energy')
            gross_sqft = safe_get(row, 'gross_square_feet') or safe_get(row, 'gross_square_feet')
            occupancy = safe_get(row, 'occupancy')
            primary_use = safe_get(row, 'primary_use')
            
            # Skip empty rows
            if not building or not year:
                continue
            
            # Convert energy (try MMBtu first, then kW)
            energy_kwh = None
            if energy_mmbtu and energy_mmbtu != '...':
                energy_kwh = convert_mmbtu_to_kwh(energy_mmbtu)
            
            if not energy_kwh:
                continue
            
            # Aggregate by building and year
            key = (building, year)
            aggregated[key]['energy_kwh'] += energy_kwh
            
            # Store metadata from first occurrence
            if not aggregated[key]['primary_use'] and primary_use and primary_use != '...':
                aggregated[key]['primary_use'] = primary_use
            if not aggregated[key]['gross_square_feet'] and gross_sqft and gross_sqft != '...':
                try:
                    aggregated[key]['gross_square_feet'] = int(float(gross_sqft))
                except (ValueError, TypeError):
                    pass
            if not aggregated[key]['occupancy'] and occupancy and occupancy != '...':
                try:
                    aggregated[key]['occupancy'] = int(float(occupancy))
                except (ValueError, TypeError):
                    pass
    
    if not aggregated:
        print("No data found in template. Please check the template file.")
        return False
    
    # Convert aggregated data to output format
    rows = []
    for (building, year), data in sorted(aggregated.items()):
        energy_kwh = data['energy_kwh']
        
        # Calculate derived values
        water_gallons = estimate_water_from_energy(energy_kwh)
        waste_diverted_lbs = estimate_waste_from_energy(energy_kwh)
        co2_emissions_tons = calculate_co2_from_energy(energy_kwh)
        metric_type = map_primary_use_to_metric_type(data['primary_use'])
        
        rows.append({
            'building': building,
            'year': int(year),
            'energy_consumption_kwh': energy_kwh,
            'water_consumption_gallons': water_gallons,
            'waste_diverted_lbs': waste_diverted_lbs,
            'co2_emissions_tons': co2_emissions_tons,
            'metric_type': metric_type
        })
    
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
    print(f"\nBuildings processed: {len(set(b['building'] for b in rows))}")
    print(f"Years: {sorted(set(b['year'] for b in rows))}")
    return True

if __name__ == "__main__":
    print("Converting UVA Energy Tracker data to sustainability_metrics.csv...")
    print("=" * 60)
    print(f"Reading from: {TEMPLATE_FILE}")
    print(f"Writing to: {OUTPUT_FILE}")
    print("=" * 60)
    
    if convert_template_to_metrics():
        print("\n✅ Conversion complete!")
        print("\nNext steps:")
        print("1. Rebuild Docker image: docker build -t madelineheathh/uva-sustain-api:latest .")
        print("2. Push to Docker Hub: docker push madelineheathh/uva-sustain-api:latest")
        print("3. Restart Azure Web App")
    else:
        print("\n❌ Conversion failed. Please check the template file and try again.")

