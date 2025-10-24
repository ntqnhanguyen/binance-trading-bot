"""
Strategy Orchestrator - Coordinates multiple strategies with priority
"""
from typing import Dict, List, Optional
import pandas as pd

from ..utils.logger import TradingLogger
from ..core.portfolio import Portfolio
from ..core.exchange import BinanceExchange
from ..risk.risk_manager import RiskManager
from ..strategies.base_strategy import BaseStrategy, Signal
from ..indicators.technical import TechnicalIndicators


class StrategyOrchestrator:
    """
    Orchestrates multiple trading strategies with priority system
    """
    
    def __init__(self, exchange: BinanceExchange, portfolio: Portfolio,
                 risk_manager: RiskManager):
        """
        Initialize orchestrator
        
        Args:
            exchange: Exchange instance
            portfolio: Portfolio instance
            risk_manager: Risk manager instance
        """
        self.logger = TradingLogger.get_logger(__name__)
        self.exchange = exchange
        self.portfolio = portfolio
        self.risk_manager = risk_manager
        
        # Strategy registry
        self.strategies: Dict[str, BaseStrategy] = {}
        
        # Priority order (as per document section 3)
        # 1. Exit/reduce risk
        # 2. Trend-following
        # 3. Mean reversion
        # 4. Grid
        # 5. DCA
        self.strategy_priority = []
        
        # Market regime cache
        self.market_regime: Dict[str, str] = {}
        
        self.logger.info("Strategy Orchestrator initialized")
    
    def register_strategy(self, strategy: BaseStrategy, priority: int = 5):
        """
        Register a strategy with priority
        
        Args:
            strategy: Strategy instance
            priority: Priority level (1 = highest, 5 = lowest)
        """
        self.strategies[strategy.name] = strategy
        self.strategy_priority.append((priority, strategy.name))
        self.strategy_priority.sort()  # Sort by priority
        
        self.logger.info(
            f"Strategy registered: {strategy.name} | Priority: {priority}"
        )
    
    def analyze_market_regime(self, symbol: str, df: pd.DataFrame) -> str:
        """
        Analyze market regime for a symbol
        
        Args:
            symbol: Trading pair symbol
            df: DataFrame with OHLCV and indicators
            
        Returns:
            Market regime: trending_high_vol, trending_low_vol, 
                          ranging_high_vol, ranging_low_vol
        """
        regime = TechnicalIndicators.calculate_market_regime(df)
        self.market_regime[symbol] = regime
        
        self.logger.debug(f"Market regime for {symbol}: {regime}")
        return regime
    
    def adjust_strategy_allocation(self, symbol: str, regime: str):
        """
        Adjust strategy capital allocation based on market regime
        
        Args:
            symbol: Trading pair symbol
            regime: Market regime
        """
        if regime == 'trending_low_vol':
            # Increase trend-following, decrease grid/mean reversion
            self._adjust_allocations({
                'trend': 1.2,
                'mean_reversion': 0.7,
                'grid': 0.5,
                'dca': 1.0
            })
        elif regime == 'trending_high_vol':
            # Reduce all except DCA
            self._adjust_allocations({
                'trend': 0.8,
                'mean_reversion': 0.5,
                'grid': 0.3,
                'dca': 1.0
            })
        elif regime == 'ranging_low_vol':
            # Increase grid/mean reversion, decrease trend
            self._adjust_allocations({
                'trend': 0.6,
                'mean_reversion': 1.2,
                'grid': 1.3,
                'dca': 1.0
            })
        elif regime == 'ranging_high_vol':
            # Reduce all risky strategies
            self._adjust_allocations({
                'trend': 0.5,
                'mean_reversion': 0.7,
                'grid': 0.5,
                'dca': 1.2
            })
    
    def _adjust_allocations(self, multipliers: Dict[str, float]):
        """Apply allocation multipliers to strategies"""
        for strategy_name, strategy in self.strategies.items():
            for key, multiplier in multipliers.items():
                if key.lower() in strategy_name.lower():
                    # Store original allocation if not already stored
                    if not hasattr(strategy, '_original_allocation'):
                        strategy._original_allocation = strategy.capital_allocation
                    
                    # Apply multiplier
                    strategy.capital_allocation = strategy._original_allocation * multiplier
                    
                    self.logger.debug(
                        f"Adjusted {strategy_name} allocation: "
                        f"{strategy._original_allocation:.2%} -> "
                        f"{strategy.capital_allocation:.2%}"
                    )
    
    def process_symbol(self, symbol: str, df: pd.DataFrame, 
                      current_price: float) -> List[Signal]:
        """
        Process a symbol through all strategies
        
        Args:
            symbol: Trading pair symbol
            df: DataFrame with OHLCV and indicators
            current_price: Current market price
            
        Returns:
            List of signals to execute
        """
        signals = []
        
        # 1. Check system safety (circuit breaker)
        if self.risk_manager.circuit_breaker_active:
            self.logger.warning("Circuit breaker active, no new signals")
            return signals
        
        # 2. Analyze market regime
        regime = self.analyze_market_regime(symbol, df)
        
        # 3. Adjust strategy allocations based on regime
        self.adjust_strategy_allocation(symbol, regime)
        
        # 4. Priority 1: Check exit conditions for existing positions
        exit_signals = self._check_exit_conditions(symbol, df, current_price)
        signals.extend(exit_signals)
        
        # 5. If we have exit signals, execute them first (return early)
        if exit_signals:
            self.logger.info(
                f"Exit signals generated for {symbol}, "
                f"skipping entry signals"
            )
            return signals
        
        # 6. Generate entry signals from strategies (by priority)
        entry_signals = self._generate_entry_signals(symbol, df, current_price)
        
        # 7. Resolve conflicts if multiple strategies want to enter
        if len(entry_signals) > 1:
            entry_signals = self._resolve_conflicts(entry_signals)
        
        signals.extend(entry_signals)
        
        # 8. Update trailing stops for existing positions
        self._update_trailing_stops(symbol, df, current_price)
        
        return signals
    
    def _check_exit_conditions(self, symbol: str, df: pd.DataFrame,
                               current_price: float) -> List[Signal]:
        """Check exit conditions for all strategies"""
        exit_signals = []
        
        for _, strategy_name in self.strategy_priority:
            strategy = self.strategies[strategy_name]
            
            # Check if strategy has position
            position = self.portfolio.get_position(symbol, strategy_name)
            if not position:
                continue
            
            # Check stop loss
            if strategy.check_stop_loss(symbol, current_price):
                exit_signals.append(Signal(
                    action='SELL',
                    symbol=symbol,
                    price=current_price,
                    metadata={'strategy': strategy_name, 'reason': 'stop_loss'}
                ))
                continue
            
            # Check take profit
            if strategy.check_take_profit(symbol, current_price):
                exit_signals.append(Signal(
                    action='SELL',
                    symbol=symbol,
                    price=current_price,
                    metadata={'strategy': strategy_name, 'reason': 'take_profit'}
                ))
                continue
            
            # Check strategy-specific exit conditions
            if strategy.should_exit(symbol, df, current_price):
                exit_signals.append(Signal(
                    action='SELL',
                    symbol=symbol,
                    price=current_price,
                    metadata={'strategy': strategy_name, 'reason': 'strategy_exit'}
                ))
        
        return exit_signals
    
    def _generate_entry_signals(self, symbol: str, df: pd.DataFrame,
                                current_price: float) -> List[Signal]:
        """Generate entry signals from all strategies"""
        entry_signals = []
        
        for _, strategy_name in self.strategy_priority:
            strategy = self.strategies[strategy_name]
            
            # Generate signal
            signal = strategy.generate_signal(symbol, df, current_price)
            
            if signal and signal.action in ['BUY', 'SELL']:
                entry_signals.append(signal)
        
        return entry_signals
    
    def _resolve_conflicts(self, signals: List[Signal]) -> List[Signal]:
        """
        Resolve conflicts when multiple strategies generate signals
        
        Args:
            signals: List of conflicting signals
            
        Returns:
            Resolved list of signals (typically just one)
        """
        if not signals:
            return signals
        
        # Take the first signal (highest priority strategy)
        selected_signal = signals[0]
        
        self.logger.info(
            f"Conflict resolved: Selected {selected_signal.metadata.get('strategy')} "
            f"over {len(signals)-1} other strategies"
        )
        
        return [selected_signal]
    
    def _update_trailing_stops(self, symbol: str, df: pd.DataFrame,
                               current_price: float):
        """Update trailing stops for all positions"""
        for strategy_name, strategy in self.strategies.items():
            position = self.portfolio.get_position(symbol, strategy_name)
            if position:
                strategy.update_stops(symbol, df, current_price)
    
    def execute_signals(self, signals: List[Signal]) -> int:
        """
        Execute a list of signals
        
        Args:
            signals: List of signals to execute
            
        Returns:
            Number of successfully executed signals
        """
        executed_count = 0
        
        for signal in signals:
            strategy_name = signal.metadata.get('strategy')
            
            if strategy_name and strategy_name in self.strategies:
                strategy = self.strategies[strategy_name]
                
                if strategy.execute_signal(signal):
                    executed_count += 1
        
        return executed_count
    
    def get_statistics(self) -> Dict:
        """
        Get statistics for all strategies
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'strategies': {},
            'total_signals': 0,
            'total_trades': 0,
            'total_pnl': 0.0
        }
        
        for strategy_name, strategy in self.strategies.items():
            strategy_stats = strategy.get_statistics()
            stats['strategies'][strategy_name] = strategy_stats
            stats['total_signals'] += strategy_stats['signals_generated']
            stats['total_trades'] += strategy_stats['trades_executed']
            stats['total_pnl'] += strategy_stats['total_pnl']
        
        return stats

