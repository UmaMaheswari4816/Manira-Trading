"""
F&O Market Data Provider
Handles derivatives market data, options chains, and pricing
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import random
import logging

from .fo_instruments import FOInstrumentManager, OptionType, ContractType, FuturesContract, OptionsContract

logger = logging.getLogger(__name__)

class FOMarketDataProvider:
    """F&O Market data provider with real and simulated data"""
    
    def __init__(self, use_real_data: bool = True):
        self.use_real_data = use_real_data
        self.fo_manager = FOInstrumentManager()
        self.price_cache = {}
        self.options_chains_cache = {}
        self.last_update = {}
        
        # F&O enabled symbols
        self.fo_symbols = {
            'NIFTY': '^NSEI',
            'BANKNIFTY': '^NSEBANK',
            'RELIANCE': 'RELIANCE.NS',
            'TCS': 'TCS.NS',
            'HDFCBANK': 'HDFCBANK.NS',
            'ICICIBANK': 'ICICIBANK.NS',
            'INFY': 'INFY.NS',
            'HINDUNILVR': 'HINDUNILVR.NS',
            'LT': 'LT.NS',
            'SBIN': 'SBIN.NS'
        }
        
        # Base prices for simulation
        self.base_prices = {
            'NIFTY': 19500,
            'BANKNIFTY': 44000,
            'RELIANCE': 2500,
            'TCS': 3600,
            'HDFCBANK': 1600,
            'ICICIBANK': 1000,
            'INFY': 1500,
            'HINDUNILVR': 2600,
            'LT': 2800,
            'SBIN': 550
        }
        
        self._initialize_mock_prices()
    
    def _initialize_mock_prices(self):
        """Initialize mock prices with random variation"""
        for symbol, base_price in self.base_prices.items():
            variation = random.uniform(-0.05, 0.05)  # ±5% variation
            self.price_cache[symbol] = base_price * (1 + variation)
    
    def get_spot_price(self, symbol: str) -> float:
        """Get current spot price for underlying"""
        if self.use_real_data and symbol in self.fo_symbols:
            try:
                ticker = yf.Ticker(self.fo_symbols[symbol])
                data = ticker.history(period="1d", interval="1m")
                
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                    self.price_cache[symbol] = current_price
                    self.last_update[symbol] = datetime.now()
                    return float(current_price)
            
            except Exception as e:
                logger.warning(f"Failed to fetch real data for {symbol}: {e}")
        
        # Use mock data
        if symbol in self.price_cache:
            # Add small random movement
            current_price = self.price_cache[symbol]
            movement = random.uniform(-0.02, 0.02)  # ±2% movement
            new_price = current_price * (1 + movement)
            self.price_cache[symbol] = new_price
            return new_price
        
        return self.base_prices.get(symbol, 100.0)
    
    def get_options_chain(self, underlying: str, expiry_date: Optional[datetime] = None) -> Dict:
        """Get options chain for underlying"""
        try:
            if expiry_date is None:
                # Get nearest expiry
                expiry_dates = self.fo_manager.get_expiry_dates(underlying)
                if not expiry_dates:
                    logging.warning(f"No expiry dates found for {underlying}")
                    return {}
                expiry_date = expiry_dates[0]
            
            # Check cache
            cache_key = f"{underlying}_{expiry_date.strftime('%Y%m%d')}"
            if cache_key in self.options_chains_cache:
                cached_time = self.last_update.get(cache_key, datetime.min)
                if (datetime.now() - cached_time).seconds < 60:  # Cache for 1 minute
                    return self.options_chains_cache[cache_key]
            
            # Get current spot price
            spot_price = self.get_spot_price(underlying)
            if spot_price <= 0:
                logging.warning(f"Invalid spot price for {underlying}: {spot_price}")
                return {}
            
            # Generate options chain
            options_chain = self.fo_manager.get_options_chain(underlying, spot_price, expiry_date)
            
            if not options_chain or not options_chain.get('calls') or not options_chain.get('puts'):
                logging.warning(f"Empty options chain generated for {underlying}")
                return {}
            
            # Add market data simulation
            self._simulate_options_market_data(options_chain)
            
            # Cache the result
            self.options_chains_cache[cache_key] = options_chain
            self.last_update[cache_key] = datetime.now()
            
            return options_chain
            
        except Exception as e:
            logging.error(f"Error generating options chain for {underlying}: {e}")
            return {}
    
    def _simulate_options_market_data(self, options_chain: Dict):
        """Add simulated market data to options chain"""
        for option_data in options_chain['calls'] + options_chain['puts']:
            contract = option_data['contract']
            
            # Add bid-ask spread (simplified)
            mid_price = contract.premium
            spread = max(0.05, mid_price * 0.02)  # 2% spread or minimum 0.05
            
            option_data.update({
                'bid': round(mid_price - spread/2, 2),
                'ask': round(mid_price + spread/2, 2),
                'last_price': round(mid_price + random.uniform(-spread, spread), 2),
                'volume': random.randint(0, 1000),
                'open_interest': random.randint(100, 10000),
                'change': round(random.uniform(-0.5, 0.5), 2),
                'change_percent': round(random.uniform(-10, 10), 2)
            })
    
    def get_futures_price(self, underlying: str, expiry_date: datetime) -> float:
        """Get futures price for given expiry"""
        spot_price = self.get_spot_price(underlying)
        
        # Simple futures pricing: F = S * e^(r*T)
        time_to_expiry = max(0, (expiry_date - datetime.now()).days / 365.0)
        risk_free_rate = 0.06  # 6%
        
        futures_price = spot_price * np.exp(risk_free_rate * time_to_expiry)
        
        # Add some random noise
        noise = random.uniform(-0.005, 0.005)  # ±0.5%
        futures_price *= (1 + noise)
        
        return round(futures_price, 2)
    
    def get_historical_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Get historical data for underlying"""
        if self.use_real_data and symbol in self.fo_symbols:
            try:
                ticker = yf.Ticker(self.fo_symbols[symbol])
                data = ticker.history(period=period)
                
                if not data.empty:
                    return data
            
            except Exception as e:
                logger.warning(f"Failed to fetch historical data for {symbol}: {e}")
        
        # Generate mock historical data
        return self._generate_mock_historical_data(symbol, period)
    
    def _generate_mock_historical_data(self, symbol: str, period: str) -> pd.DataFrame:
        """Generate mock historical data"""
        # Determine number of days
        if period == "1d":
            days = 1
        elif period == "5d":
            days = 5
        elif period == "1mo":
            days = 30
        elif period == "3mo":
            days = 90
        elif period == "6mo":
            days = 180
        elif period == "1y":
            days = 365
        elif period == "2y":
            days = 730
        else:
            days = 365
        
        # Generate dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Generate prices using random walk
        base_price = self.base_prices.get(symbol, 100.0)
        prices = [base_price]
        
        for _ in range(len(dates) - 1):
            # Random walk with slight upward bias
            change = random.gauss(0.001, 0.02)  # 0.1% daily return, 2% volatility
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 1.0))  # Prevent negative prices
        
        # Create OHLCV data
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            # Generate OHLC from close price
            volatility = 0.02  # 2% intraday volatility
            
            high = close * (1 + random.uniform(0, volatility))
            low = close * (1 - random.uniform(0, volatility))
            
            if i == 0:
                open_price = close
            else:
                open_price = prices[i-1] * (1 + random.uniform(-volatility/2, volatility/2))
            
            volume = random.randint(100000, 1000000)
            
            data.append({
                'Open': round(open_price, 2),
                'High': round(high, 2),
                'Low': round(low, 2),
                'Close': round(close, 2),
                'Volume': volume
            })
        
        df = pd.DataFrame(data, index=dates)
        return df
    
    def get_fo_watchlist(self) -> List[str]:
        """Get list of F&O enabled symbols"""
        return list(self.fo_symbols.keys())
    
    def get_expiry_dates(self, underlying: str) -> List[datetime]:
        """Get available expiry dates for underlying"""
        return self.fo_manager.get_expiry_dates(underlying)
    
    def calculate_implied_volatility(self, option_contract: OptionsContract, market_price: float) -> float:
        """Calculate implied volatility from market price (simplified)"""
        # This is a simplified IV calculation
        # In practice, you'd use numerical methods like Newton-Raphson
        
        spot_price = self.get_spot_price(option_contract.underlying)
        
        # Try different volatilities to find the one that matches market price
        for iv in np.arange(0.1, 1.0, 0.01):  # 10% to 100% in 1% steps
            theoretical_price = self.fo_manager.bs_calculator.calculate_option_price(
                spot_price=spot_price,
                strike_price=option_contract.strike_price,
                time_to_expiry=option_contract.time_to_expiry,
                risk_free_rate=self.fo_manager.risk_free_rate,
                volatility=iv,
                option_type=option_contract.option_type
            )
            
            if abs(theoretical_price - market_price) < 0.01:  # Within 1 paisa
                return iv
        
        # Default to 25% if no match found
        return 0.25
    
    def get_margin_requirement(self, contract, quantity: int, position_type: str) -> float:
        """Calculate margin requirement for F&O position"""
        if isinstance(contract, FuturesContract):
            # Futures margin
            return contract.margin_required * abs(quantity)
        
        elif isinstance(contract, OptionsContract):
            # Options margin
            if position_type.upper() == 'BUY':
                # Long options: pay full premium
                return contract.premium * quantity * contract.lot_size
            else:
                # Short options: margin requirement
                spot_price = self.get_spot_price(contract.underlying)
                
                # Simplified margin calculation
                # Actual SPAN margin is more complex
                premium_received = contract.premium * quantity * contract.lot_size
                
                if contract.option_type == OptionType.CALL:
                    # Short call margin
                    margin = max(
                        premium_received + 0.1 * spot_price * quantity * contract.lot_size,
                        premium_received + 0.05 * spot_price * quantity * contract.lot_size
                    )
                else:
                    # Short put margin
                    margin = max(
                        premium_received + 0.1 * contract.strike_price * quantity * contract.lot_size,
                        premium_received + 0.05 * spot_price * quantity * contract.lot_size
                    )
                
                return margin
        
        return 0.0

# Global instance
fo_market_data = FOMarketDataProvider()
