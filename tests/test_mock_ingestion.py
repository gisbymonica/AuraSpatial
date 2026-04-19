import pytest
from unittest.mock import MagicMock, patch
import mock_ingestion
from google.api_core.exceptions import GoogleAPIError

def test_fan_init_and_move():
    fan = mock_ingestion.Fan("f1")
    assert fan.fan_id == "f1"
    assert "lat" in fan.get_payload()
    initial_lat = fan.lat
    fan.move()
    # It should have moved minimally
    # Check if target_gate is valid
    assert fan.target_gate in mock_ingestion.GATES

def test_get_bigquery_client_with_file(mocker):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("mock_ingestion.service_account.Credentials.from_service_account_file")
    mocker.patch("mock_ingestion.bigquery.Client")
    
    client = mock_ingestion.get_bigquery_client()
    assert client is not None

def test_get_bigquery_client_with_adc(mocker):
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("mock_ingestion.google.auth.default", return_value=(MagicMock(), "project"))
    mocker.patch("mock_ingestion.bigquery.Client")
    
    client = mock_ingestion.get_bigquery_client()
    assert client is not None

def test_get_bigquery_client_failure(mocker):
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("mock_ingestion.google.auth.default", side_effect=Exception("No ADC"))
    
    client = mock_ingestion.get_bigquery_client()
    assert client is None

def test_setup_bigquery(mocker):
    mock_client = MagicMock()
    table_id = mock_ingestion.setup_bigquery(mock_client)
    assert "fan_trajectories_raw" in table_id
    mock_client.create_dataset.assert_called_once()
    mock_client.create_table.assert_called_once()

def test_setup_bigquery_exceptions(mocker):
    mock_client = MagicMock()
    mock_client.create_dataset.side_effect = Exception("err")
    mock_client.create_table.side_effect = Exception("err")
    table_id = mock_ingestion.setup_bigquery(mock_client)
    assert table_id is not None # should not crash

def test_run_once(mocker):
    mock_client = MagicMock()
    mocker.patch("mock_ingestion.get_bigquery_client", return_value=mock_client)
    mocker.patch("mock_ingestion.setup_bigquery", return_value="table_ref")
    
    # Should work without exception
    mock_ingestion.run_once(num_fans=2)
    mock_client.load_table_from_json.assert_called_once()

def test_run_once_no_client(mocker):
    mocker.patch("mock_ingestion.get_bigquery_client", return_value=None)
    # Should safely return
    mock_ingestion.run_once(num_fans=2)

def test_run_once_job_failure(mocker):
    mock_client = MagicMock()
    mock_client.load_table_from_json.side_effect = Exception("Load err")
    mocker.patch("mock_ingestion.get_bigquery_client", return_value=mock_client)
    mocker.patch("mock_ingestion.setup_bigquery", return_value="table_ref")
    
    # Should catch exception and not crash
    mock_ingestion.run_once(num_fans=2)

def test_main_keyboard_interrupt(mocker):
    mocker.patch("mock_ingestion.get_bigquery_client", return_value=None)
    mocker.patch("mock_ingestion.time.sleep", side_effect=KeyboardInterrupt)
    
    mock_ingestion.main() # Should catch KeyboardInterrupt and exit gracefully

def test_main_loop_api_error(mocker):
    mock_client = MagicMock()
    mock_client.load_table_from_json.side_effect = mock_ingestion.GoogleAPIError("API error")
    mocker.patch("mock_ingestion.get_bigquery_client", return_value=mock_client)
    mocker.patch("mock_ingestion.setup_bigquery", return_value="table_ref")
    
    # exit loop via sleep
    mocker.patch("mock_ingestion.time.sleep", side_effect=KeyboardInterrupt)
    
    mock_ingestion.main()
