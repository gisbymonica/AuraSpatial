import pytest
import json
from unittest.mock import MagicMock
import spatial_analytics

def test_get_bigquery_client_with_file(mocker):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("spatial_analytics.service_account.Credentials.from_service_account_file")
    mocker.patch("spatial_analytics.bigquery.Client")
    
    assert spatial_analytics.get_bigquery_client() is not None

def test_get_bigquery_client_with_adc(mocker):
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("spatial_analytics.google.auth.default", return_value=(MagicMock(), "project"))
    mocker.patch("spatial_analytics.bigquery.Client")
    
    assert spatial_analytics.get_bigquery_client() is not None

def test_get_bigquery_client_failure(mocker):
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("spatial_analytics.google.auth.default", side_effect=Exception("No ADC"))
    
    assert spatial_analytics.get_bigquery_client() is None

def test_setup_views_no_client(mocker):
    mocker.patch("spatial_analytics.get_bigquery_client", return_value=None)
    # Should safely return
    spatial_analytics.setup_views()

def test_setup_views_success(mocker):
    mock_client = MagicMock()
    mocker.patch("spatial_analytics.get_bigquery_client", return_value=mock_client)
    mocker.patch("json.load", return_value={"TEST_GATE": {"lat": 12.0, "lon": 77.0}})
    
    # mock builtins open
    mocker.patch("builtins.open", mocker.mock_open(read_data='{}'))
    
    spatial_analytics.setup_views()
    assert mock_client.create_table.call_count == 2
    assert mock_client.update_table.call_count == 2

def test_setup_views_exceptions(mocker):
    mock_client = MagicMock()
    mock_client.create_table.side_effect = Exception("err")
    mocker.patch("spatial_analytics.get_bigquery_client", return_value=mock_client)
    mocker.patch("builtins.open", mocker.mock_open(read_data='{}'))
    mocker.patch("json.load", return_value={"TEST_GATE": {"lat": 12.0, "lon": 77.0}})
    
    spatial_analytics.setup_views()
    # Should handle exceptions

def test_get_spatial_context_no_client(mocker):
    mocker.patch("spatial_analytics.get_bigquery_client", return_value=None)
    assert spatial_analytics.get_spatial_context() == "{}"

def test_get_spatial_context_success(mocker):
    mock_client = MagicMock()
    mocker.patch("spatial_analytics.get_bigquery_client", return_value=mock_client)
    
    # Needs to mock client.query returning an iterable
    def mock_query(sql):
        if "gate_status" in sql:
            return [{"gate_name": "GateA", "occupancy_percentage": 50}]
        if "fan_clusters" in sql:
            return [{"cluster_id": 1, "fan_count": 10, "cluster_center_geojson": '{"type": "Point", "coordinates": [77, 12]}'} ]
        return []
    
    mock_client.query.side_effect = mock_query
    
    ctx_str = spatial_analytics.get_spatial_context()
    ctx = json.loads(ctx_str)
    
    assert "gates" in ctx
    assert len(ctx["gates"]) == 1
    assert ctx["gates"][0]["gate_name"] == "GateA"
    
    assert "hotspot_clusters" in ctx
    assert len(ctx["hotspot_clusters"]) == 1
    assert ctx["hotspot_clusters"][0]["cluster_id"] == 1
