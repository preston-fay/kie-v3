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

        result = client.process_command("/status")
        assert result is True
        client.handler.handle_status.assert_called_once()

    def test_process_command_exit(self, tmp_path):
        """Test exit commands."""
        client = KIEClient(project_root=tmp_path)

        # Test various exit commands
        assert client.process_command("/quit") is False
        assert client.process_command("/exit") is False
        assert client.process_command("quit") is False
        assert client.process_command("exit") is False

    def test_process_command_help(self, tmp_path):
        """Test help command."""
        client = KIEClient(project_root=tmp_path)

        # Should return True and not raise
        result = client.process_command("/help")
        assert result is True

    def test_process_command_startkie(self, tmp_path):
        """Test /startkie command."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_startkie = Mock(return_value={
            "success": True,
            "message": "Project created"
        })

        result = client.process_command("/startkie")
        assert result is True
        client.handler.handle_startkie.assert_called_once()

    def test_process_command_interview(self, tmp_path):
        """Test /interview command."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_interview = Mock(return_value={
            "complete": False,
            "completion_percentage": 50
        })

        result = client.process_command("/interview")
        assert result is True
        client.handler.handle_interview.assert_called_once()

    def test_process_command_eda(self, tmp_path):
        """Test /eda command."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_eda = Mock(return_value={
            "success": True,
            "profile": {}
        })

        result = client.process_command("/eda")
        assert result is True
        client.handler.handle_eda.assert_called_once()

    def test_process_command_analyze(self, tmp_path):
        """Test /analyze command."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_analyze = Mock(return_value={
            "success": True,
            "insights_count": 5
        })

        result = client.process_command("/analyze")
        assert result is True
        client.handler.handle_analyze.assert_called_once()

    def test_process_command_map(self, tmp_path):
        """Test /map command."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_map = Mock(return_value={
            "success": True,
            "map_path": "/path/to/map.html"
        })

        result = client.process_command("/map")
        assert result is True
        client.handler.handle_map.assert_called_once()

    def test_process_command_validate(self, tmp_path):
        """Test /validate command."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_validate = Mock(return_value={
            "total_reports": 5,
            "passed": 5
        })

        result = client.process_command("/validate")
        assert result is True
        client.handler.handle_validate.assert_called_once()

    def test_process_command_build(self, tmp_path):
        """Test /build command with various targets."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_build = Mock(return_value={
            "success": True,
            "outputs": {}
        })

        # Test default (all)
        result = client.process_command("/build")
        assert result is True
        client.handler.handle_build.assert_called_with(target="all")

        # Test specific target
        result = client.process_command("/build presentation")
        assert result is True
        client.handler.handle_build.assert_called_with(target="presentation")

    def test_process_command_preview(self, tmp_path):
        """Test /preview command."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_preview = Mock(return_value={
            "charts": [],
            "tables": []
        })

        result = client.process_command("/preview")
        assert result is True
        client.handler.handle_preview.assert_called_once()

    def test_process_command_unknown(self, tmp_path):
        """Test unknown command."""
        client = KIEClient(project_root=tmp_path)

        # Should return True but show error
        result = client.process_command("/unknown")
        assert result is True

    def test_process_command_empty(self, tmp_path):
        """Test empty command."""
        client = KIEClient(project_root=tmp_path)

        # Should return True and do nothing
        result = client.process_command("")
        assert result is True
        result = client.process_command("   ")
        assert result is True

    def test_process_command_exception(self, tmp_path):
        """Test command that raises exception."""
        client = KIEClient(project_root=tmp_path)

        client.handler.handle_status = Mock(side_effect=Exception("Test error"))

        # Should return True (continue) but show error
        result = client.process_command("/status")
        assert result is True


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
