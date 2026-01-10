"""
Tests for KIE CLI loop functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from io import StringIO

from kie.cli import KIEClient, main


class TestKIEClient:
    """Test KIE CLI client."""

    def test_client_initialization(self, tmp_path):
        """Test client initializes correctly."""
        client = KIEClient(project_root=tmp_path)
        assert client.project_root == tmp_path
        assert client.handler is not None

    def test_process_command_status(self, tmp_path):
        """Test /status command."""
        client = KIEClient(project_root=tmp_path)

        # Mock handler
        client.handler.handle_status = Mock(return_value={
            "has_spec": False,
            "has_data": False,
            "outputs": {}
        })

        should_continue, command_succeeded = client.process_command("/status")
        assert should_continue is True
        assert command_succeeded is True
        client.handler.handle_status.assert_called_once()

    def test_process_command_rails(self, tmp_path):
        """Test /rails command (alias for /status)."""
        client = KIEClient(project_root=tmp_path)

        # Mock handler
        client.handler.handle_status = Mock(return_value={
            "has_spec": False,
            "has_data": False,
            "outputs": {},
            "rails_progress": {}
        })

        # /rails should call handle_status
        should_continue, command_succeeded = client.process_command("/rails")
        assert should_continue is True
        assert command_succeeded is True
        client.handler.handle_status.assert_called_once()

    def test_process_command_exit(self, tmp_path):
        """Test exit commands."""
        client = KIEClient(project_root=tmp_path)

        # Test various exit commands
        should_continue, command_succeeded = client.process_command("/quit")
        assert should_continue is False
        assert command_succeeded is True

        should_continue, command_succeeded = client.process_command("/exit")
        assert should_continue is False
        assert command_succeeded is True

        should_continue, command_succeeded = client.process_command("quit")
        assert should_continue is False
        assert command_succeeded is True

        should_continue, command_succeeded = client.process_command("exit")
        assert should_continue is False
        assert command_succeeded is True

    def test_process_command_help(self, tmp_path):
        """Test help command."""
        client = KIEClient(project_root=tmp_path)

        # Should return True and not raise
        should_continue, command_succeeded = client.process_command("/help")
        assert should_continue is True
        assert command_succeeded is True

    def test_process_command_startkie(self, tmp_path):
        """Test /startkie command."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_startkie = Mock(return_value={
            "success": True,
            "message": "Project created"
        })

        should_continue, command_succeeded = client.process_command("/startkie")
        assert should_continue is True
        assert command_succeeded is True
        client.handler.handle_startkie.assert_called_once()

    def test_process_command_interview(self, tmp_path):
        """Test /interview command."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_interview = Mock(return_value={
            "complete": False,
            "completion_percentage": 50
        })

        should_continue, command_succeeded = client.process_command("/interview")
        assert should_continue is True
        assert command_succeeded is True
        client.handler.handle_interview.assert_called_once()

    def test_process_command_eda(self, tmp_path):
        """Test /eda command."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_eda = Mock(return_value={
            "success": True,
            "profile": {}
        })

        should_continue, command_succeeded = client.process_command("/eda")
        assert should_continue is True
        assert command_succeeded is True
        client.handler.handle_eda.assert_called_once()

    def test_process_command_analyze(self, tmp_path):
        """Test /analyze command."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_analyze = Mock(return_value={
            "success": True,
            "insights_count": 5
        })

        should_continue, command_succeeded = client.process_command("/analyze")
        assert should_continue is True
        assert command_succeeded is True
        client.handler.handle_analyze.assert_called_once()

    def test_process_command_map(self, tmp_path):
        """Test /map command."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_map = Mock(return_value={
            "success": True,
            "map_path": "/path/to/map.html"
        })

        should_continue, command_succeeded = client.process_command("/map")
        assert should_continue is True
        assert command_succeeded is True
        client.handler.handle_map.assert_called_once()

    def test_process_command_validate(self, tmp_path):
        """Test /validate command."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_validate = Mock(return_value={
            "total_reports": 5,
            "passed": 5
        })

        should_continue, command_succeeded = client.process_command("/validate")
        assert should_continue is True
        assert command_succeeded is True
        client.handler.handle_validate.assert_called_once()

    def test_process_command_build(self, tmp_path):
        """Test /build command with various targets."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_build = Mock(return_value={
            "success": True,
            "outputs": {}
        })

        # Test default (all)
        should_continue, command_succeeded = client.process_command("/build")
        assert should_continue is True
        assert command_succeeded is True
        client.handler.handle_build.assert_called_with(target="all")

        # Test specific target
        should_continue, command_succeeded = client.process_command("/build presentation")
        assert should_continue is True
        assert command_succeeded is True
        client.handler.handle_build.assert_called_with(target="presentation")

    def test_process_command_preview(self, tmp_path):
        """Test /preview command."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_preview = Mock(return_value={
            "charts": [],
            "tables": []
        })

        should_continue, command_succeeded = client.process_command("/preview")
        assert should_continue is True
        assert command_succeeded is True
        client.handler.handle_preview.assert_called_once()

    def test_process_command_unknown(self, tmp_path):
        """Test unknown command."""
        client = KIEClient(project_root=tmp_path)

        # Should return True but command fails
        should_continue, command_succeeded = client.process_command("/unknown")
        assert should_continue is True
        assert command_succeeded is False

    def test_process_command_empty(self, tmp_path):
        """Test empty command."""
        client = KIEClient(project_root=tmp_path)

        # Should return True and do nothing
        should_continue, command_succeeded = client.process_command("")
        assert should_continue is True
        assert command_succeeded is True
        should_continue, command_succeeded = client.process_command("   ")
        assert should_continue is True
        assert command_succeeded is True

    def test_process_command_exception(self, tmp_path):
        """Test command that raises exception."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_status = Mock(side_effect=Exception("Test error"))

        # Should return True (continue) but command fails
        should_continue, command_succeeded = client.process_command("/status")
        assert should_continue is True
        assert command_succeeded is False


