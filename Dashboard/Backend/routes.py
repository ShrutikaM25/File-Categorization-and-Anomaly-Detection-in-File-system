import json
import os
import time
import pickle
import magic
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from datetime import datetime, timedelta
from collections import defaultdict
import ZODB, ZODB.FileStorage
import collections.abc
import sys
import ZODB, ZODB.FileStorage
import transaction
from persistent.mapping import PersistentMapping
# Get the absolute path of the `Phase-2` directory
PHASE_2_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Phase2"))

sys.path.append(PHASE_2_PATH)

from anomaly import (
    detect_anomalies_with_scores,
    combine_anomaly_scores,
    extract_features,
    save_anomalies_sequentially,
    explain_anomalies
)
app = Flask(__name__)
CORS(app)

def load_model():
    with open('hash_mappings.pkl', 'rb') as file:
        file_extension_hash = pickle.load(file)
    return file_extension_hash

# Function to initialize and manage cache (SQLite-based cache storage logic)
def initialize_cache():
    try:
        with open('cache.pkl', 'rb') as cache_file:
            cache = pickle.load(cache_file)
    except FileNotFoundError:
        cache = {}

    return cache

def save_cache(cache):
    # Save the cache back to the pickle file
    with open('cache.pkl', 'wb') as cache_file:
        pickle.dump(cache, cache_file)

def add_to_cache(extension, mime_type, category, cache):
    if len(cache) >= 1000:  # Cache size limit
        print("Cache size limit reached, merging cache.")
        merge_cache_with_model(cache)

    cache[extension] = {'mime_type': mime_type, 'category': category}
    save_cache(cache)

def merge_cache_with_model(cache):
    # Assuming `file_extension_hash.pkl` is a dictionary
    model = load_model()
    model.update(cache)
    
    with open('hash_mappings.pkl', 'wb') as model_file:
        pickle.dump(model, model_file)
    
    save_cache({})  

def load_mappings(pickle_file_path):
    """Load the mappings from the pickle file."""
    with open(pickle_file_path, 'rb') as pickle_file:
        mappings = pickle.load(pickle_file)
    return mappings

def predict_category_from_buffer(extension, mime_type, mappings):
    """
    Predict the category of a file based on its extension and MIME type,
    using in-memory data from the mappings.
    """
    # Normalize: remove leading dot from extension and convert both to lowercase
    extension = extension.lower()
    mime_type = mime_type.lower()
    
    # Retrieve mappings
    ext_to_idx = mappings['ext_to_idx']
    mime_to_idx = mappings['mime_to_idx']
    idx_to_category = mappings['idx_to_category']
    prediction_map = mappings['prediction_map']
    
    # Encode extension and MIME type
    ext_encoded = ext_to_idx.get(extension, -1)
    mime_encoded = mime_to_idx.get(mime_type, -1)
    print(ext_encoded, mime_encoded)
    
    # Check exact combo (extension + MIME type)
    if ext_encoded != -1 and mime_encoded != -1:
        category_encoded = prediction_map.get((ext_encoded, mime_encoded), -1)
        if category_encoded != -1:
            return idx_to_category.get(category_encoded, "Unknown Category")
    
    # If exact combo not found, try extension only
    if ext_encoded != -1:
        for (ext, mime), category in prediction_map.items():
            if ext == ext_encoded:
                return idx_to_category.get(category, "Unknown Category")

    # Fallback to "Unknown Category"
    return "Unknown Category"


