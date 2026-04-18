import os
from flask import Flask, render_template, jsonify
from agent import invoke_incident_commander

app = Flask(__name__)

@app.route("/")
def index():
    # Serves the main Dashboard UI
    return render_template("index.html")

@app.route("/api/stadium_state")
def stadium_state():
    # Polls BigQuery for context and Gemini for Agent logic
    state = invoke_incident_commander()
    if not state:
        return jsonify({"error": "Failed to invoke Agent logic."}), 500
    
    return jsonify(state)

if __name__ == "__main__":
    # Ensure this runs on Cloud Run's port (default 8080)
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host="0.0.0.0", port=port)
