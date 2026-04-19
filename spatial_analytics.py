import os
import json
from google.cloud import bigquery
from google.oauth2 import service_account
import google.auth
import google.auth.exceptions
import logging


# Configuration
PROJECT_ID = "aurageo"
DATASET_ID = "stadium_ops"
TABLE_ID = "fan_trajectories_raw"
CREDENTIALS_FILE = "aurageo-3468d6ddc9c1.json"

# Customizable ENV settings
CLUSTER_RADIUS_METERS = int(os.getenv("CLUSTER_RADIUS_METERS", "20"))
GATE_CAPACITY = int(os.getenv("GATE_CAPACITY", "50"))

def get_bigquery_client() -> bigquery.Client | None:
    """Gets the authenticated BigQuery client."""
    try:
        # 1. Prefer local service account file if it exists (for local testing)
        if os.path.exists(CREDENTIALS_FILE):
            credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
            client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
            return client
            
        # 2. Attempt to load Application Default Credentials (Secure Native Cloud Run Context)
        credentials, project = google.auth.default()
        client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
        return client
    except Exception as e:
        logging.error(f"Failed to initialize BigQuery client: {e}")
        return None

def setup_views() -> None:
    """Sets up the Spatial Analytics views if they don't exist yet."""
    client = get_bigquery_client()
    if not client:
        return
        
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    
    # 1. Setup 'fan_clusters' view
    # Uses ST_CLUSTERDBSCAN to cluster fans within X meters where minimum fans in a cluster is 3. 
    fan_clusters_view_id = f"{dataset_ref}.fan_clusters"
    fan_clusters_sql = f"""
    SELECT 
        ST_ASGEOJSON(ST_CENTROID(ST_UNION_AGG(ST_GEOGFROMTEXT(location_wkt)))) as cluster_center_geojson,
        COUNT(fan_id) as fan_count,
        cluster_id
    FROM (
        SELECT 
            fan_id,
            location_wkt,
            ST_CLUSTERDBSCAN(ST_GEOGFROMTEXT(location_wkt), {CLUSTER_RADIUS_METERS}, 3) OVER() AS cluster_id
        FROM (
            -- Extract latest position of every active fan within the last 15 minutes
            SELECT fan_id, location_wkt
            FROM `{dataset_ref}.{TABLE_ID}`
            WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 MINUTE)
            QUALIFY ROW_NUMBER() OVER(PARTITION BY fan_id ORDER BY timestamp DESC) = 1
        )
    )
    WHERE cluster_id IS NOT NULL
    GROUP BY cluster_id
    """
    try:
        view = bigquery.Table(fan_clusters_view_id)
        view.view_query = fan_clusters_sql
        # create or replace view
        client.create_table(view, exists_ok=True)
        # Update view if it already exists but we want to refresh params
        client.update_table(view, ["view_query"])
        logging.info(f"Successfully configured View: {fan_clusters_view_id}")
    except Exception as e:
        logging.error(f"Error creating fan_clusters view: {e}")
    # Load dynamic gates from gates.json
    with open("gates.json", "r") as f:
        gates_data = json.load(f)
        
    gate_unions = []
    for g_name, coords in gates_data.items():
        gate_unions.append(f"SELECT '{g_name}' as gate_name, ST_GEOGPOINT({coords['lon']}, {coords['lat']}) as gate_loc, {coords['lon']} as lon, {coords['lat']} as lat, {GATE_CAPACITY} as capacity")
    gate_unions_sql = "\n        UNION ALL ".join(gate_unions)

    # 2. Setup 'gate_status' view
    gate_status_view_id = f"{dataset_ref}.gate_status"
    gate_status_sql = f"""
    WITH gates AS (
        {gate_unions_sql}
    ),
    current_fans AS (
        SELECT fan_id, target_gate
        FROM `{dataset_ref}.{TABLE_ID}`
        WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 MINUTE)
        QUALIFY ROW_NUMBER() OVER(PARTITION BY fan_id ORDER BY timestamp DESC) = 1
    )
    SELECT 
        g.gate_name, 
        g.lon,
        g.lat,
        g.capacity,
        COUNT(f.fan_id) as current_occupancy,
        ROUND((COUNT(f.fan_id) / g.capacity) * 100, 1) AS occupancy_percentage
    FROM gates g
    LEFT JOIN current_fans f ON g.gate_name = f.target_gate
    GROUP BY g.gate_name, g.lon, g.lat, g.capacity
    """
    try:
        view = bigquery.Table(gate_status_view_id)
        view.view_query = gate_status_sql
        client.create_table(view, exists_ok=True)
        client.update_table(view, ["view_query"])
        logging.info(f"Successfully configured View: {gate_status_view_id}")
    except Exception as e:
        logging.error(f"Error creating gate_status view: {e}")

def get_spatial_context() -> str:
    """Extracts the spatial summaries as JSON for the Agent."""
    client = get_bigquery_client()
    if not client:
        return "{}"
        
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    context = {}
    
    # Get Gate Status
    query_gates = f"SELECT * FROM `{dataset_ref}.gate_status`"
    gates_iter = client.query(query_gates)
    context['gates'] = [dict(row) for row in gates_iter]
    
    # Get Crowd Clusters
    query_clusters = f"SELECT * FROM `{dataset_ref}.fan_clusters` ORDER BY fan_count DESC"
    clusters_iter = client.query(query_clusters)
    cluster_list = []
    for row in clusters_iter:
        cluster_list.append({
            "cluster_id": row['cluster_id'],
            "fan_count": row['fan_count'],
            "geometry": json.loads(row['cluster_center_geojson'])
        })
    context['hotspot_clusters'] = cluster_list
    
    return json.dumps(context, indent=2)

if __name__ == "__main__":  # pragma: no cover
    logging.info("Setting up Spatial Views...")
    setup_views()
    logging.info("Extracting Live Spatial Context JSON:")
    logging.info(get_spatial_context())
