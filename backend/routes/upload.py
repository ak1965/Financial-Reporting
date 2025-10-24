from flask import Blueprint, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename
from services.excel_processor import process_trial_balance_file
import uuid

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}

@upload_bp.route('/upload', methods=['POST'])
def upload_trial_balance():
    # Validate file exists
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload .xlsx or .xls files'}), 400
    
    # Validate company
    company = request.form.get('company')
    if not company:
        return jsonify({'error': 'Company name required'}), 400
    
    # Initialize variables
    filepath = None
    upload_id = str(uuid.uuid4())
    
    try:
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{upload_id}_{filename}")
        file.save(filepath)
        
        # Process the Excel file with company parameter
        result = process_trial_balance_file(filepath, upload_id, filename, company)
        
        # Clean up temporary file
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({
            'message': 'Trial balance processed successfully',
            'upload_id': upload_id,
            'filename': filename,
            'company': company,
            'rows_processed': result['rows_processed']
        })
        
    except Exception as e:
        # Clean up file if processing failed
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        
        # Update upload record to show failure
        try:
            from services.database_service import update_upload_status
            update_upload_status(upload_id, 'failed', str(e))
        except Exception:
            pass  # Don't fail if status update fails
        
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500
    
@upload_bp.route('/tb/delete', methods=['DELETE'])
def delete_trial_balance():
    try:
        company = request.args.get('company')
        period = request.args.get('period')
        
        if not company or not period:
            return jsonify({'error': 'Company and period required'}), 400
        
        from services.database_service import delete_tb_by_company_period
        delete_tb_by_company_period(company, period)
        
        return jsonify({
            'message': 'Trial balance deleted'
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500
    