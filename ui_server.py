from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import csv
import os
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Path to the CSV file containing test results
RESULT_CSV_PATH = "/home/pi/test_project/test_results/results.csv"


def read_test_results():
    """Read and parse test results from the CSV file."""
    results = []
    if os.path.exists(RESULT_CSV_PATH):
        with open(RESULT_CSV_PATH, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(row)
    return results


@app.route('/')
def index():
    status_filter = request.args.get('status', 'all').lower()
    data = read_test_results()

    # Filter data based on status (all, passed, failed)
    if status_filter != 'all':
        data = [row for row in data if row['Status'].lower() == status_filter]

    return render_template('index.html', data=data[::-1], status_filter=status_filter)


@app.route('/api/results/latest')
def latest_result():
    """API endpoint to get the latest test result."""
    data = read_test_results()
    if not data:
        return jsonify({"error": "No test results found"}), 404
    return jsonify(data[-1])


@app.route('/api/results/all')
def all_results():
    """API endpoint to get all test results."""
    data = read_test_results()
    if not data:
        return jsonify({"error": "No test results found"}), 404
    return jsonify(data)


@app.route('/static/results.csv')
def download_csv():
    """Download the test results CSV file."""
    if os.path.exists(RESULT_CSV_PATH):
        return send_from_directory(
            os.path.dirname(RESULT_CSV_PATH),
            os.path.basename(RESULT_CSV_PATH),
            as_attachment=True
        )
    return "CSV file not found", 404


@app.route('/download/excel')
def download_excel():
    """Download the test results as an Excel file."""
    if not os.path.exists(RESULT_CSV_PATH):
        return "CSV file not found", 404

    df = pd.read_csv(RESULT_CSV_PATH)
    excel_path = "/tmp/results.xlsx"
    df.to_excel(excel_path, index=False)
    return send_file(excel_path, as_attachment=True, download_name="results.xlsx")


if __name__ == '__main__':
    # Start the Flask app
    app.run(host='0.0.0.0', port=7897, debug=True)
