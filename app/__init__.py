#----------------------------------------------
# core part of the application
#----------------------------------------------

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flasgger import Swagger

from config import config

# Create DB
db = SQLAlchemy()

# Create Swagger
swagger = Swagger()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    db.init_app(app)
    # Apply all modification in the DB Schema
    migrate = Migrate(app, db)
    swagger.init_app(app)
    
    return app