class TestCLILoop:
    """Test full CLI loop with mocked input."""

    @patch('builtins.input')
    def test_repl_loop_with_status_then_exit(self, mock_input, tmp_path):
        """Test REPL loop: /status then /exit."""
        client = KIEClient(project_root=tmp_path)

        # Mock inputs
        mock_input.side_effect = ["/status", "/exit"]

        # Mock handler
        client.handler.handle_status = Mock(return_value={
            "has_spec": False,
            "has_data": False
        })

        # Run start (should exit after /exit)
        client.start()

        # Verify status was called
        client.handler.handle_status.assert_called_once()

    @patch('builtins.input')
    def test_repl_loop_keyboard_interrupt(self, mock_input, tmp_path):
        """Test REPL loop handles Ctrl+C."""
        client = KIEClient(project_root=tmp_path)

        # First input raises KeyboardInterrupt, second exits
        mock_input.side_effect = [KeyboardInterrupt(), "/exit"]

        # Should handle interrupt and continue
        client.start()

    @patch('builtins.input')
    def test_repl_loop_eof(self, mock_input, tmp_path):
        """Test REPL loop handles EOF (Ctrl+D)."""
        client = KIEClient(project_root=tmp_path)

        # Simulate EOF
        mock_input.side_effect = EOFError()

        # Should exit cleanly
        client.start()


def test_main_with_help(capsys):
    """Test main() with --help flag."""
    with patch('sys.argv', ['kie', '--help']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "Usage: kie" in captured.out


def test_main_with_version(capsys):
    """Test main() with --version flag."""
    with patch('sys.argv', ['kie', '--version']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "KIE v" in captured.out


def test_main_with_invalid_directory(capsys):
    """Test main() with non-existent directory."""
    with patch('sys.argv', ['kie', '/nonexistent/path']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "does not exist" in captured.out


@patch('builtins.input')
def test_main_default_directory(mock_input, tmp_path):
    """Test main() with default (current) directory."""
    mock_input.side_effect = ["/exit"]

    with patch('sys.argv', ['kie']):
        with patch('kie.cli.Path.cwd', return_value=tmp_path):
            main()


def test_main_with_rails_command(tmp_path, capsys):
    """Test main() with rails command (should not treat it as directory)."""
    # Create test workspace structure
    (tmp_path / "project_state").mkdir()

    with patch('sys.argv', ['kie', 'rails']):
        with patch('kie.cli.Path.cwd', return_value=tmp_path):
            with patch('kie.commands.handler.CommandHandler.handle_status') as mock_status:
                mock_status.return_value = {
                    "success": True,
                    "has_spec": False,
                    "has_data": False,
                    "rails_progress": {}
                }
                with pytest.raises(SystemExit) as exc_info:
                    main()

                # Should exit with 0 (success)
                assert exc_info.value.code == 0

                # Should have called handle_status, not tried to open directory
                mock_status.assert_called_once()

                # Should NOT show "Directory does not exist" error
                captured = capsys.readouterr()
                assert "Directory does not exist" not in captured.out
