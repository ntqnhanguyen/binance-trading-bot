"""
Hybrid Strategy Engine - Option A Implementation

Combines Grid Trading + DCA with dynamic spread, PnL Gate, and Stop-Loss.
Follows v1.1.2 specification with IndicatorEngine integration.

Responsibilities:
1. Collect technical signals from IndicatorEngine
2. Calculate dynamic spread (near/mid/far bands) based on ATR% + RSI adjustment
3. Plan Grid orders around ref_price
4. Plan DCA orders when oversold
5. Suggest TP trailing when overbought
6. Apply PnL Gate + Stop-Loss for state management (RUN/DEGRADED/PAUSED)

Interface (Option-A):
    on_bar(bar, equity) -> plan dict with:
        - "pnl_gate_state": "RUN" | "DEGRADED" | "PAUSED"
        - "sl_action": {"stop": bool, "reason"?: str}
        - "grid_orders": [{side, price, qty?, tag?}, ...]
        - "dca_orders": [{side, price, qty?, tag?}, ...]
        - "tp_orders": [{side, price, qty?, tag?}, ...]
        - "band": "near" | "mid" | "far"
        - "spread_pct": float
        - "ref_price": float
        - "kill_replace": bool

Note: This engine does NOT send orders. Orchestrator handles tick/lot/min_notional.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging


class HybridStrategyEngine:
    """
    Hybrid Strategy Engine combining Grid + DCA with dynamic spread
    """
    
    def __init__(self, symbol: str, policy_cfg: Dict, indicator_engine):
        """
        Initialize Hybrid Strategy Engine
        
        Args:
            symbol: Trading pair symbol
            policy_cfg: Policy configuration from YAML
            indicator_engine: IndicatorEngine instance for technical signals
        """
        self.symbol = symbol
        self.policy_cfg = policy_cfg
        self.indicator_engine = indicator_engine
        
        self.logger = logging.getLogger(f"HybridEngine.{symbol}")
        
        # State tracking
        self._last_grid_ref_price: Optional[float] = None
        self._last_grid_timestamp: Optional[datetime] = None
        self._last_dca_timestamp: Optional[datetime] = None
        self._last_dca_fill_price: Optional[float] = None
        
        # PnL Gate tracking
        self._open_price_day: Optional[float] = None
        self._equity_open: Optional[float] = None
        self._last_date: Optional[str] = None
        
        # Configuration
        self._load_config()
        
        self.logger.info(f"HybridStrategyEngine initialized for {symbol}")
    
    def _load_config(self):
        """Load configuration from policy_cfg"""
        # Spread configuration
        self.use_dynamic_spread = self.policy_cfg.get('use_dynamic_spread', True)
        self.fixed_spread_pct = self.policy_cfg.get('fixed_spread_pct', 0.5)
        
        # Band thresholds (ATR%)
        self.band_near_threshold = self.policy_cfg.get('band_near_threshold', 1.0)
        self.band_mid_threshold = self.policy_cfg.get('band_mid_threshold', 2.0)
        
        # Spread by band
        self.spread_near_pct = self.policy_cfg.get('spread_near_pct', 0.3)
        self.spread_mid_pct = self.policy_cfg.get('spread_mid_pct', 0.5)
        self.spread_far_pct = self.policy_cfg.get('spread_far_pct', 0.8)
        
        # RSI adjustment
        self.rsi_adjust_enabled = self.policy_cfg.get('rsi_adjust_enabled', True)
        self.rsi_adjust_factor = self.policy_cfg.get('rsi_adjust_factor', 0.1)
        
        # Grid configuration
        self.grid_enabled = self.policy_cfg.get('grid_enabled', True)
        self.grid_levels_per_side = self.policy_cfg.get('grid_levels_per_side', 3)
        self.grid_kill_replace_threshold_pct = self.policy_cfg.get(
            'grid_kill_replace_threshold_pct', 1.0
        )
        self.grid_min_seconds_between = self.policy_cfg.get('grid_min_seconds_between', 300)
        
        # DCA configuration
        self.dca_enabled = self.policy_cfg.get('dca_enabled', True)
        self.dca_rsi_threshold = self.policy_cfg.get('dca_rsi_threshold', 35)
        self.dca_use_ema_gate = self.policy_cfg.get('dca_use_ema_gate', True)
        self.dca_cooldown_bars = self.policy_cfg.get('dca_cooldown_bars', 5)
        self.dca_min_distance_from_last_fill_pct = self.policy_cfg.get(
            'dca_min_distance_from_last_fill_pct', 1.0
        )
        self.dca_price_offset_pct = self.policy_cfg.get('dca_price_offset_pct', 0.1)
        
        # TP configuration
        self.tp_enabled = self.policy_cfg.get('tp_enabled', True)
        self.tp_rsi_threshold = self.policy_cfg.get('tp_rsi_threshold', 65)
        self.tp_spread_near_pct = self.policy_cfg.get('tp_spread_near_pct', 0.5)
        self.tp_spread_mid_pct = self.policy_cfg.get('tp_spread_mid_pct', 0.8)
        self.tp_spread_far_pct = self.policy_cfg.get('tp_spread_far_pct', 1.2)
        
        # PnL Gate configuration
        self.gate_degraded_gap_pct = self.policy_cfg.get('gate_degraded_gap_pct', -3.0)
        self.gate_paused_gap_pct = self.policy_cfg.get('gate_paused_gap_pct', -5.0)
        self.gate_degraded_daily_pnl_pct = self.policy_cfg.get('gate_degraded_daily_pnl_pct', -2.0)
        self.gate_paused_daily_pnl_pct = self.policy_cfg.get('gate_paused_daily_pnl_pct', -4.0)
        
        # Stop-Loss configuration
        self.hard_stop_daily_pnl_pct = self.policy_cfg.get('hard_stop_daily_pnl_pct', -5.0)
        self.hard_stop_gap_pct = self.policy_cfg.get('hard_stop_gap_pct', -8.0)
        
        # Bar timeframe (for cooldown calculation)
        self.bar_timeframe = self.policy_cfg.get('bar_timeframe', '1m')
        self._bar_seconds = self._parse_timeframe_to_seconds(self.bar_timeframe)
        
        # Auto-resume configuration
        self.auto_resume_enabled = self.policy_cfg.get('auto_resume_enabled', True)
        self.resume_rsi_threshold = self.policy_cfg.get('resume_rsi_threshold', 40)  # RSI > 40 = oversold recovery
        self.resume_price_recovery_pct = self.policy_cfg.get('resume_price_recovery_pct', 2.0)  # Price recovers 2%
        self.resume_cooldown_bars = self.policy_cfg.get('resume_cooldown_bars', 60)  # Wait 60 bars after stop
        
        # Hard stop tracking
        self._hard_stop_active = False
        self._hard_stop_timestamp = None
        self._hard_stop_price = None
        self._hard_stop_reason = None
    
    def _parse_timeframe_to_seconds(self, timeframe: str) -> int:
        """Parse timeframe string to seconds"""
        if timeframe.endswith('m'):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith('h'):
            return int(timeframe[:-1]) * 3600
        elif timeframe.endswith('d'):
            return int(timeframe[:-1]) * 86400
        else:
            return 60  # Default 1 minute
    
    def on_bar(self, bar: Dict, equity: float) -> Dict:
        """
        Main entry point - process new bar and generate trading plan
        
        Args:
            bar: OHLCV bar data with timestamp
            equity: Current portfolio equity
            
        Returns:
            Plan dictionary with orders and state
        """
        # Initialize plan
        plan = {
            "pnl_gate_state": "RUN",
            "sl_action": {"stop": False},
            "grid_orders": [],
            "dca_orders": [],
            "tp_orders": [],
            "band": "mid",
            "spread_pct": self.fixed_spread_pct,
            "ref_price": bar['close'],
            "kill_replace": False
        }
        
        try:
            # Get technical signals from IndicatorEngine
            signals = self._get_technical_signals()
            
            if not signals:
                self.logger.warning("No technical signals available")
                return plan
            
            # Update ref_price from bar
            ref_price = bar['close']
            plan['ref_price'] = ref_price
            
            # Compute dynamic spread and band
            band, spread_pct = self._compute_band_and_spread(signals)
            plan['band'] = band
            plan['spread_pct'] = spread_pct
            
            # Evaluate PnL Gate and Stop-Loss
            gate_state, sl_action = self._evaluate_gate_and_sl(
                bar, equity, ref_price
            )
            plan['pnl_gate_state'] = gate_state
            plan['sl_action'] = sl_action
            
            # If hard stop triggered, return immediately
            if sl_action['stop']:
                self.logger.critical(f"Hard stop triggered: {sl_action.get('reason')}")
                return plan
            
            # Plan orders based on state
            if gate_state == "RUN":
                # Full operation
                if self.grid_enabled:
                    grid_orders, kill_replace = self._plan_grid(
                        ref_price, spread_pct, bar['timestamp']
                    )
                    plan['grid_orders'] = grid_orders
                    plan['kill_replace'] = kill_replace
                
                if self.dca_enabled:
                    dca_orders = self._plan_dca(
                        ref_price, signals, bar['timestamp']
                    )
                    plan['dca_orders'] = dca_orders
                
                if self.tp_enabled:
                    tp_orders = self._plan_tp(
                        ref_price, signals, band
                    )
                    plan['tp_orders'] = tp_orders
            
            elif gate_state == "DEGRADED":
                # Reduced operation - only DCA and TP
                if self.dca_enabled:
                    dca_orders = self._plan_dca(
                        ref_price, signals, bar['timestamp']
                    )
                    plan['dca_orders'] = dca_orders
                
                if self.tp_enabled:
                    tp_orders = self._plan_tp(
                        ref_price, signals, band
                    )
                    plan['tp_orders'] = tp_orders
            
            # PAUSED: no new orders
            
        except Exception as e:
            self.logger.error(f"Error in on_bar: {e}", exc_info=True)
        
        return plan
    
    def _get_technical_signals(self) -> Optional[Dict]:
        """
        Get technical signals from IndicatorEngine
        
        Returns:
            Dictionary with technical indicators or None
        """
        try:
            signals = self.indicator_engine.latest()
            
            if not signals:
                return None
            
            # Validate required fields
            required = ['close', 'rsi', 'atr_pct', 'ema_fast', 'ema_mid', 'ema_slow']
            for field in required:
                if field not in signals:
                    self.logger.warning(f"Missing required field: {field}")
                    return None
            
            return signals
        
        except Exception as e:
            self.logger.error(f"Error getting technical signals: {e}")
            return None
    
    def _compute_band_and_spread(self, signals: Dict) -> tuple:
        """
        Compute band (near/mid/far) and spread percentage
        
        Args:
            signals: Technical signals dictionary
            
        Returns:
            Tuple of (band, spread_pct)
        """
        if not self.use_dynamic_spread:
            return "mid", self.fixed_spread_pct
        
        try:
            atr_pct = signals.get('atr_pct', 1.0)
            rsi = signals.get('rsi', 50.0)
            
            # Determine band based on ATR%
            if atr_pct < self.band_near_threshold:
                band = "near"
                base_spread = self.spread_near_pct
            elif atr_pct < self.band_mid_threshold:
                band = "mid"
                base_spread = self.spread_mid_pct
            else:
                band = "far"
                base_spread = self.spread_far_pct
            
            # RSI adjustment
            if self.rsi_adjust_enabled:
                # RSI < 30: tighten spread (more aggressive buying)
                # RSI > 70: widen spread (more conservative)
                rsi_factor = 1.0
                if rsi < 30:
                    rsi_factor = 1.0 - self.rsi_adjust_factor
                elif rsi > 70:
                    rsi_factor = 1.0 + self.rsi_adjust_factor
                
                spread_pct = base_spread * rsi_factor
            else:
                spread_pct = base_spread
            
            # Clamp to reasonable range
            spread_pct = max(0.1, min(2.0, spread_pct))
            
            return band, spread_pct
        
        except Exception as e:
            self.logger.error(f"Error computing band and spread: {e}")
            return "mid", self.fixed_spread_pct
    
    def _plan_grid(self, ref_price: float, spread_pct: float, 
                   timestamp: datetime) -> tuple:
        """
        Plan grid orders around ref_price
        
        Args:
            ref_price: Reference price for grid center
            spread_pct: Spread percentage between levels
            timestamp: Current bar timestamp
            
        Returns:
            Tuple of (grid_orders, kill_replace)
        """
        grid_orders = []
        kill_replace = False
        
        try:
            # Check if we should kill and replace existing grid
            if self._last_grid_ref_price is not None:
                price_drift_pct = abs(ref_price - self._last_grid_ref_price) / self._last_grid_ref_price * 100
                
                if price_drift_pct > self.grid_kill_replace_threshold_pct:
                    kill_replace = True
                    self.logger.info(
                        f"Grid kill_replace triggered: drift={price_drift_pct:.2f}% > "
                        f"threshold={self.grid_kill_replace_threshold_pct}%"
                    )
            
            # Check cooldown
            if self._last_grid_timestamp is not None and not kill_replace:
                elapsed = (timestamp - self._last_grid_timestamp).total_seconds()
                if elapsed < self.grid_min_seconds_between:
                    self.logger.debug(
                        f"Grid cooldown active: {elapsed:.0f}s < {self.grid_min_seconds_between}s"
                    )
                    return grid_orders, False
            
            # Generate grid levels
            for i in range(1, self.grid_levels_per_side + 1):
                # Buy orders below ref_price
                buy_price = ref_price * (1 - (spread_pct / 100) * i)
                grid_orders.append({
                    'side': 'BUY',
                    'price': buy_price,
                    'tag': f'grid_buy_{i}'
                })
                
                # Sell orders above ref_price
                sell_price = ref_price * (1 + (spread_pct / 100) * i)
                grid_orders.append({
                    'side': 'SELL',
                    'price': sell_price,
                    'tag': f'grid_sell_{i}'
                })
            
            # Update state
            if grid_orders or kill_replace:
                self._last_grid_ref_price = ref_price
                self._last_grid_timestamp = timestamp
            
            self.logger.debug(
                f"Grid planned: {len(grid_orders)} orders, "
                f"spread={spread_pct:.3f}%, kill_replace={kill_replace}"
            )
        
        except Exception as e:
            self.logger.error(f"Error planning grid: {e}")
        
        return grid_orders, kill_replace
    
    def _plan_dca(self, ref_price: float, signals: Dict, 
                  timestamp: datetime) -> List[Dict]:
        """
        Plan DCA orders when oversold
        
        Args:
            ref_price: Current reference price
            signals: Technical signals
            timestamp: Current bar timestamp
            
        Returns:
            List of DCA orders
        """
        dca_orders = []
        
        try:
            rsi = signals.get('rsi', 50.0)
            ema_fast = signals.get('ema_fast', ref_price)
            
            # Check RSI threshold
            if rsi >= self.dca_rsi_threshold:
                return dca_orders
            
            # Optional EMA gate (price below EMA fast)
            if self.dca_use_ema_gate and ref_price >= ema_fast:
                return dca_orders
            
            # Check cooldown (bars)
            if self._last_dca_timestamp is not None:
                bars_elapsed = (timestamp - self._last_dca_timestamp).total_seconds() / self._bar_seconds
                if bars_elapsed < self.dca_cooldown_bars:
                    self.logger.debug(
                        f"DCA cooldown active: {bars_elapsed:.1f} bars < {self.dca_cooldown_bars}"
                    )
                    return dca_orders
            
            # Check distance from last fill
            if self._last_dca_fill_price is not None:
                distance_pct = abs(ref_price - self._last_dca_fill_price) / self._last_dca_fill_price * 100
                if distance_pct < self.dca_min_distance_from_last_fill_pct:
                    self.logger.debug(
                        f"DCA too close to last fill: {distance_pct:.2f}% < "
                        f"{self.dca_min_distance_from_last_fill_pct}%"
                    )
                    return dca_orders
            
            # Create DCA buy order slightly below ref_price
            dca_price = ref_price * (1 - self.dca_price_offset_pct / 100)
            
            dca_orders.append({
                'side': 'BUY',
                'price': dca_price,
                'tag': f'dca_rsi{rsi:.0f}'
            })
            
            # Update state
            self._last_dca_timestamp = timestamp
            
            self.logger.info(
                f"DCA triggered: RSI={rsi:.1f}, price={dca_price:.2f}"
            )
        
        except Exception as e:
            self.logger.error(f"Error planning DCA: {e}")
        
        return dca_orders
    
    def _plan_tp(self, ref_price: float, signals: Dict, band: str) -> List[Dict]:
        """
        Plan TP (take profit) orders when overbought
        
        Args:
            ref_price: Current reference price
            signals: Technical signals
            band: Current volatility band
            
        Returns:
            List of TP orders (suggestions for trailing)
        """
        tp_orders = []
        
        try:
            rsi = signals.get('rsi', 50.0)
            ema_fast = signals.get('ema_fast', ref_price)
            
            # Check overbought condition
            if rsi < self.tp_rsi_threshold:
                return tp_orders
            
            # Price should be above EMA fast
            if ref_price < ema_fast:
                return tp_orders
            
            # Determine TP spread based on band
            if band == "near":
                tp_spread = self.tp_spread_near_pct
            elif band == "mid":
                tp_spread = self.tp_spread_mid_pct
            else:  # far
                tp_spread = self.tp_spread_far_pct
            
            # Create TP sell order above ref_price
            tp_price = ref_price * (1 + tp_spread / 100)
            
            tp_orders.append({
                'side': 'SELL',
                'price': tp_price,
                'tag': f'tp_rsi{rsi:.0f}_band{band}'
            })
            
            self.logger.info(
                f"TP triggered: RSI={rsi:.1f}, band={band}, price={tp_price:.2f}"
            )
        
        except Exception as e:
            self.logger.error(f"Error planning TP: {e}")
        
        return tp_orders
    
    def _evaluate_gate_and_sl(self, bar: Dict, equity: float, 
                              ref_price: float) -> tuple:
        """
        Evaluate PnL Gate state and Stop-Loss action
        
        Args:
            bar: Current bar with timestamp
            equity: Current portfolio equity
            ref_price: Current reference price
            
        Returns:
            Tuple of (gate_state, sl_action)
        """
        gate_state = "RUN"
        sl_action = {"stop": False}
        
        try:
            timestamp = bar['timestamp']
            current_date = timestamp.strftime('%Y-%m-%d')
            
            # Reset daily tracking on new day
            if self._last_date != current_date:
                self._open_price_day = ref_price
                self._equity_open = equity
                self._last_date = current_date
                self.logger.info(
                    f"New trading day: date={current_date}, "
                    f"open_price={ref_price:.2f}, equity={equity:.2f}"
                )
            
            # Calculate Gap% (price vs open price)
            if self._open_price_day is not None and self._open_price_day > 0:
                gap_pct = ((ref_price - self._open_price_day) / self._open_price_day) * 100
            else:
                gap_pct = 0.0
            
            # Calculate Daily PnL%
            if self._equity_open is not None and self._equity_open > 0:
                daily_pnl_pct = ((equity - self._equity_open) / self._equity_open) * 100
            else:
                daily_pnl_pct = 0.0
            
            # Check if we're in hard stop state
            if self._hard_stop_active:
                # Check if we can resume
                if self.auto_resume_enabled and self._can_resume(bar, ref_price):
                    self.logger.warning(
                        f"Auto-resume triggered: Good market signal detected. "
                        f"Resuming trading from hard stop."
                    )
                    self._hard_stop_active = False
                    self._hard_stop_timestamp = None
                    self._hard_stop_price = None
                    self._hard_stop_reason = None
                    # Continue to normal gate evaluation
                else:
                    # Still in hard stop
                    sl_action = {
                        "stop": True,
                        "reason": f"Hard stop active: {self._hard_stop_reason}"
                    }
                    return "PAUSED", sl_action
            
            # Check hard stop conditions (if not already stopped)
            if daily_pnl_pct <= self.hard_stop_daily_pnl_pct:
                self._activate_hard_stop(
                    timestamp=timestamp,
                    price=ref_price,
                    reason=f"Daily PnL {daily_pnl_pct:.2f}% <= {self.hard_stop_daily_pnl_pct}%"
                )
                sl_action = {
                    "stop": True,
                    "reason": self._hard_stop_reason
                }
                return "PAUSED", sl_action
            
            if gap_pct <= self.hard_stop_gap_pct:
                self._activate_hard_stop(
                    timestamp=timestamp,
                    price=ref_price,
                    reason=f"Gap {gap_pct:.2f}% <= {self.hard_stop_gap_pct}%"
                )
                sl_action = {
                    "stop": True,
                    "reason": self._hard_stop_reason
                }
                return "PAUSED", sl_action
            
            # Determine gate state
            if (daily_pnl_pct <= self.gate_paused_daily_pnl_pct or 
                gap_pct <= self.gate_paused_gap_pct):
                gate_state = "PAUSED"
            elif (daily_pnl_pct <= self.gate_degraded_daily_pnl_pct or 
                  gap_pct <= self.gate_degraded_gap_pct):
                gate_state = "DEGRADED"
            else:
                gate_state = "RUN"
            
            self.logger.debug(
                f"Gate evaluation: state={gate_state}, "
                f"gap={gap_pct:.2f}%, daily_pnl={daily_pnl_pct:.2f}%"
            )
        
        except Exception as e:
            self.logger.error(f"Error evaluating gate and SL: {e}")
        
        return gate_state, sl_action
    
    def notify_dca_fill(self, fill_price: float):
        """
        Notify engine of DCA fill (for distance tracking)
        
        Args:
            fill_price: Price at which DCA order was filled
        """
        self._last_dca_fill_price = fill_price
        self.logger.info(f"DCA fill recorded at {fill_price:.2f}")
    
    def _activate_hard_stop(self, timestamp: datetime, price: float, reason: str):
        """
        Activate hard stop
        
        Args:
            timestamp: Time when hard stop triggered
            price: Price when hard stop triggered
            reason: Reason for hard stop
        """
        self._hard_stop_active = True
        self._hard_stop_timestamp = timestamp
        self._hard_stop_price = price
        self._hard_stop_reason = reason
        
        self.logger.critical(
            f"Hard stop activated: {reason} at price=${price:.2f}"
        )
    
    def _can_resume(self, bar: Dict, current_price: float) -> bool:
        """
        Check if trading can resume after hard stop
        
        Conditions for resume:
        1. Cooldown period passed (default 60 bars)
        2. RSI recovered above threshold (default 40)
        3. Price recovered by X% from stop price (default 2%)
        
        Args:
            bar: Current bar with timestamp and indicators
            current_price: Current market price
            
        Returns:
            True if can resume, False otherwise
        """
        if not self._hard_stop_active or self._hard_stop_timestamp is None:
            return False
        
        try:
            # Get signals
            signals = self.indicator_engine.latest()
            if not signals:
                return False
            
            # Check cooldown period
            timestamp = bar['timestamp']
            bars_since_stop = (timestamp - self._hard_stop_timestamp).total_seconds() / self._bar_seconds
            
            if bars_since_stop < self.resume_cooldown_bars:
                self.logger.debug(
                    f"Resume cooldown: {bars_since_stop:.0f}/{self.resume_cooldown_bars} bars"
                )
                return False
            
            # Check RSI recovery
            rsi = signals.get('rsi', 50)
            if rsi <= self.resume_rsi_threshold:
                self.logger.debug(
                    f"Resume RSI check: {rsi:.1f} <= {self.resume_rsi_threshold}"
                )
                return False
            
            # Check price recovery
            if self._hard_stop_price is not None and self._hard_stop_price > 0:
                price_change_pct = ((current_price - self._hard_stop_price) / self._hard_stop_price) * 100
                
                if price_change_pct < self.resume_price_recovery_pct:
                    self.logger.debug(
                        f"Resume price check: {price_change_pct:+.2f}% < {self.resume_price_recovery_pct}%"
                    )
                    return False
            
            # All conditions met
            self.logger.info(
                f"Resume conditions met: "
                f"cooldown={bars_since_stop:.0f} bars, "
                f"RSI={rsi:.1f}, "
                f"price_recovery={price_change_pct:+.2f}%"
            )
            return True
        
        except Exception as e:
            self.logger.error(f"Error checking resume conditions: {e}")
            return False
    
    def get_state(self) -> Dict:
        """
        Get current engine state
        
        Returns:
            Dictionary with state information
        """
        return {
            'symbol': self.symbol,
            'last_grid_ref_price': self._last_grid_ref_price,
            'last_grid_timestamp': self._last_grid_timestamp,
            'last_dca_timestamp': self._last_dca_timestamp,
            'last_dca_fill_price': self._last_dca_fill_price,
            'open_price_day': self._open_price_day,
            'equity_open': self._equity_open,
            'last_date': self._last_date,
            'hard_stop_active': self._hard_stop_active,
            'hard_stop_timestamp': self._hard_stop_timestamp,
            'hard_stop_price': self._hard_stop_price,
            'hard_stop_reason': self._hard_stop_reason
        }

