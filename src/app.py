"""
UVA Sustainability Metrics API

A REST API that serves summarized sustainability metrics for UVA buildings
or campus-wide aggregations.
"""

import os
import logging
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .flaskenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)  # Enable CORS for frontend integration

# Configuration
# Azure App Service uses WEBSITES_PORT, fallback to PORT or default 8080
PORT = int(os.getenv('WEBSITES_PORT', os.getenv('PORT', 8080)))
HOST = os.getenv('HOST', '0.0.0.0')

# All data is now loaded from uva_energy_data_template.csv on-demand


@app.route('/', methods=['GET'])
def root():
    """Root endpoint - serve web interface."""
    return render_template('index.html')


@app.route('/api', methods=['GET'])
def api_info():
    """API information endpoint."""
    return jsonify({
        'service': 'UVA Sustainability Metrics API',
        'version': '1.0',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'buildings': '/api/v1/buildings',
            'metrics': '/api/v1/metrics',
            'building_metrics': '/api/v1/metrics/<building_name>',
            'campus_wide': '/api/v1/metrics/campus-wide',
            'monthly_data': '/api/v1/metrics/<building_name>/monthly'
        },
        'documentation': 'See README.md for API documentation'
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    data_file = Path(__file__).parent.parent / 'assets' / 'uva_energy_data_template.csv'
    return jsonify({
        'status': 'healthy',
        'service': 'uva-sustainability-api',
        'data_file_exists': data_file.exists()
    }), 200


@app.route('/api/v1/metrics', methods=['GET'])
def get_all_metrics():
    """
    Get all sustainability metrics.
    Calculates from uva_energy_data_template.csv.
    
    Query parameters:
    - building: Filter by building name (optional)
    - year: Filter by year (optional)
    """
    try:
        monthly_data_path = Path(__file__).parent.parent / 'assets' / 'uva_energy_data_template.csv'
        
        if not monthly_data_path.exists():
            return jsonify({
                'error': 'Building data file not found'
            }), 404
        
        # Get all buildings and calculate their metrics
        monthly_df = pd.read_csv(monthly_data_path)
        
        # Check if file has monthly format
        if 'month' not in monthly_df.columns or 'energy_MMBtu' not in monthly_df.columns:
            return jsonify({
                'error': 'Monthly data format not found'
            }), 500
        
        # Filter by building if provided
        building = request.args.get('building')
        if building:
            monthly_df = monthly_df[
                monthly_df['building'].str.contains(building, case=False, na=False)
            ]
        
        # Aggregate by building and year
        MMBTU_TO_KWH = 293.071
        result = []
        
        for (building_name, year), group in monthly_df.groupby(['building', 'year']):
            energy_kwh = 0
            for _, row in group.iterrows():
                if pd.notna(row.get('energy_MMBtu')) and str(row.get('energy_MMBtu')).strip() != '':
                    try:
                        energy_mmbtu = float(row.get('energy_MMBtu'))
                        energy_kwh += energy_mmbtu * MMBTU_TO_KWH
                    except (ValueError, TypeError):
                        continue
            
            if energy_kwh > 0:
                # Filter by year if provided
                year_filter = request.args.get('year')
                if year_filter and int(year) != int(year_filter):
                    continue
                
                result.append({
                    'building': building_name,
                    'year': int(year),
                    'energy_consumption_kwh': int(energy_kwh),
                    'water_consumption_gallons': int(energy_kwh * 0.5),
                    'waste_diverted_lbs': int(energy_kwh * 0.033),
                    'co2_emissions_tons': round(energy_kwh * 0.0004, 1)
                })
        
        logger.info(f"Returning {len(result)} records")
        return jsonify({
            'count': len(result),
            'data': result
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            'error': f'Error processing request: {str(e)}'
        }), 500


@app.route('/api/v1/metrics/<building_name>', methods=['GET'])
def get_building_metrics(building_name):
    """
    Get sustainability metrics for a specific building.
    Calculates yearly totals from monthly data in uva_energy_data_template.csv.
    
    Path parameters:
    - building_name: Name of the building
    """
    try:
        monthly_data_path = Path(__file__).parent.parent / 'assets' / 'uva_energy_data_template.csv'
        
        if not monthly_data_path.exists():
            return jsonify({
                'error': 'Building data file not found'
            }), 404
        
        monthly_df = pd.read_csv(monthly_data_path)
        
        # Check if file has monthly format
        if 'month' not in monthly_df.columns or 'energy_MMBtu' not in monthly_df.columns:
            return jsonify({
                'error': 'Monthly data format not found. Please ensure uva_energy_data_template.csv has month and energy_MMBtu columns.'
            }), 500
        
        # Filter by building
        building_data = monthly_df[
            monthly_df['building'].str.contains(building_name, case=False, na=False)
        ]
        
        if building_data.empty:
            return jsonify({
                'error': f'Building "{building_name}" not found'
            }), 404
        
        # Extract building info from first row that has it
        building_info = {}
        for _, row in building_data.iterrows():
            gross_sqft = row.get('gross_square_feet', '')
            occupancy = row.get('occupancy', '')
            primary_use = row.get('primary_use', '')
            
            if 'gross_square_feet' not in building_info:
                if pd.notna(gross_sqft) and str(gross_sqft).strip() != '' and str(gross_sqft).strip() != '...':
                    try:
                        building_info['gross_square_feet'] = int(float(gross_sqft))
                    except (ValueError, TypeError):
                        pass
            
            if 'occupancy' not in building_info:
                if pd.notna(occupancy) and str(occupancy).strip() != '' and str(occupancy).strip() != '...':
                    try:
                        building_info['occupancy'] = int(float(occupancy))
                    except (ValueError, TypeError):
                        pass
            
            if 'primary_use' not in building_info:
                if pd.notna(primary_use) and str(primary_use).strip() != '' and str(primary_use).strip() != '...':
                    building_info['primary_use'] = str(primary_use).strip()
            
            if len(building_info) >= 3:
                break
        
        # Convert MMBtu to kWh and aggregate by year
        MMBTU_TO_KWH = 293.071
        yearly_data = {}
        
        for _, row in building_data.iterrows():
            if pd.notna(row.get('energy_MMBtu')) and str(row.get('energy_MMBtu')).strip() != '':
                try:
                    year = int(row.get('year', 0))
                    energy_mmbtu = float(row.get('energy_MMBtu'))
                    energy_kwh = energy_mmbtu * MMBTU_TO_KWH
                    
                    if year not in yearly_data:
                        yearly_data[year] = {
                            'building': building_name,
                            'year': year,
                            'energy_consumption_kwh': 0,
                            'water_consumption_gallons': 0,
                            'waste_diverted_lbs': 0,
                            'co2_emissions_tons': 0,
                            'metric_type': building_info.get('primary_use', 'unknown')
                        }
                    
                    yearly_data[year]['energy_consumption_kwh'] += energy_kwh
                    
                    # Estimate other metrics (can be improved with actual data)
                    # Water: ~0.5 gallons per kWh (rough estimate)
                    yearly_data[year]['water_consumption_gallons'] += energy_kwh * 0.5
                    # Waste: ~0.033 lbs per kWh
                    yearly_data[year]['waste_diverted_lbs'] += energy_kwh * 0.033
                    # CO2: ~0.0004 tons per kWh (varies by energy source)
                    yearly_data[year]['co2_emissions_tons'] += energy_kwh * 0.0004
                    
                except (ValueError, TypeError):
                    continue
        
        # Convert to list and round values
        result = []
        for year_data in sorted(yearly_data.values(), key=lambda x: x['year']):
            year_data['energy_consumption_kwh'] = int(year_data['energy_consumption_kwh'])
            year_data['water_consumption_gallons'] = int(year_data['water_consumption_gallons'])
            year_data['waste_diverted_lbs'] = int(year_data['waste_diverted_lbs'])
            year_data['co2_emissions_tons'] = round(year_data['co2_emissions_tons'], 1)
            result.append(year_data)
        
        logger.info(f"Returning metrics for building: {building_name}")
        return jsonify({
            'building': building_name,
            'count': len(result),
            'data': result
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            'error': f'Error processing request: {str(e)}'
        }), 500


@app.route('/api/v1/metrics/campus-wide', methods=['GET'])
def get_campus_wide_metrics():
    """
    Get campus-wide aggregated sustainability metrics.
    Calculates from uva_energy_data_template.csv.
    
    Query parameters:
    - year: Filter by year (optional)
    - aggregate_by: Group by 'year' or 'metric_type' (default: 'year')
    """
    try:
        monthly_data_path = Path(__file__).parent.parent / 'assets' / 'uva_energy_data_template.csv'
        
        if not monthly_data_path.exists():
            return jsonify({
                'error': 'Building data file not found'
            }), 404
        
        monthly_df = pd.read_csv(monthly_data_path)
        
        # Check if file has monthly format
        if 'month' not in monthly_df.columns or 'energy_MMBtu' not in monthly_df.columns:
            return jsonify({
                'error': 'Monthly data format not found'
            }), 500
        
        # Filter by year if provided
        year_filter = request.args.get('year')
        if year_filter:
            monthly_df = monthly_df[monthly_df['year'] == int(year_filter)]
        
        # Aggregate metrics
        aggregate_by = request.args.get('aggregate_by', 'year')
        MMBTU_TO_KWH = 293.071
        
        if aggregate_by == 'year':
            # Aggregate by year
            yearly_totals = {}
            for (building_name, year), group in monthly_df.groupby(['building', 'year']):
                energy_kwh = 0
                for _, row in group.iterrows():
                    if pd.notna(row.get('energy_MMBtu')) and str(row.get('energy_MMBtu')).strip() != '':
                        try:
                            energy_mmbtu = float(row.get('energy_MMBtu'))
                            energy_kwh += energy_mmbtu * MMBTU_TO_KWH
                        except (ValueError, TypeError):
                            continue
                
                if year not in yearly_totals:
                    yearly_totals[year] = {
                        'year': int(year),
                        'energy_consumption_kwh': 0,
                        'water_consumption_gallons': 0,
                        'waste_diverted_lbs': 0,
                        'co2_emissions_tons': 0,
                        'buildings': set()
                    }
                
                if energy_kwh > 0:
                    yearly_totals[year]['energy_consumption_kwh'] += energy_kwh
                    yearly_totals[year]['water_consumption_gallons'] += int(energy_kwh * 0.5)
                    yearly_totals[year]['waste_diverted_lbs'] += int(energy_kwh * 0.033)
                    yearly_totals[year]['co2_emissions_tons'] += energy_kwh * 0.0004
                    yearly_totals[year]['buildings'].add(building_name)
            
            result = []
            for year_data in sorted(yearly_totals.values(), key=lambda x: x['year']):
                year_data['energy_consumption_kwh'] = int(year_data['energy_consumption_kwh'])
                year_data['water_consumption_gallons'] = int(year_data['water_consumption_gallons'])
                year_data['waste_diverted_lbs'] = int(year_data['waste_diverted_lbs'])
                year_data['co2_emissions_tons'] = round(year_data['co2_emissions_tons'], 1)
                year_data['total_buildings'] = len(year_data['buildings'])
                del year_data['buildings']
                result.append(year_data)
            
        elif aggregate_by == 'metric_type':
            # Aggregate all metrics
            total_energy = 0
            buildings_set = set()
            
            for (building_name, year), group in monthly_df.groupby(['building', 'year']):
                buildings_set.add(building_name)
                for _, row in group.iterrows():
                    if pd.notna(row.get('energy_MMBtu')) and str(row.get('energy_MMBtu')).strip() != '':
                        try:
                            energy_mmbtu = float(row.get('energy_MMBtu'))
                            total_energy += energy_mmbtu * MMBTU_TO_KWH
                        except (ValueError, TypeError):
                            continue
            
            result = {
                'total_energy_kwh': int(total_energy),
                'total_water_gallons': int(total_energy * 0.5),
                'total_waste_lbs': int(total_energy * 0.033),
                'total_co2_tons': round(total_energy * 0.0004, 1),
                'total_buildings': len(buildings_set),
                'date_range': {
                    'start': int(monthly_df['year'].min()) if len(monthly_df) > 0 else None,
                    'end': int(monthly_df['year'].max()) if len(monthly_df) > 0 else None
                }
            }
        else:
            return jsonify({
                'error': f'Invalid aggregate_by parameter: {aggregate_by}. Use "year" or "metric_type"'
            }), 400
        
        logger.info(f"Returning campus-wide metrics aggregated by: {aggregate_by}")
        return jsonify({
            'aggregation': aggregate_by,
            'data': result
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            'error': f'Error processing request: {str(e)}'
        }), 500


@app.route('/api/v1/buildings', methods=['GET'])
def list_buildings():
    """Get list of all buildings from uva_energy_data_template.csv."""
    try:
        monthly_data_path = Path(__file__).parent.parent / 'assets' / 'uva_energy_data_template.csv'
        
        if not monthly_data_path.exists():
            return jsonify({
                'error': 'Building data file not found'
            }), 404
        
        monthly_df = pd.read_csv(monthly_data_path)
        
        # Check if file has building column
        if 'building' not in monthly_df.columns:
            return jsonify({
                'error': 'Invalid data format: building column not found'
            }), 500
        
        # Get unique buildings - handle both formats
        # Remove any empty/NaN building names
        buildings = monthly_df['building'].dropna()
        buildings = buildings[buildings.str.strip() != '']
        buildings = sorted(buildings.unique().tolist())
        
        logger.info(f"Found {len(buildings)} unique buildings in CSV")
        
        return jsonify({
            'count': len(buildings),
            'buildings': buildings
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            'error': f'Error processing request: {str(e)}'
        }), 500


@app.route('/api/v1/metrics/<building_name>/monthly', methods=['GET'])
def get_building_monthly_data(building_name):
    """
    Get monthly energy data for a specific building.
    Uses the monthly data from uva_energy_data_template.csv if available.
    """
    try:
        # Try to load monthly data
        monthly_data_path = Path(__file__).parent.parent / 'assets' / 'uva_energy_data_template.csv'
        
        if not monthly_data_path.exists():
            return jsonify({
                'error': 'Monthly data not available'
            }), 404
        
        monthly_df = pd.read_csv(monthly_data_path)
        
        # Check if file has monthly format (has 'month' column) or yearly format
        has_monthly_format = 'month' in monthly_df.columns and 'energy_MMBtu' in monthly_df.columns
        
        if not has_monthly_format:
            return jsonify({
                'error': 'Monthly data format not found. Please ensure uva_energy_data_template.csv has month and energy_MMBtu columns.'
            }), 404
        
        # Filter by building
        building_data = monthly_df[
            monthly_df['building'].str.contains(building_name, case=False, na=False)
        ]
        
        if building_data.empty:
            return jsonify({
                'error': f'Building "{building_name}" not found in monthly data'
            }), 404
        
        # Extract building info from first row that has it
        building_info = {}
        for _, row in building_data.iterrows():
            gross_sqft = row.get('gross_square_feet', '')
            occupancy = row.get('occupancy', '')
            primary_use = row.get('primary_use', '')
            
            # Extract gross_square_feet
            if 'gross_square_feet' not in building_info:
                if pd.notna(gross_sqft) and str(gross_sqft).strip() != '' and str(gross_sqft).strip() != '...':
                    try:
                        building_info['gross_square_feet'] = int(float(gross_sqft))
                    except (ValueError, TypeError):
                        pass
            
            # Extract occupancy
            if 'occupancy' not in building_info:
                if pd.notna(occupancy) and str(occupancy).strip() != '' and str(occupancy).strip() != '...':
                    try:
                        building_info['occupancy'] = int(float(occupancy))
                    except (ValueError, TypeError):
                        pass
            
            # Extract primary_use
            if 'primary_use' not in building_info:
                if pd.notna(primary_use) and str(primary_use).strip() != '' and str(primary_use).strip() != '...':
                    building_info['primary_use'] = str(primary_use).strip()
            
            # Continue until we have all info or checked all rows
            if len(building_info) >= 3:
                break
        
        # Convert MMBtu to kWh and prepare monthly data
        MMBTU_TO_KWH = 293.071
        monthly_data = []
        
        for _, row in building_data.iterrows():
            if pd.notna(row.get('energy_MMBtu')) and str(row.get('energy_MMBtu')).strip() != '':
                try:
                    energy_mmbtu = float(row.get('energy_MMBtu'))
                    energy_kwh = int(energy_mmbtu * MMBTU_TO_KWH)
                    
                    monthly_data.append({
                        'month': row.get('month', ''),
                        'year': int(row.get('year', 0)),
                        'energy_kwh': energy_kwh,
                        'energy_MMBtu': round(energy_mmbtu, 1)
                    })
                except (ValueError, TypeError):
                    continue
        
        # Sort by year and month
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        monthly_data.sort(key=lambda x: (x['year'], month_order.index(x['month']) if x['month'] in month_order else 99))
        
        return jsonify({
            'building': building_name,
            'count': len(monthly_data),
            'building_info': building_info,
            'data': monthly_data
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing monthly data request: {str(e)}")
        return jsonify({
            'error': f'Error processing request: {str(e)}'
        }), 500


if __name__ == '__main__':
    # Run the Flask app
    logger.info("Starting UVA Sustainability Metrics API...")
    logger.info("All data loaded from uva_energy_data_template.csv on-demand")
    logger.info(f"Server starting on {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)

