"""Google Drive uploader using rclone CLI directly."""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from synapse.config import get_settings

logger = logging.getLogger(__name__)


class GoogleDriveUploader:
    """Handle Google Drive uploads and downloads using rclone CLI."""
    
    def __init__(self, service_account_path: str | None = None):
        """Initialize Google Drive uploader.
        
        Args:
            service_account_path: Path to service account JSON file. If not provided,
                                uses the path from settings.
        """
        settings = get_settings()
        self.service_account_path = service_account_path or settings.gdrive.service_account_path
        self.team_data_folder_id = settings.gdrive.team_data_folder_id
        self.team_digests_folder_id = settings.gdrive.team_digests_folder_id
        
        if not self.service_account_path:
            raise ValueError('Service account path is required for Google Drive authentication')
        
        if not Path(self.service_account_path).exists():
            raise FileNotFoundError(f'Service account file not found: {self.service_account_path}')
        
        # Ensure absolute path
        self.service_account_path = str(Path(self.service_account_path).resolve())
        
        # Setup rclone config
        self._setup_rclone_config()
    
    def _setup_rclone_config(self):
        """Setup rclone configuration."""
        # Create config in user's home directory
        config_path = Path.home() / '.config' / 'rclone' / 'rclone.conf'
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config = f"""[gdrive]
type = drive
scope = drive
service_account_file = {self.service_account_path}
"""
        
        config_path.write_text(config)
        logger.info(f'Created rclone config at {config_path}')
    
    def _run_rclone(self, args: list[str]) -> dict[str, Any]:
        """Run rclone command and return result."""
        cmd = ['rclone'] + args
        logger.debug(f'Running: {" ".join(cmd)}')
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                logger.error(f'rclone error: {result.stderr}')
                return {'success': False, 'error': result.stderr, 'stdout': result.stdout}
            return {'success': True, 'stdout': result.stdout, 'stderr': result.stderr}
        except Exception as e:
            logger.error(f'Failed to run rclone: {e}')
            return {'success': False, 'error': str(e)}
    
    def download_team_data(self, since: datetime, output_dir: Path) -> list[Path]:
        """Download new team data from Google Drive input folder.
        
        Args:
            since: Download files modified after this timestamp.
            output_dir: Local directory to save downloaded files.
            
        Returns:
            List of paths to downloaded files.
        """
        if not self.team_data_folder_id:
            raise ValueError('team_data_folder_id is required in configuration')
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # List files first
        # Calculate how many days ago 'since' was
        days_ago = (datetime.now() - since).days
        list_args = [
            'lsjson',
            'gdrive:',
            '--drive-root-folder-id', self.team_data_folder_id,
            '--max-age', f'{days_ago}d',
            '--recursive'
        ]
        
        result = self._run_rclone(list_args)
        if not result['success']:
            logger.error(f"Failed to list files: {result['error']}")
            return []
        
        # Parse file list
        try:
            files = json.loads(result['stdout']) if result['stdout'].strip() else []
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON: {result['stdout']}")
            return []
        
        downloaded_files = []
        
        # Download each file
        for file_info in files:
            if file_info.get('IsDir', False):
                continue
            
            file_path = file_info['Path']
            local_path = output_dir / file_path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            download_args = [
                'copyto',
                f'gdrive:{file_path}',
                str(local_path),
                '--drive-root-folder-id', self.team_data_folder_id
            ]
            
            result = self._run_rclone(download_args)
            if result['success']:
                logger.info(f'Downloaded: {file_path}')
                downloaded_files.append(local_path)
            else:
                logger.error(f"Failed to download {file_path}: {result['error']}")
        
        return downloaded_files
    
    def upload_team_digest(self, digest_path: Path, filename: str) -> str:
        """Upload team digest to Google Drive output folder.
        
        Args:
            digest_path: Path to the digest file to upload.
            filename: Name for the file in Google Drive.
            
        Returns:
            Share link for the uploaded file.
        """
        if not self.team_digests_folder_id:
            raise ValueError('team_digests_folder_id is required in configuration')
        
        if not digest_path.exists():
            raise FileNotFoundError(f'Digest file not found: {digest_path}')
        
        # Upload file
        upload_args = [
            'copyto',
            str(digest_path),
            f'gdrive:{filename}',
            '--drive-root-folder-id', self.team_digests_folder_id
        ]
        
        result = self._run_rclone(upload_args)
        if not result['success']:
            raise RuntimeError(f"Failed to upload digest: {result['error']}")
        
        logger.info(f'Successfully uploaded digest: {filename}')
        
        # Get file ID for share link
        list_args = [
            'lsjson',
            f'gdrive:{filename}',
            '--drive-root-folder-id', self.team_digests_folder_id,
            '--no-modtime',
            '--no-mimetype'
        ]
        
        result = self._run_rclone(list_args)
        if result['success'] and result['stdout'].strip():
            try:
                file_data = json.loads(result['stdout'])
                if file_data and len(file_data) > 0:
                    file_id = file_data[0].get('ID', '')
                    if file_id:
                        return f'https://drive.google.com/file/d/{file_id}/view'
            except json.JSONDecodeError:
                pass
        
        # Fallback to folder link
        return f'https://drive.google.com/drive/folders/{self.team_digests_folder_id}'