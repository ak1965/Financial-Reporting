from flask import Blueprint, jsonify, request
from services.database_service import (
    get_uploaded_trial_balances, 
    get_trial_balance_gl_codes,
    get_existing_mappings,
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

@mappings_bp.route('/mappings/<report_type>', methods=['GET'])
def get_mappings(report_type):
    """Get existing mappings for a report type"""
    try:
        mappings = get_existing_mappings(report_type)
        return jsonify({'mappings': mappings})
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

# Report line definitions
@mappings_bp.route('/mappings/report-lines/<report_type>', methods=['GET'])
def get_report_lines(report_type):
    """Get available report line options"""
    try:
        if report_type == 'profit_loss':
            lines = {
                'revenue': [
                    {'id': 'sales_revenue', 'name': 'Sales Revenue', 'sign_multiplier': -1},
                    {'id': 'other_income', 'name': 'Other Income', 'sign_multiplier': -1}
                ],
                'expenses': [
                    {'id': 'cost_of_sales', 'name': 'Cost of Sales', 'sign_multiplier': 1},
                    {'id': 'operating_expenses', 'name': 'Operating Expenses', 'sign_multiplier': 1},
                    {'id': 'admin_expenses', 'name': 'Admin Expenses', 'sign_multiplier': 1}
                ]
            }
        elif report_type == 'balance_sheet':
            lines = {
                'assets': [
                    {'id': 'current_assets', 'name': 'Current Assets', 'sign_multiplier': 1},
                    {'id': 'fixed_assets', 'name': 'Fixed Assets', 'sign_multiplier': 1}
                ],
                'liabilities': [
                    {'id': 'current_liabilities', 'name': 'Current Liabilities', 'sign_multiplier': -1},
                    {'id': 'long_term_liabilities', 'name': 'Long Term Liabilities', 'sign_multiplier': -1}
                ],
                'equity': [
                    {'id': 'equity', 'name': 'Equity', 'sign_multiplier': -1}
                ]
            }
        else:
            return jsonify({'error': 'Invalid report type'}), 400
            
        return jsonify({'report_lines': lines})
    except Exception as e:
        return jsonify({'error': str(e)}), 500