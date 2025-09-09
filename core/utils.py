"""
Utility functions for the trading simulator
"""

import logging
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
import numpy as np

def setup_logging():
    """Setup application logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('trading_simulator.log'),
            logging.StreamHandler()
        ]
    )

def format_currency(amount: float) -> str:
    """Format amount as Indian currency"""
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.2f}Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.2f}L"
    else:
        return f"₹{amount:,.2f}"

def format_percentage(value: float) -> str:
    """Format percentage with appropriate sign and color"""
    if value > 0:
        return f"+{value:.2f}%"
    elif value < 0:
        return f"{value:.2f}%"
    else:
        return "0.00%"

def get_color_for_pnl(pnl: float) -> str:
    """Get color for P&L display"""
    if pnl > 0:
        return "#28a745"  # Green
    elif pnl < 0:
        return "#dc3545"  # Red
    else:
        return "#6c757d"  # Gray

def calculate_returns(prices: List[float]) -> List[float]:
    """Calculate returns from price series"""
    if len(prices) < 2:
        return []
    
    returns = []
    for i in range(1, len(prices)):
        ret = (prices[i] - prices[i-1]) / prices[i-1]
        returns.append(ret)
    
    return returns

def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.05) -> float:
    """Calculate Sharpe ratio"""
    if not returns or len(returns) < 2:
        return 0.0
    
    excess_returns = [r - risk_free_rate/252 for r in returns]  # Daily risk-free rate
    
    mean_excess_return = np.mean(excess_returns)
    std_excess_return = np.std(excess_returns)
    
    if std_excess_return == 0:
        return 0.0
    
    return (mean_excess_return / std_excess_return) * np.sqrt(252)  # Annualized

def calculate_max_drawdown(portfolio_values: List[float]) -> float:
    """Calculate maximum drawdown"""
    if len(portfolio_values) < 2:
        return 0.0
    
    peak = portfolio_values[0]
    max_drawdown = 0.0
    
    for value in portfolio_values:
        if value > peak:
            peak = value
        
        drawdown = (peak - value) / peak
        max_drawdown = max(max_drawdown, drawdown)
    
    return max_drawdown * 100  # Return as percentage

def calculate_volatility(returns: List[float]) -> float:
    """Calculate annualized volatility"""
    if not returns or len(returns) < 2:
        return 0.0
    
    return np.std(returns) * np.sqrt(252) * 100  # Annualized percentage

def validate_trade_params(symbol: str, quantity: int, price: float) -> tuple:
    """Validate trading parameters"""
    errors = []
    
    if not symbol or not symbol.strip():
        errors.append("Symbol is required")
    
    if quantity <= 0:
        errors.append("Quantity must be positive")
    
    if price <= 0:
        errors.append("Price must be positive")
    
    return len(errors) == 0, errors

def time_ago(timestamp: datetime) -> str:
    """Get human readable time difference"""
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

def add_notification(message: str, type: str = "info"):
    """Add notification to session state"""
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []
    
    st.session_state.notifications.append({
        'message': message,
        'type': type,
        'timestamp': datetime.now()
    })

def show_notifications():
    """Display notifications as toasts"""
    if 'notifications' in st.session_state and st.session_state.notifications:
        for notification in st.session_state.notifications:
            if notification['type'] == 'success':
                st.toast(notification['message'], icon='✅')
            elif notification['type'] == 'error':
                st.toast(notification['message'], icon='❌')
            elif notification['type'] == 'warning':
                st.toast(notification['message'], icon='⚠️')
            else:
                st.toast(notification['message'], icon='ℹ️')
        
        # Clear notifications after showing
        st.session_state.notifications = []

def calculate_position_size(capital: float, risk_per_trade: float, entry_price: float, stop_loss: float) -> int:
    """Calculate position size based on risk management"""
    if stop_loss >= entry_price or risk_per_trade <= 0:
        return 0
    
    risk_amount = capital * (risk_per_trade / 100)
    risk_per_share = entry_price - stop_loss
    
    if risk_per_share <= 0:
        return 0
    
    position_size = int(risk_amount / risk_per_share)
    return max(1, position_size)

def calculate_support_resistance(prices: pd.Series, window: int = 20) -> tuple:
    """Calculate support and resistance levels"""
    if len(prices) < window:
        return None, None
    
    # Simple support/resistance calculation
    recent_prices = prices.tail(window)
    
    support = recent_prices.min()
    resistance = recent_prices.max()
    
    return support, resistance

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator"""
    if len(prices) < period + 1:
        return pd.Series([50] * len(prices), index=prices.index)
    
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_moving_averages(prices: pd.Series, windows: List[int]) -> Dict[str, pd.Series]:
    """Calculate multiple moving averages"""
    mas = {}
    
    for window in windows:
        if len(prices) >= window:
            mas[f'MA_{window}'] = prices.rolling(window=window).mean()
        else:
            mas[f'MA_{window}'] = pd.Series([prices.iloc[-1]] * len(prices), index=prices.index)
    
    return mas

