from flask import Blueprint

# Import blueprints
from app.api import auth, services, professionals, customers, admin

# Each module has its own blueprint
# Registration is done in app/__init__.py
