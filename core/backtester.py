"""
Backtesting Engine for Strategy Validation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

from core.market_data import MarketDataProvider
from core.strategy_engine import StrategyEngine

logger = logging.getLogger(__name__)

class BacktestResult:
    """Backtest result container"""
    
    def __init__(self):
        self.strategy_name = ""
        self.symbol = ""
        self.start_date = None
        self.end_date = None
        self.initial_capital = 100000
        
        # Performance metrics
        self.total_return = 0.0
        self.annual_return = 0.0
        self.max_drawdown = 0.0
        self.sharpe_ratio = 0.0
        self.win_rate = 0.0
        
        # Trade statistics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.avg_win = 0.0
        self.avg_loss = 0.0
        
        # Portfolio history
        self.portfolio_values = []
        self.trades = []
        self.signals = []
        
        # Risk metrics
        self.volatility = 0.0
        self.beta = 1.0
        self.var_95 = 0.0  # Value at Risk

class Trade:
    """Individual trade record"""
    
    def __init__(self, entry_date: datetime, entry_price: float, quantity: int, side: str):
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.quantity = quantity
        self.side = side  # BUY or SELL
        
        self.exit_date = None
        self.exit_price = None
        self.pnl = 0.0
        self.pnl_pct = 0.0
        self.duration_days = 0
        
        self.is_closed = False
    
    def close_trade(self, exit_date: datetime, exit_price: float):
        """Close the trade and calculate P&L"""
        self.exit_date = exit_date
        self.exit_price = exit_price
        self.is_closed = True
        
        # Calculate P&L
        if self.side == "BUY":
            self.pnl = (exit_price - self.entry_price) * self.quantity
        else:  # SELL (short)
            self.pnl = (self.entry_price - exit_price) * self.quantity
        
        self.pnl_pct = (self.pnl / (self.entry_price * self.quantity)) * 100
        self.duration_days = (exit_date - self.entry_date).days

class Backtester:
    """Main backtesting engine"""
    
    def __init__(self):
        self.market_data = MarketDataProvider(use_real_data=True)
        self.strategy_engine = StrategyEngine()
    
    def run_backtest(self, strategy: str, symbol: str, start_date: datetime, 
                    end_date: datetime, initial_capital: float, params: Dict) -> BacktestResult:
        """Run comprehensive backtest"""
        
        result = BacktestResult()
        result.strategy_name = strategy
        result.symbol = symbol
        result.start_date = start_date
        result.end_date = end_date
        result.initial_capital = initial_capital
        
        try:
            # Get historical data
            hist_data = self._get_backtest_data(symbol, start_date, end_date)
            
            if hist_data.empty:
                logger.error(f"No historical data available for {symbol}")
                return result
            
            # Run strategy simulation
            if strategy == "MA_Crossover":
                result = self._backtest_ma_crossover(hist_data, params, result)
            elif strategy == "RSI_MeanReversion":
                result = self._backtest_rsi_strategy(hist_data, params, result)
            elif strategy == "Breakout":
                result = self._backtest_breakout_strategy(hist_data, params, result)
            else:
                logger.error(f"Unknown strategy: {strategy}")
                return result
            
            # Calculate performance metrics
            self._calculate_performance_metrics(result)
            
            logger.info(f"Backtest completed: {strategy} on {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Backtest failed for {strategy} on {symbol}: {e}")
            return result
    
    def _get_backtest_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical data for backtesting"""
        try:
            # Calculate period in days
            days = (end_date - start_date).days
            
            if days <= 30:
                period = "1mo"
            elif days <= 90:
                period = "3mo"
            elif days <= 180:
                period = "6mo"
            elif days <= 365:
                period = "1y"
            else:
                period = "2y"
            
            hist_data = self.market_data.get_historical_data(symbol, period=period)
            
            # Filter by date range
            if not hist_data.empty and 'Date' in hist_data.columns:
                hist_data['Date'] = pd.to_datetime(hist_data['Date'])
                mask = (hist_data['Date'] >= start_date) & (hist_data['Date'] <= end_date)
                hist_data = hist_data.loc[mask]
            
            return hist_data
            
        except Exception as e:
            logger.error(f"Error getting backtest data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _backtest_ma_crossover(self, data: pd.DataFrame, params: Dict, result: BacktestResult) -> BacktestResult:
        """Backtest Moving Average Crossover strategy"""
        
        fast_period = params.get("fast_ma", 10)
        slow_period = params.get("slow_ma", 50)
        
        if len(data) < slow_period:
            return result
        
        # Calculate moving averages
        data['MA_Fast'] = data['Close'].rolling(window=fast_period).mean()
        data['MA_Slow'] = data['Close'].rolling(window=slow_period).mean()
        
        # Initialize portfolio
        cash = result.initial_capital
        shares = 0
        portfolio_values = [cash]
        trades = []
        current_trade = None
        
        # Simulate trading
        for i in range(slow_period, len(data)):
            current_date = data.iloc[i]['Date']
            current_price = data.iloc[i]['Close']
            
            prev_fast = data.iloc[i-1]['MA_Fast']
            prev_slow = data.iloc[i-1]['MA_Slow']
            curr_fast = data.iloc[i]['MA_Fast']
            curr_slow = data.iloc[i]['MA_Slow']
            
            # Buy signal: Fast MA crosses above Slow MA
            if (prev_fast <= prev_slow and curr_fast > curr_slow and 
                shares == 0 and not pd.isna(curr_fast) and not pd.isna(curr_slow)):
                
                shares = int(cash / current_price)
                if shares > 0:
                    cost = shares * current_price
                    cash -= cost
                    
                    current_trade = Trade(current_date, current_price, shares, "BUY")
                    
                    result.signals.append({
                        'date': current_date,
                        'action': 'BUY',
                        'price': current_price,
                        'reason': f'Golden Cross: Fast MA crossed above Slow MA'
                    })
            
            # Sell signal: Fast MA crosses below Slow MA
            elif (prev_fast >= prev_slow and curr_fast < curr_slow and 
                  shares > 0 and not pd.isna(curr_fast) and not pd.isna(curr_slow)):
                
                proceeds = shares * current_price
                cash += proceeds
                
                if current_trade:
                    current_trade.close_trade(current_date, current_price)
                    trades.append(current_trade)
                
                shares = 0
                current_trade = None
                
                result.signals.append({
                    'date': current_date,
                    'action': 'SELL',
                    'price': current_price,
                    'reason': f'Death Cross: Fast MA crossed below Slow MA'
                })
            
            # Calculate portfolio value
            portfolio_value = cash + (shares * current_price)
            portfolio_values.append(portfolio_value)
        
        # Close any remaining position
        if current_trade and shares > 0:
            final_price = data.iloc[-1]['Close']
            final_date = data.iloc[-1]['Date']
            current_trade.close_trade(final_date, final_price)
            trades.append(current_trade)
            
            cash += shares * final_price
            shares = 0
        
        result.portfolio_values = portfolio_values
        result.trades = trades
        
        return result
    
    def _backtest_rsi_strategy(self, data: pd.DataFrame, params: Dict, result: BacktestResult) -> BacktestResult:
        """Backtest RSI Mean Reversion strategy"""
        
        rsi_period = params.get("rsi_period", 14)
        oversold = params.get("oversold", 30)
        overbought = params.get("overbought", 70)
        
        if len(data) < rsi_period + 10:
            return result
        
        # Calculate RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # Initialize portfolio
        cash = result.initial_capital
        shares = 0
        portfolio_values = [cash]
        trades = []
        current_trade = None
        
        # Simulate trading
        for i in range(rsi_period + 1, len(data)):
            current_date = data.iloc[i]['Date']
            current_price = data.iloc[i]['Close']
            current_rsi = data.iloc[i]['RSI']
            
            if pd.isna(current_rsi):
                continue
            
            # Buy signal: RSI oversold
            if current_rsi < oversold and shares == 0:
                shares = int(cash / current_price)
                if shares > 0:
                    cost = shares * current_price
                    cash -= cost
                    
                    current_trade = Trade(current_date, current_price, shares, "BUY")
                    
                    result.signals.append({
                        'date': current_date,
                        'action': 'BUY',
                        'price': current_price,
                        'reason': f'RSI Oversold: {current_rsi:.1f} < {oversold}'
                    })
            
            # Sell signal: RSI overbought
            elif current_rsi > overbought and shares > 0:
                proceeds = shares * current_price
                cash += proceeds
                
                if current_trade:
                    current_trade.close_trade(current_date, current_price)
                    trades.append(current_trade)
                
                shares = 0
                current_trade = None
                
                result.signals.append({
                    'date': current_date,
                    'action': 'SELL',
                    'price': current_price,
                    'reason': f'RSI Overbought: {current_rsi:.1f} > {overbought}'
                })
            
            # Calculate portfolio value
            portfolio_value = cash + (shares * current_price)
            portfolio_values.append(portfolio_value)
        
        # Close any remaining position
        if current_trade and shares > 0:
            final_price = data.iloc[-1]['Close']
            final_date = data.iloc[-1]['Date']
            current_trade.close_trade(final_date, final_price)
            trades.append(current_trade)
        
        result.portfolio_values = portfolio_values
        result.trades = trades
        
        return result
    
    def _backtest_breakout_strategy(self, data: pd.DataFrame, params: Dict, result: BacktestResult) -> BacktestResult:
        """Backtest Breakout strategy"""
        
        lookback_period = params.get("lookback_period", 20)
        breakout_threshold = params.get("breakout_threshold", 0.02)
        
        if len(data) < lookback_period + 10:
            return result
        
        # Initialize portfolio
        cash = result.initial_capital
        shares = 0
        portfolio_values = [cash]
        trades = []
        current_trade = None
        
        # Simulate trading
        for i in range(lookback_period, len(data)):
            current_date = data.iloc[i]['Date']
            current_price = data.iloc[i]['Close']
            current_high = data.iloc[i]['High']
            current_low = data.iloc[i]['Low']
            
            # Calculate support and resistance
            lookback_data = data.iloc[i-lookback_period:i]
            resistance = lookback_data['High'].max()
            support = lookback_data['Low'].min()
            
            # Bullish breakout
            if (current_high > resistance * (1 + breakout_threshold) and shares == 0):
                shares = int(cash / current_price)
                if shares > 0:
                    cost = shares * current_price
                    cash -= cost
                    
                    current_trade = Trade(current_date, current_price, shares, "BUY")
                    
                    result.signals.append({
                        'date': current_date,
                        'action': 'BUY',
                        'price': current_price,
                        'reason': f'Bullish Breakout: {current_price:.2f} > {resistance:.2f}'
                    })
            
            # Bearish breakdown (exit long position)
            elif (current_low < support * (1 - breakout_threshold) and shares > 0):
                proceeds = shares * current_price
                cash += proceeds
                
                if current_trade:
                    current_trade.close_trade(current_date, current_price)
                    trades.append(current_trade)
                
                shares = 0
                current_trade = None
                
                result.signals.append({
                    'date': current_date,
                    'action': 'SELL',
                    'price': current_price,
                    'reason': f'Bearish Breakdown: {current_price:.2f} < {support:.2f}'
                })
            
            # Calculate portfolio value
            portfolio_value = cash + (shares * current_price)
            portfolio_values.append(portfolio_value)
        
        # Close any remaining position
        if current_trade and shares > 0:
            final_price = data.iloc[-1]['Close']
            final_date = data.iloc[-1]['Date']
            current_trade.close_trade(final_date, final_price)
            trades.append(current_trade)
        
        result.portfolio_values = portfolio_values
        result.trades = trades
        
        return result
    
    def _calculate_performance_metrics(self, result: BacktestResult):
        """Calculate comprehensive performance metrics"""
        
        if not result.portfolio_values or len(result.portfolio_values) < 2:
            return
        
        # Basic returns
        initial_value = result.portfolio_values[0]
        final_value = result.portfolio_values[-1]
        
        result.total_return = ((final_value - initial_value) / initial_value) * 100
        
        # Annualized return
        days = (result.end_date - result.start_date).days
        if days > 0:
            result.annual_return = ((final_value / initial_value) ** (365.0 / days) - 1) * 100
        
        # Calculate returns series
        portfolio_series = pd.Series(result.portfolio_values)
        returns = portfolio_series.pct_change().dropna()
        
        # Volatility
        if len(returns) > 1:
            result.volatility = returns.std() * np.sqrt(252) * 100  # Annualized
        
        # Sharpe Ratio (assuming 5% risk-free rate)
        risk_free_rate = 0.05
        if result.volatility > 0:
            excess_return = result.annual_return - risk_free_rate
            result.sharpe_ratio = excess_return / result.volatility
        
        # Max Drawdown
        peak = initial_value
        max_drawdown = 0
        
        for value in result.portfolio_values:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        result.max_drawdown = max_drawdown
        
        # Trade statistics
        if result.trades:
            result.total_trades = len(result.trades)
            winning_trades = [t for t in result.trades if t.pnl > 0]
            losing_trades = [t for t in result.trades if t.pnl < 0]
            
            result.winning_trades = len(winning_trades)
            result.losing_trades = len(losing_trades)
            result.win_rate = (result.winning_trades / result.total_trades) * 100
            
            if winning_trades:
                result.avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades)
            
            if losing_trades:
                result.avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades)
        
        # Value at Risk (95% confidence)
        if len(returns) > 10:
            result.var_95 = np.percentile(returns, 5) * initial_value * -1
    
    def compare_strategies(self, strategies: List[Dict], symbol: str, 
                          start_date: datetime, end_date: datetime, 
                          initial_capital: float) -> Dict:
        """Compare multiple strategies on the same symbol"""
        
        results = {}
        
        for strategy_config in strategies:
            strategy_name = strategy_config['name']
            params = strategy_config['params']
            
            result = self.run_backtest(
                strategy_name, symbol, start_date, end_date, initial_capital, params
            )
            
            results[strategy_name] = {
                'total_return': result.total_return,
                'annual_return': result.annual_return,
                'max_drawdown': result.max_drawdown,
                'sharpe_ratio': result.sharpe_ratio,
                'win_rate': result.win_rate,
                'total_trades': result.total_trades,
                'volatility': result.volatility
            }
        
        return results
    
    def optimize_strategy(self, strategy: str, symbol: str, 
                         start_date: datetime, end_date: datetime,
                         param_ranges: Dict) -> Dict:
        """Optimize strategy parameters"""
        
        best_result = None
        best_params = None
        best_sharpe = -999
        
        # Simple grid search optimization
        if strategy == "MA_Crossover":
            fast_range = param_ranges.get("fast_ma", [5, 10, 15, 20])
            slow_range = param_ranges.get("slow_ma", [30, 40, 50, 60])
            
            for fast in fast_range:
                for slow in slow_range:
                    if fast >= slow:
                        continue
                    
                    params = {"fast_ma": fast, "slow_ma": slow}
                    result = self.run_backtest(strategy, symbol, start_date, end_date, 100000, params)
                    
                    if result.sharpe_ratio > best_sharpe:
                        best_sharpe = result.sharpe_ratio
                        best_params = params
                        best_result = result
        
        return {
            'best_params': best_params,
            'best_result': best_result,
            'optimization_metric': 'sharpe_ratio',
            'best_value': best_sharpe
        }