def detect_chart_patterns(prices: pd.Series, volumes: pd.Series = None) -> List[Dict]:
    """Simple chart pattern detection"""
    patterns = []
    
    if len(prices) < 20:
        return patterns
    
    recent_prices = prices.tail(20)
    
    # Simple breakout detection
    resistance = recent_prices.iloc[:-5].max()
    current_price = recent_prices.iloc[-1]
    
    if current_price > resistance * 1.02:  # 2% breakout
        patterns.append({
            'pattern': 'Breakout',
            'level': resistance,
            'confidence': 'Medium',
            'signal': 'Bullish'
        })
    
    # Simple support test
    support = recent_prices.iloc[:-5].min()
    
    if current_price < support * 1.02 and current_price > support * 0.98:
        patterns.append({
            'pattern': 'Support Test',
            'level': support,
            'confidence': 'Low',
            'signal': 'Neutral'
        })
    
    return patterns

def export_to_csv(data: List[Dict], filename: str) -> str:
    """Export data to CSV format"""
    df = pd.DataFrame(data)
    
    if not df.empty:
        csv_string = df.to_csv(index=False)
        return csv_string
    
    return ""

def calculate_portfolio_beta(portfolio_returns: List[float], market_returns: List[float]) -> float:
    """Calculate portfolio beta relative to market"""
    if len(portfolio_returns) != len(market_returns) or len(portfolio_returns) < 10:
        return 1.0  # Default beta
    
    # Calculate covariance and variance
    portfolio_array = np.array(portfolio_returns)
    market_array = np.array(market_returns)
    
    covariance = np.cov(portfolio_array, market_array)[0][1]
    market_variance = np.var(market_array)
    
    if market_variance == 0:
        return 1.0
    
    beta = covariance / market_variance
    return beta

def get_trading_session_info() -> Dict[str, Any]:
    """Get current trading session information"""
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    weekday = now.weekday()
    
    # Indian market hours: 9:15 AM to 3:30 PM, Monday to Friday
    market_open_time = 9 * 60 + 15  # 9:15 AM in minutes
    market_close_time = 15 * 60 + 30  # 3:30 PM in minutes
    current_time = hour * 60 + minute
    
    is_market_day = weekday < 5  # Monday = 0, Friday = 4
    is_market_hours = market_open_time <= current_time <= market_close_time
    
    if is_market_day and is_market_hours:
        session = "MARKET_OPEN"
        status_color = "#28a745"
        message = "Market is open for trading"
    elif is_market_day and current_time < market_open_time:
        session = "PRE_MARKET"
        status_color = "#ffc107"
        message = "Pre-market session"
    elif is_market_day and current_time > market_close_time:
        session = "POST_MARKET"
        status_color = "#17a2b8"
        message = "Post-market session"
    else:
        session = "MARKET_CLOSED"
        status_color = "#dc3545"
        message = "Market is closed"
    
    return {
        "session": session,
        "is_trading_hours": is_market_hours and is_market_day,
        "status_color": status_color,
        "message": message,
        "next_open": "Monday 9:15 AM" if not is_market_day else "9:15 AM"
    }

# Constants
INDIAN_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", 
    "KOTAKBANK", "SBIN", "BHARTIARTL", "ITC", "LT", "ASIANPAINT",
    "AXISBANK", "MARUTI", "SUNPHARMA", "ULTRACEMCO", "WIPRO", "NESTLEIND",
    "HCLTECH", "TATAMOTORS", "POWERGRID", "NTPC", "COALINDIA", "DRREDDY",
    "JSWSTEEL", "TECHM", "INDUSINDBK", "ADANIPORTS", "TATASTEEL", "GRASIM"
]

SECTORS = {
    "Banking": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "INDUSINDBK"],
    "IT": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM"],
    "Energy": ["RELIANCE", "POWERGRID", "NTPC", "COALINDIA"],
    "Auto": ["MARUTI", "TATAMOTORS"],
    "Pharma": ["SUNPHARMA", "DRREDDY"],
    "FMCG": ["HINDUNILVR", "ITC", "NESTLEIND"],
    "Materials": ["ULTRACEMCO", "JSWSTEEL", "TATASTEEL", "GRASIM"],
    "Infrastructure": ["LT", "ADANIPORTS"],
    "Telecom": ["BHARTIARTL"],
    "Paints": ["ASIANPAINT"]
}
