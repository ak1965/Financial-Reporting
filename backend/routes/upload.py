from flask import Blueprint, request, jsonify
import os
from werkzeug.utils import secure_filename

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
    
    # For now, just return success - we'll add processing logic later
    return jsonify({
        'message': 'File uploaded successfully',
        'filename': file.filename
    })