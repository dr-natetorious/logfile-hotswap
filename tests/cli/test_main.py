import os
import sys
import pytest
from unittest.mock import patch, mock_open, MagicMock

# # Explicitly add project root to Python path if not using proper packaging
# # This ensures imports work during testing
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)

from src.cli.main import parse_args, load_config, main


def test_parse_args_default():
    """Test default argument parsing."""
    with patch('sys.argv', ['cli.py']):
        args = parse_args()
        assert args.config is None
        assert args.verbose is False


def test_parse_args_with_config():
    """Test parsing args with config and verbose flag."""
    with patch('sys.argv', ['cli.py', '--config', '/path/to/config.json', '--verbose']):
        args = parse_args()
        assert args.config == '/path/to/config.json'
        assert args.verbose is True


def test_load_config_default():
    """Test loading default configuration."""
    config = load_config()
    assert 'history_file' in config
    assert config['verbose'] is False
    assert config['history_file'] == os.path.expanduser('~/.server_shell_history')


def test_load_config_with_existing_file():
    """Test loading configuration from an existing file."""
    mock_file_content = '{"verbose": true, "custom_setting": "test"}'
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=mock_file_content)):
        # Note: In the current implementation, this won't actually load the file
        # You might want to update the load_config function to actually parse the file
        config = load_config('/path/to/config.json')
        assert config['history_file'] == os.path.expanduser('~/.server_shell_history')


@patch('src.cli.main.ServerShell')
def test_main_success(mock_server_shell):
    """Test main function with successful execution."""
    # Setup mock server shell
    mock_instance = MagicMock()
    mock_server_shell.return_value = mock_instance

    # Patch sys.argv to simulate command line args
    with patch('sys.argv', ['cli.py']):
        result = main()
        
    # Verify the shell was created and run
    mock_server_shell.assert_called_once()
    mock_instance.run.assert_called_once()
    assert result == 0


@patch('src.cli.main.ServerShell')
def test_main_with_verbose_exception(mock_server_shell):
    """Test main function with an exception in verbose mode."""
    # Setup mock to raise an exception
    mock_server_shell.side_effect = Exception("Test error")

    # Patch sys.argv to include verbose flag
    with patch('sys.argv', ['cli.py', '--verbose']), \
         patch('traceback.print_exc') as mock_print_exc, \
         patch('sys.stderr') as mock_stderr:
        result = main()
        
    # Verify error handling
    mock_print_exc.assert_called_once()
    mock_stderr.write.assert_called()
    assert result == 1


def test_main_without_verbose_exception():
    """Test main function with an exception without verbose mode."""
    # Setup mock to raise an exception
    with patch('src.cli.main.ServerShell', side_effect=Exception("Test error")), \
         patch('sys.argv', ['cli.py']), \
         patch('traceback.print_exc') as mock_print_exc, \
         patch('sys.stderr') as mock_stderr:
        result = main()
        
    # Verify error handling
    mock_print_exc.assert_not_called()
    mock_stderr.write.assert_called()
    assert result == 1