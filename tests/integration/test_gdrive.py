"""
Integration tests for Google Drive uploader.

These tests require a valid service account and will make actual API calls.
Run with: pytest -m integration tests/test_gdrive_integration.py
"""

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from synapse.config import Settings
from synapse.uploaders.gdrive import GoogleDriveUploader


@pytest.mark.integration
class TestGoogleDriveIntegration:
    """Minimal integration tests for Google Drive functionality."""
    
    @pytest.fixture
    def settings(self):
        """Create settings from configuration."""
        settings = Settings()
        
        # Check if service account file exists
        if not settings.gdrive.service_account_path or not Path(settings.gdrive.service_account_path).exists():
            pytest.fail(f'Google Drive service account file not found at: {settings.gdrive.service_account_path}')
        
        # Check if folder IDs are configured
        if not settings.gdrive.team_data_folder_id:
            pytest.fail('Google Drive team_data_folder_id not configured in config.toml')
        
        if not settings.gdrive.team_digests_folder_id:
            pytest.fail('Google Drive team_digests_folder_id not configured in config.toml')
        
        return settings
    
    def test_rclone_available(self):
        """Test that rclone is installed and accessible."""
        result = subprocess.run(
            ['rclone', 'version'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "rclone must be installed"
    
    def test_configuration_valid(self, settings):
        """Test that configuration and service account are valid."""
        # Check service account file can be parsed
        with open(settings.gdrive.service_account_path) as f:
            sa_data = json.load(f)
        
        assert sa_data.get('type') == 'service_account', "Invalid service account type"
        assert 'client_email' in sa_data, "Service account missing client_email"
        assert 'private_key' in sa_data, "Service account missing private_key"
    
    def test_basic_upload_download(self, settings, tmp_path):
        """Single smoke test for upload and download functionality."""
        uploader = GoogleDriveUploader(service_account_path=settings.gdrive.service_account_path)
        
        # Test upload
        test_file = tmp_path / 'smoke_test.txt'
        test_file.write_text(f'Smoke test at {datetime.now()}')
        
        filename = f'smoke_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        result = uploader.upload_team_digest(
            digest_path=test_file,
            filename=filename
        )
        
        assert result is not None, "Upload should return a share link"
        assert result.startswith('https://drive.google.com/'), "Should return Google Drive URL"
        
        # Test download (just verify it doesn't crash)
        download_path = tmp_path / 'downloads'
        since = datetime.now() - timedelta(hours=1)
        downloaded_files = uploader.download_team_data(
            since=since,
            output_dir=download_path
        )
        
        assert isinstance(downloaded_files, list), "Download should return a list"
        
        # Clean up the test file we uploaded
        subprocess.run([
            'rclone', 'delete', f'gdrive:{filename}',
            '--drive-root-folder-id', settings.gdrive.team_digests_folder_id
        ], capture_output=True)

