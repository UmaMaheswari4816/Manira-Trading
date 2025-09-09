"""
F&O (Futures & Options) Instruments
Handles derivatives contracts, pricing, and specifications
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math
import logging

logger = logging.getLogger(__name__)

class OptionType(Enum):
    CALL = "CALL"
    PUT = "PUT"

class ContractType(Enum):
    FUTURES = "FUTURES"
    OPTIONS = "OPTIONS"

@dataclass
class FuturesContract:
    """Futures contract specification"""
    symbol: str
    underlying: str
    expiry_date: datetime
    lot_size: int
    tick_size: float
    margin_required: float
    contract_size: int
    
    def __post_init__(self):
        self.contract_id = f"{self.underlying}{self.expiry_date.strftime('%y%m%d')}FUT"
        self.days_to_expiry = (self.expiry_date - datetime.now()).days
        self.is_expired = self.days_to_expiry <= 0
    
    def __str__(self):
        """String representation of futures contract"""
        return f"{self.underlying} {self.expiry_date.strftime('%d%b%y')} FUT"

@dataclass
class OptionsContract:
    """Options contract specification"""
    symbol: str
    underlying: str
    strike_price: float
    option_type: OptionType
    expiry_date: datetime
    lot_size: int
    tick_size: float
    premium: float
    
    def __post_init__(self):
        option_suffix = "CE" if self.option_type == OptionType.CALL else "PE"
        self.contract_id = f"{self.underlying}{self.expiry_date.strftime('%y%m%d')}{int(self.strike_price)}{option_suffix}"
        self.days_to_expiry = (self.expiry_date - datetime.now()).days
        self.time_to_expiry = self.days_to_expiry / 365.0
        self.is_expired = self.days_to_expiry <= 0
    
    def __str__(self):
        """String representation of options contract"""
        option_suffix = "CE" if self.option_type == OptionType.CALL else "PE"
        return f"{self.underlying} {self.expiry_date.strftime('%d%b%y')} {int(self.strike_price)} {option_suffix}"

class BlackScholesCalculator:
    """Black-Scholes options pricing model"""
    
    @staticmethod
    def calculate_option_price(spot_price: float, strike_price: float, time_to_expiry: float,
                              risk_free_rate: float, volatility: float, option_type: OptionType) -> float:
        """
        Calculate option price using Black-Scholes formula
        
        Args:
            spot_price: Current price of underlying
            strike_price: Strike price of option
            time_to_expiry: Time to expiry in years
            risk_free_rate: Risk-free interest rate
            volatility: Implied volatility
            option_type: CALL or PUT
            
        Returns:
            Option price
        """
        if time_to_expiry <= 0:
            if option_type == OptionType.CALL:
                return max(0, spot_price - strike_price)
            else:
                return max(0, strike_price - spot_price)
        
        try:
            # Calculate d1 and d2
            d1 = (math.log(spot_price / strike_price) + 
                  (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / (volatility * math.sqrt(time_to_expiry))
            d2 = d1 - volatility * math.sqrt(time_to_expiry)
            
            # Standard normal CDF approximation
            def norm_cdf(x):
                return 0.5 * (1 + math.erf(x / math.sqrt(2)))
            
            if option_type == OptionType.CALL:
                price = (spot_price * norm_cdf(d1) - 
                        strike_price * math.exp(-risk_free_rate * time_to_expiry) * norm_cdf(d2))
            else:  # PUT
                price = (strike_price * math.exp(-risk_free_rate * time_to_expiry) * norm_cdf(-d2) - 
                        spot_price * norm_cdf(-d1))
            
            return max(0, price)
            
        except Exception as e:
            logger.error(f"Error calculating option price: {e}")
            # Fallback to intrinsic value
            if option_type == OptionType.CALL:
                return max(0, spot_price - strike_price)
            else:
                return max(0, strike_price - spot_price)
    
    @staticmethod
    def calculate_greeks(spot_price: float, strike_price: float, time_to_expiry: float,
                        risk_free_rate: float, volatility: float, option_type: OptionType) -> Dict[str, float]:
        """
        Calculate option Greeks (Delta, Gamma, Theta, Vega)
        
        Returns:
            Dictionary with Greek values
        """
        if time_to_expiry <= 0:
            return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0}
        
        try:
            # Calculate d1 and d2
            d1 = (math.log(spot_price / strike_price) + 
                  (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / (volatility * math.sqrt(time_to_expiry))
            d2 = d1 - volatility * math.sqrt(time_to_expiry)
            
            # Standard normal PDF and CDF
            def norm_pdf(x):
                return math.exp(-0.5 * x**2) / math.sqrt(2 * math.pi)
            
            def norm_cdf(x):
                return 0.5 * (1 + math.erf(x / math.sqrt(2)))
            
            # Delta
            if option_type == OptionType.CALL:
                delta = norm_cdf(d1)
            else:
                delta = norm_cdf(d1) - 1
            
            # Gamma (same for both calls and puts)
            gamma = norm_pdf(d1) / (spot_price * volatility * math.sqrt(time_to_expiry))
            
            # Theta
            theta_common = (-spot_price * norm_pdf(d1) * volatility / (2 * math.sqrt(time_to_expiry)) -
                           risk_free_rate * strike_price * math.exp(-risk_free_rate * time_to_expiry))
            
            if option_type == OptionType.CALL:
                theta = (theta_common * norm_cdf(d2)) / 365  # Per day
            else:
                theta = (theta_common * norm_cdf(-d2) + 
                        risk_free_rate * strike_price * math.exp(-risk_free_rate * time_to_expiry)) / 365
            
            # Vega (same for both calls and puts)
            vega = spot_price * norm_pdf(d1) * math.sqrt(time_to_expiry) / 100  # Per 1% volatility change
            
            return {
                "delta": round(delta, 4),
                "gamma": round(gamma, 4),
                "theta": round(theta, 2),
                "vega": round(vega, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating Greeks: {e}")
            return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0}

class FOInstrumentManager:
    """Manager for F&O instruments and contracts"""
    
    def __init__(self):
        self.risk_free_rate = 0.06  # 6% risk-free rate
        self.default_volatility = 0.25  # 25% default volatility
        
        # Indian F&O specifications
        self.fo_specs = {
            'NIFTY': {
                'lot_size': 50,
                'tick_size': 0.05,
                'margin_percent': 10,
                'strikes_range': 100,  # Strike interval
                'underlying': 'NIFTY'
            },
            'BANKNIFTY': {
                'lot_size': 25,
                'tick_size': 0.05,
                'margin_percent': 12,
                'strikes_range': 100,
                'underlying': 'BANKNIFTY'
            },
            'RELIANCE': {
                'lot_size': 250,
                'tick_size': 0.05,
                'margin_percent': 15,
                'strikes_range': 25,
                'underlying': 'RELIANCE'
            },
            'TCS': {
                'lot_size': 150,
                'tick_size': 0.05,
                'margin_percent': 15,
                'strikes_range': 50,
                'underlying': 'TCS'
            },
            'HDFCBANK': {
                'lot_size': 550,
                'tick_size': 0.05,
                'margin_percent': 15,
                'strikes_range': 25,
                'underlying': 'HDFCBANK'
            },
            'ICICIBANK': {
                'lot_size': 1375,
                'tick_size': 0.05,
                'margin_percent': 15,
                'strikes_range': 10,
                'underlying': 'ICICIBANK'
            },
            'INFY': {
                'lot_size': 300,
                'tick_size': 0.05,
                'margin_percent': 15,
                'strikes_range': 25,
                'underlying': 'INFY'
            },
            'HINDUNILVR': {
                'lot_size': 300,
                'tick_size': 0.05,
                'margin_percent': 15,
                'strikes_range': 50,
                'underlying': 'HINDUNILVR'
            },
            'LT': {
                'lot_size': 125,
                'tick_size': 0.05,
                'margin_percent': 15,
                'strikes_range': 50,
                'underlying': 'LT'
            },
            'SBIN': {
                'lot_size': 1500,
                'tick_size': 0.05,
                'margin_percent': 15,
                'strikes_range': 10,
                'underlying': 'SBIN'
            }
        }
        
        self.bs_calculator = BlackScholesCalculator()
    
    def get_expiry_dates(self, underlying: str) -> List[datetime]:
        """Get available expiry dates for F&O contracts"""
        expiry_dates = []
        current_date = datetime.now()
        
        # Generate monthly expiries for next 6 months to ensure we have data
        for i in range(6):
            # Calculate target month
            year = current_date.year
            month = current_date.month + i
            
            while month > 12:
                month -= 12
                year += 1
            
            # Find last Thursday of the month (more accurate method)
            # Start from last day of month and work backwards
            if month == 12:
                next_month = datetime(year + 1, 1, 1)
            else:
                next_month = datetime(year, month + 1, 1)
            
            last_day = next_month - timedelta(days=1)
            
            # Find last Thursday
            days_back = (last_day.weekday() - 3) % 7
            if days_back == 0 and last_day.weekday() != 3:
                days_back = 7
            
            expiry_date = last_day - timedelta(days=days_back)
            expiry_date = expiry_date.replace(hour=15, minute=30, second=0, microsecond=0)
            
            # Only add future dates
            if expiry_date > current_date:
                expiry_dates.append(expiry_date)
        
        # Add weekly expiries for indices
        if underlying in ['NIFTY', 'BANKNIFTY']:
            # Add next 8 Thursdays for better coverage
            days_until_thursday = (3 - current_date.weekday()) % 7
            if days_until_thursday == 0:
                days_until_thursday = 7
            
            for week in range(8):
                weekly_expiry = current_date + timedelta(days=days_until_thursday + week * 7)
                weekly_expiry = weekly_expiry.replace(hour=15, minute=30, second=0, microsecond=0)
                
                # Avoid duplicates and ensure it's in the future
                if weekly_expiry > current_date and weekly_expiry not in expiry_dates:
                    expiry_dates.append(weekly_expiry)
        
        # Ensure we have at least one expiry date
        if not expiry_dates:
            # Add a fallback expiry (next Thursday)
            days_until_thursday = (3 - current_date.weekday()) % 7
            if days_until_thursday == 0:
                days_until_thursday = 7
            fallback_expiry = current_date + timedelta(days=days_until_thursday)
            fallback_expiry = fallback_expiry.replace(hour=15, minute=30, second=0, microsecond=0)
            expiry_dates.append(fallback_expiry)
        
        return sorted(expiry_dates)
    
    def generate_strike_prices(self, underlying: str, spot_price: float, expiry_date: datetime) -> List[float]:
        """Generate available strike prices for options"""
        if underlying not in self.fo_specs:
            return []
        
        strike_interval = self.fo_specs[underlying]['strikes_range']
        
        # Generate strikes around current price
        strikes = []
        
        # Round spot price to nearest strike interval
        base_strike = round(spot_price / strike_interval) * strike_interval
        
        # Generate 10 strikes above and below
        for i in range(-10, 11):
            strike = base_strike + (i * strike_interval)
            if strike > 0:
                strikes.append(float(strike))
        
        return sorted(strikes)
    
    def create_futures_contract(self, underlying: str, spot_price: float, expiry_date: datetime) -> FuturesContract:
        """Create futures contract"""
        if underlying not in self.fo_specs:
            raise ValueError(f"Unsupported underlying: {underlying}")
        
        specs = self.fo_specs[underlying]
        
        # Calculate margin required (percentage of contract value)
        contract_value = spot_price * specs['lot_size']
        margin_required = contract_value * specs['margin_percent'] / 100
        
        return FuturesContract(
            symbol=f"{underlying}FUT",
            underlying=underlying,
            expiry_date=expiry_date,
            lot_size=specs['lot_size'],
            tick_size=specs['tick_size'],
            margin_required=margin_required,
            contract_size=specs['lot_size']
        )
    
    def create_options_contract(self, underlying: str, strike_price: float, option_type: OptionType,
                               expiry_date: datetime, spot_price: float) -> OptionsContract:
        """Create options contract with calculated premium"""
        if underlying not in self.fo_specs:
            raise ValueError(f"Unsupported underlying: {underlying}")
        
        specs = self.fo_specs[underlying]
        
        # Calculate time to expiry
        time_to_expiry = max(0, (expiry_date - datetime.now()).days / 365.0)
        
        # Calculate option premium using Black-Scholes
        premium = self.bs_calculator.calculate_option_price(
            spot_price=spot_price,
            strike_price=strike_price,
            time_to_expiry=time_to_expiry,
            risk_free_rate=self.risk_free_rate,
            volatility=self.default_volatility,
            option_type=option_type
        )
        
        return OptionsContract(
            symbol=f"{underlying}OPT",
            underlying=underlying,
            strike_price=strike_price,
            option_type=option_type,
            expiry_date=expiry_date,
            lot_size=specs['lot_size'],
            tick_size=specs['tick_size'],
            premium=premium
        )
    
    def get_options_chain(self, underlying: str, spot_price: float, expiry_date: datetime) -> Dict:
        """Get complete options chain for underlying"""
        strike_prices = self.generate_strike_prices(underlying, spot_price, expiry_date)
        
        options_chain = {
            'underlying': underlying,
            'spot_price': spot_price,
            'expiry_date': expiry_date,
            'calls': [],
            'puts': []
        }
        
        for strike in strike_prices:
            # Create call option
            call_option = self.create_options_contract(
                underlying, strike, OptionType.CALL, expiry_date, spot_price
            )
            
            # Calculate Greeks for call
            call_greeks = self.bs_calculator.calculate_greeks(
                spot_price, strike, call_option.time_to_expiry,
                self.risk_free_rate, self.default_volatility, OptionType.CALL
            )
            
            # Create put option
            put_option = self.create_options_contract(
                underlying, strike, OptionType.PUT, expiry_date, spot_price
            )
            
            # Calculate Greeks for put
            put_greeks = self.bs_calculator.calculate_greeks(
                spot_price, strike, put_option.time_to_expiry,
                self.risk_free_rate, self.default_volatility, OptionType.PUT
            )
            
            options_chain['calls'].append({
                'contract': call_option,
                'greeks': call_greeks,
                'intrinsic_value': max(0, spot_price - strike),
                'time_value': call_option.premium - max(0, spot_price - strike)
            })
            
            options_chain['puts'].append({
                'contract': put_option,
                'greeks': put_greeks,
                'intrinsic_value': max(0, strike - spot_price),
                'time_value': put_option.premium - max(0, strike - spot_price)
            })
        
        return options_chain
    
    def calculate_position_pnl(self, contract, entry_price: float, current_price: float, 
                              quantity: int, position_type: str) -> Dict:
        """Calculate P&L for F&O position"""
        if isinstance(contract, FuturesContract):
            # Futures P&L
            price_diff = current_price - entry_price
            if position_type.upper() == 'SHORT':
                price_diff = -price_diff
            
            pnl = price_diff * quantity * contract.lot_size
            
        elif isinstance(contract, OptionsContract):
            # Options P&L
            premium_diff = current_price - entry_price
            if position_type.upper() == 'SHORT':
                premium_diff = -premium_diff
            
            pnl = premium_diff * quantity * contract.lot_size
        
        else:
            pnl = 0
        
        return {
            'pnl': pnl,
            'pnl_percent': (pnl / (entry_price * quantity * getattr(contract, 'lot_size', 1))) * 100 if entry_price > 0 else 0,
            'current_value': current_price * quantity * getattr(contract, 'lot_size', 1)
        }

# Global instance
fo_manager = FOInstrumentManager()
