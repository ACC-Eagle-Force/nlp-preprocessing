"""
ACC API - Academic Calendar Core
All-in-one Flask API for parsing academic text and managing tasks.
"""

import sqlite3
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

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

# Database configuration
DB_PATH = "tasks.db"


# ============================================================================
# Database Functions
# ============================================================================

def init_database():
    """Initialize database schema."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    courses TEXT,
                    keywords TEXT,
                    due_date TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    original_text TEXT,
                    parsed_data TEXT
                )
            """)
            conn.commit()
            logger.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        raise


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
        "description": "Parse academic text and manage tasks",
        "endpoints": {
            "GET /": "API information",
            "GET /health": "Health check",
            "POST /parse": "Parse academic text",
            "POST /parse/batch": "Parse multiple texts",
            "POST /tasks": "Create a task",
            "GET /tasks": "Get all tasks",
            "GET /tasks/<id>": "Get specific task",
            "PUT /tasks/<id>": "Update task",
            "DELETE /tasks/<id>": "Delete task",
            "POST /tasks/<id>/complete": "Mark task as completed"
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


@app.route('/tasks', methods=['POST'])
def create_task():
    """
    Create a new task.
    
    Request Body:
        {
            "title": "Task title",
            "description": "Optional description",
            "text": "Optional text to parse"
        }
    """
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
        
        data = request.get_json()
        
        if 'title' not in data:
            return jsonify({"success": False, "error": "Missing required field: 'title'"}), 400
        
        title = data['title']
        description = data.get('description', '')
        
        # Parse text if provided
        courses = []
        keywords = []
        due_date = None
        original_text = ""
        parsed_data = {}
        
        if 'text' in data and data['text']:
            original_text = data['text']
            parsed_data = parse_dates_from_text(original_text)
            courses = parsed_data.get('courses', [])
            keywords = parsed_data.get('keywords', [])
            due_date = parsed_data.get('datetime_iso')
        
        # Insert into database
        now = datetime.now(timezone.utc).isoformat()
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (
                    title, description, courses, keywords, due_date,
                    status, created_at, updated_at, original_text, parsed_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title,
                description,
                json.dumps(courses),
                json.dumps(keywords),
                due_date,
                'pending',
                now,
                now,
                original_text,
                json.dumps(serialize_result(parsed_data)) if parsed_data else json.dumps({})
            ))
            conn.commit()
            task_id = cursor.lastrowid
        
        return jsonify({
            "success": True,
            "data": {"id": task_id, "title": title},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating task: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/tasks', methods=['GET'])
def get_tasks():
    """
    Get all tasks.
    
    Query Parameters:
        status: Filter by status (pending, completed, cancelled)
    """
    try:
        status = request.args.get('status')
        
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if status:
                cursor.execute("SELECT * FROM tasks WHERE status = ? ORDER BY due_date ASC", (status,))
            else:
                cursor.execute("SELECT * FROM tasks ORDER BY due_date ASC")
            
            rows = cursor.fetchall()
            tasks = []
            
            for row in rows:
                tasks.append({
                    'id': row['id'],
                    'title': row['title'],
                    'description': row['description'],
                    'courses': json.loads(row['courses']) if row['courses'] else [],
                    'keywords': json.loads(row['keywords']) if row['keywords'] else [],
                    'due_date': row['due_date'],
                    'status': row['status'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'original_text': row['original_text']
                })
        
        return jsonify({
            "success": True,
            "data": {
                "tasks": tasks,
                "count": len(tasks)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting tasks: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a specific task by ID."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            
            if not row:
                return jsonify({"success": False, "error": "Task not found"}), 404
            
            task = {
                'id': row['id'],
                'title': row['title'],
                'description': row['description'],
                'courses': json.loads(row['courses']) if row['courses'] else [],
                'keywords': json.loads(row['keywords']) if row['keywords'] else [],
                'due_date': row['due_date'],
                'status': row['status'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'original_text': row['original_text'],
                'parsed_data': json.loads(row['parsed_data']) if row['parsed_data'] else {}
            }
        
        return jsonify({
            "success": True,
            "data": task,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting task: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """
    Update a task.
    
    Request Body:
        {
            "title": "New title",
            "description": "New description",
            "status": "completed"
        }
    """
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
        
        data = request.get_json()
        updates = []
        params = []
        
        if 'title' in data:
            updates.append("title = ?")
            params.append(data['title'])
        if 'description' in data:
            updates.append("description = ?")
            params.append(data['description'])
        if 'status' in data:
            updates.append("status = ?")
            params.append(data['status'])
        if 'due_date' in data:
            updates.append("due_date = ?")
            params.append(data['due_date'])
        
        if not updates:
            return jsonify({"success": False, "error": "No fields to update"}), 400
        
        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append(task_id)
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({"success": False, "error": "Task not found"}), 404
        
        return jsonify({
            "success": True,
            "data": {"id": task_id},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating task: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({"success": False, "error": "Task not found"}), 404
        
        return jsonify({
            "success": True,
            "data": {"id": task_id},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting task: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/tasks/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """Mark a task as completed."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                ('completed', datetime.now(timezone.utc).isoformat(), task_id)
            )
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({"success": False, "error": "Task not found"}), 404
        
        return jsonify({
            "success": True,
            "data": {"id": task_id, "status": "completed"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error completing task: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


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
    # Initialize database
    init_database()
    
    # Run Flask development server
    logger.info("Starting ACC API server...")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )

