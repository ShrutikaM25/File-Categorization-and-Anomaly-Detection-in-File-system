import json
from anomaly import (
    detect_anomalies_with_scores,
    combine_anomaly_scores,
    extract_features,
    save_anomalies_by_operation,
    save_anomalies_sequentially, 
    explain_anomalies
)
import ZODB, ZODB.FileStorage
import transaction
from persistent.mapping import PersistentMapping
import os

# -----------------------------
# Data Preprocessing
# -----------------------------

def json_to_fs(json_file, fs_path):
    """Transfers all data from a JSON file to a ZODB .fs file."""
    import json  # Temporarily using json just for this function
    
    if not os.path.exists(json_file):
        print(f"File {json_file} not found!")
        return
    
    with open(json_file, "r") as f:
        log_data = json.load(f)
    
    storage = ZODB.FileStorage.FileStorage(fs_path)
    db = ZODB.DB(storage)
    connection = db.open()
    root = connection.root()
    
    if not hasattr(root, 'logs'):
        root.logs = PersistentMapping()
    
    root.logs.update({i: log for i, log in enumerate(log_data)})
    transaction.commit()
    
    connection.close()
    db.close()
    print(f"Transferred {len(log_data)} log entries from {json_file} to {fs_path}.")


def initialize_db(db_path):
    """Initializes ZODB and ensures transaction safety."""
    storage = ZODB.FileStorage.FileStorage(db_path)
    db = ZODB.DB(storage)
    connection = db.open()
    root = connection.root()
    
    if not hasattr(root, 'logs'):
        root.logs = PersistentMapping()
        transaction.commit()
    
    if transaction.isDoomed():
        transaction.abort()
    
    connection.close()
    db.close()

def read_data(db_path, key="logs"):
    """Generalized function to read data from ZODB based on the key provided."""
    storage = ZODB.FileStorage.FileStorage(db_path)
    db = ZODB.DB(storage)
    connection = db.open()
    root = connection.root()
    
    data = list(getattr(root, key, {}).values()) if hasattr(root, key) else []
    connection.close()
    db.close()
    return data

if __name__ == "__main__":

# -----------------------------
# Directory Setup
# -----------------------------

    ANOMALIES_DIR = "Anomalies"
    RESULTS_DIR = "Results"
    LOGS_DIR = "Logs"

    os.makedirs(ANOMALIES_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    json_file = "synthetic_log_file.json"
    db_path = os.path.join(LOGS_DIR, "zodb_logs.fs")
    json_to_fs(json_file, db_path)

    initialize_db(db_path)
    logs = read_data(db_path, key="logs")

    if not logs:
        print("Warning: No logs found in ZODB. Check your data transfer process.")
    else:
        print(f"Total logs in ZODB: {len(logs)}")

    if logs:
        features, labels = extract_features(logs)
        scores, predictions, anomaly_counts, final_anomalies, updated_weights, anomaly_with_risk = detect_anomalies_with_scores(features)
        
        combined_predictions, aggregated_scores = combine_anomaly_scores(scores, updated_weights)
        
        save_anomalies_sequentially(logs, predictions, os.path.join(ANOMALIES_DIR, "anomalies.fs"))
        print("Anomalies saved successfully!")

        db_path = db_path = os.path.join(ANOMALIES_DIR, "anomalies.fs")
        anomaly_reasons = explain_anomalies(db_path)

        if anomaly_reasons is None:
            print("Error: `explain_anomalies` returned None. Skipping saving anomalies.")
            anomaly_reasons = []

        optimized_db_path = os.path.join(RESULTS_DIR, "optimized_anomalies.fs")
        storage = ZODB.FileStorage.FileStorage(optimized_db_path)
        db = ZODB.DB(storage)
        connection = db.open()
        root = connection.root()

        if not hasattr(root, 'optimized_anomalies'):
            root.optimized_anomalies = PersistentMapping()

        root.optimized_anomalies["anomaly_count"] = anomaly_reasons["anomaly_count"]
        root.optimized_anomalies["logs"] = anomaly_reasons["logs"]
        transaction.commit()

        if transaction.isDoomed():
            transaction.abort()

        connection.close()
        db.close()
        print("Explainable anomaly detection completed and saved.")
    else:
        print("Skipping anomaly detection because no logs are available.")

# -----------------------------