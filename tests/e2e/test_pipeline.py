"""
Minimal smoke test for the Synapse Pipeline CLI.

This single test verifies that all expected commands are registered in the main app.
Individual command functionality is tested in their respective unit test files.
"""

from typer.testing import CliRunner

from synapse.cli import app


def test_all_commands_registered():
    """Verify all expected CLI commands are properly registered in the app."""
    runner = CliRunner()
    result = runner.invoke(app, ['--help'])
    
    assert result.exit_code == 0
    
    # Verify all expected commands are listed in help output
    expected_commands = [
        'transform-telegram',
        'batch-transform',
        'export-telegram',
        'list-channels',
        'download-gdrive',
        'upload-digest',
        'notify'
    ]
    
    for cmd in expected_commands:
        assert cmd in result.output, f'Command {cmd} not found in CLI help'


# Note: Individual command functionality is tested in:
# - test_telegram_transformer.py
# - test_telegram_exporter.py  
# - test_gdrive_uploader.py
# - test_telegram_notifier.py / test_telegram_notifier_integration.py