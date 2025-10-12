from flask import Blueprint, jsonify, request
from services.database_service import (
    get_uploaded_trial_balances, 
    get_trial_balance_gl_codes,
   get_available_report_lines,
   get_existing_gl_mappings,
    save_gl_mapping,
    delete_gl_mapping
)

mappings_bp = Blueprint('mappings', __name__)

@mappings_bp.route('/mappings/trial-balances', methods=['GET'])
def get_trial_balances():
    """Get list of available trial balances"""
    try:
        trial_balances = get_uploaded_trial_balances()
        return jsonify({'trial_balances': trial_balances})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/mappings/gl-codes/<upload_id>', methods=['GET'])
def get_gl_codes(upload_id):
    """Get GL codes for a specific trial balance"""
    try:
        gl_codes = get_trial_balance_gl_codes(upload_id)
        return jsonify({'gl_codes': gl_codes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mappings_bp.route('/mappings', methods=['POST'])
def save_mapping():
    """Save a GL mapping"""
    try:
        data = request.json
        result = save_gl_mapping(
            data['gl_code'],
            data['report_type'], 
            data['line_id'],
            data['sign_multiplier']
        )
        return jsonify({'success': True, 'message': 'Mapping saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/mappings/<gl_code>/<report_type>', methods=['DELETE'])
def delete_mapping(gl_code, report_type):
    """Delete a GL mapping"""
    try:
        result = delete_gl_mapping(gl_code, report_type)
        return jsonify({'success': True, 'message': 'Mapping deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/mappings/mappings/<report_type>', methods=['GET'])
def get_existing_mappings_route(report_type):
    """Get existing GL code mappings"""
    try:
        mappings = get_existing_gl_mappings(report_type)  # Changed function name
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/mappings/report-lines/<report_type>', methods=['GET'])
def get_report_lines_route(report_type):
    """Get available report line options for dropdown"""
    try:
        lines_data = get_available_report_lines(report_type)
        
        # Transform into nested structure
        lines = {}
        for row in lines_data:
            section = row['section_name']
            if section not in lines:
                lines[section] = []
            lines[section].append({
                'id': row['line_id'],
                'name': row['line_name'],
                'sign_multiplier': row['sign_multiplier']
            })
        
        return jsonify({'report_lines': lines})
    except Exception as e:
        return jsonify({'error': str(e)}), 500