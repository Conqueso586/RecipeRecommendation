from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from config import config
from models.models import db
from api.routes import api
from data.data_loader import init_sample_data



def create_app(config_name=None):
    """Application factory pattern for creating Flask app."""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(api)
    
    # Initialize database and sample data
    with app.app_context():
        db.create_all()
        init_sample_data()
    
    return app

def main():
    """Main entry point for running the application."""
    app = create_app()
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print("=" * 50)
    print("🍳 Recipe Recommendation API")
    print("=" * 50)
    print(f"Server running on: http://localhost:{port}")
    print(f"Health check: http://localhost:{port}/api/health")
    print(f"Debug mode: {debug}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main()