@app.route('/classify-dir', methods=['POST'])
def classify_directory():
    pickle_file_path = './hash_mappings.pkl'

    # Load the mappings
    try:
        mappings = load_mappings(pickle_file_path)
    except FileNotFoundError:
        print(f"Error: Pickle file '{pickle_file_path}' not found.")
        sys.exit(1)
    
    try:
        if 'files' not in request.files:
            return jsonify({"error": "No files uploaded"}), 400

        files = request.files.getlist('files')
        classified_files = {}

        for file in files:
            file_name = file.filename
            # print("Processing file:", file_name)
            
            # Get the file extension from file.filename
            extension = os.path.splitext(file.filename)[1].lower()
            # Use a small part of the file buffer to detect MIME type
            mime_type = magic.Magic(mime=True).from_buffer(file.read(1024)).lower()
            file.seek(0)  # Reset the file pointer if needed
            # print("File extension:", extension, "MIME type:", mime_type)
            
            predicted_category = predict_category_from_buffer(extension, mime_type, mappings)
            # print("Predicted category for", file_name, "is", predicted_category)

            if predicted_category not in classified_files:
                classified_files[predicted_category] = []
            classified_files[predicted_category].append({
                "file": file_name,
            })

        return jsonify(classified_files)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

ANOMALIES_FILE_PATH ="../../Phase-2/Results/optimized_anomalies.fs"
ANOMALIES_FILE_KEY = "optimized_anomalies"
#ANOMALIES_FILE_PATH = os.path.join(os.path.dirname(__file__), "../../Phase-2/anomalies_llm_reasons.json")
# ANOMALIES_FILE_PATH = "F:\mahesh\BE Project\Phase-2\anomalies_llm_reasons.json"
def load_anomalies():
    """Loads the anomaly data from a JSON file."""
    if not os.path.exists(ANOMALIES_FILE_PATH):
        return None
    with open(ANOMALIES_FILE_PATH, 'r', encoding='utf-8') as file:
        return json.load(file)

# -----------------------------
# Directory Setup
# -----------------------------

ANOMALIES_DIR = "../../Phase-2/Anomalies"
RESULTS_DIR = "../../Phase-2/Results"
LOGS_DIR = "../../Phase-2/Logs"

