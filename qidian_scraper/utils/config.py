import json
import os
from pathlib import Path

class Config:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.data = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @property
    def llm(self):
        return self.data.get('llm', {})

    @property
    def scraper(self):
        return self.data.get('scraper', {})

    @property
    def search(self):
        return self.data.get('search', {})

# Global instance
try:
    # Adjust path if running from root or inside module
    base_path = Path(__file__).parent.parent
    config_path = base_path / "config.json"
    CONF = Config(str(config_path))
except Exception:
    CONF = None
