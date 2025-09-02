import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from wandern.cli.main import app
from wandern.models import Config, Revision

runner = CliRunner()


def test_init_command_non_interactive_default():
    """Test init command in non-interactive mode with default directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / ".wd.json"

        with patch("wandern.cli.main.config_path", config_path):
            with patch("os.getcwd", return_value=temp_dir):
                with patch("os.listdir", return_value=[]):  # Empty migration dir
                    result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert "Created config with empty dsn" in result.stdout
        assert config_path.exists()


def test_init_command_non_interactive_with_directory():
    """Test init command in non-interactive mode with specified directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / ".wd.json"
        migration_dir = "custom_migrations"

        with patch("wandern.cli.main.config_path", config_path):
            with patch("os.listdir", return_value=[]):  # Empty migration dir
                result = runner.invoke(app, ["init", migration_dir])

        assert result.exit_code == 0
        assert "Created config with empty dsn" in result.stdout


def test_init_command_interactive_flag():
    """Test init command recognizes interactive flag"""
    # This test verifies the command accepts the --interactive flag
    # Interactive mode is complex to test with questionary, so we just test the flag recognition
    result = runner.invoke(app, ["init", "--help"])

    assert result.exit_code == 0
    assert "--interactive" in result.stdout or "-i" in result.stdout


def test_init_command_config_already_exists():
    """Test init command when config already exists"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / ".wd.json"
        config_path.touch()  # Create existing config file

        with patch("wandern.cli.main.config_path", config_path):
            result = runner.invoke(app, ["init"])

        assert result.exit_code == 1
        assert "Wandern config already exists" in result.stdout


def test_init_command_migration_directory_exists():
    """Test init command when migration directory already exists and is not empty"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / ".wd.json"

        with patch("wandern.cli.main.config_path", config_path):
            with patch("os.access") as mock_access:
                with patch(
                    "os.listdir", return_value=["existing_file.sql"]
                ):  # Non-empty
                    # First call checks config (doesn't exist), second checks migration dir (exists)
                    mock_access.side_effect = [False, True]
                    result = runner.invoke(app, ["init"])

        assert result.exit_code == 1

        stdout = result.stdout.replace("\n", "")
        assert "Migration directory" in stdout
        assert "already exists" in stdout


def test_generate_command_basic():
    """Test generate command with basic options"""
    mock_config = Config(dsn="sqlite:///test.db", migration_dir="/migrations")
    mock_revision = Revision(
        revision_id="abc123", down_revision_id="def456", message="test migration"
    )

    with patch("wandern.cli.main.load_config", return_value=mock_config):
        with patch("wandern.cli.main.MigrationService") as mock_service_class:
            with patch("wandern.cli.main.create_migration", return_value=mock_revision):
                mock_service = Mock()
                mock_service.graph.get_last_migration.return_value = None
                mock_service.save_migration.return_value = "test_migration.sql"
                mock_service_class.return_value = mock_service

                result = runner.invoke(app, ["generate", "--message", "test migration"])

    assert result.exit_code == 0
    assert "Generated migration file" in result.stdout
    assert "abc123" in result.stdout


def test_prompt_command():
    """Test prompt command with AI generation"""
    mock_config = Config(dsn="sqlite:///test.db", migration_dir="/migrations")
    mock_revision = Revision(
        revision_id="abc123", down_revision_id=None, message="test migration"
    )

    from wandern.agents.migration_agent import MigrationAgentResponse, MigrationSQL

    mock_agent_data = MigrationSQL(
        up_sql="CREATE TABLE test (id INTEGER);",
        down_sql="DROP TABLE test;",
        message="create test table",
    )
    mock_agent_response = MigrationAgentResponse(
        data=mock_agent_data, message="Migration generated"
    )

    with patch("wandern.cli.main.load_config", return_value=mock_config):
        with patch("wandern.cli.main.MigrationService") as mock_service_class:
            with patch("wandern.cli.main.create_migration", return_value=mock_revision):
                with patch(
                    "wandern.agents.migration_agent.MigrationAgent"
                ) as mock_agent_class:
                    mock_service = Mock()
                    mock_service.graph.get_last_migration.return_value = None
                    mock_service.save_migration.return_value = "test_migration.sql"
                    mock_service_class.return_value = mock_service

                    mock_agent = Mock()
                    mock_agent.generate_revision.return_value = mock_agent_response
                    mock_agent_class.return_value = mock_agent

                    result = runner.invoke(
                        app, ["prompt"], input="Create a users table\n"
                    )

    assert result.exit_code == 0
    assert "Generated migration file" in result.stdout


