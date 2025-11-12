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
DATA_FILE = os.getenv('DATA_FILE', 'assets/sustainability_metrics.csv')
# Azure App Service uses WEBSITES_PORT, fallback to PORT or default 8080
PORT = int(os.getenv('WEBSITES_PORT', os.getenv('PORT', 8080)))
HOST = os.getenv('HOST', '0.0.0.0')

# Global variable to store loaded data
metrics_data = None


def load_data():
    """Load sustainability metrics data from CSV file."""
    global metrics_data
    try:
        data_path = Path(__file__).parent.parent / DATA_FILE
        logger.info(f"Loading data from: {data_path}")
        
        if not data_path.exists():
            logger.error(f"Data file not found: {data_path}")
            return None
        
        metrics_data = pd.read_csv(data_path)
        logger.info(f"Loaded {len(metrics_data)} records from {DATA_FILE}")
        logger.info(f"Columns: {list(metrics_data.columns)}")
        return metrics_data
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        return None


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
    return jsonify({
        'status': 'healthy',
        'service': 'uva-sustainability-api',
        'data_loaded': metrics_data is not None
    }), 200


@app.route('/api/v1/metrics', methods=['GET'])
def get_all_metrics():
    """
    Get all sustainability metrics.
    
    Query parameters:
    - building: Filter by building name (optional)
    - year: Filter by year (optional)
    """
    if metrics_data is None:
        return jsonify({
            'error': 'Data not loaded. Please check server logs.'
        }), 500
    
    try:
        filtered_data = metrics_data.copy()
        
        # Filter by building if provided
        building = request.args.get('building')
        if building:
            filtered_data = filtered_data[
                filtered_data['building'].str.contains(building, case=False, na=False)
            ]
        
        # Filter by year if provided
        year = request.args.get('year')
        if year:
            filtered_data = filtered_data[filtered_data['year'] == int(year)]
        
        # Convert to JSON
        result = filtered_data.to_dict(orient='records')
        
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
    
    Path parameters:
    - building_name: Name of the building
    """
    if metrics_data is None:
        return jsonify({
            'error': 'Data not loaded. Please check server logs.'
        }), 500
    
    try:
        building_data = metrics_data[
            metrics_data['building'].str.contains(building_name, case=False, na=False)
        ]
        
        if building_data.empty:
            return jsonify({
                'error': f'Building "{building_name}" not found'
            }), 404
        
        result = building_data.to_dict(orient='records')
        
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
    
    Query parameters:
    - year: Filter by year (optional)
    - aggregate_by: Group by 'year' or 'metric_type' (default: 'year')
    """
    if metrics_data is None:
        return jsonify({
            'error': 'Data not loaded. Please check server logs.'
        }), 500
    
    try:
        filtered_data = metrics_data.copy()
        
        # Filter by year if provided
        year = request.args.get('year')
        if year:
            filtered_data = filtered_data[filtered_data['year'] == int(year)]
        
        # Aggregate metrics
        aggregate_by = request.args.get('aggregate_by', 'year')
        
        if aggregate_by == 'year':
            # Aggregate by year
            numeric_cols = ['energy_consumption_kwh', 'water_consumption_gallons', 
                          'waste_diverted_lbs', 'co2_emissions_tons']
            aggregated = filtered_data.groupby('year')[numeric_cols].sum().reset_index()
            
            # Calculate additional metrics
            aggregated['total_buildings'] = filtered_data.groupby('year')['building'].nunique().values
            
        elif aggregate_by == 'metric_type':
            # Aggregate by metric type (sum all numeric metrics)
            numeric_cols = ['energy_consumption_kwh', 'water_consumption_gallons',
                          'waste_diverted_lbs', 'co2_emissions_tons']
            aggregated = {
                'total_energy_kwh': filtered_data['energy_consumption_kwh'].sum(),
                'total_water_gallons': filtered_data['water_consumption_gallons'].sum(),
                'total_waste_lbs': filtered_data['waste_diverted_lbs'].sum(),
                'total_co2_tons': filtered_data['co2_emissions_tons'].sum(),
                'total_buildings': filtered_data['building'].nunique(),
                'date_range': {
                    'start': int(filtered_data['year'].min()),
                    'end': int(filtered_data['year'].max())
                }
            }
        else:
            return jsonify({
                'error': f'Invalid aggregate_by parameter: {aggregate_by}. Use "year" or "metric_type"'
            }), 400
        
        result = aggregated.to_dict(orient='records') if aggregate_by == 'year' else aggregated
        
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
    """Get list of all buildings in the dataset."""
    if metrics_data is None:
        return jsonify({
            'error': 'Data not loaded. Please check server logs.'
        }), 500
    
    try:
        buildings = sorted(metrics_data['building'].unique().tolist())
        
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
        
        # Filter by building
        building_data = monthly_df[
            monthly_df['building'].str.contains(building_name, case=False, na=False)
        ]
        
        if building_data.empty:
            return jsonify({
                'error': f'Building "{building_name}" not found in monthly data'
            }), 404
        
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
                        'energy_MMBtu': round(energy_mmbtu, 1),
                        'gross_square_feet': row.get('gross_square_feet', ''),
                        'occupancy': row.get('occupancy', ''),
                        'primary_use': row.get('primary_use', '')
                    })
                except (ValueError, TypeError):
                    continue
        
        # Sort by year and month
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        monthly_data.sort(key=lambda x: (x['year'], month_order.index(x['month']) if x['month'] in month_order else 99))
        
        return jsonify({
            'building': building_name,
            'count': len(monthly_data),
            'data': monthly_data
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing monthly data request: {str(e)}")
        return jsonify({
            'error': f'Error processing request: {str(e)}'
        }), 500


# Load data when module is imported (for flask run)
@app.before_request
def ensure_data_loaded():
    """Ensure data is loaded before handling requests."""
    global metrics_data
    if metrics_data is None:
        logger.info("Loading data on first request...")
        load_data()
        if metrics_data is None:
            logger.warning("Data not loaded. API will return errors for data endpoints.")


if __name__ == '__main__':
    # Load data on startup (for python src/app.py)
    logger.info("Starting UVA Sustainability Metrics API...")
    load_data()
    
    if metrics_data is None:
        logger.warning("Data not loaded. API will return errors for data endpoints.")
    
    logger.info(f"Server starting on {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)

