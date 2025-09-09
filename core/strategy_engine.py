"""
Strategy Engine for automated trading strategies
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

from core.market_data import MarketDataProvider
from core.utils import calculate_rsi, calculate_moving_averages

logger = logging.getLogger(__name__)

class Signal:
    """Trading signal class"""
    def __init__(self, action: str, symbol: str, price: float, confidence: float, reason: str):
        self.action = action  # BUY, SELL, HOLD
        self.symbol = symbol
        self.price = price
        self.confidence = confidence  # 0.0 to 1.0
        self.reason = reason
        self.timestamp = datetime.now()

class Strategy:
    """Base strategy class"""
    
    def __init__(self, name: str, params: Dict):
        self.name = name
        self.params = params
        self.market_data = MarketDataProvider()
    
    def generate_signal(self, symbol: str) -> Optional[Signal]:
        """Generate trading signal for symbol"""
        raise NotImplementedError("Subclasses must implement generate_signal")
    
    def backtest(self, symbol: str, start_date: datetime, end_date: datetime) -> Dict:
        """Backtest strategy on historical data"""
        raise NotImplementedError("Subclasses must implement backtest")

class MovingAverageCrossoverStrategy(Strategy):
    """Moving Average Crossover Strategy"""
    
    def __init__(self, fast_period: int = 10, slow_period: int = 50):
        params = {"fast_period": fast_period, "slow_period": slow_period}
        super().__init__("MA_Crossover", params)
    
    def generate_signal(self, symbol: str) -> Optional[Signal]:
        """Generate MA crossover signal"""
        try:
            # Get historical data
            hist_data = self.market_data.get_historical_data(symbol, period="3mo")
            
            if len(hist_data) < self.params["slow_period"]:
                return None
            
            prices = hist_data['Close']
            
            # Calculate moving averages
            fast_ma = prices.rolling(window=self.params["fast_period"]).mean()
            slow_ma = prices.rolling(window=self.params["slow_period"]).mean()
            
            # Check for crossover
            current_fast = fast_ma.iloc[-1]
            current_slow = slow_ma.iloc[-1]
            prev_fast = fast_ma.iloc[-2]
            prev_slow = slow_ma.iloc[-2]
            
            current_price = prices.iloc[-1]
            
            # Golden cross (fast MA crosses above slow MA)
            if prev_fast <= prev_slow and current_fast > current_slow:
                return Signal(
                    action="BUY",
                    symbol=symbol,
                    price=current_price,
                    confidence=0.7,
                    reason=f"Golden cross: Fast MA({self.params['fast_period']}) crossed above Slow MA({self.params['slow_period']})"
                )
            
            # Death cross (fast MA crosses below slow MA)
            elif prev_fast >= prev_slow and current_fast < current_slow:
                return Signal(
                    action="SELL",
                    symbol=symbol,
                    price=current_price,
                    confidence=0.7,
                    reason=f"Death cross: Fast MA({self.params['fast_period']}) crossed below Slow MA({self.params['slow_period']})"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating MA signal for {symbol}: {e}")
            return None
    
    def backtest(self, symbol: str, start_date: datetime, end_date: datetime) -> Dict:
        """Backtest MA crossover strategy"""
        try:
            # Get historical data
            hist_data = self.market_data.get_historical_data(symbol, period="1y")
            
            if len(hist_data) < self.params["slow_period"]:
                return {"error": "Insufficient data"}
            
            prices = hist_data['Close']
            dates = hist_data['Date']
            
            # Calculate moving averages
            fast_ma = prices.rolling(window=self.params["fast_period"]).mean()
            slow_ma = prices.rolling(window=self.params["slow_period"]).mean()
            
            # Generate signals
            signals = []
            positions = []
            portfolio_value = [100000]  # Starting with 1L
            cash = 100000
            shares = 0
            
            for i in range(self.params["slow_period"], len(prices)):
                # Check for crossover
                if (fast_ma.iloc[i-1] <= slow_ma.iloc[i-1] and 
                    fast_ma.iloc[i] > slow_ma.iloc[i] and shares == 0):
                    # Buy signal
                    shares = int(cash / prices.iloc[i])
                    cash = cash - (shares * prices.iloc[i])
                    
                    signals.append({
                        'date': dates.iloc[i],
                        'action': 'BUY',
                        'price': prices.iloc[i],
                        'shares': shares
                    })
                
                elif (fast_ma.iloc[i-1] >= slow_ma.iloc[i-1] and 
                      fast_ma.iloc[i] < slow_ma.iloc[i] and shares > 0):
                    # Sell signal
                    cash = cash + (shares * prices.iloc[i])
                    
                    signals.append({
                        'date': dates.iloc[i],
                        'action': 'SELL',
                        'price': prices.iloc[i],
                        'shares': shares
                    })
                    
                    shares = 0
                
                # Calculate portfolio value
                current_value = cash + (shares * prices.iloc[i])
                portfolio_value.append(current_value)
            
            # Calculate performance metrics
            total_return = (portfolio_value[-1] - portfolio_value[0]) / portfolio_value[0] * 100
            
            # Calculate max drawdown
            peak = portfolio_value[0]
            max_drawdown = 0
            
            for value in portfolio_value:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak * 100
                max_drawdown = max(max_drawdown, drawdown)
            
            return {
                'strategy': self.name,
                'symbol': symbol,
                'total_return': total_return,
                'max_drawdown': max_drawdown,
                'total_trades': len(signals),
                'signals': signals,
                'portfolio_value': portfolio_value,
                'final_value': portfolio_value[-1]
            }
            
        except Exception as e:
            logger.error(f"Error backtesting MA strategy for {symbol}: {e}")
            return {"error": str(e)}

class RSIMeanReversionStrategy(Strategy):
    """RSI Mean Reversion Strategy"""
    
    def __init__(self, rsi_period: int = 14, oversold: float = 30, overbought: float = 70):
        params = {"rsi_period": rsi_period, "oversold": oversold, "overbought": overbought}
        super().__init__("RSI_MeanReversion", params)
    
    def generate_signal(self, symbol: str) -> Optional[Signal]:
        """Generate RSI mean reversion signal"""
        try:
            # Get historical data
            hist_data = self.market_data.get_historical_data(symbol, period="3mo")
            
            if len(hist_data) < self.params["rsi_period"] + 5:
                return None
            
            prices = hist_data['Close']
            
            # Calculate RSI
            rsi = calculate_rsi(prices, self.params["rsi_period"])
            
            current_rsi = rsi.iloc[-1]
            current_price = prices.iloc[-1]
            
            # Oversold condition (potential buy)
            if current_rsi < self.params["oversold"]:
                return Signal(
                    action="BUY",
                    symbol=symbol,
                    price=current_price,
                    confidence=0.6,
                    reason=f"RSI oversold: {current_rsi:.1f} < {self.params['oversold']}"
                )
            
            # Overbought condition (potential sell)
            elif current_rsi > self.params["overbought"]:
                return Signal(
                    action="SELL",
                    symbol=symbol,
                    price=current_price,
                    confidence=0.6,
                    reason=f"RSI overbought: {current_rsi:.1f} > {self.params['overbought']}"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating RSI signal for {symbol}: {e}")
            return None
    
    def backtest(self, symbol: str, start_date: datetime, end_date: datetime) -> Dict:
        """Backtest RSI mean reversion strategy"""
        try:
            # Get historical data
            hist_data = self.market_data.get_historical_data(symbol, period="1y")
            
            if len(hist_data) < self.params["rsi_period"] + 10:
                return {"error": "Insufficient data"}
            
            prices = hist_data['Close']
            dates = hist_data['Date']
            
            # Calculate RSI
            rsi = calculate_rsi(prices, self.params["rsi_period"])
            
            # Generate signals
            signals = []
            portfolio_value = [100000]
            cash = 100000
            shares = 0
            
            for i in range(self.params["rsi_period"] + 1, len(prices)):
                current_rsi = rsi.iloc[i]
                
                # Buy on oversold
                if current_rsi < self.params["oversold"] and shares == 0:
                    shares = int(cash / prices.iloc[i])
                    cash = cash - (shares * prices.iloc[i])
                    
                    signals.append({
                        'date': dates.iloc[i],
                        'action': 'BUY',
                        'price': prices.iloc[i],
                        'rsi': current_rsi,
                        'shares': shares
                    })
                
                # Sell on overbought
                elif current_rsi > self.params["overbought"] and shares > 0:
                    cash = cash + (shares * prices.iloc[i])
                    
                    signals.append({
                        'date': dates.iloc[i],
                        'action': 'SELL',
                        'price': prices.iloc[i],
                        'rsi': current_rsi,
                        'shares': shares
                    })
                    
                    shares = 0
                
                # Calculate portfolio value
                current_value = cash + (shares * prices.iloc[i])
                portfolio_value.append(current_value)
            
            # Calculate performance metrics
            total_return = (portfolio_value[-1] - portfolio_value[0]) / portfolio_value[0] * 100
            
            return {
                'strategy': self.name,
                'symbol': symbol,
                'total_return': total_return,
                'total_trades': len(signals),
                'signals': signals,
                'portfolio_value': portfolio_value,
                'final_value': portfolio_value[-1]
            }
            
        except Exception as e:
            logger.error(f"Error backtesting RSI strategy for {symbol}: {e}")
            return {"error": str(e)}

class BreakoutStrategy(Strategy):
    """Breakout Trading Strategy"""
    
    def __init__(self, lookback_period: int = 20, breakout_threshold: float = 0.02):
        params = {"lookback_period": lookback_period, "breakout_threshold": breakout_threshold}
        super().__init__("Breakout", params)
    
    def generate_signal(self, symbol: str) -> Optional[Signal]:
        """Generate breakout signal"""
        try:
            # Get historical data
            hist_data = self.market_data.get_historical_data(symbol, period="3mo")
            
            if len(hist_data) < self.params["lookback_period"] + 5:
                return None
            
            prices = hist_data['Close']
            highs = hist_data['High']
            lows = hist_data['Low']
            
            # Calculate resistance and support levels
            lookback_data = prices.iloc[-(self.params["lookback_period"]+1):-1]
            resistance = lookback_data.max()
            support = lookback_data.min()
            
            current_price = prices.iloc[-1]
            current_high = highs.iloc[-1]
            current_low = lows.iloc[-1]
            
            # Bullish breakout (price breaks above resistance)
            if current_high > resistance * (1 + self.params["breakout_threshold"]):
                return Signal(
                    action="BUY",
                    symbol=symbol,
                    price=current_price,
                    confidence=0.8,
                    reason=f"Bullish breakout: Price {current_price:.2f} broke above resistance {resistance:.2f}"
                )
            
            # Bearish breakdown (price breaks below support)
            elif current_low < support * (1 - self.params["breakout_threshold"]):
                return Signal(
                    action="SELL",
                    symbol=symbol,
                    price=current_price,
                    confidence=0.8,
                    reason=f"Bearish breakdown: Price {current_price:.2f} broke below support {support:.2f}"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating breakout signal for {symbol}: {e}")
            return None

class StrategyEngine:
    """Main strategy engine for managing multiple strategies"""
    
    def __init__(self):
        self.strategies = {}
        self.active_strategies = {}
        
        # Register available strategies
        self._register_strategies()
    
    def _register_strategies(self):
        """Register available strategies"""
        self.strategies = {
            "MA_Crossover": MovingAverageCrossoverStrategy,
            "RSI_MeanReversion": RSIMeanReversionStrategy,
            "Breakout": BreakoutStrategy
        }
    
    def create_strategy(self, strategy_type: str, params: Dict) -> Optional[Strategy]:
        """Create strategy instance with parameters"""
        if strategy_type not in self.strategies:
            logger.error(f"Unknown strategy type: {strategy_type}")
            return None
        
        try:
            strategy_class = self.strategies[strategy_type]
            
            if strategy_type == "MA_Crossover":
                return strategy_class(
                    fast_period=params.get("fast_ma", 10),
                    slow_period=params.get("slow_ma", 50)
                )
            elif strategy_type == "RSI_MeanReversion":
                return strategy_class(
                    rsi_period=params.get("rsi_period", 14),
                    oversold=params.get("oversold", 30),
                    overbought=params.get("overbought", 70)
                )
            elif strategy_type == "Breakout":
                return strategy_class(
                    lookback_period=params.get("lookback_period", 20),
                    breakout_threshold=params.get("breakout_threshold", 0.02)
                )
            
        except Exception as e:
            logger.error(f"Error creating strategy {strategy_type}: {e}")
            return None
    
    def scan_for_signals(self, symbols: List[str], strategy_type: str, params: Dict) -> List[Signal]:
        """Scan multiple symbols for trading signals"""
        strategy = self.create_strategy(strategy_type, params)
        
        if not strategy:
            return []
        
        signals = []
        
        for symbol in symbols:
            try:
                signal = strategy.generate_signal(symbol)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error scanning {symbol} with {strategy_type}: {e}")
        
        return signals
    
    def get_strategy_performance(self, strategy_type: str, symbol: str, params: Dict) -> Dict:
        """Get strategy performance metrics"""
        strategy = self.create_strategy(strategy_type, params)
        
        if not strategy:
            return {"error": "Failed to create strategy"}
        
        # Backtest over last year
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        return strategy.backtest(symbol, start_date, end_date)
    
    def get_available_strategies(self) -> List[Dict]:
        """Get list of available strategies with descriptions"""
        return [
            {
                "name": "MA_Crossover",
                "display_name": "Moving Average Crossover",
                "description": "Buy when fast MA crosses above slow MA, sell when it crosses below",
                "parameters": [
                    {"name": "fast_ma", "type": "int", "default": 10, "min": 5, "max": 50},
                    {"name": "slow_ma", "type": "int", "default": 50, "min": 20, "max": 200}
                ],
                "risk_level": "Medium",
                "timeframe": "Daily"
            },
            {
                "name": "RSI_MeanReversion",
                "display_name": "RSI Mean Reversion",
                "description": "Buy when RSI is oversold, sell when overbought",
                "parameters": [
                    {"name": "rsi_period", "type": "int", "default": 14, "min": 5, "max": 30},
                    {"name": "oversold", "type": "float", "default": 30, "min": 10, "max": 40},
                    {"name": "overbought", "type": "float", "default": 70, "min": 60, "max": 90}
                ],
                "risk_level": "Low",
                "timeframe": "Intraday"
            },
            {
                "name": "Breakout",
                "display_name": "Breakout Trading",
                "description": "Trade breakouts from support and resistance levels",
                "parameters": [
                    {"name": "lookback_period", "type": "int", "default": 20, "min": 10, "max": 50},
                    {"name": "breakout_threshold", "type": "float", "default": 0.02, "min": 0.01, "max": 0.05}
                ],
                "risk_level": "High",
                "timeframe": "Swing"
            }
        ]
