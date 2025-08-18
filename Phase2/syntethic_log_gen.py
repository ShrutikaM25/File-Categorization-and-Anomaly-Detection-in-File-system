import json
import random
import string
from datetime import datetime, timedelta

# Define possible categories, operations, and other fields
categories = {
    "Email related": [".eml", ".msg", ".pst"],
    "Document/Letter": [".docx", ".pdf", ".txt"],
    "Program executable": [".exe", ".sh", ".bat"],
    "Media File": [".mp4", ".mp3", ".jpg", ".png"],
    "System Log": [".log", ".cfg"],
    "Backup": [".bak", ".zip", ".tar"],
    "Configuration File": [".ini", ".conf", ".xml"],
    "Empty File": [".tmp", ".null"],
    "Unknown": [ ".unknown"]
}

operations = ["insertion", "update", "deletion", "rename"]
base_timestamp = datetime(2024, 10, 15, 10, 0, 0)

def generate_ip():
    return "{}.{}.{}.{}".format(random.randint(1, 255), random.randint(0, 255), random.randint(0, 255), random.randint(1, 255))

def generate_mac():
    return ":".join("{:02x}".format(random.randint(0, 255)) for _ in range(6))

def generate_log_entries(num_entries):
    log_entries = []
    for i in range(num_entries):
        category = random.choice(list(categories.keys()))
        extension = random.choice(categories[category])
        operation = random.choice(operations)
        ip_address = generate_ip()
        mac_address = generate_mac()
        
        random_time = base_timestamp + timedelta(
            hours=random.randint(0, 48),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )

        if operation == "update":
            bytes_modified = random.randint(-5000, 5000)
        else:
            bytes_modified = 0

        log_entry = {
            "file": f"E:/file_{i}{extension}",
            "operation": operation,
            "timestamp": random_time.isoformat(),
            "category": category,
            "ip_address": ip_address,
            "mac_address": mac_address
        }
        
        if operation == "update":
            log_entry["bytes_modified"] = bytes_modified
        
        if operation == "rename":
            log_entry["new_name"] = f"E:/file_renamed_{i}{extension}"

        log_entries.append(log_entry)
    
    return log_entries

log_entries = generate_log_entries(10000)
log_file_path = 'synthetic_log_file.json'

with open(log_file_path, 'w') as log_file:
    json.dump(log_entries, log_file, indent=4)

print(f"Generated {len(log_entries)} log entries with multiple file extensions and saved to {log_file_path}")
