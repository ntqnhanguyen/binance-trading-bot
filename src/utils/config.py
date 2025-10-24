"""
Configuration management for the trading bot
"""
import os
import yaml
from typing import Dict, Any
from dotenv import load_dotenv


class Config:
    """Configuration manager"""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize configuration
        
        Args:
            config_dir: Path to configuration directory
        """
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), '../../config')
        
        self.config_dir = config_dir
        self._config = {}
        
        # Load environment variables
        load_dotenv()
        
        # Load configuration files
        self._load_configs()
    
    def _load_configs(self):
        """Load all YAML configuration files"""
        config_files = ['config.yaml', 'strategies.yaml', 'risk_limits.yaml']
        
        for config_file in config_files:
            file_path = os.path.join(self.config_dir, config_file)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    if config_data:
                        self._config.update(config_data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'risk.max_daily_loss')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_env(self, key: str, default: Any = None) -> Any:
        """
        Get environment variable
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Environment variable value
        """
        return os.getenv(key, default)
    
    def get_trading_mode(self) -> str:
        """
        Get current trading mode
        
        Returns:
            Trading mode: backtest, testnet, paper, or mainnet
        """
        return self.get_env('TRADING_MODE', 'paper')
    
    def get_binance_credentials(self) -> Dict[str, str]:
        """
        Get Binance API credentials based on trading mode
        
        Returns:
            Dictionary with api_key and api_secret
        """
        mode = self.get_trading_mode()
        
        if mode == 'mainnet':
            return {
                'api_key': self.get_env('BINANCE_API_KEY'),
                'api_secret': self.get_env('BINANCE_API_SECRET'),
                'testnet': False
            }
        elif mode == 'testnet':
            return {
                'api_key': self.get_env('BINANCE_TESTNET_API_KEY'),
                'api_secret': self.get_env('BINANCE_TESTNET_API_SECRET'),
                'testnet': True
            }
        else:
            # For paper and backtest modes
            return {
                'api_key': self.get_env('BINANCE_API_KEY', ''),
                'api_secret': self.get_env('BINANCE_API_SECRET', ''),
                'testnet': False
            }
    
    def get_risk_limits(self) -> Dict[str, float]:
        """
        Get risk management limits
        
        Returns:
            Dictionary with risk limits
        """
        return {
            'max_risk_per_trade': float(self.get_env('MAX_RISK_PER_TRADE', 
                                        self.get('risk.max_risk_per_trade', 0.005))),
            'max_daily_loss': float(self.get_env('MAX_DAILY_LOSS',
                                    self.get('risk.max_daily_loss', 0.02))),
            'max_weekly_loss': float(self.get_env('MAX_WEEKLY_LOSS',
                                     self.get('risk.max_weekly_loss', 0.05))),
            'min_cash_reserve': float(self.get_env('MIN_CASH_RESERVE',
                                      self.get('risk.min_cash_reserve', 0.30))),
            'max_positions': int(self.get('risk.max_positions', 7)),
            'max_strategies_per_pair': int(self.get('risk.max_strategies_per_pair', 2))
        }
    
    def get_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific strategy
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Strategy configuration dictionary
        """
        return self.get(f'strategies.{strategy_name}', {})
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration
        
        Returns:
            Complete configuration dictionary
        """
        return self._config.copy()


# Global configuration instance
config = Config()

