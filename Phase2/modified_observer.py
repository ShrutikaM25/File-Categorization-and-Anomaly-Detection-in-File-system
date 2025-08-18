import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import json
import datetime
import pickle
import magic
import psutil  # For automatic drive detection

# ---- Utility Functions ---- 
# Function to get a writable directory for logs
def get_log_directory():
    log_dir = os.path.join(os.path.expanduser("~"), "Documents", "DriveLogs")
    os.makedirs(log_dir, exist_ok=True)  # Create folder if it doesn't exist
    return log_dir

# Function to get log file path for a given drive
def get_log_file_for_drive(drive):
    log_dir = get_log_directory()  # Use a safe directory
    drive_letter = drive.replace("\\", "").replace(":", "")
    return os.path.join(log_dir, f"{drive_letter}_drive_operations_log.json")

# Get all available drives dynamically
def get_available_drives():
    return [drive.device for drive in psutil.disk_partitions() if 'cdrom' not in drive.opts]

# ---- CATEGORIZER CODE START ---- #
class Categorizer:
    def __init__(self):
        self.mappings = self.load_hash_mappings()

    def load_hash_mappings(self):
        try:
            with open('hash_mappings.pkl', 'rb') as file:
                mappings = pickle.load(file)
            return mappings
        except FileNotFoundError:
            print("Error: hash_mappings.pkl file not found.")
            raise
        except Exception as e:
            print(f"Error loading hash_mappings.pkl: {e}")
            raise

    def predict_category(self, extension, mime_type=None):
        mappings = self.mappings
        ext_to_idx = mappings['ext_to_idx']
        mime_to_idx = mappings['mime_to_idx']
        idx_to_category = mappings['idx_to_category']
        prediction_map = mappings['prediction_map']

        ext_encoded = ext_to_idx.get(extension, -1)
        if ext_encoded == -1:
            return "Unknown Category"

        mime_encoded = mime_to_idx.get(mime_type, -1) if mime_type else None

        if mime_encoded is not None and mime_encoded != -1:
            category_encoded = prediction_map.get((ext_encoded, mime_encoded), -1)
            if category_encoded != -1:
                return idx_to_category.get(category_encoded, "Unknown Category")

        for (ext, _), category_encoded in prediction_map.items():
            if ext == ext_encoded:
                return idx_to_category.get(category_encoded, "Unknown Category")

        return "Unknown Category"

    def categorize(self, file_path):
        extension = os.path.splitext(file_path)[1].lower()
        mime_type = magic.Magic(mime=True).from_file(file_path).lower()

        if mime_type == 'inode/x-empty':
            return "Empty File"

        return self.predict_category(extension, mime_type)

# ---- CATEGORIZER CODE END ---- #

