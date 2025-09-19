from flask import Blueprint, jsonify, request

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/profit-loss', methods=['GET'])
def generate_profit_loss():
    # Placeholder - we'll implement this later
    return jsonify({
        'report_type': 'Profit & Loss',
        'data': {'message': 'P&L report endpoint ready'}
    })

@reports_bp.route('/reports/balance-sheet', methods=['GET'])
def generate_balance_sheet():
    # Placeholder - we'll implement this later
    return jsonify({
        'report_type': 'Balance Sheet',
        'data': {'message': 'Balance Sheet report endpoint ready'}
    })