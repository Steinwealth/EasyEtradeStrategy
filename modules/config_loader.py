# modules/config_loader.py
"""
Unified Configuration Loader for ETrade Strategy
Loads and manages configuration from multiple .env files based on mode and environment
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

log = logging.getLogger("config_loader")

class ConfigLoader:
    """
    Unified configuration loader that combines multiple .env files
    based on strategy mode, automation mode, and environment
    """
    
    def __init__(self, base_path: str = "configs"):
        self.base_path = Path(base_path)
        self.config = {}
        self.loaded_files = []
    
    def load_configuration(
        self, 
        strategy_mode: str = "standard",
        automation_mode: str = "off", 
        environment: str = "development"
    ) -> Dict[str, Any]:
        """
        Load unified configuration based on mode and environment
        
        Args:
            strategy_mode: Strategy mode (standard, advanced, quantum)
            automation_mode: Automation mode (off, demo, live)
            environment: Environment (development, production, sandbox)
        
        Returns:
            Dict containing all configuration values
        """
        
        log.info(f"Loading configuration: strategy={strategy_mode}, "
                f"automation={automation_mode}, environment={environment}")
        
        # Clear previous configuration
        self.config = {}
        self.loaded_files = []
        
        # Load base configuration files (order matters)
        self._load_env_file(self.base_path / "base.env")
        self._load_env_file(self.base_path / "data-providers.env")
        self._load_env_file(self.base_path / "strategies.env")
        self._load_env_file(self.base_path / "position-sizing.env")
        self._load_env_file(self.base_path / "risk-management.env")
        self._load_env_file(self.base_path / "automation.env")
        self._load_env_file(self.base_path / "alerts.env")
        self._load_env_file(self.base_path / "deployment.env")
        self._load_env_file(self.base_path / "trading-parameters.env")
        
        # Load mode-specific overrides
        mode_file = self.base_path / "modes" / f"{strategy_mode}.env"
        if mode_file.exists():
            self._load_env_file(mode_file)
        else:
            log.warning(f"Mode configuration file not found: {mode_file}")
        
        # Load environment-specific overrides
        env_file = self.base_path / "environments" / f"{environment}.env"
        if env_file.exists():
            self._load_env_file(env_file)
        else:
            log.warning(f"Environment configuration file not found: {env_file}")
        
        # Set runtime configuration
        self.config["STRATEGY_MODE"] = strategy_mode
        self.config["AUTOMATION_MODE"] = automation_mode
        self.config["ENVIRONMENT"] = environment
        
        # Validate configuration
        self._validate_configuration()
        
        log.info(f"Configuration loaded from {len(self.loaded_files)} files")
        return self.config
    
    def _load_env_file(self, file_path: Path):
        """Load environment file if it exists"""
        if not file_path.exists():
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        self.config[key] = value
                    else:
                        log.warning(f"Invalid line in {file_path}:{line_num}: {line}")
            
            self.loaded_files.append(str(file_path))
            log.debug(f"Loaded configuration from: {file_path}")
            
        except Exception as e:
            log.error(f"Error loading configuration file {file_path}: {e}")
    
    def _validate_configuration(self):
        """Validate required configuration values"""
        required_keys = [
            "STRATEGY_MODE",
            "AUTOMATION_MODE",
            "ENVIRONMENT"
        ]
        
        # Optional but recommended keys
        recommended_keys = [
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID"
        ]
        
        # Add E*TRADE keys only if not in Demo Mode and E*TRADE is enabled
        if (self.config.get("TRADING_MODE", "").upper() != "DEMO_MODE" and 
            self.config.get("ETRADE_ENABLED", "false").lower() == "true"):
            recommended_keys.extend([
                "ETRADE_CONSUMER_KEY",
                "ETRADE_CONSUMER_SECRET"
            ])
        
        missing_keys = []
        for key in required_keys:
            if key not in self.config or not self.config[key]:
                missing_keys.append(key)
        
        if missing_keys:
            log.error(f"Missing required configuration keys: {missing_keys}")
            raise ValueError(f"Missing required configuration: {missing_keys}")
        
        # Check recommended keys
        missing_recommended = []
        for key in recommended_keys:
            if key not in self.config or not self.config[key]:
                missing_recommended.append(key)
        
        if missing_recommended:
            log.warning(f"Missing recommended configuration keys: {missing_recommended}")
        
        # Validate strategy mode
        valid_strategies = ["standard", "advanced", "quantum"]
        if self.config["STRATEGY_MODE"] not in valid_strategies:
            raise ValueError(f"Invalid strategy mode: {self.config['STRATEGY_MODE']}")
        
        # Validate automation mode
        valid_automation = ["off", "demo", "live"]
        if self.config["AUTOMATION_MODE"] not in valid_automation:
            raise ValueError(f"Invalid automation mode: {self.config['AUTOMATION_MODE']}")
        
        # Validate environment
        valid_environments = ["development", "production", "sandbox"]
        if self.config["ENVIRONMENT"] not in valid_environments:
            raise ValueError(f"Invalid environment: {self.config['ENVIRONMENT']}")
        
        # Validate data provider priority
        if "DATA_PRIORITY" in self.config:
            providers = self.config["DATA_PRIORITY"].split(",")
            valid_providers = ["etrade", "alpha_vantage", "polygon", "yfinance"]
            for provider in providers:
                if provider.strip() not in valid_providers:
                    log.warning(f"Unknown data provider in DATA_PRIORITY: {provider}")
        
        # Validate numeric ranges
        self._validate_numeric_ranges()
        
        log.info("Configuration validation passed")
    
    def _validate_numeric_ranges(self):
        """Validate numeric configuration values are within reasonable ranges"""
        numeric_validations = {
            "MAX_POSITION_SIZE_PCT": (1.0, 100.0),
            "MIN_POSITION_SIZE_PCT": (0.1, 50.0),
            "RESERVE_CASH_PCT": (5.0, 50.0),
            "PER_TRADE_RISK_CAP_PCT": (1.0, 25.0),
            "PER_TRADE_ALLOC_CAP_PCT": (5.0, 50.0),
            "MAX_DAILY_LOSS_PCT": (1.0, 20.0),
            "STOP_LOSS_ATR_MULTIPLIER": (0.5, 5.0),
            "TAKE_PROFIT_ATR_MULTIPLIER": (1.0, 10.0),
            "POLL_SECONDS": (0.1, 60.0),
            "MAX_WORKERS": (1, 32),
            "CACHE_TTL_SECONDS": (1, 3600)
        }
        
        for key, (min_val, max_val) in numeric_validations.items():
            if key in self.config:
                try:
                    value = float(self.config[key])
                    if value < min_val or value > max_val:
                        log.warning(f"Configuration value {key}={value} is outside recommended range [{min_val}, {max_val}]")
                except (ValueError, TypeError):
                    log.warning(f"Configuration value {key}={self.config[key]} is not a valid number")
    
    def get_config_value(self, key: str, default: Any = None, convert_type: bool = True) -> Any:
        """
        Get configuration value with optional type conversion
        
        Args:
            key: Configuration key
            default: Default value if key not found
            convert_type: Whether to convert string values to appropriate types
        
        Returns:
            Configuration value
        """
        value = self.config.get(key, default)
        
        if not convert_type or value is None:
            return value
        
        # Type conversion for common patterns
        if isinstance(value, str):
            # Boolean conversion
            if value.lower() in ('true', 'yes', '1', 'on'):
                return True
            elif value.lower() in ('false', 'no', '0', 'off'):
                return False
            
            # Numeric conversion
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                pass
        
        return value
    
    def get_strategy_config(self) -> Dict[str, Any]:
        """Get strategy-specific configuration values"""
        strategy_mode = self.config.get("STRATEGY_MODE", "standard")
        
        prefix = strategy_mode.upper() + "_"
        strategy_config = {}
        
        for key, value in self.config.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                strategy_config[config_key] = self.get_config_value(key)
        
        return strategy_config
    
    def get_automation_config(self) -> Dict[str, Any]:
        """Get automation-specific configuration values"""
        automation_mode = self.config.get("AUTOMATION_MODE", "off")
        
        prefix = automation_mode.upper() + "_"
        automation_config = {}
        
        for key, value in self.config.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                automation_config[config_key] = self.get_config_value(key)
        
        return automation_config
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return self.get_config_value(f"{feature.upper()}_ENABLED", False)
    
    def get_performance_mode(self) -> str:
        """Get the current performance mode"""
        return self.config.get("PERFORMANCE_MODE", "standard")
    
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode"""
        return self.config.get("AUTOMATION_MODE") == "demo"
    
    def is_live_mode(self) -> bool:
        """Check if running in live mode"""
        return self.config.get("AUTOMATION_MODE") == "live"
    
    def is_alert_only_mode(self) -> bool:
        """Check if running in alert-only mode"""
        return self.config.get("AUTOMATION_MODE") == "off"
    
    def get_loaded_files(self) -> list:
        """Get list of loaded configuration files"""
        return self.loaded_files.copy()
    
    def export_config(self, filepath: str):
        """Export current configuration to a file"""
        with open(filepath, 'w') as f:
            f.write("# ETrade Strategy Configuration Export\n")
            f.write(f"# Generated at: {os.popen('date').read().strip()}\n")
            f.write(f"# Strategy Mode: {self.config.get('STRATEGY_MODE')}\n")
            f.write(f"# Automation Mode: {self.config.get('AUTOMATION_MODE')}\n")
            f.write(f"# Environment: {self.config.get('ENVIRONMENT')}\n\n")
            
            for key, value in sorted(self.config.items()):
                f.write(f"{key}={value}\n")
        
        log.info(f"Configuration exported to: {filepath}")

# Global configuration loader instance
_config_loader = None

def get_config_loader() -> ConfigLoader:
    """Get global configuration loader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader

def load_configuration(
    strategy_mode: str = "standard",
    automation_mode: str = "off",
    environment: str = "development"
) -> Dict[str, Any]:
    """Load configuration using global loader"""
    loader = get_config_loader()
    return loader.load_configuration(strategy_mode, automation_mode, environment)

def get_config_value(key: str, default: Any = None) -> Any:
    """Get configuration value using global loader"""
    loader = get_config_loader()
    return loader.get_config_value(key, default)

def is_feature_enabled(feature: str) -> bool:
    """Check if feature is enabled using global loader"""
    loader = get_config_loader()
    return loader.is_feature_enabled(feature)
