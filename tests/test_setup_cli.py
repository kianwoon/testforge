"""Tests for the interactive setup CLI."""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from scripts.setup_cli import ConfigSetup


class TestConfigSetup:
    """Test the ConfigSetup class."""

    def test_init(self):
        """Test initialization."""
        setup = ConfigSetup()
        assert setup.project_root.exists()
        assert setup.env_example.name == ".env.example"
        assert setup.env_file.name == ".env"

    def test_prompt_required_with_valid_input(self):
        """Test prompt_required accepts valid input."""
        setup = ConfigSetup()

        with patch('builtins.input', return_value='test-api-key'):
            result = setup.prompt_required('TEST_KEY', 'Description')
            assert result == 'test-api-key'

    def test_prompt_required_with_empty_input_reprompts(self):
        """Test prompt_required rejects empty input."""
        setup = ConfigSetup()

        with patch('builtins.input', side_effect=['', 'valid-input']):
            result = setup.prompt_required('TEST_KEY', 'Description')
            assert result == 'valid-input'

    def test_prompt_optional_with_input(self):
        """Test prompt_optional accepts input."""
        setup = ConfigSetup()

        with patch('builtins.input', return_value='custom-value'):
            result = setup.prompt_optional('OPTIONAL_KEY', 'Description')
            assert result == 'custom-value'

    def test_prompt_optional_skip_with_enter(self):
        """Test prompt_optional skips when ENTER pressed."""
        setup = ConfigSetup()

        with patch('builtins.input', return_value=''):
            result = setup.prompt_optional('OPTIONAL_KEY', 'Description')
            assert result is None

    def test_validate_api_key_valid(self):
        """Test API key validation for valid key."""
        setup = ConfigSetup()
        assert setup.validate_api_key('sk-ant-test1234567890') == 'sk-ant-test1234567890'

    def test_validate_api_key_invalid_empty(self):
        """Test API key validation rejects empty key."""
        setup = ConfigSetup()
        assert not setup.validate_api_key('')

    def test_validate_api_key_invalid_format(self):
        """Test API key validation rejects wrong format."""
        setup = ConfigSetup()
        assert not setup.validate_api_key('invalid-format')

    def test_validate_port_valid(self):
        """Test port validation for valid port."""
        setup = ConfigSetup()
        assert setup.validate_port('8000') == 8000

    def test_validate_port_invalid(self):
        """Test port validation rejects invalid port."""
        setup = ConfigSetup()
        assert not setup.validate_port('invalid')

    def test_validate_port_out_of_range(self):
        """Test port validation rejects out of range."""
        setup = ConfigSetup()
        assert not setup.validate_port('99999')

    def test_validate_url_valid(self):
        """Test URL validation for valid URL."""
        setup = ConfigSetup()
        assert setup.validate_url('http://localhost:8000') == 'http://localhost:8000'

    def test_validate_url_invalid(self):
        """Test URL validation rejects invalid URL."""
        setup = ConfigSetup()
        assert not setup.validate_url('not-a-url')

    def test_setup_claude_api_section(self):
        """Test Claude API configuration section."""
        setup = ConfigSetup()

        with patch('builtins.input', return_value='sk-ant-test123'):
            with patch.object(setup, 'validate_api_key', return_value='sk-ant-test123'):
                result = setup.setup_claude_api()
                assert result == {'ANTHROPIC_API_KEY': 'sk-ant-test123'}

    def test_setup_agent_section(self):
        """Test Agent settings section."""
        setup = ConfigSetup()

        with patch('builtins.input', side_effect=['0.0.0.0', '8000', '/nanoclaw']):
            result = setup.setup_agent()
            assert result == {
                'AGENT_HOST': '0.0.0.0',
                'AGENT_PORT': '8000',
                'SHARED_VOLUME_PATH': '/nanoclaw'
            }

    def test_setup_bot_section(self):
        """Test Bot settings section."""
        setup = ConfigSetup()

        with patch('builtins.input', side_effect=['0.0.0.0', '5000', 'http://agent:8000']):
            result = setup.setup_bot()
            assert result == {
                'BOT_HOST': '0.0.0.0',
                'BOT_PORT': '5000',
                'AGENT_API_URL': 'http://agent:8000'
            }

    def test_skip_whatsapp_section(self):
        """Test skipping WhatsApp section."""
        setup = ConfigSetup()

        with patch('builtins.input', return_value=''):
            result = setup.setup_whatsapp()
            assert result == {}

    def test_setup_whatsapp_section(self):
        """Test WhatsApp section with values."""
        setup = ConfigSetup()

        with patch('builtins.input', side_effect=['phone-id', 'token', 'verify']):
            result = setup.setup_whatsapp()
            assert result == {
                'WHATSAPP_PHONE_NUMBER_ID': 'phone-id',
                'WHATSAPP_ACCESS_TOKEN': 'token',
                'WHATSAPP_WEBHOOK_VERIFY_TOKEN': 'verify'
            }

    def test_skip_teams_section(self):
        """Test skipping Teams section."""
        setup = ConfigSetup()

        with patch('builtins.input', side_effect=['', '', '']):
            result = setup.setup_teams()
            assert result == {}

    def test_setup_teams_section(self):
        """Test Teams section with values."""
        setup = ConfigSetup()

        with patch('builtins.input', side_effect=['teams-app-id', 'teams-password', '3978']):
            result = setup.setup_teams()
            assert result == {
                'TEAMS_APP_ID': 'teams-app-id',
                'TEAMS_APP_PASSWORD': 'teams-password',
                'TEAMS_PORT': '3978'
            }

    def test_write_env_file(self):
        """Test writing .env file."""
        setup = ConfigSetup()
        config = {
            'TEST_KEY': 'test-value',
            'ANOTHER_KEY': 'another-value'
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            test_env = Path(tmpdir) / '.env'
            setup.env_file = test_env
            setup.write_env_file(config)

            assert test_env.exists()
            content = test_env.read_text()
            assert 'TEST_KEY=test-value' in content
            assert 'ANOTHER_KEY=another-value' in content

    def test_create_shared_directories(self):
        """Test creating shared volume directories."""
        setup = ConfigSetup()

        with tempfile.TemporaryDirectory() as tmpdir:
            setup.project_root = Path(tmpdir)
            shared_path = setup.project_root / 'shared'

            setup.create_shared_directories()

            assert (shared_path / 'ingress').exists()
            assert (shared_path / 'egress').exists()
            assert (shared_path / 'page_objects').exists()
            assert (shared_path / 'html_dumps').exists()
            assert (shared_path / 'logs').exists()
