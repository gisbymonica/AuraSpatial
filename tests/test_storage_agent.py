import pytest
from unittest.mock import MagicMock
import storage_agent

def test_upload_incident_log_success(mocker):
    # Mock storage client
    mock_client = mocker.patch("storage_agent.storage.Client")
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    
    mock_client.return_value.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    
    result = storage_agent.upload_incident_log({"status": "test"})
    assert result is True
    mock_blob.upload_from_string.assert_called_once()

def test_upload_incident_log_failure(mocker):
    mock_client = mocker.patch("storage_agent.storage.Client")
    mock_client.side_effect = Exception("Auth failed")
    
    result = storage_agent.upload_incident_log({"status": "test"})
    assert result is False
