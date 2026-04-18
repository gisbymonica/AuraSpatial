import os
import time
import threading
from flask import Flask, render_template, jsonify
from agent import invoke_incident_commander
import mock_ingestion

app = Flask(__name__)
LAST_INGESTION_TIME = 0

@app.route("/")
def index():
    # Serves the main Dashboard UI
    return render_template("index.html")

@app.route("/api/stadium_state")
def stadium_state():
    global LAST_INGESTION_TIME
    
    # Only populate data on-demand gracefully (max once every 3 minutes per container)
    if time.time() - LAST_INGESTION_TIME > 180:
        LAST_INGESTION_TIME = time.time()
        threading.Thread(target=mock_ingestion.run_once, daemon=True).start()

    # Polls BigQuery for context and Gemini for Agent logic
    state = invoke_incident_commander()
    if not state:
        return jsonify({"error": "Failed to invoke Agent logic."}), 500
    
    return jsonify(state)

if __name__ == "__main__":
    # Ensure this runs on Cloud Run's port (default 8080)
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host="0.0.0.0", port=port)
