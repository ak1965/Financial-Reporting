from flask import Flask
from flask_cors import CORS
from config import config
import os

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Enable CORS for React frontend
    CORS(app)
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints (routes)
    from routes.upload import upload_bp
    from routes.reports import reports_bp
    
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/api')
    
    @app.route('/')
    def health_check():
        return {'status': 'Flask backend is running!'}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)