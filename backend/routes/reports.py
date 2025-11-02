from flask import Blueprint, jsonify, request
from services.report_generator import generate_profit_loss_report
from services.report_generator import generate_balance_sheet_report
from services.database_service import get_available_periods
from services.database_service import get_available_companies
from services.database_service import get_available_periods_delete


reports_bp = Blueprint('reports', __name__)



@reports_bp.route('/reports/profit-loss', methods=['GET'])
def get_profit_loss():
    try:
        period_end_date = request.args.get('period_end_date')
        company = request.args.get('company')  # Get company parameter
        
        if not period_end_date:
            return jsonify({'error': 'period_end_date is required'}), 400
        
        if not company:
            return jsonify({'error': 'company is required'}), 400
        
        from services.report_generator import generate_profit_loss_report
        report = generate_profit_loss_report(period_end_date, company)  # Pass company
        
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/reports/balance-sheet', methods=['GET'])
def generate_balance_sheet():
    try:
        period_end_date = request.args.get('period_end_date')
        
        if not period_end_date:
            return jsonify({'error': 'period_end_date parameter is required'}), 400
        
        # Call your actual balance sheet generation function
        report_data = generate_balance_sheet_report(period_end_date)
        
        return jsonify(report_data)
        
    except Exception as e:
        print(f"❌ Balance Sheet API Error: {str(e)}")
        return jsonify({'error': f'Failed to generate balance sheet: {str(e)}'}), 500

@reports_bp.route('/reports/available-periods', methods=['GET'])
def get_available_periods_route():
    """Get list of available reporting periods"""
    try:
        company = request.args.get('company')
        
        if not company:
            return jsonify({'error': 'Company parameter is required'}), 400
        
        periods = get_available_periods(company)
        return jsonify({'periods': periods})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/reports/available-periods-delete', methods=['GET'])
def get_available_periods_delete_route():
    """Get list of available reporting periods"""
    try:
        company = request.args.get('company')
        
        if not company:
            return jsonify({'error': 'Company parameter is required'}), 400
        
        periods = get_available_periods_delete(company)
        return jsonify({'periods': periods})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@reports_bp.route('/reports/available-companies', methods=['GET'])
def get_available_companies_route():
    """Get list of available companies"""
    try:
        
        companies = get_available_companies()
        return jsonify({'companies': companies})
    except Exception as e:
        return jsonify({'error': str(e)}), 500