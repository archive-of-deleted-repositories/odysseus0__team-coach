"""Test Google Drive uploader functionality."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from synapse.uploaders.gdrive import GoogleDriveUploader


@pytest.fixture
def mock_settings():
    """Mock settings for Google Drive configuration."""
    with patch('synapse.uploaders.gdrive.get_settings') as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.gdrive.service_account_path = './service-account.json'
        mock_settings.gdrive.team_data_folder_id = 'input_folder_id'
        mock_settings.gdrive.team_digests_folder_id = 'output_folder_id'
        mock_get_settings.return_value = mock_settings
        yield mock_settings


@pytest.fixture
def service_account_file():
    """Create a temporary service account file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({'type': 'service_account', 'project_id': 'test-project'}, f)
        yield Path(f.name)
    # Cleanup
    Path(f.name).unlink()


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run for rclone commands."""
    with patch('synapse.uploaders.gdrive.subprocess.run') as mock_run:
        # Default to successful response
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ''
        mock_result.stderr = ''
        mock_run.return_value = mock_result
        yield mock_run


def test_google_drive_uploader_init_success(mock_settings, service_account_file, mock_subprocess):
    """Test successful initialization of GoogleDriveUploader."""
    mock_settings.gdrive.service_account_path = str(service_account_file)
    
    uploader = GoogleDriveUploader()
    
    assert uploader.service_account_path == str(service_account_file.resolve())
    assert uploader.team_data_folder_id == 'input_folder_id'
    assert uploader.team_digests_folder_id == 'output_folder_id'


def test_google_drive_uploader_init_no_service_account(mock_settings):
    """Test initialization fails without service account path."""
    mock_settings.gdrive.service_account_path = None
    
    with pytest.raises(ValueError, match='Service account path is required'):
        GoogleDriveUploader()


def test_google_drive_uploader_init_missing_file(mock_settings):
    """Test initialization fails with non-existent service account file."""
    mock_settings.gdrive.service_account_path = '/nonexistent/file.json'
    
    with pytest.raises(FileNotFoundError, match='Service account file not found'):
        GoogleDriveUploader()


def test_download_team_data_success(mock_settings, service_account_file, mock_subprocess):
    """Test successful download of team data."""
    mock_settings.gdrive.service_account_path = str(service_account_file)
    
    # Mock file listing response
    files_json = json.dumps([
        {'Path': 'meeting_notes.txt', 'IsDir': False, 'ModTime': '2024-01-01T10:00:00Z'},
        {'Path': 'transcript.md', 'IsDir': False, 'ModTime': '2024-01-01T11:00:00Z'},
        {'Path': 'subdir', 'IsDir': True}  # Should be skipped
    ])
    
    # Configure mock responses - list files, then download each
    mock_result_list = MagicMock()
    mock_result_list.returncode = 0
    mock_result_list.stdout = files_json
    mock_result_list.stderr = ''
    
    mock_result_download = MagicMock()
    mock_result_download.returncode = 0
    mock_result_download.stdout = ''
    mock_result_download.stderr = ''
    
    mock_subprocess.side_effect = [mock_result_list, mock_result_download, mock_result_download]
    
    uploader = GoogleDriveUploader()
    
    # Test download
    output_dir = Path(tempfile.mkdtemp())
    since = datetime.now() - timedelta(days=7)
    downloaded_files = uploader.download_team_data(since, output_dir)
    
    # Verify results
    assert len(downloaded_files) == 2
    assert output_dir / 'meeting_notes.txt' in downloaded_files
    assert output_dir / 'transcript.md' in downloaded_files
    
    # Cleanup
    import shutil
    shutil.rmtree(output_dir)


def test_upload_team_digest_success(mock_settings, service_account_file, mock_subprocess):
    """Test successful upload of team digest."""
    mock_settings.gdrive.service_account_path = str(service_account_file)
    
    # Mock file info response with file ID
    file_info_json = json.dumps([{'ID': 'file123', 'Name': 'digest.md'}])
    
    # Configure mock responses
    mock_result_upload = MagicMock()
    mock_result_upload.returncode = 0
    mock_result_upload.stdout = ''
    mock_result_upload.stderr = ''
    
    mock_result_list = MagicMock()
    mock_result_list.returncode = 0
    mock_result_list.stdout = file_info_json
    mock_result_list.stderr = ''
    
    mock_subprocess.side_effect = [mock_result_upload, mock_result_list]
    
    uploader = GoogleDriveUploader()
    
    # Create a temporary digest file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write('# Team Digest\nContent here.')
        digest_path = Path(f.name)
    
    try:
        # Test upload
        share_link = uploader.upload_team_digest(digest_path, 'weekly_digest.md')
        
        # Verify share link
        assert share_link == 'https://drive.google.com/file/d/file123/view'
        
    finally:
        # Cleanup
        digest_path.unlink()