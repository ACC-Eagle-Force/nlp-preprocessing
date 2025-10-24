"""
ACC API - Academic Calendar Core
Flask API for parsing academic text.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from flask import Flask, request, jsonify
from flask_cors import CORS

# Import core parsing module
from acc_core import parse_dates_from_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)


def serialize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize parse result, removing non-JSON-serializable objects."""
    serialized = result.copy()
    if 'datetime_utc' in serialized:
        serialized.pop('datetime_utc')
    return serialized


# ============================================================================
# API Endpoints
# ============================================================================

@app.route('/', methods=['GET'])
def index():
    """API information and available endpoints."""
    return jsonify({
        "service": "Academic Calendar Core (ACC) API",
        "version": "2.0.0",
        "description": "Parse academic text to extract course codes, keywords, and dates",
        "endpoints": {
            "GET /": "API information",
            "GET /health": "Health check",
            "POST /parse": "Parse academic text",
            "POST /parse/batch": "Parse multiple texts"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "ACC API",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


@app.route('/parse', methods=['POST'])
def parse_text():
    """
    Parse a single academic text string.
    
    Request Body:
        {
            "text": "CSC101 assignment due by 5 Oct 2025 at 11:59pm"
        }
    """
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Request must be JSON"
            }), 400
        
        data = request.get_json()
        
        if 'text' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: 'text'"
            }), 400
        
        text = data['text']
        
        if not isinstance(text, str):
            return jsonify({
                "success": False,
                "error": "Field 'text' must be a string"
            }), 400
        
        # Parse the text
        result = parse_dates_from_text(text)
        serialized_result = serialize_result(result)
        
        return jsonify({
            "success": True,
            "data": serialized_result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in parse_text: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500


@app.route('/parse/batch', methods=['POST'])
def parse_batch():
    """
    Parse multiple academic text strings.
    
    Request Body:
        {
            "texts": ["text1", "text2", ...]
        }
    """
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Request must be JSON"
            }), 400
        
        data = request.get_json()
        
        if 'texts' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: 'texts'"
            }), 400
        
        texts = data['texts']
        
        if not isinstance(texts, list):
            return jsonify({
                "success": False,
                "error": "Field 'texts' must be a list"
            }), 400
        
        if len(texts) > 100:
            return jsonify({
                "success": False,
                "error": "Maximum batch size is 100 texts"
            }), 400
        
        results = []
        for text in texts:
            if isinstance(text, str):
                result = parse_dates_from_text(text)
                serialized_result = serialize_result(result)
                results.append(serialized_result)
            else:
                results.append({"error": "Invalid text type"})
        
        return jsonify({
            "success": True,
            "data": {
                "results": results,
                "count": len(results)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in parse_batch: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500




# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"success": False, "error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({"success": False, "error": "Internal server error"}), 500


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    # Run Flask development server
    logger.info("Starting ACC API server...")
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )

