from flask import Flask
from flask_cors import CORS
from config import get_config
import os
from routes.mappings import mappings_bp

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Load configuration
    config_obj = get_config(config_name)
    app.config.from_object(config_obj)
    
    # Enable CORS for React frontend
    # Enable CORS for React frontend
    CORS(app, 
     resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints (routes)
    from routes.upload import upload_bp
    from routes.reports import reports_bp
    
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/api')
    app.register_blueprint(mappings_bp, url_prefix='/api') 
    
    @app.route('/')
    def health_check():
        return {'status': 'Flask backend is running!', 'env': app.config['FLASK_ENV']}
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(debug=True, port=port, host='0.0.0.0')