def test_prompt_command_error():
    """Test prompt command with AI generation returning error"""
    mock_config = Config(dsn="sqlite:///test.db", migration_dir="/migrations")
    mock_revision = Revision(
        revision_id="abc123", down_revision_id=None, message="test migration"
    )

    from wandern.agents.migration_agent import MigrationAgentResponse, MigrationSQL

    mock_agent_data = MigrationSQL(up_sql=None, down_sql=None, message=None)
    mock_agent_response = MigrationAgentResponse(
        data=mock_agent_data, message="Failed to generate", error="Invalid prompt"
    )

    with patch("wandern.cli.main.load_config", return_value=mock_config):
        with patch("wandern.cli.main.MigrationService") as mock_service_class:
            with patch("wandern.cli.main.create_migration", return_value=mock_revision):
                with patch(
                    "wandern.agents.migration_agent.MigrationAgent"
                ) as mock_agent_class:
                    mock_service = Mock()
                    mock_service.graph.get_last_migration.return_value = None
                    mock_service_class.return_value = mock_service

                    mock_agent = Mock()
                    mock_agent.generate_revision.return_value = mock_agent_response
                    mock_agent_class.return_value = mock_agent

                    result = runner.invoke(app, ["prompt"], input="Invalid prompt\n")

    assert result.exit_code == 1
    assert "Error:" in result.stdout


@pytest.mark.parametrize(
    "command_args,expected_output",
    [
        (["--message", "test", "--author", "testuser"], "testuser"),
        (["--message", "test", "--tags", "feature, database"], "feature, database"),
        (["--message", "test"], "Generated migration file"),
    ],
)
def test_generate_command_options(command_args, expected_output):
    """Test generate command with various options"""
    mock_config = Config(dsn="sqlite:///test.db", migration_dir="/migrations")
    mock_revision = Revision(
        revision_id="abc123", down_revision_id=None, message="test migration"
    )

    with patch("wandern.cli.main.load_config", return_value=mock_config):
        with patch("wandern.cli.main.MigrationService") as mock_service_class:
            with patch("wandern.cli.main.create_migration", return_value=mock_revision):
                with patch("getpass.getuser", return_value="defaultuser"):
                    mock_service = Mock()
                    mock_service.graph.get_last_migration.return_value = None
                    mock_service.save_migration.return_value = "test_migration.sql"
                    mock_service_class.return_value = mock_service

                    result = runner.invoke(app, ["generate"] + command_args)

    assert result.exit_code == 0


def test_upgrade_command_basic():
    """Test upgrade command with basic usage"""
    mock_config = Config(dsn="sqlite:///test.db", migration_dir="/migrations")

    with patch("wandern.cli.main.load_config", return_value=mock_config):
        with patch("wandern.cli.main.MigrationService") as mock_service_class:
            mock_service = Mock()
            mock_service.upgrade.return_value = None
            mock_service_class.return_value = mock_service

            result = runner.invoke(app, ["up"])

    assert result.exit_code == 0
    mock_service.upgrade.assert_called_once_with(steps=None, author=None, tags=[])


