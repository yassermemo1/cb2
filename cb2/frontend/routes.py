from flask import Blueprint, render_template, redirect, url_for, request, jsonify, current_app, send_from_directory
import os

frontend_bp = Blueprint('frontend', __name__, template_folder='templates')

@frontend_bp.route('/')
def index():
    """Render the index page."""
    return render_template('index.html')

@frontend_bp.route('/dashboard')
def dashboard():
    """Render the dashboard page."""
    return render_template('dashboard.html')

@frontend_bp.route('/instances')
def instances():
    """Serve the instances page."""
    return render_template('index.html')

@frontend_bp.route('/agents')
def agents():
    """Serve the agents page."""
    return render_template('index.html')

@frontend_bp.route('/cbapi')
def cbapi():
    """Render the CB API console page."""
    return render_template('cbapi.html')

@frontend_bp.route('/cbaudit')
def cbaudit():
    """Render the audit logs page."""
    return render_template('cbaudit.html')

@frontend_bp.route('/favicon.ico')
def favicon():
    """Serve the favicon."""
    return send_from_directory(
        os.path.join(frontend_bp.root_path, 'static'),
        'favicon.ico', 
        mimetype='image/vnd.microsoft.icon'
    ) 