# ---- DIRECTORY MONITORING CODE ---- #
class FileHandler(FileSystemEventHandler):
    def __init__(self, categorizer, monitored_drives):
        super().__init__()
        self.categorizer = categorizer
        self.category_cache = {}  # Cache for file categories
        self.file_size_cache = {}  # Cache for file sizes
        self.log_files = {drive: get_log_file_for_drive(drive) for drive in monitored_drives}

    def process_event(self, event_type, file_path, bytes_modified=None):
        # List of ignored directories (expand as needed)
        ignored_paths = [
            os.path.expanduser("~") + "\\AppData",  # Ignore AppData
            os.path.expanduser("~") + "\\Temp",     # Ignore Temp
            "C:\\Windows",  # Ignore Windows system files
            "C:\\Program Files",  # Ignore Program Files (includes MongoDB)
            "C:\\ProgramData",  # Common for logs/configs
            "C:\\Users\\Public"  # Common for temp files
        ]

        # List of ignored file extensions and patterns
        ignored_extensions = {".tmp", ".temp", ".interim", ".lnk", ".vscdb-journal"}
        ignored_keywords = ["diagnostic.data", "metrics", "log", "cache"]  # Ignore database logs

        # Ignore files in specific directories
        if any(file_path.startswith(ignored) for ignored in ignored_paths):
            print(f"Skipping log for system/Program Files: {file_path}")
            return

        # Ignore specific extensions
        if any(file_path.lower().endswith(ext) for ext in ignored_extensions):
            print(f"Skipping log for ignored file type: {file_path}")
            return

        # Ignore files containing certain keywords
        if any(keyword in file_path.lower() for keyword in ignored_keywords):
            print(f"Skipping log for database/log-related file: {file_path}")
            return

        drive = os.path.splitdrive(file_path)[0] + "\\"  # Ensure drive path format
        log_file = self.log_files.get(drive)

        if not log_file or file_path == log_file:
            print(f"Skipping logging for: {file_path}")  # Avoid infinite logging loop
            return

        log_entry = {
            "file": file_path,
            "operation": event_type,
            "timestamp": str(datetime.datetime.now()),
            "category": self.category_cache.get(file_path, "Unknown")
        }

        if event_type in ["insertion", "update"]:
            if os.path.isfile(file_path):
                file_category = self.categorizer.categorize(file_path)
                self.category_cache[file_path] = file_category
                log_entry["category"] = file_category

                if event_type == "update" and bytes_modified is not None:
                    log_entry["bytes_modified"] = bytes_modified

                self.file_size_cache[file_path] = os.path.getsize(file_path)

        elif event_type == "deletion":
            file_category = self.category_cache.get(file_path, "Unknown")
            log_entry["category"] = file_category

            if file_path in self.category_cache:
                del self.category_cache[file_path]
            if file_path in self.file_size_cache:
                del self.file_size_cache[file_path]

        elif event_type == "rename":
            log_entry["new_name"] = file_path
            log_entry["category"] = self.category_cache.get(file_path, "Unknown")

        # Append log entry to the drive-specific log file
        with open(log_file, "a") as log:
            log.write(json.dumps(log_entry) + "\n")

        print(f"Logged: {log_entry} to {log_file}")



    def on_created(self, event):
        if not event.is_directory:
            try:
                # Attempt to get the file size
                file_size = os.path.getsize(event.src_path)
                self.file_size_cache[event.src_path] = file_size
                self.process_event("insertion", event.src_path)
            except FileNotFoundError:
                print(f"File {event.src_path} was deleted before logging.")
            except PermissionError:
                print(f"Skipping {event.src_path} due to permission restrictions.")


    def on_modified(self, event):
        if not event.is_directory:
            try:
                time.sleep(0.0001)  # Allow time for file write completion

                current_size = os.path.getsize(event.src_path)
                previous_size = self.file_size_cache.get(event.src_path)

                if previous_size is None:
                    previous_size = current_size
                    self.file_size_cache[event.src_path] = previous_size

                bytes_modified = current_size - previous_size

                print(f"CURR: {current_size} / Previous Size: {previous_size} / Bytes Modified: {bytes_modified}")

                if bytes_modified == 0:
                    print(f"Skipping logging for {event.src_path}: 0 bytes modified (possible metadata change).")
                    return

                self.process_event("update", event.src_path, bytes_modified=bytes_modified)
                self.file_size_cache[event.src_path] = current_size  # Update cache

            except FileNotFoundError:
                print(f"File not found: {event.src_path}, likely deleted.")

            except PermissionError:
                print(f"Skipping {event.src_path}, permission denied.")

    def on_deleted(self, event):
        if not event.is_directory:
            self.process_event("deletion", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            print(f"File moved from {event.src_path} to {event.dest_path}")
            self.process_event("rename", event.dest_path)

# ---- START MONITORING ---- #
def monitor_drives(categorizer):
    drives = get_available_drives()
    print(f"Monitoring Drives: {drives}")

    observer = Observer()
    event_handler = FileHandler(categorizer, drives)

    for drive in drives:
        observer.schedule(event_handler, drive, recursive=True)

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    categorizer = Categorizer()
    monitor_drives(categorizer)