def test_upgrade_command_with_options():
    """Test upgrade command with steps, tags, and author"""
    mock_config = Config(dsn="sqlite:///test.db", migration_dir="/migrations")

    with patch("wandern.cli.main.load_config", return_value=mock_config):
        with patch("wandern.cli.main.MigrationService") as mock_service_class:
            mock_service = Mock()
            mock_service.upgrade.return_value = None
            mock_service_class.return_value = mock_service

            result = runner.invoke(
                app,
                [
                    "up",
                    "--steps",
                    "2",
                    "--tags",
                    "feature, database",
                    "--author",
                    "testuser",
                ],
            )

    assert result.exit_code == 0
    assert "Applying migrations by author: testuser" in result.stdout
    assert "Applying migrations with tags: feature, database" in result.stdout
    mock_service.upgrade.assert_called_once_with(
        steps=2, author="testuser", tags=["feature", "database"]
    )


def test_upgrade_command_with_error():
    """Test upgrade command when service raises ValueError"""
    mock_config = Config(dsn="sqlite:///test.db", migration_dir="/migrations")

    with patch("wandern.cli.main.load_config", return_value=mock_config):
        with patch("wandern.cli.main.MigrationService") as mock_service_class:
            mock_service = Mock()
            mock_service.upgrade.side_effect = ValueError("Migration failed")
            mock_service_class.return_value = mock_service

            result = runner.invoke(app, ["up"])

    assert result.exit_code == 1
    assert "Error:" in result.stdout
    assert "Migration failed" in result.stdout


def test_downgrade_command_basic():
    """Test downgrade command with basic usage"""
    mock_config = Config(dsn="sqlite:///test.db", migration_dir="/migrations")

    with patch("wandern.cli.main.load_config", return_value=mock_config):
        with patch("wandern.cli.main.MigrationService") as mock_service_class:
            mock_service = Mock()
            mock_service.downgrade.return_value = None
            mock_service_class.return_value = mock_service

            result = runner.invoke(app, ["down"])

    assert result.exit_code == 0
    mock_service.downgrade.assert_called_once_with(steps=None)


def test_downgrade_command_with_steps():
    """Test downgrade command with specific number of steps"""
    mock_config = Config(dsn="sqlite:///test.db", migration_dir="/migrations")

    with patch("wandern.cli.main.load_config", return_value=mock_config):
        with patch("wandern.cli.main.MigrationService") as mock_service_class:
            mock_service = Mock()
            mock_service.downgrade.return_value = None
            mock_service_class.return_value = mock_service

            result = runner.invoke(app, ["down", "--steps", "3"])

    assert result.exit_code == 0
    mock_service.downgrade.assert_called_once_with(steps=3)


def test_reset_command():
    """Test reset command"""
    mock_config = Config(dsn="sqlite:///test.db", migration_dir="/migrations")

    with patch("wandern.cli.main.load_config", return_value=mock_config):
        with patch("wandern.cli.main.MigrationService") as mock_service_class:
            mock_service = Mock()
            mock_service.downgrade.return_value = None
            mock_service_class.return_value = mock_service

            result = runner.invoke(app, ["reset"])

    assert result.exit_code == 0
    assert "Reset all migrations successfully!" in result.stdout
    mock_service.downgrade.assert_called_once_with(steps=None)


def test_browse_command_help():
    """Test browse command help"""
    result = runner.invoke(app, ["browse", "--help"])

    assert result.exit_code == 0
    assert "Browse database migrations interactively" in result.stdout


def test_browse_command_all_flag():
    """Test browse command recognizes --all flag"""
    result = runner.invoke(app, ["browse", "--help"])

    assert result.exit_code == 0
    assert "--all" in result.stdout or "-A" in result.stdout


def test_load_config_file_not_found():
    """Test commands when config file is not found"""
    with patch("wandern.cli.main.load_config") as mock_load:
        mock_load.side_effect = FileNotFoundError("Config not found")

        result = runner.invoke(app, ["generate"])

    # The command should fail when config is not found
    assert result.exit_code != 0


def test_app_help():
    """Test that help command works"""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Usage:" in result.stdout


@pytest.mark.parametrize(
    "command",
    ["init", "generate", "up", "down", "reset", "browse"],
)
def test_command_help(command):
    """Test help for individual commands"""
    result = runner.invoke(app, [command, "--help"])

    assert result.exit_code == 0
    assert "Usage:" in result.stdout
