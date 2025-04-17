from flask import Flask, jsonify, request, Response
from prometheus_client import Counter, Summary, Gauge, generate_latest
import time
import os
import psutil
import subprocess  # Optional, for script execution failure tracking
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import make_wsgi_app

app = Flask(__name__)

# In-memory storage for testing
test_data = {
    "user1": {"name": "Alice", "age": 30},
    "user2": {"name": "Bob", "age": 25}
}

# Prometheus Metrics
REQUEST_COUNT = Counter('flask_request_count', 'Total request count', ['method', 'endpoint'])
REQUEST_LATENCY = Summary('flask_request_latency_seconds', 'Request latency', ['endpoint'])
JWT_SUCCESS_COUNT = Counter('flask_jwt_success_count', 'Count of successful JWT authentications')
JWT_FAILURE_COUNT = Counter('flask_jwt_failure_count', 'Count of failed JWT authentications')
SCRIPT_FAILURE_COUNT = Counter('flask_script_failures', 'Number of script execution failures')
CPU_USAGE = Gauge('flask_cpu_usage', 'CPU usage percentage')
MEMORY_USAGE = Gauge('flask_memory_usage', 'Memory usage percentage')
UPTIME = Gauge('flask_uptime', 'Uptime of the system')

@app.before_request
def before_request():
    """Record request count and start timing the request."""
    REQUEST_COUNT.labels(method=request.method, endpoint=request.path).inc()
    request.start_time = time.time()

@app.after_request
def after_request(response):
    """Record request latency after the request is processed."""
    latency = time.time() - request.start_time
    REQUEST_LATENCY.labels(endpoint=request.path).observe(latency)
    return response

@app.route('/data', methods=['GET'])
def get_data():
    """A simple GET API to return a test message."""
    return jsonify({"message": "This is a test API"})

@app.route('/users', methods=['GET'])
def get_users():
    """GET API to return all users."""
    return jsonify(test_data)

@app.route('/user/<username>', methods=['GET'])
def get_user(username):
    """GET API to return a specific user's data."""
    user = test_data.get(username)
    if user:
        return jsonify(user)
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/user', methods=['POST'])
def create_user():
    """POST API to create a new user."""
    data = request.get_json()
    username = data.get('username')
    name = data.get('name')
    age = data.get('age')

    if username and name and age:
        test_data[username] = {"name": name, "age": age}
        return jsonify({"message": "User created successfully", "user": test_data[username]}), 201
    else:
        return jsonify({"error": "Missing required fields"}), 400

@app.route('/user/<username>', methods=['PUT'])
def update_user(username):
    """PUT API to update a user's information."""
    if username in test_data:
        data = request.get_json()
        test_data[username].update(data)
        return jsonify({"message": "User updated successfully", "user": test_data[username]})
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/user/<username>', methods=['DELETE'])
def delete_user(username):
    """DELETE API to remove a user."""
    if username in test_data:
        del test_data[username]
        return jsonify({"message": f"User {username} deleted successfully"})
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/health', methods=['GET'])
def health_check():
    """Health check for uptime."""
    return jsonify({"status": "healthy"})

# Update CPU, memory, and uptime metrics before each request
@app.before_request
def update_system_metrics():
    REQUEST_COUNT.labels(method=request.method, endpoint=request.path).inc()
    request.start_time = time.time()
    CPU_USAGE.set(psutil.cpu_percent())
    MEMORY_USAGE.set(psutil.virtual_memory().percent)
    UPTIME.set(time.time() - psutil.boot_time())

# Use DispatcherMiddleware to serve /metrics
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

# Example JWT validation (placeholder)
def verify_jwt(token):
    """Mock JWT validation logic."""
    if token == "valid-token":
        JWT_SUCCESS_COUNT.inc()
        return True
    else:
        JWT_FAILURE_COUNT.inc()
        return False

# Example of script execution tracking
@app.route('/run-script', methods=['POST'])
def run_script():
    """Mock shell script execution."""
    try:
        subprocess.run(['echo', 'Hello from script!'], check=True)
        return jsonify({"message": "Script executed successfully"})
    except subprocess.CalledProcessError:
        SCRIPT_FAILURE_COUNT.inc()
        return jsonify({"error": "Script execution failed"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
