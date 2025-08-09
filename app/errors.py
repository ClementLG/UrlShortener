from flask import render_template, request, jsonify, Blueprint
import logging

errors_bp = Blueprint('errors', __name__)
logger = logging.getLogger(__name__)

@errors_bp.app_errorhandler(500)
def internal_server_error(e):
    """Handles 500 Internal Server Error."""
    logger.error(f"Internal Server Error (500) - IP: {request.remote_addr} - URL: {request.url} - Error: {e}", exc_info=True)
    if request.is_json:
        return jsonify(error="Internal server error"), 500
    return render_template('500.html'), 500

@errors_bp.app_errorhandler(400)
def bad_request(e):
    """Handles 400 Bad Request errors."""
    description = e.description or "The browser (or proxy) sent a request that this server could not understand."
    logger.warning(f"Bad Request (400) - IP: {request.remote_addr} - URL: {request.url} - Description: {description}")
    if request.is_json:
        return jsonify(error=description), 400
    return render_template('400.html', error_message=description), 400

@errors_bp.app_errorhandler(404)
def page_not_found(e):
    """Handles 404 Not Found errors."""
    description = e.description or "Page not found."
    logger.warning(f"Page not found (404) - IP: {request.remote_addr} - URL: {request.url}")
    if request.is_json:
        return jsonify(error=description), 404
    return render_template('404.html', error_message=description), 404

@errors_bp.app_errorhandler(429)
def ratelimit_handler(e):
    """Handles 429 Too Many Requests errors."""
    logger.warning(f"Rate limit exceeded (429) - IP: {request.remote_addr} - Limit: {e.description}")
    if request.is_json:
        return jsonify(error=f"Rate limit exceeded: {e.description}"), 429
    return render_template('429.html', limit=e.description), 429