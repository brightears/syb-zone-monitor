"""Account configuration management for SYB Offline Alarm.

This module loads account IDs from the account_ids.json file which is
generated from the CSV files. This approach makes it easy to update
account IDs by regenerating the JSON file from new CSV data.
"""

import json
import os
from typing import List, Dict, Optional
from pathlib import Path


class AccountConfig:
    """Manages account IDs and related configuration."""
    
    def __init__(self, json_file: str = "account_ids.json"):
        self.json_file = Path(json_file)
        self._account_ids: List[str] = []
        self._account_names: Dict[str, str] = {}
        self.load_accounts()
    
    def load_accounts(self) -> None:
        """Load account IDs from JSON file."""
        if not self.json_file.exists():
            raise FileNotFoundError(
                f"Account IDs file not found: {self.json_file}\n"
                "Run 'python extract_account_ids.py' to generate it from CSV files."
            )
        
        with open(self.json_file, 'r') as f:
            data = json.load(f)
            
        if isinstance(data, list):
            # Simple list of account IDs
            self._account_ids = data
        elif isinstance(data, dict) and 'account_ids' in data:
            # Structured format with metadata
            self._account_ids = data['account_ids']
            if 'account_names' in data:
                self._account_names = data['account_names']
        else:
            raise ValueError(f"Invalid format in {self.json_file}")
    
    @property
    def account_ids(self) -> List[str]:
        """Get list of account IDs."""
        return self._account_ids
    
    @property
    def account_count(self) -> int:
        """Get total number of accounts."""
        return len(self._account_ids)
    
    def get_account_name(self, account_id: str) -> Optional[str]:
        """Get account name by ID if available."""
        return self._account_names.get(account_id)
    
    def refresh(self) -> None:
        """Reload account IDs from file."""
        self.load_accounts()
    
    @classmethod
    def from_csv_files(cls) -> 'AccountConfig':
        """Create AccountConfig by processing CSV files first."""
        # First run the extraction script to ensure account_ids.json is up to date
        import subprocess
        import sys
        
        script_path = Path(__file__).parent / "extract_account_ids.py"
        if script_path.exists():
            subprocess.run([sys.executable, str(script_path)], check=True)
        
        return cls()


# Global instance for easy access
_account_config: Optional[AccountConfig] = None


def get_account_config() -> AccountConfig:
    """Get or create the global AccountConfig instance."""
    global _account_config
    if _account_config is None:
        _account_config = AccountConfig()
    return _account_config


def refresh_accounts() -> None:
    """Refresh the account configuration from file."""
    config = get_account_config()
    config.refresh()


# For backward compatibility or direct access
def get_all_account_ids() -> List[str]:
    """Get all account IDs."""
    return get_account_config().account_ids