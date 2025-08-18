# 🚀 File Categorization & Anomaly Detection - README

## 📌 Project Overview
This project automates **file categorization** and **anomaly detection** to enhance **system security** and **organization**. It classifies files based on extensions and MIME types, while detecting anomalies in file operations using an **ensemble of machine learning models**.

🔹 **Phase 1:** Categorizes files by extensions & MIME types.  
🔹 **Phase 2:** Detects anomalies with an **ensemble of ML models** and provides explainability using **Ollama's Llama3 model**.

---

## ⚙️ System Architecture

### 🗂 **Phase 1: File Categorization**
1. **Data Collection:** Scraped file information from sources like fileinfo.com, resulting in a dataset of **~20K file extensions**, **400 categories**, and **3,000 MIME types**.
2. **Data Processing:** Cleaned and preprocessed data to ensure high accuracy.
3. **Initial Model Training Approach:** Used **Decision Tree & Random Forest** models trained on labeled data.  
4. **Current Optimization:** Now using a **hash data structure (hash map) instead of model training** for improved efficiency.
5. **MIME Type Verification:** Prevents misclassification of altered file extensions using the `magic` library.
6. **Classification Approaches:**
   - 📂 **Directory-based & file-based classification.**
   - 🚀 **Dynamic dataset update** when new file types are detected.

---

### 🚨 **Phase 2: Anomaly Detection**
1. **Logging System:** Tracks file operations such as `insert`, `update`, `rename`, `delete`.
2. **Storage:** Logs are stored in **ZODB** (.fs file format).
3. **Anomaly Detection Models:**
   - ✅ **Autoencoder**
   - ✅ **Isolation Forest**
   - ✅ **Local Outlier Factor**
   - ✅ **One-Class SVM**
   - ✅ **River Model**
4. **Aggregation Approach:** Uses **ensemble learning** to combine model outputs, improving detection accuracy.
5. **Explainability & LLM Integration:**
   - 🧠 Uses **Ollama's Llama3 model** for reasoning.
   - 🔍 **DBSCAN clustering** groups similar anomalies for efficient processing before passing to LLM.
6. **Dashboard & Alerts:** Displays anomalies and **notifies users based on severity**.

---

## 🛠️ Installation & Setup

### 📌 Prerequisites
- ✅ Python 3.8+
- ✅ Flask
- ✅ ZODB
- ✅ Ollama (Llama3 model)
- ✅ Node.js & npm (for frontend)
- ✅ Conda (for backend virtual environment)
- ✅ Required Python libraries (see `requirements.txt`)

### 📥 Installation Steps

#### 🎨 **Frontend Setup**
```bash
# Navigate to the frontend directory
cd Dashboard/dashboard

# Install dependencies
npm i
```

#### 🖥 **Backend Setup**
```bash
# Navigate to the backend directory
cd Dashboard/Backend

# Create and activate a Conda environment
conda create -n venv_name python=3.12.2
conda activate venv_name

# Install required dependencies
pip install -r requirements.txt

# Start the backend server
python routes.py
```

---

## 🎯 Usage Guide

### 🔍 **Running the File Categorization**
```python
from categorizer import categorize_file
category = categorize_file("example.pdf")
print(category)
```

### 🛑 **Running the Anomaly Detection System**
```bash
python Phase2/synthetic_anomaly_run.py  
# or  
python Phase2/driver_anomaly_run.py  
```

---

## 🏛 Database Details
📂 Logs are stored in `Phase2\Logs\zodb_logs.fs` using **ZODB**.  
📌 Anomalies are **indexed based on severity and category**.

---

## 📡 API Endpoints

| Method  | Endpoint           | Description                             |
|---------|--------------------|------------------------------------------|
| 🔵 POST | `/classify`         | Classifies a given file.                |
| 🟢 GET  | `/logs`             | Retrieves logged file operations.       |
| 🔴 POST | `/detect_anomalies` | Runs anomaly detection on logs.         |

---

## 📊 Dashboard & Alerts
🎯 **User-friendly dashboard** to visualize file categories & anomalies.  
⚠️ **Real-time notifications** based on anomaly severity.

---

## 🚀 Contributing & Future Enhancements
📌 **Cloud-based storage integration.**  
📌 **Enhanced LLM explanations** for more file types.  
📌 **Expand anomaly detection capabilities** for better edge case handling.

---

## 📩 Contact & Support
For queries, contact **Shrutika Malve** at **@ShrutikaM25**.  

