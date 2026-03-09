#!/usr/bin/env python3
"""
TestForge Interactive Setup CLI

Guides users through interactive configuration setup,
validating inputs and creating .env file without manual editing.
"""
import os
import sys
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama for cross-platform support
init(autoreset=True)


class ConfigSetup:
    """Interactive configuration setup for TestForge."""

    def __init__(self):
        """Initialize the configuration setup."""
        self.project_root = Path(__file__).parent.parent
        self.env_example = self.project_root / ".env.example"
        self.env_file = self.project_root / ".env"
        self.shared_path = self.project_root / "shared"

    # Color helper methods
    @staticmethod
    def success(msg):
        """Print success message in green."""
        print(f"{Fore.GREEN}{msg}{Style.RESET_ALL}")

    @staticmethod
    def error(msg):
        """Print error message in red."""
        print(f"{Fore.RED}{msg}{Style.RESET_ALL}")

    @staticmethod
    def warning(msg):
        """Print warning message in yellow."""
        print(f"{Fore.YELLOW}{msg}{Style.RESET_ALL}")

    @staticmethod
    def info(msg):
        """Print info message in cyan."""
        print(f"{Fore.CYAN}{msg}{Style.RESET_ALL}")

    @staticmethod
    def header(msg):
        """Print header in bold blue."""
        print(f"{Fore.BLUE}{Style.BRIGHT}{msg}{Style.RESET_ALL}")

    def run(self):
        """Run the interactive setup process."""
        self.print_header()

        # Collect configuration from all sections
        config = {}
        config.update(self.setup_claude_api())
        config.update(self.setup_agent())
        config.update(self.setup_bot())
        config.update(self.setup_whatsapp())
        config.update(self.setup_teams())
        config.update(self.setup_docker())

        # Preview and write
        self.preview_and_write(config)

        # Create directories
        self.create_shared_directories()

        self.print_success()

    def print_header(self):
        """Print setup header."""
        print("\n" + "="*50)
        self.header("🔧 TestForge Interactive Setup")
        print("="*50 + "\n")

    def prompt_required(self, key, description, validator=None):
        """
        Prompt for required configuration value.

        Args:
            key: Configuration key name
            description: User-friendly description
            validator: Optional validation function that returns value on success
                       or None/error message on failure

        Returns:
            Validated configuration value
        """
        while True:
            value = input(f"{description}:\n").strip()

            if value:
                # Validate if validator provided
                if validator:
                    try:
                        validated = validator(value)
                        if validated is None or validated is False:
                            self.warning("⚠️  Invalid value. Please try again.\n")
                            continue
                        return validated
                    except ValueError as e:
                        self.error(f"❌ {e}")
                        continue
                return value

            self.warning("⚠️  This field is required. Please enter a value.\n")

    def prompt_optional(self, key, description, default=None):
        """
        Prompt for optional configuration value.

        Args:
            key: Configuration key name
            description: User-friendly description with default
            default: Default value to show in brackets

        Returns:
            Configuration value or None if skipped
        """
        default_str = f" [{default}]" if default else ""
        skip_hint = " (press ENTER to skip)" if not default else ""

        prompt_line = f"{description}{default_str}:"
        if skip_hint:
            prompt_line += f" {skip_hint}"

        value = input(prompt_line).strip()

        # Return None if skipped
        if not value:
            return None

        return value

    def validate_api_key(self, value):
        """
        Validate Anthropic API key format.

        Args:
            value: API key to validate

        Returns:
            The API key if valid, None if invalid
        """
        if not value:
            return None

        if not value.startswith("sk-ant-"):
            return None

        if len(value) < 20:
            return None

        return value

    def validate_port(self, value):
        """
        Validate port number.

        Args:
            value: Port number as string

        Returns:
            Port as integer if valid, None if invalid
        """
        try:
            port = int(value)
            if 1 <= port <= 65535:
                return port
            return None
        except ValueError:
            return None

    def validate_url(self, value):
        """
        Validate URL format.

        Args:
            value: URL string

        Returns:
            The URL if valid, None if invalid
        """
        if not value:
            return value  # Optional field - return as-is

        # Basic URL validation
        if value.startswith(('http://', 'https://')):
            return value

        return None

    def setup_claude_api(self):
        """Setup Claude API configuration."""
        print("\n📝 Section 1/6: Claude API Configuration\n")

        api_key = self.prompt_required(
            'ANTHROPIC_API_KEY',
            'Enter your Claude API key',
            validator=lambda x: self.validate_api_key(x)
        )

        self.success("✓ API key validated\n")
        return {'ANTHROPIC_API_KEY': api_key}

    def setup_agent(self):
        """Setup Agent settings."""
        self.info("\n⚙️  Section 2/6: Agent Settings\n")

        host = self.prompt_optional(
            'AGENT_HOST',
            'Agent host [0.0.0.0]',
            default='0.0.0.0'
        )

        port = self.prompt_required(
            'AGENT_PORT',
            'Agent port [8000]:',
            validator=lambda x: self.validate_port(x)
        )

        volume = self.prompt_optional(
            'SHARED_VOLUME_PATH',
            'Shared volume path [/testforge]:',
            default='/testforge'
        )

        return {
            'AGENT_HOST': host or '0.0.0.0',
            'AGENT_PORT': str(port),
            'SHARED_VOLUME_PATH': volume or '/testforge'
        }

    def setup_bot(self):
        """Setup Bot settings."""
        self.info("\n🤖 Section 3/6: Bot Settings\n")

        host = self.prompt_optional(
            'BOT_HOST',
            'Bot host [0.0.0.0]:',
            default='0.0.0.0'
        )

        port = self.prompt_required(
            'BOT_PORT',
            'Bot port [5000]:',
            validator=lambda x: self.validate_port(x)
        )

        api_url = self.prompt_optional(
            'AGENT_API_URL',
            'Agent API URL [http://agent:8000]:',
            default='http://agent:8000'
        )

        return {
            'BOT_HOST': host or '0.0.0.0',
            'BOT_PORT': str(port),
            'AGENT_API_URL': api_url or 'http://agent:8000'
        }

    def setup_whatsapp(self):
        """Setup WhatsApp configuration (optional)."""
        self.info("\n📱 Section 4/6: WhatsApp Configuration (optional)")
        print("Press ENTER to skip this section...\n")

        phone_id = self.prompt_optional('WHATSAPP_PHONE_NUMBER_ID', 'Phone number ID:')
        if phone_id is None:
            return {}

        access_token = self.prompt_required('WHATSAPP_ACCESS_TOKEN', 'Access token:')
        verify_token = self.prompt_required('WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'Verify token:')

        return {
            'WHATSAPP_PHONE_NUMBER_ID': phone_id,
            'WHATSAPP_ACCESS_TOKEN': access_token,
            'WHATSAPP_WEBHOOK_VERIFY_TOKEN': verify_token
        }

    def setup_teams(self):
        """Setup Teams configuration (optional)."""
        self.info("\n💬 Section 5/6: Microsoft Teams Configuration (optional)")
        print("Press ENTER to skip this section...\n")

        app_id = self.prompt_optional('TEAMS_APP_ID', 'Teams App ID:')
        if app_id is None:
            return {}

        app_password = self.prompt_required('TEAMS_APP_PASSWORD', 'Teams App Password:')
        port = self.prompt_optional(
            'TEAMS_PORT',
            'Teams port [3978]:',
            default='3978'
        )

        return {
            'TEAMS_APP_ID': app_id,
            'TEAMS_APP_PASSWORD': app_password,
            'TEAMS_PORT': port or '3978'
        }

    def setup_docker(self):
        """Setup Docker configuration."""
        self.info("\n🐳 Section 6/6: Docker Settings\n")

        project_name = self.prompt_optional(
            'COMPOSE_PROJECT_NAME',
            'Docker Compose project name [testforge]:',
            default='testforge'
        )

        return {
            'COMPOSE_PROJECT_NAME': project_name or 'testforge'
        }

    def preview_and_write(self, config):
        """Preview configuration and write to .env file."""
        print("\n" + "="*50)
        print("📋 Configuration Preview")
        print("="*50 + "\n")

        # Display configuration
        for key, value in config.items():
            # Mask sensitive values for display
            if 'KEY' in key or 'TOKEN' in key or 'PASSWORD' in key:
                display_value = value[:8] + "..." if value else "(not set)"
            else:
                display_value = value or "(not set)"
            print(f"{key}={display_value}")

        print("\n" + "="*50 + "\n")

        # Confirm
        response = input("Write to .env? [Y/n]: ").strip().lower()
        if response == 'y':
            self.write_env_file(config)
            self.success("✅ Configuration written to .env\n")
        else:
            self.error("❌ Setup cancelled. No changes made.")
            sys.exit(0)

    def write_env_file(self, config):
        """Write configuration to .env file.

        Args:
            config: Dictionary of configuration values
        """
        with open(self.env_file, 'w') as f:
            for key, value in config.items():
                if value is not None:
                    f.write(f"{key}={value}\n")

    def create_shared_directories(self):
        """Create shared volume directories."""
        print("📁 Creating shared volume directories...")

        shared_path = self.project_root / 'shared'
        directories = [
            shared_path / 'ingress',
            shared_path / 'egress',
            shared_path / 'page_objects',
            shared_path / 'html_dumps',
            shared_path / 'logs'
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        self.success("✅ Directories created\n")

    def print_success(self):
        """Print success message and next steps."""
        print("="*50)
        self.success("✅ Setup complete!")
        print("="*50)
        print("\nTo start TestForge:")
        print("  cd docker && docker-compose up")
        print()


def main():
    """Main entry point."""
    setup = ConfigSetup()
    setup.run()


if __name__ == "__main__":
    main()
