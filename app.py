import os
import time
import threading
from flask import Flask, render_template, jsonify
from agent import invoke_incident_commander
import mock_ingestion

app = Flask(__name__)
LAST_INGESTION_TIME = 0

# Security Caching to prevent API abuse/cost spikes
LAST_API_STATE = None
LAST_API_UPDATE = 0
API_CACHE_EXPIRY = 20 # seconds

@app.route("/")
def index():
    # Serves the main Dashboard UI
    return render_template("index.html")

@app.route("/api/stadium_state")
def stadium_state():
    global LAST_INGESTION_TIME, LAST_API_STATE, LAST_API_UPDATE
    
    current_time = time.time()
    
    # 1. Protection cache: If heavily spammed, return cached state to block rapid Cloud API charges
    if LAST_API_STATE and (current_time - LAST_API_UPDATE) < API_CACHE_EXPIRY:
        return jsonify(LAST_API_STATE)
    
    # 2. Only populate data on-demand gracefully (max once every 3 minutes per container)
    if current_time - LAST_INGESTION_TIME > 180:
        LAST_INGESTION_TIME = current_time
        threading.Thread(target=mock_ingestion.run_once, daemon=True).start()

    # 3. Polls BigQuery for context and Gemini for Agent logic
    state = invoke_incident_commander()
    if not state:
        return jsonify({"error": "Failed to invoke Agent logic."}), 500
    
    # Cache valid output
    LAST_API_STATE = state
    LAST_API_UPDATE = current_time
    
    return jsonify(state)

if __name__ == "__main__":
    # Ensure this runs on Cloud Run's port (default 8080)
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host="0.0.0.0", port=port)
