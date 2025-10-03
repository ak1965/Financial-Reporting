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
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload .xlsx or .xls files'}), 400
    
    filepath = None
    upload_id = str(uuid.uuid4())
    
    try:
        # Generate unique filename
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{upload_id}_{filename}")
        
        # Save file temporarily
        file.save(filepath)
        
        # Process the Excel file - this now handles both upload record AND data
        result = process_trial_balance_file(filepath, upload_id, filename)
        
        # Clean up temporary file
        os.remove(filepath)
        
        return jsonify({
            'message': 'Trial balance processed successfully',
            'upload_id': upload_id,
            'filename': filename,
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
        except:
            pass  # Don't fail if update fails
        
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500