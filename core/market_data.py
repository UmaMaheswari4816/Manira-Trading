"""
Market Data Provider
Handles real and mock market data
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
import logging

logger = logging.getLogger(__name__)

class MarketDataProvider:
    """Market data provider with real and mock data support"""
    
    def __init__(self, use_real_data: bool = True):
        self.use_real_data = use_real_data
        self.price_cache = {}
        self.last_update = {}
        
        # Indian stock symbol mapping
        self.symbol_mapping = {
            'RELIANCE': 'RELIANCE.NS',
            'TCS': 'TCS.NS', 
            'INFY': 'INFY.NS',
            'HDFCBANK': 'HDFCBANK.NS',
            'ICICIBANK': 'ICICIBANK.NS',
            'SBIN': 'SBIN.NS',
            'HINDUNILVR': 'HINDUNILVR.NS',
            'LT': 'LT.NS',
            'ITC': 'ITC.NS',
            'TATAMOTORS': 'TATAMOTORS.NS',
            'NIFTY': '^NSEI',
            'SENSEX': '^BSESN'
        }
        
        # Base prices for mock data
        self.base_prices = {
            'RELIANCE': 2500, 'TCS': 3600, 'INFY': 1500, 'HDFCBANK': 1600,
            'ICICIBANK': 1000, 'SBIN': 550, 'HINDUNILVR': 2600, 'LT': 2800,
            'ITC': 400, 'TATAMOTORS': 450, 'NIFTY': 19500, 'SENSEX': 65000
        }
        
        self._initialize_mock_prices()
    
    def _initialize_mock_prices(self):
        """Initialize mock prices with random variation"""
        for symbol in self.base_prices:
            base = self.base_prices[symbol]
            current = base * (0.95 + random.random() * 0.1)  # ±5% variation
            
            self.price_cache[symbol] = {
                'price': current,
                'open': current * (0.99 + random.random() * 0.02),
                'high': current * (1 + random.random() * 0.03),
                'low': current * (0.97 + random.random() * 0.03),
                'volume': random.randint(100000, 5000000),
                'prev_close': current * (0.98 + random.random() * 0.04),
                'last_update': datetime.now()
            }
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        if self.use_real_data:
            return self._get_real_price(symbol)
        else:
            return self._get_mock_price(symbol)
    
    def _get_real_price(self, symbol: str) -> float:
        """Get real price from Yahoo Finance"""
        try:
            # TODO: Replace with actual broker API for Indian stocks
            yf_symbol = self.symbol_mapping.get(symbol, f"{symbol}.NS")
            
            # Check cache (5 minute TTL)
            now = datetime.now()
            if (symbol in self.price_cache and 
                (now - self.price_cache[symbol]['last_update']).seconds < 300):
                return self.price_cache[symbol]['price']
            
            # Fetch from Yahoo Finance
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period="1d")
            
            if not hist.empty:
                price = float(hist['Close'].iloc[-1])
                
                # Update cache
                self.price_cache[symbol] = {
                    'price': price,
                    'open': float(hist['Open'].iloc[-1]),
                    'high': float(hist['High'].iloc[-1]),
                    'low': float(hist['Low'].iloc[-1]),
                    'volume': int(hist['Volume'].iloc[-1]),
                    'prev_close': float(hist['Close'].iloc[-2]) if len(hist) > 1 else price,
                    'last_update': now
                }
                
                return price
            else:
                logger.warning(f"No data found for {symbol}, using mock price")
                return self._get_mock_price(symbol)
                
        except Exception as e:
            logger.error(f"Error fetching real price for {symbol}: {e}")
            return self._get_mock_price(symbol)
    
    def _get_mock_price(self, symbol: str) -> float:
        """Get mock price with random walk"""
        now = datetime.now()
        
        # Update price every 15 seconds
        if (symbol not in self.last_update or 
            (now - self.last_update.get(symbol, now)).seconds > 15):
            
            if symbol in self.price_cache:
                # Random walk
                current_price = self.price_cache[symbol]['price']
                change_pct = random.gauss(0, 0.01)  # 1% volatility
                new_price = current_price * (1 + change_pct)
                
                # Update cache
                self.price_cache[symbol]['price'] = max(1.0, new_price)
                self.price_cache[symbol]['high'] = max(
                    self.price_cache[symbol]['high'], 
                    new_price
                )
                self.price_cache[symbol]['low'] = min(
                    self.price_cache[symbol]['low'], 
                    new_price
                )
                self.price_cache[symbol]['volume'] += random.randint(1000, 10000)
                
            self.last_update[symbol] = now
        
        return self.price_cache.get(symbol, {}).get('price', 100.0)
    
    def get_price_change(self, symbol: str) -> float:
        """Get price change from previous close"""
        current_price = self.get_current_price(symbol)
        
        if symbol in self.price_cache:
            prev_close = self.price_cache[symbol]['prev_close']
            return current_price - prev_close
        
        return 0.0
    
    def get_historical_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Get historical price data"""
        if self.use_real_data:
            return self._get_real_historical(symbol, period)
        else:
            return self._get_mock_historical(symbol, period)
    
    def _get_real_historical(self, symbol: str, period: str) -> pd.DataFrame:
        """Get real historical data"""
        try:
            yf_symbol = self.symbol_mapping.get(symbol, f"{symbol}.NS")
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period=period)
            
            if not hist.empty:
                # Reset index to get Date as column
                hist = hist.reset_index()
                hist.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']
                return hist[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            else:
                return self._get_mock_historical(symbol, period)
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return self._get_mock_historical(symbol, period)
    
    def _get_mock_historical(self, symbol: str, period: str) -> pd.DataFrame:
        """Generate mock historical data"""
        # Parse period
        if period == "1y":
            days = 365
        elif period == "6mo":
            days = 180
        elif period == "3mo":
            days = 90
        elif period == "1mo":
            days = 30
        else:
            days = 365
        
        # Generate dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Get base price
        base_price = self.base_prices.get(symbol, 1000)
        
        # Generate price series with random walk
        prices = []
        price = base_price
        
        for _ in dates:
            # Random walk with mean reversion
            change = random.gauss(0, 0.02)  # 2% daily volatility
            price = price * (1 + change)
            
            # Mean reversion (pull towards base price)
            if price > base_price * 1.3:  # 30% above base
                price *= 0.99
            elif price < base_price * 0.7:  # 30% below base
                price *= 1.01
            
            prices.append(price)
        
        # Generate OHLCV data
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            open_price = prices[i-1] if i > 0 else close
            high = close * (1 + random.uniform(0, 0.03))
            low = close * (1 - random.uniform(0, 0.03))
            volume = random.randint(100000, 2000000)
            
            data.append({
                'Date': date,
                'Open': open_price,
                'High': high,
                'Low': low,
                'Close': close,
                'Volume': volume
            })
        
        return pd.DataFrame(data)
    
    def get_intraday_data(self, symbol: str, interval: str = "5m") -> pd.DataFrame:
        """Get intraday data for strategy testing"""
        if self.use_real_data:
            try:
                yf_symbol = self.symbol_mapping.get(symbol, f"{symbol}.NS")
                ticker = yf.Ticker(yf_symbol)
                hist = ticker.history(period="1d", interval=interval)
                
                if not hist.empty:
                    hist = hist.reset_index()
                    return hist
                    
            except Exception as e:
                logger.error(f"Error fetching intraday data for {symbol}: {e}")
        
        # Return mock intraday data
        return self._generate_mock_intraday(symbol, interval)
    
    def _generate_mock_intraday(self, symbol: str, interval: str) -> pd.DataFrame:
        """Generate mock intraday data"""
        # Generate timestamps for today
        now = datetime.now()
        start_time = now.replace(hour=9, minute=15, second=0, microsecond=0)  # Market open
        end_time = now.replace(hour=15, minute=30, second=0, microsecond=0)   # Market close
        
        # Parse interval
        if interval == "1m":
            freq = "1T"
        elif interval == "5m":
            freq = "5T"
        elif interval == "15m":
            freq = "15T"
        else:
            freq = "5T"
        
        timestamps = pd.date_range(start=start_time, end=end_time, freq=freq)
        
        # Generate price data
        base_price = self.get_current_price(symbol)
        data = []
        price = base_price
        
        for ts in timestamps:
            # Intraday random walk (smaller moves)
            change = random.gauss(0, 0.005)  # 0.5% volatility
            price = price * (1 + change)
            
            # Generate OHLCV
            open_price = price
            high = price * (1 + random.uniform(0, 0.01))
            low = price * (1 - random.uniform(0, 0.01))
            close = low + random.random() * (high - low)
            volume = random.randint(1000, 50000)
            
            data.append({
                'Datetime': ts,
                'Open': open_price,
                'High': high,
                'Low': low,
                'Close': close,
                'Volume': volume
            })
            
            price = close
        
        return pd.DataFrame(data)
    
    def get_market_status(self) -> Dict[str, any]:
        """Get current market status"""
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        weekday = now.weekday()
        
        # Market hours: 9:15 AM to 3:30 PM, Monday to Friday
        market_open = (hour == 9 and minute >= 15) or (9 < hour < 15) or (hour == 15 and minute <= 30)
        is_market_day = weekday < 5  # Monday = 0, Friday = 4
        
        if is_market_day and market_open:
            status = "OPEN"
        elif is_market_day and hour < 9:
            status = "PRE_MARKET"
        elif is_market_day and hour > 15:
            status = "POST_MARKET"
        else:
            status = "CLOSED"
        
        return {
            "status": status,
            "is_trading": status == "OPEN",
            "next_open": "9:15 AM" if status == "CLOSED" else None
        }
    
    def get_top_movers(self, move_type: str = "gainers") -> List[Dict]:
        """Get top gainers or losers"""
        symbols = list(self.base_prices.keys())[:10]  # Top 10 stocks
        movers = []
        
        for symbol in symbols:
            current_price = self.get_current_price(symbol)
            change = self.get_price_change(symbol)
            change_pct = (change / current_price) * 100
            
            movers.append({
                'symbol': symbol,
                'price': current_price,
                'change': change,
                'change_pct': change_pct
            })
        
        # Sort by change percentage
        reverse_sort = move_type == "gainers"
        movers.sort(key=lambda x: x['change_pct'], reverse=reverse_sort)
        
        return movers[:5]  # Return top 5
