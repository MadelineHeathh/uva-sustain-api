"""
Process UVA Energy Tracker data: aggregate monthly to yearly and convert format.
"""

import csv
from pathlib import Path
from collections import defaultdict

TEMPLATE_FILE = Path(__file__).parent.parent / 'assets' / 'uva_energy_data_template.csv'
OUTPUT_FILE = Path(__file__).parent.parent / 'assets' / 'sustainability_metrics.csv'

MMBTU_TO_KWH = 293.071  # 1 MMBtu = 293.071 kWh

def convert_mmbtu_to_kwh(mmbtu):
    """Convert MMBtu to kWh."""
    if not mmbtu or mmbtu == '' or mmbtu == '...':
        return None
    try:
        return int(float(mmbtu) * MMBTU_TO_KWH)
    except (ValueError, TypeError):
        return None

def calculate_co2_from_energy(energy_kwh):
    """Calculate CO2 emissions (tons) from energy consumption."""
    if not energy_kwh:
        return 0.0
    try:
        return round(float(energy_kwh) * 0.0004, 1)
    except (ValueError, TypeError):
        return 0.0

def estimate_water_from_energy(energy_kwh):
    """Estimate water consumption from energy."""
    if not energy_kwh:
        return 0
    try:
        return int(float(energy_kwh) * 0.5)
    except (ValueError, TypeError):
        return 0

def estimate_waste_from_energy(energy_kwh):
    """Estimate waste diverted from energy."""
    if not energy_kwh:
        return 0
    try:
        return int(float(energy_kwh) / 30)
    except (ValueError, TypeError):
        return 0

def map_primary_use_to_metric_type(primary_use):
    """Map primary_use to metric_type."""
    if not primary_use or primary_use == '' or primary_use == '...':
        return 'other'
    
    primary_use_lower = str(primary_use).lower()
    
    mapping = {
        'academic': 'academic',
        'multi-use': 'student_life',
        'multi-purpose': 'student_life',
        'fitness': 'athletic',
        'medical': 'healthcare',
        'dining': 'student_life'
    }
    
    for key, value in mapping.items():
        if key in primary_use_lower:
            return value
    
    return 'other'

# Aggregate monthly data to yearly
aggregated = defaultdict(lambda: {
    'energy_kwh': 0,
    'primary_use': ''
})

with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        building = (row.get('building') or '').strip()
        year = (row.get('year') or '').strip()
        energy_mmbtu = (row.get('energy_MMBtu') or '').strip()
        primary_use = (row.get('primary_use') or '').strip()
        
        if not building or not year:
            continue
        
        energy_kwh = convert_mmbtu_to_kwh(energy_mmbtu)
        if not energy_kwh:
            continue
        
        key = (building, year)
        aggregated[key]['energy_kwh'] += energy_kwh
        
        if not aggregated[key]['primary_use'] and primary_use and primary_use != '...':
            aggregated[key]['primary_use'] = primary_use

# Convert to output format
rows = []
for (building, year), data in sorted(aggregated.items()):
    energy_kwh = data['energy_kwh']
    
    rows.append({
        'building': building,
        'year': int(year),
        'energy_consumption_kwh': energy_kwh,
        'water_consumption_gallons': estimate_water_from_energy(energy_kwh),
        'waste_diverted_lbs': estimate_waste_from_energy(energy_kwh),
        'co2_emissions_tons': calculate_co2_from_energy(energy_kwh),
        'metric_type': map_primary_use_to_metric_type(data['primary_use'])
    })

# Write output
fieldnames = ['building', 'year', 'energy_consumption_kwh', 'water_consumption_gallons',
              'waste_diverted_lbs', 'co2_emissions_tons', 'metric_type']

with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Converted {len(rows)} rows")
print(f"📁 Output: {OUTPUT_FILE}")
print(f"🏢 Buildings: {len(set(b['building'] for b in rows))}")
print(f"📅 Years: {sorted(set(b['year'] for b in rows))}")

