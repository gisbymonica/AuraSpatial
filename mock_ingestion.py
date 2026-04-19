import time
import uuid
import random
import json
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError
from google.oauth2 import service_account
import google.auth
import google.auth.exceptions
import logging


# Configuration
PROJECT_ID = "aurageo"
DATASET_ID = "stadium_ops"
TABLE_ID = "fan_trajectories_raw"
UPDATE_INTERVAL = 2  # seconds between each move

# M. Chinnaswamy Stadium Coordinates
CENTER_LAT = 12.978816
CENTER_LON = 77.599719

# Defining some arbitrary gates around the stadium (loaded from gates.json)
with open("gates.json", "r") as f:
    GATES = json.load(f)

NUM_FANS = 50
STEP_SIZE = 0.00004 # Approx 4 meters

class Fan:
    def __init__(self, fan_id: str):
        self.fan_id = fan_id
        # Start randomly near the center
        self.lat = CENTER_LAT + random.uniform(-0.0005, 0.0005)
        self.lon = CENTER_LON + random.uniform(-0.0005, 0.0005)
        # Assign a random target gate
        self.target_gate = random.choice(list(GATES.keys()))
        
    def move(self) -> None:
        target_lat = GATES[self.target_gate]["lat"]
        target_lon = GATES[self.target_gate]["lon"]
        
        # Move slightly towards the target gate with some noise
        lat_diff = target_lat - self.lat
        lon_diff = target_lon - self.lon
        
        # Normalize distance and step
        dist = (lat_diff**2 + lon_diff**2)**0.5
        if dist > 0.00001:  # Only move if not entirely at the target
            self.lat += (lat_diff / dist) * STEP_SIZE + random.uniform(-0.00001, 0.00001)
            self.lon += (lon_diff / dist) * STEP_SIZE + random.uniform(-0.00001, 0.00001)
            
    def get_payload(self) -> dict:
        return {
            "fan_id": self.fan_id,
            "timestamp": time.time(),
            "target_gate": self.target_gate,
            # Using WKT (Well-Known Text) for Geography type
            "location_wkt": f"POINT({self.lon} {self.lat})",
            "lat": self.lat,
            "lon": self.lon
        }

def get_bigquery_client() -> bigquery.Client | None:
    import os
    try:
        # 1. Prefer local service account file if it exists (for local testing)
        key_path = "aurageo-3468d6ddc9c1.json"
        if os.path.exists(key_path):
            credentials = service_account.Credentials.from_service_account_file(key_path)
            client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
            return client
            
        # 2. Attempt to load Application Default Credentials (Secure Native Cloud Run Context)
        credentials, project = google.auth.default()
        client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
        return client
    except Exception as e:
        logging.warning(f"BigQuery client could not be initialized: {e}")
        return None

def setup_bigquery(client: bigquery.Client) -> str:
    """Ensure the dataset and table exist before loading data."""
    dataset_id = f"{PROJECT_ID}.{DATASET_ID}"
    
    # 1. Create dataset if it doesn't exist
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"
    try:
        client.create_dataset(dataset, exists_ok=True)
        logging.info(f"Dataset {dataset_id} is ready.")
    except Exception as e:
        logging.warning(f"Error creating dataset: {e}")

    # 2. Configure the table schema and create it
    table_id = f"{dataset_id}.{TABLE_ID}"
    schema = [
        bigquery.SchemaField("fan_id", "STRING"),
        bigquery.SchemaField("timestamp", "FLOAT64"),
        bigquery.SchemaField("target_gate", "STRING"),
        bigquery.SchemaField("location_wkt", "GEOGRAPHY"),
        bigquery.SchemaField("lat", "FLOAT64"),
        bigquery.SchemaField("lon", "FLOAT64"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    try:
        client.create_table(table, exists_ok=True)
        logging.info(f"Table {table_id} is ready.")
    except Exception as e:
        logging.warning(f"Error creating table: {e}")
        
    return table_id

def main() -> None:
    logging.info(f"Initializing {NUM_FANS} fan agents around M. Chinnaswamy Stadium...")
    fans = [Fan(str(uuid.uuid4())[:8]) for _ in range(NUM_FANS)]
    
    bq_client = get_bigquery_client()
    table_ref = None
    if bq_client:
        table_ref = setup_bigquery(bq_client)

    logging.info("Starting simulation loop. Press Ctrl+C to stop.")
    try:
        while True:
            records = []
            for fan in fans:
                fan.move()
                records.append(fan.get_payload())
                
            logging.info(f"Generated {len(records)} trajectory points. Sample: {records[0]}")
            
            # Load to BigQuery via Load Job (Free Tier compatible)
            if bq_client and table_ref:
                try:
                    # In Sandbox/Free Tier, streaming insert_rows_json is blocked.
                    # As a hackathon workaround, we use load_table_from_json (batch jobs).
                    job_config = bigquery.LoadJobConfig(
                        write_disposition=bigquery.WriteDisposition.WRITE_APPEND
                    )
                    job = bq_client.load_table_from_json(records, table_ref, job_config=job_config)
                    job.result()  # Wait for the job to complete
                    logging.info(f"Successfully loaded {len(records)} points to BigQuery.")
                except GoogleAPIError as e:  # pragma: no cover
                    logging.error(f"BigQuery Load Error: {e}")
            else:
                logging.info("BigQuery not configured. Skipping streaming.")
                
            time.sleep(UPDATE_INTERVAL)
            
    except KeyboardInterrupt:
        logging.info("Simulation stopped.")

def run_once(num_fans: int = 50) -> None:
    """Generates exactly one static batch of Fan Data and safely terminates."""
    fans = [Fan(str(uuid.uuid4())[:8]) for _ in range(num_fans)]
    bq_client = get_bigquery_client()
    table_ref = None
    if bq_client:
        table_ref = setup_bigquery(bq_client)
        
    records = []
    # Step the fans 3 times silently so they are slightly displaced from center
    for _ in range(3):
        for fan in fans:
            fan.move()
            
    for fan in fans:
        records.append(fan.get_payload())
        
    if bq_client and table_ref:
        try:
            job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_APPEND)
            job = bq_client.load_table_from_json(records, table_ref, job_config=job_config)
            job.result()
            logging.info(f"Single-batch injected {len(records)} fans to BQ.")
        except Exception as e:
            logging.error(f"Batch Insert Failed: {e}")

if __name__ == "__main__":  # pragma: no cover
    main()