os.makedirs(ANOMALIES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_DB_PATH = os.path.join(LOGS_DIR, "zodb_logs.fs")
ANOMALY_DB_PATH = os.path.join(ANOMALIES_DIR, "anomalies.fs")
RESULT_DB_PATH = os.path.join(RESULTS_DIR, "optimized_anomalies.fs")

# -----------------------------
# ZODB Utility Functions
# -----------------------------

def initialize_db(db_path, key="logs"):
    """Ensure ZODB database is properly initialized."""
    storage = ZODB.FileStorage.FileStorage(db_path)
    db = ZODB.DB(storage)
    connection = db.open()
    root = connection.root()

    if not hasattr(root, key):
        setattr(root, key, PersistentMapping())
        transaction.commit()

    connection.close()
    db.close()

def read_data(db_path, key="logs"):
    """Read data from ZODB based on key."""
    storage = ZODB.FileStorage.FileStorage(db_path)
    db = ZODB.DB(storage)
    connection = db.open()
    root = connection.root()
    
    data = list(getattr(root, key, {}).values()) if hasattr(root, key) else []
    connection.close()
    db.close()
    return data

def save_data(db_path, key, data):
    """Save data into ZODB under a given key."""
    storage = ZODB.FileStorage.FileStorage(db_path)
    db = ZODB.DB(storage)
    connection = db.open()
    root = connection.root()

    if not hasattr(root, key):
        setattr(root, key, PersistentMapping())

    getattr(root, key).clear()
    getattr(root, key).update(data)
    transaction.commit()

    connection.close()
    db.close()

# -----------------------------
# Anomaly Detection Pipeline
# -----------------------------

def run_anomaly_detection():
    """Runs the anomaly detection pipeline using ZODB."""
    initialize_db(LOG_DB_PATH, key="logs")
    logs = read_data(LOG_DB_PATH, key="logs")

    if not logs:
        return {"error": "No logs found in ZODB. Check your data import process."}

    features, labels = extract_features(logs)
    scores, predictions, _, _, updated_weights, anomaly_with_risk = detect_anomalies_with_scores(features)

    # Combine anomaly scores
    combined_predictions, aggregated_scores = combine_anomaly_scores(scores, updated_weights)

    # Save anomalies to ZODB
    save_anomalies_sequentially(logs, predictions, ANOMALY_DB_PATH)

    # Explain anomalies
    anomaly_reasons = explain_anomalies(ANOMALY_DB_PATH)
    if anomaly_reasons is None:
        return {"error": "`explain_anomalies` returned None."}

    save_data(RESULT_DB_PATH, "optimized_anomalies", anomaly_reasons)
    
    return {"message": "Pipeline executed successfully!", "anomalies_count": anomaly_reasons["anomaly_count"]}

# -----------------------------
# API Routes
# -----------------------------

@app.route('/run-pipeline', methods=['POST'])
def trigger_pipeline():
    """Endpoint to trigger anomaly detection pipeline."""
    result = run_anomaly_detection()
    return jsonify(result)

@app.route('/get-anomalies1', methods=['GET'])
def get_anomalies1():
    """Fetch the latest anomalies from ZODB."""
    anomalies = read_data(RESULT_DB_PATH, key="optimized_anomalies")
    
    if not anomalies:
        return jsonify({"error": "No anomaly data found. Run the pipeline first."})

    return jsonify(anomalies)
def persistent_to_dict(obj):
    """
    Recursively convert a persistent mapping (or any mapping/list) into a plain Python dict or list.
    """
    if isinstance(obj, collections.abc.Mapping):
        return {k: persistent_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [persistent_to_dict(item) for item in obj]
    else:
        return obj

def load_anomalies(fs_path, key):
    """Reads stored data from a ZODB .fs file and returns a detached copy, using read-only mode to avoid file locking."""
    storage = ZODB.FileStorage.FileStorage(fs_path, read_only=True)
    db = ZODB.DB(storage)
    connection = db.open()
    root = connection.root()

    data = None
    if hasattr(root, key):
        data = getattr(root, key)
        # Detach the persistent data by converting it to plain Python structures
        data = persistent_to_dict(data)
    connection.close()
    db.close()
    return data

    
#Return All anamolies
@app.route('/get-anomalies', methods=['GET'])
def get_anomalies():
    """
    Fetches anomalies with pagination and filtering.
    """

    try:
        anomalies_data = load_anomalies(ANOMALIES_FILE_PATH, ANOMALIES_FILE_KEY)
        if anomalies_data is None:
            return jsonify({"error": "Anomalies file not found"}), 404

        anomalies_list = anomalies_data.get("logs", [])
        total_anomalies = anomalies_data.get("anomaly_count", 0)

        # Extract query parameters
        page = int(request.args.get('page', 1))
        per_page = 50
        operation_filter = request.args.get('operation', '').lower()
        category_filter = request.args.get('category', '').lower()
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')

        # Apply filters
        filtered_anomalies = anomalies_list

        if operation_filter:
            filtered_anomalies = [a for a in filtered_anomalies if a["operation"].lower() == operation_filter]

        if category_filter:
            filtered_anomalies = [a for a in filtered_anomalies if a["category"].lower() == category_filter]

        if start_time and end_time:
            try:
                start_dt = datetime.fromisoformat(start_time)
                end_dt = datetime.fromisoformat(end_time)
                filtered_anomalies = [
                    a for a in filtered_anomalies if start_dt <= datetime.fromisoformat(a["timestamp"]) <= end_dt
                ]
            except ValueError:
                return jsonify({"error": "Invalid timestamp format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400

        # Paginate results
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_anomalies = filtered_anomalies[start_idx:end_idx]

        return jsonify({
            "total": total_anomalies,
            "page": page,
            "per_page": per_page,
            "anomalies": paginated_anomalies
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#Return all sorted anamolies in ascending form
@app.route('/get-anomalies-sorted', methods=['GET'])
def get_anomalies_sorted():
    """
    Fetches anomalies sorted in decreasing order of time (newest first) with pagination and filtering.
    """
    try:
        anomalies_data = load_anomalies(ANOMALIES_FILE_PATH, ANOMALIES_FILE_KEY)
        if anomalies_data is None:
            return jsonify({"error": "Anomalies file not found"}), 404

        anomalies_list = anomalies_data.get("logs", [])
        
        # Extract filtering query parameters
        operation_filter = request.args.get('operation', '').lower()
        category_filter = request.args.get('category', '').lower()
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')

        # Apply filters if provided
        filtered_anomalies = anomalies_list

        if operation_filter:
            filtered_anomalies = [a for a in filtered_anomalies if a["operation"].lower() == operation_filter]

        if category_filter:
            filtered_anomalies = [a for a in filtered_anomalies if a["category"].lower() == category_filter]

        if start_time and end_time:
            try:
                start_dt = datetime.fromisoformat(start_time)
                end_dt = datetime.fromisoformat(end_time)
                filtered_anomalies = [
                    a for a in filtered_anomalies 
                    if start_dt <= datetime.fromisoformat(a["timestamp"]) <= end_dt
                ]
            except ValueError:
                return jsonify({"error": "Invalid timestamp format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400

        # Determine sort order and sort the filtered list by timestamp
        sort_order = request.args.get('sort', 'desc')  # Default: descending
        reverse_sort = sort_order == 'desc'
        filtered_anomalies.sort(key=lambda x: datetime.fromisoformat(x["timestamp"]), reverse=reverse_sort)

        # Pagination logic
        page = int(request.args.get('page', 1))
        per_page = 50
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_anomalies = filtered_anomalies[start_idx:end_idx]

        return jsonify({
            "total": len(filtered_anomalies),
            "page": page,
            "per_page": per_page,
            "anomalies": paginated_anomalies
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#Return all unique categories in the db
@app.route('/get-unique-categories', methods=['GET'])
def get_unique_categories():
    """
    Returns a list of unique anomaly categories.
    """
    try:
        anomalies_data = load_anomalies(ANOMALIES_FILE_PATH, ANOMALIES_FILE_KEY)
        if anomalies_data is None:
            return jsonify({"error": "Anomalies file not found"}), 404

        # Extract unique categories
        unique_categories = list({anomaly["category"] for anomaly in anomalies_data.get("logs", [])})

        return jsonify({"unique_categories": unique_categories})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
#Return anamolies betweeen start and end time
@app.route('/get-anomalies-by-time', methods=['GET'])
def get_anomalies_by_time():
    """
    Returns anomalies that occurred within a specific time period.
    """
    try:
        anomalies_data = load_anomalies(ANOMALIES_FILE_PATH, ANOMALIES_FILE_KEY)
        if anomalies_data is None:
            return jsonify({"error": "Anomalies file not found"}), 404

        anomalies_list = anomalies_data.get("logs", [])

        # Extract query parameters
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')

        if not (start_time and end_time):
            return jsonify({"error": "Both start_time and end_time must be provided"}), 400

        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
        except ValueError:
            return jsonify({"error": "Invalid timestamp format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400

        # Filter anomalies based on the given time range
        filtered_anomalies = [
            anomaly for anomaly in anomalies_list
            if start_dt <= datetime.fromisoformat(anomaly["timestamp"]) <= end_dt
        ]

        return jsonify({"total": len(filtered_anomalies), "anomalies": filtered_anomalies})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#Return count of anamoly of each operation
@app.route('/get-anomaly-counts', methods=['GET'])
def get_anomaly_counts():
    """
    Returns a count of anomalies grouped by operation type, along with the total anomaly count.
    """
    try:
        anomalies_data = load_anomalies(ANOMALIES_FILE_PATH, ANOMALIES_FILE_KEY)
        if anomalies_data is None:
            return jsonify({"error": "Anomalies file not found"}), 404

        operation_counts = defaultdict(int)
        total_anomalies = anomalies_data.get("anomaly_count", 0)

        # Count occurrences of each operation type
        for anomaly in anomalies_data.get("logs", []):
            operation = anomaly["operation"]
            operation_counts[operation] += 1

        return jsonify({"total_anomalies": total_anomalies, "operation_counts": dict(operation_counts)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-anomalies-over-time', methods=['GET'])
def get_anomalies_over_time():
    """
    Returns the number of anomalies detected per day.
    """
    try:
        anomalies_data = load_anomalies(ANOMALIES_FILE_PATH, ANOMALIES_FILE_KEY)
        if anomalies_data is None:
            return jsonify({"error": "Anomalies file not found"}), 404

        date_counts = defaultdict(int)

        for anomaly in anomalies_data.get("logs", []):
            timestamp = anomaly["timestamp"]
            date_str = datetime.fromisoformat(timestamp).date().isoformat()  # Extracting date part
            date_counts[date_str] += 1

        return jsonify({"anomalies_over_time": dict(date_counts)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#Return anamoliey count filter by file category
@app.route('/get-category-anomaly-count', methods=['GET'])
def get_category_anomaly_count():
    """
    Returns anomaly count grouped by category.
    """
    try:
        anomalies_data = load_anomalies(ANOMALIES_FILE_PATH, ANOMALIES_FILE_KEY)
        if anomalies_data is None:
            return jsonify({"error": "Anomalies file not found"}), 404

        category_counts = defaultdict(int)
        for anomaly in anomalies_data.get("logs", []):
            category = anomaly.get("category", "unknown")
            category_counts[category] += 1

        return jsonify({"category_anomaly_count": dict(category_counts)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def parse_time_range(time_range):
    """Converts time range (e.g., '30m', '2h', '1d') to a datetime object."""
    now = datetime.utcnow()
    unit = time_range[-1]
    value = int(time_range[:-1])

    if unit == "m":  # Minutes
        return now - timedelta(minutes=value)
    elif unit == "h":  # Hours
        return now - timedelta(hours=value)
    elif unit == "d":  # Days
        return now - timedelta(days=value)
    return now

@app.route('/get-recent-anomalies', methods=['GET'])
def get_recent_anomalies():
    """
    Fetches anomalies that occurred within a specified recent time range (e.g., last 30 minutes, 2 hours).
    """
    try:
        anomalies_data = load_anomalies()
        if anomalies_data is None:
            return jsonify({"error": "Anomalies file not found"}), 404

        anomalies_list = anomalies_data.get("logs", [])

        # Extract query parameter
        time_range = request.args.get("time_range", "30m")  # Default to 30 minutes
        now = datetime.utcnow()

        # Parse the time range
        unit = time_range[-1]
        value = int(time_range[:-1])

        if unit == "m":
            start_time = now - timedelta(minutes=value)
        elif unit == "h":
            start_time = now - timedelta(hours=value)
        elif unit == "d":
            start_time = now - timedelta(days=value)
        else:
            return jsonify({"error": "Invalid time_range format. Use 'Xm', 'Xh', or 'Xd'"}), 400

        # Filter anomalies within the time range
        filtered_anomalies = [
            anomaly for anomaly in anomalies_list
            if datetime.fromisoformat(anomaly["timestamp"]) >= start_time
        ]

        return jsonify({"total": len(filtered_anomalies), "anomalies": filtered_anomalies})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get-anomaly-trends', methods=['GET'])
def get_anomaly_trends():
    """
    Returns the number of anomalies grouped by a specified time interval (daily, weekly, or monthly).
    """
    try:
        anomalies_data = load_anomalies(ANOMALIES_FILE_PATH, ANOMALIES_FILE_KEY)
        if anomalies_data is None:
            return jsonify({"error": "Anomalies file not found"}), 404

        anomalies_list = anomalies_data.get("logs", [])

        # Extract query parameter
        interval = request.args.get("interval", "weekly")  # Default to weekly
        trends = defaultdict(int)

        for anomaly in anomalies_list:
            timestamp = datetime.fromisoformat(anomaly["timestamp"])

            if interval == "daily":
                key = timestamp.strftime("%Y-%m-%d")
            elif interval == "weekly":
                key = f"Week {timestamp.strftime('%U')} of {timestamp.year}"
            elif interval == "monthly":
                key = timestamp.strftime("%Y-%m")
            else:
                return jsonify({"error": "Invalid interval. Use 'daily', 'weekly', or 'monthly'"}), 400

            trends[key] += 1

        return jsonify({"trends": dict(trends)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

"""
    Returns anomaly counts grouped by operation and category for a heat map.
"""
@app.route('/get-operation-category-heatmap', methods=['GET'])
def get_operation_category_heatmap():
   
    try:
        anomalies_data = load_anomalies(ANOMALIES_FILE_PATH, ANOMALIES_FILE_KEY)
        if anomalies_data is None:
            return jsonify({"error": "Anomalies file not found"}), 404

        heatmap_dict = defaultdict(lambda: defaultdict(int))
        for anomaly in anomalies_data.get("logs", []):
            operation = anomaly.get("operation", "unknown")
            category = anomaly.get("category", "unknown")
            heatmap_dict[operation][category] += 1

        # Flatten the nested dict into a list of objects.
        heatmap_data = []
        for operation, categories in heatmap_dict.items():
            for category, count in categories.items():
                heatmap_data.append({
                    "operation": operation,
                    "category": category,
                    "count": count
                })

        return jsonify({"heatmap": heatmap_data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-anomaly-trend', methods=['GET'])
def get_anomaly_trend():
    """
    Returns time series anomaly data with a 7-day moving average.
    """
    try:
        anomalies_data = load_anomalies(ANOMALIES_FILE_PATH, ANOMALIES_FILE_KEY)
        if anomalies_data is None:
            return jsonify({"error": "Anomalies file not found"}), 404

        # Group anomalies by day (YYYY-MM-DD)
        date_counts = defaultdict(int)
        for anomaly in anomalies_data.get("logs", []):
            try:
                ts = datetime.fromisoformat(anomaly["timestamp"])
                date_str = ts.date().isoformat()
                date_counts[date_str] += 1
            except Exception:
                continue

        # Sort dates and compute the moving average (7-day window)
        sorted_dates = sorted(date_counts.keys())
        trend_data = []
        window_size = 7
        counts = [date_counts[date] for date in sorted_dates]

        for i, date in enumerate(sorted_dates):
            # Get the window: current day and previous (window_size - 1) days
            window = counts[max(0, i - window_size + 1): i + 1]
            moving_average = sum(window) / len(window)
            trend_data.append({
                "date": date,
                "count": date_counts[date],
                "movingAverage": moving_average
            })

        return jsonify({"trend": trend_data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

last_sent_time = None
def event_stream():
    """Streams new anomalies in real time using SSE."""
    global last_sent_time

    while True:
        time.sleep(5)  # Check every 5 seconds
        try:
            with open("anomalies_sequential.json", "r") as file:
                anomalies = json.load(file)  # Load latest anomalies
            # print("Anomalies: ", anomalies)
        except (FileNotFoundError, json.JSONDecodeError):
            anomalies = []
        
        if not anomalies:
            continue

        valid_anomalies = [a for a in anomalies if "timestamp" in a]

        if not valid_anomalies:
            continue 

        last_sent_time = last_sent_time or valid_anomalies[-1]["timestamp"]  # Initialize if None

        new_anomalies = [a for a in valid_anomalies if a["timestamp"] > last_sent_time]

        if new_anomalies:
            last_sent_time = new_anomalies[-1]["timestamp"]  # Update last sent time
            yield f"data: {json.dumps(new_anomalies)}\n\n"

def trigger_anomaly():
    anomaly = {
        "file": "/home/user/sensitive.doc",
        "operation": "rename",
        "timestamp": "2025-03-03T15:01:12"
    }

    try:
        with open("anomalies_sequential.json", "r") as file:
            anomalies = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        anomalies = []

    # Add new anomaly and save
    anomalies.append(anomaly)
    with open("anomalies_sequential.json", "w") as file:
        json.dump(anomalies, file, indent=4)

# Call this function when an anomaly is detected

@app.route("/events")
def sse():
    """SSE endpoint for real-time anomaly notifications."""
    trigger_anomaly()   #Testing notification
    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
