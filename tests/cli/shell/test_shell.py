"""
Tests for the core ServerShell implementation.
"""
import sys
import pytest
from unittest.mock import patch, MagicMock, call

from src.cli.shell.shell import ServerShell
from src.cli.shell.exceptions import ShellExit

class TestServerShell:
    """Test suite for the ServerShell class."""

    @pytest.fixture
    def mock_command_handler(self):
        """Fixture for mocked CommandHandler."""
        with patch('src.cli.shell.shell.CommandHandler') as mock:
            handler = mock.return_value
            handler.get_commands.return_value = {
                'help': MagicMock(),
                'exit': MagicMock()
            }
            yield handler

    @pytest.fixture
    def mock_variable_manager(self):
        """Fixture for mocked VariableManager."""
        with patch('src.cli.shell.shell.VariableManager') as mock:
            manager = mock.return_value
            # Set up expand_variables to return input by default
            manager.expand_variables.side_effect = lambda x: x
            yield manager

    @pytest.fixture
    def mock_config_store_manager(self):
        """Fixture for mocked ConfigStoreManager."""
        with patch('src.cli.shell.shell.ConfigStoreManager') as mock:
            manager = mock.return_value
            manager.get_store.return_value = MagicMock()
            yield manager

    @pytest.fixture
    def mock_discovery_coordinator(self):
        """Fixture for mocked DiscoveryCoordinator."""
        with patch('src.cli.shell.shell.DiscoveryCoordinator') as mock:
            yield mock.return_value

    @pytest.fixture
    def mock_prompt_session(self):
        """Fixture for mocked PromptSession."""
        with patch('src.cli.shell.shell.PromptSession') as mock:
            session = mock.return_value
            # Set up prompt to return empty string by default
            session.prompt.return_value = ""
            yield session

    @pytest.fixture
    def shell(self, mock_command_handler, mock_variable_manager, 
              mock_config_store_manager, mock_discovery_coordinator, 
              mock_prompt_session):
        """Fixture that returns a ServerShell instance with mocked dependencies."""
        return ServerShell()

    def test_initialization(self, shell, mock_command_handler, mock_variable_manager,
                           mock_config_store_manager, mock_discovery_coordinator):
        """Test ServerShell initialization."""
        # Verify all components are initialized
        assert shell.running is False
        assert shell.command_handler is mock_command_handler
        assert shell.variable_manager is mock_variable_manager
        assert shell.config_store_manager is mock_config_store_manager
        assert shell.discovery_coordinator is mock_discovery_coordinator
        assert shell.context == {'current_server': None}

    def test_initialization_with_config(self):
        """Test ServerShell initialization with custom config."""
        with patch('src.cli.shell.shell.CommandHandler'), \
             patch('src.cli.shell.shell.VariableManager'), \
             patch('src.cli.shell.shell.ConfigStoreManager') as mock_csm, \
             patch('src.cli.shell.shell.DiscoveryCoordinator') as mock_dc, \
             patch('src.cli.shell.shell.PromptSession'):
            
            custom_config = {
                'config_path': '/custom/path',
                'parallel_discovery': False,
                'discovery_workers': 10,
                'history_file': '/custom/history'
            }
            
            shell = ServerShell(config=custom_config)
            
            # Verify config was passed to dependencies
            mock_csm.assert_called_with(config_path='/custom/path')
            mock_dc.assert_called_with(
                mock_csm.return_value.get_store.return_value,
                parallel=False,
                max_workers=10
            )

    def test_get_prompt_text_no_server(self, shell):
        """Test prompt text generation with no current server."""
        assert shell.get_prompt_text() == "shell> "

    def test_get_prompt_text_with_server(self, shell):
        """Test prompt text generation with current server."""
        shell.context['current_server'] = 'test-server'
        assert shell.get_prompt_text() == "test-server> "

    def test_process_command(self, shell, mock_variable_manager, mock_command_handler):
        """Test processing a command."""
        # Setup variable expansion
        mock_variable_manager.expand_variables.return_value = "test expanded args"
        
        # Call process_command
        shell.process_command("test expanded args")
        
        # Verify variable expansion and command execution
        mock_variable_manager.expand_variables.assert_called_with("test expanded args")
        mock_command_handler.execute.assert_called_with(
            "test", "expanded args", shell
        )

    def test_process_command_no_args(self, shell, mock_variable_manager, mock_command_handler):
        """Test processing a command with no arguments."""
        mock_variable_manager.expand_variables.return_value = "test"
        
        shell.process_command("test")
        
        mock_command_handler.execute.assert_called_with(
            "test", "", shell
        )

    def test_run_normal_exit(self, shell, mock_prompt_session):
        """Test normal shell run loop with exit command."""
        # Setup prompt to return command and then raise EOFError
        mock_prompt_session.prompt.side_effect = [
            "help",
            "test command",
            EOFError()
        ]
        
        # Set up process_command to handle the inputs
        shell.process_command = MagicMock()
        
        # Run the shell
        with patch('builtins.print') as mock_print:
            shell.run()
            
            # Verify welcome message and goodbye message
            mock_print.assert_any_call("Welcome to Server Management Shell")
            mock_print.assert_any_call("\nExiting shell. Goodbye!")
            
            # Verify commands were processed
            assert shell.process_command.call_count == 2
            shell.process_command.assert_has_calls([
                call("help"),
                call("test command")
            ])
            
            # Verify shell was stopped
            assert shell.running is False

    def test_run_keyboard_interrupt(self, shell, mock_prompt_session):
        """Test shell run loop with keyboard interrupt."""
        # Setup prompt to raise KeyboardInterrupt and then EOFError
        mock_prompt_session.prompt.side_effect = [
            KeyboardInterrupt(),
            EOFError()
        ]
        
        # Run the shell
        shell.run()
        
        # Verify shell continues after KeyboardInterrupt
        assert mock_prompt_session.prompt.call_count == 2

    def test_run_shell_exit_exception(self, shell, mock_prompt_session):
        """Test shell run loop with ShellExit exception."""
        # Setup prompt to return a command and process_command to raise ShellExit
        mock_prompt_session.prompt.return_value = "exit"
        shell.process_command = MagicMock(side_effect=ShellExit())
        
        # Run the shell
        with patch('builtins.print') as mock_print:
            shell.run()
            
            # Verify goodbye message
            mock_print.assert_any_call("Exiting shell. Goodbye!")
            
            # Verify shell was stopped
            assert shell.running is False

    def test_run_generic_exception(self, shell, mock_prompt_session):
        """Test shell run loop with generic exception."""
        # Setup prompt to return a command, then raise exception, then exit
        mock_prompt_session.prompt.side_effect = [
            "test",
            "another_test",
            EOFError()
        ]
        
        # Setup process_command to raise an exception on first call
        shell.process_command = MagicMock(side_effect=[
            Exception("Test error"),
            None
        ])
        
        # Run the shell
        with patch('builtins.print') as mock_print, \
             patch('traceback.print_exc') as mock_traceback:
            shell.run()
            
            # Verify error was printed
            mock_print.assert_any_call("Error: Test error")
            mock_traceback.assert_called_once()
            
            # Verify shell continued running after exception
            assert shell.process_command.call_count == 2

    def test_run_empty_input(self, shell, mock_prompt_session):
        """Test shell run loop with empty input."""
        # Setup prompt to return empty string, then a command, then exit
        mock_prompt_session.prompt.side_effect = [
            "",
            "   ",
            "test",
            EOFError()
        ]
        
        # Set up process_command to handle the inputs
        shell.process_command = MagicMock()
        
        # Run the shell
        shell.run()
        
        # Verify only non-empty command was processed
        assert shell.process_command.call_count == 1
        shell.process_command.assert_called_once_with("test")