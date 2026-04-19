import os
import json
import time
import logging
from google.cloud import storage

BUCKET_NAME = "aurageo_data"

def upload_incident_log(incident_data: dict) -> bool:
    """
    Uploads the incident reasoning to Google Cloud Storage (Bucket: gs://aurageo_data).
    This functions as a persistent archive of the AI Agent's decisions.
    """
    try:
        # Fallback to default credentials or no-op if no credentials in local dev
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        
        timestamp = int(time.time())
        blob_name = f"incident_logs/log_{timestamp}.json"
        
        blob = bucket.blob(blob_name)
        blob.upload_from_string(
            json.dumps(incident_data, indent=2),
            content_type="application/json"
        )
        logging.info(f"Successfully uploaded incident log to gs://{BUCKET_NAME}/{blob_name}")
        return True
    except Exception as e:
        logging.error(f"Failed to upload to Google Cloud Storage: {e}")
        return False

# Quick test if run directly
if __name__ == "__main__":  # pragma: no cover
    upload_incident_log({"test": "data", "status": "ok"})
