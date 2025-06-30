from pathlib import Path
import yaml
from typing import Self


class YamlConfig():
    def __init__(self, root_path: Path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_path = root_path

    @classmethod
    def load_config(cls) -> dict:
        """Load config from file, create if it doesn't exist."""
        config_file = cls.get_config_file_path()

        # Should bubble up exception handling maybe error logging eventually
        if not config_file.exists():
            print("Config file not found. Creating new configuration...")
            cls.create_config()

        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
            return YamlConfig(Path(config_data.get("tracking_root_directory")))

    @staticmethod
    def get_config_file_path() -> Path:
        """Get the path to the config file.
        If the path does not already exist, it is created. 
        The final path looks like: $HOME/.config/python-helpers/config.yaml

        Returns:
            Path: location of config.yaml file
        """
        config_dir = Path.home() / '.config' / 'python-helpers'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'config.yaml'

    @classmethod
    def create_config(cls) -> Self:
        """Create a new config file by prompting the user for the tracking root directory."""
        print("Setting up time tracker configuration...")

        while True:
            root_dir = input(
                "Enter the tracking root directory to your sprints: "
            ).strip()
            if not root_dir:
                print("Please enter a directory path.")
                continue

            path = Path(root_dir).absolute()

            if not path.exists():
                create = input(
                    f"Directory {path} doesn't exist. Create it? (y/n): ").strip().lower()
                if create == 'y':
                    path.mkdir(parents=True, exist_ok=True)
                    print(f"Created directory: {path}")
                else:
                    continue

            config = {
                'tracking_root_directory': str(path)
            }

            yamlConfig = cls(path)

            config_file = yamlConfig.get_config_file_path()
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

            print(f"Config saved to: {config_file}")
            print(f"Tracking root directory set to: {path}")
            break

        return yamlConfig
