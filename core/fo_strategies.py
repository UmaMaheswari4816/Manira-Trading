"""
F&O Trading Strategies
Implements common options and futures trading strategies
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

from .fo_instruments import FOInstrumentManager, OptionType, FuturesContract, OptionsContract
from .fo_market_data import FOMarketDataProvider

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    COVERED_CALL = "COVERED_CALL"
    PROTECTIVE_PUT = "PROTECTIVE_PUT"
    BULL_CALL_SPREAD = "BULL_CALL_SPREAD"
    BEAR_PUT_SPREAD = "BEAR_PUT_SPREAD"
    IRON_CONDOR = "IRON_CONDOR"
    STRADDLE = "STRADDLE"
    STRANGLE = "STRANGLE"
    BUTTERFLY = "BUTTERFLY"
    FUTURES_LONG = "FUTURES_LONG"
    FUTURES_SHORT = "FUTURES_SHORT"

@dataclass
class StrategyLeg:
    """Individual leg of a multi-leg strategy"""
    contract: Any  # FuturesContract or OptionsContract
    position_type: str  # "BUY" or "SELL"
    quantity: int
    entry_price: float
    current_price: float = 0.0
    pnl: float = 0.0

@dataclass
class FOStrategy:
    """F&O Strategy definition"""
    name: str
    strategy_type: StrategyType
    legs: List[StrategyLeg]
    underlying: str
    expiry_date: datetime
    max_profit: float
    max_loss: float
    breakeven_points: List[float]
    net_premium: float  # Net premium paid/received
    margin_required: float

class FOStrategyBuilder:
    """Builder for F&O strategies"""
    
    def __init__(self):
        self.fo_manager = FOInstrumentManager()
        self.market_data = FOMarketDataProvider()
    
    def create_covered_call(self, underlying: str, spot_price: float, expiry_date: datetime,
                           call_strike: float, stock_quantity: int = 100) -> FOStrategy:
        """
        Covered Call Strategy
        - Long stock + Short call option
        - Bullish but limited upside
        """
        # Create call option
        call_option = self.fo_manager.create_options_contract(
            underlying, call_strike, OptionType.CALL, expiry_date, spot_price
        )
        
        legs = [
            StrategyLeg(
                contract="STOCK",  # Placeholder for stock
                position_type="BUY",
                quantity=stock_quantity,
                entry_price=spot_price
            ),
            StrategyLeg(
                contract=call_option,
                position_type="SELL",
                quantity=stock_quantity // call_option.lot_size,
                entry_price=call_option.premium
            )
        ]
        
        # Calculate strategy metrics
        premium_received = call_option.premium * (stock_quantity // call_option.lot_size) * call_option.lot_size
        max_profit = (call_strike - spot_price) * stock_quantity + premium_received
        max_loss = spot_price * stock_quantity - premium_received  # If stock goes to zero
        breakeven = spot_price - (premium_received / stock_quantity)
        
        return FOStrategy(
            name="Covered Call",
            strategy_type=StrategyType.COVERED_CALL,
            legs=legs,
            underlying=underlying,
            expiry_date=expiry_date,
            max_profit=max_profit,
            max_loss=max_loss,
            breakeven_points=[breakeven],
            net_premium=-premium_received,  # Received premium
            margin_required=spot_price * stock_quantity  # Stock value
        )
    
    def create_protective_put(self, underlying: str, spot_price: float, expiry_date: datetime,
                             put_strike: float, stock_quantity: int = 100) -> FOStrategy:
        """
        Protective Put Strategy
        - Long stock + Long put option
        - Bullish with downside protection
        """
        # Create put option
        put_option = self.fo_manager.create_options_contract(
            underlying, put_strike, OptionType.PUT, expiry_date, spot_price
        )
        
        legs = [
            StrategyLeg(
                contract="STOCK",  # Placeholder for stock
                position_type="BUY",
                quantity=stock_quantity,
                entry_price=spot_price
            ),
            StrategyLeg(
                contract=put_option,
                position_type="BUY",
                quantity=stock_quantity // put_option.lot_size,
                entry_price=put_option.premium
            )
        ]
        
        # Calculate strategy metrics
        premium_paid = put_option.premium * (stock_quantity // put_option.lot_size) * put_option.lot_size
        max_profit = float('inf')  # Unlimited upside
        max_loss = (spot_price - put_strike) * stock_quantity + premium_paid
        breakeven = spot_price + (premium_paid / stock_quantity)
        
        return FOStrategy(
            name="Protective Put",
            strategy_type=StrategyType.PROTECTIVE_PUT,
            legs=legs,
            underlying=underlying,
            expiry_date=expiry_date,
            max_profit=max_profit,
            max_loss=max_loss,
            breakeven_points=[breakeven],
            net_premium=premium_paid,  # Paid premium
            margin_required=spot_price * stock_quantity + premium_paid
        )
    
    def create_bull_call_spread(self, underlying: str, spot_price: float, expiry_date: datetime,
                               lower_strike: float, upper_strike: float, quantity: int = 1) -> FOStrategy:
        """
        Bull Call Spread Strategy
        - Buy lower strike call + Sell higher strike call
        - Moderately bullish with limited risk and reward
        """
        # Create call options
        long_call = self.fo_manager.create_options_contract(
            underlying, lower_strike, OptionType.CALL, expiry_date, spot_price
        )
        short_call = self.fo_manager.create_options_contract(
            underlying, upper_strike, OptionType.CALL, expiry_date, spot_price
        )
        
        legs = [
            StrategyLeg(
                contract=long_call,
                position_type="BUY",
                quantity=quantity,
                entry_price=long_call.premium
            ),
            StrategyLeg(
                contract=short_call,
                position_type="SELL",
                quantity=quantity,
                entry_price=short_call.premium
            )
        ]
        
        # Calculate strategy metrics
        net_premium = (long_call.premium - short_call.premium) * quantity * long_call.lot_size
        max_profit = (upper_strike - lower_strike) * quantity * long_call.lot_size - net_premium
        max_loss = net_premium
        breakeven = lower_strike + (net_premium / (quantity * long_call.lot_size))
        
        return FOStrategy(
            name="Bull Call Spread",
            strategy_type=StrategyType.BULL_CALL_SPREAD,
            legs=legs,
            underlying=underlying,
            expiry_date=expiry_date,
            max_profit=max_profit,
            max_loss=max_loss,
            breakeven_points=[breakeven],
            net_premium=net_premium,
            margin_required=max_loss  # Maximum possible loss
        )
    
    def create_bear_put_spread(self, underlying: str, spot_price: float, expiry_date: datetime,
                              lower_strike: float, upper_strike: float, quantity: int = 1) -> FOStrategy:
        """
        Bear Put Spread Strategy
        - Buy higher strike put + Sell lower strike put
        - Moderately bearish with limited risk and reward
        """
        # Create put options
        long_put = self.fo_manager.create_options_contract(
            underlying, upper_strike, OptionType.PUT, expiry_date, spot_price
        )
        short_put = self.fo_manager.create_options_contract(
            underlying, lower_strike, OptionType.PUT, expiry_date, spot_price
        )
        
        legs = [
            StrategyLeg(
                contract=long_put,
                position_type="BUY",
                quantity=quantity,
                entry_price=long_put.premium
            ),
            StrategyLeg(
                contract=short_put,
                position_type="SELL",
                quantity=quantity,
                entry_price=short_put.premium
            )
        ]
        
        # Calculate strategy metrics
        net_premium = (long_put.premium - short_put.premium) * quantity * long_put.lot_size
        max_profit = (upper_strike - lower_strike) * quantity * long_put.lot_size - net_premium
        max_loss = net_premium
        breakeven = upper_strike - (net_premium / (quantity * long_put.lot_size))
        
        return FOStrategy(
            name="Bear Put Spread",
            strategy_type=StrategyType.BEAR_PUT_SPREAD,
            legs=legs,
            underlying=underlying,
            expiry_date=expiry_date,
            max_profit=max_profit,
            max_loss=max_loss,
            breakeven_points=[breakeven],
            net_premium=net_premium,
            margin_required=max_loss
        )
    
    def create_straddle(self, underlying: str, spot_price: float, expiry_date: datetime,
                       strike: float, quantity: int = 1, position_type: str = "BUY") -> FOStrategy:
        """
        Straddle Strategy
        - Buy/Sell call and put at same strike
        - Expects high/low volatility
        """
        # Create call and put options
        call_option = self.fo_manager.create_options_contract(
            underlying, strike, OptionType.CALL, expiry_date, spot_price
        )
        put_option = self.fo_manager.create_options_contract(
            underlying, strike, OptionType.PUT, expiry_date, spot_price
        )
        
        legs = [
            StrategyLeg(
                contract=call_option,
                position_type=position_type,
                quantity=quantity,
                entry_price=call_option.premium
            ),
            StrategyLeg(
                contract=put_option,
                position_type=position_type,
                quantity=quantity,
                entry_price=put_option.premium
            )
        ]
        
        # Calculate strategy metrics
        total_premium = (call_option.premium + put_option.premium) * quantity * call_option.lot_size
        
        if position_type == "BUY":
            # Long straddle
            max_profit = float('inf')  # Unlimited
            max_loss = total_premium
            breakeven_upper = strike + (total_premium / (quantity * call_option.lot_size))
            breakeven_lower = strike - (total_premium / (quantity * call_option.lot_size))
            net_premium = total_premium
            margin_required = total_premium
        else:
            # Short straddle
            max_profit = total_premium
            max_loss = float('inf')  # Unlimited
            breakeven_upper = strike + (total_premium / (quantity * call_option.lot_size))
            breakeven_lower = strike - (total_premium / (quantity * call_option.lot_size))
            net_premium = -total_premium
            margin_required = total_premium * 2  # Simplified margin
        
        return FOStrategy(
            name=f"{'Long' if position_type == 'BUY' else 'Short'} Straddle",
            strategy_type=StrategyType.STRADDLE,
            legs=legs,
            underlying=underlying,
            expiry_date=expiry_date,
            max_profit=max_profit,
            max_loss=max_loss,
            breakeven_points=[breakeven_lower, breakeven_upper],
            net_premium=net_premium,
            margin_required=margin_required
        )
    
    def create_iron_condor(self, underlying: str, spot_price: float, expiry_date: datetime,
                          put_lower: float, put_upper: float, call_lower: float, call_upper: float,
                          quantity: int = 1) -> FOStrategy:
        """
        Iron Condor Strategy
        - Sell put spread + Sell call spread
        - Neutral strategy expecting low volatility
        """
        # Create all four options
        long_put = self.fo_manager.create_options_contract(
            underlying, put_lower, OptionType.PUT, expiry_date, spot_price
        )
        short_put = self.fo_manager.create_options_contract(
            underlying, put_upper, OptionType.PUT, expiry_date, spot_price
        )
        short_call = self.fo_manager.create_options_contract(
            underlying, call_lower, OptionType.CALL, expiry_date, spot_price
        )
        long_call = self.fo_manager.create_options_contract(
            underlying, call_upper, OptionType.CALL, expiry_date, spot_price
        )
        
        legs = [
            StrategyLeg(contract=long_put, position_type="BUY", quantity=quantity, entry_price=long_put.premium),
            StrategyLeg(contract=short_put, position_type="SELL", quantity=quantity, entry_price=short_put.premium),
            StrategyLeg(contract=short_call, position_type="SELL", quantity=quantity, entry_price=short_call.premium),
            StrategyLeg(contract=long_call, position_type="BUY", quantity=quantity, entry_price=long_call.premium)
        ]
        
        # Calculate strategy metrics
        net_premium = ((short_put.premium + short_call.premium) - 
                      (long_put.premium + long_call.premium)) * quantity * long_put.lot_size
        
        max_profit = net_premium
        max_loss = min(
            (put_upper - put_lower) * quantity * long_put.lot_size - net_premium,
            (call_upper - call_lower) * quantity * long_call.lot_size - net_premium
        )
        
        breakeven_lower = put_upper + (net_premium / (quantity * long_put.lot_size))
        breakeven_upper = call_lower - (net_premium / (quantity * long_call.lot_size))
        
        return FOStrategy(
            name="Iron Condor",
            strategy_type=StrategyType.IRON_CONDOR,
            legs=legs,
            underlying=underlying,
            expiry_date=expiry_date,
            max_profit=max_profit,
            max_loss=max_loss,
            breakeven_points=[breakeven_lower, breakeven_upper],
            net_premium=-net_premium,  # Net credit received
            margin_required=abs(max_loss)
        )
    
    def create_futures_position(self, underlying: str, expiry_date: datetime, 
                               position_type: str, quantity: int) -> FOStrategy:
        """
        Simple Futures Position
        - Long or Short futures contract
        """
        spot_price = self.market_data.get_spot_price(underlying)
        futures_contract = self.fo_manager.create_futures_contract(underlying, spot_price, expiry_date)
        futures_price = self.market_data.get_futures_price(underlying, expiry_date)
        
        legs = [
            StrategyLeg(
                contract=futures_contract,
                position_type=position_type,
                quantity=quantity,
                entry_price=futures_price
            )
        ]
        
        # Futures have unlimited profit/loss potential
        max_profit = float('inf')
        max_loss = float('inf')
        
        if position_type == "BUY":
            breakeven = futures_price
        else:
            breakeven = futures_price
        
        return FOStrategy(
            name=f"{'Long' if position_type == 'BUY' else 'Short'} Futures",
            strategy_type=StrategyType.FUTURES_LONG if position_type == "BUY" else StrategyType.FUTURES_SHORT,
            legs=legs,
            underlying=underlying,
            expiry_date=expiry_date,
            max_profit=max_profit,
            max_loss=max_loss,
            breakeven_points=[breakeven],
            net_premium=0.0,  # No premium for futures
            margin_required=futures_contract.margin_required * quantity
        )
    
    def calculate_strategy_pnl(self, strategy: FOStrategy, current_spot_price: float) -> Dict:
        """Calculate current P&L for the strategy"""
        total_pnl = 0.0
        total_current_value = 0.0
        
        for leg in strategy.legs:
            if isinstance(leg.contract, str):  # Stock position
                if leg.position_type == "BUY":
                    leg_pnl = (current_spot_price - leg.entry_price) * leg.quantity
                else:
                    leg_pnl = (leg.entry_price - current_spot_price) * leg.quantity
                
                current_value = current_spot_price * leg.quantity
                
            elif isinstance(leg.contract, (FuturesContract, OptionsContract)):
                # Get current price for the contract
                if isinstance(leg.contract, FuturesContract):
                    current_price = self.market_data.get_futures_price(
                        leg.contract.underlying, leg.contract.expiry_date
                    )
                else:
                    # For options, recalculate premium based on current spot
                    current_price = self.fo_manager.bs_calculator.calculate_option_price(
                        spot_price=current_spot_price,
                        strike_price=leg.contract.strike_price,
                        time_to_expiry=leg.contract.time_to_expiry,
                        risk_free_rate=self.fo_manager.risk_free_rate,
                        volatility=self.fo_manager.default_volatility,
                        option_type=leg.contract.option_type
                    )
                
                if leg.position_type == "BUY":
                    leg_pnl = (current_price - leg.entry_price) * leg.quantity * leg.contract.lot_size
                else:
                    leg_pnl = (leg.entry_price - current_price) * leg.quantity * leg.contract.lot_size
                
                current_value = current_price * leg.quantity * leg.contract.lot_size
                
            else:
                leg_pnl = 0.0
                current_value = 0.0
            
            leg.current_price = current_price if 'current_price' in locals() else leg.entry_price
            leg.pnl = leg_pnl
            
            total_pnl += leg_pnl
            total_current_value += current_value
        
        return {
            'total_pnl': total_pnl,
            'total_current_value': total_current_value,
            'pnl_percent': (total_pnl / strategy.margin_required * 100) if strategy.margin_required > 0 else 0,
            'legs_pnl': [{'leg_index': i, 'pnl': leg.pnl, 'current_price': leg.current_price} 
                        for i, leg in enumerate(strategy.legs)]
        }
    
    def get_payoff_diagram_data(self, strategy: FOStrategy, price_range: Optional[Tuple[float, float]] = None) -> Dict:
        """Generate payoff diagram data for the strategy"""
        if price_range is None:
            # Auto-determine price range based on strategy
            spot_price = self.market_data.get_spot_price(strategy.underlying)
            price_range = (spot_price * 0.7, spot_price * 1.3)
        
        prices = np.linspace(price_range[0], price_range[1], 100)
        payoffs = []
        
        for price in prices:
            total_payoff = 0.0
            
            for leg in strategy.legs:
                if isinstance(leg.contract, str):  # Stock
                    if leg.position_type == "BUY":
                        payoff = (price - leg.entry_price) * leg.quantity
                    else:
                        payoff = (leg.entry_price - price) * leg.quantity
                
                elif isinstance(leg.contract, FuturesContract):
                    if leg.position_type == "BUY":
                        payoff = (price - leg.entry_price) * leg.quantity * leg.contract.lot_size
                    else:
                        payoff = (leg.entry_price - price) * leg.quantity * leg.contract.lot_size
                
                elif isinstance(leg.contract, OptionsContract):
                    # Calculate option payoff at expiry
                    if leg.contract.option_type == OptionType.CALL:
                        intrinsic_value = max(0, price - leg.contract.strike_price)
                    else:
                        intrinsic_value = max(0, leg.contract.strike_price - price)
                    
                    if leg.position_type == "BUY":
                        payoff = (intrinsic_value - leg.entry_price) * leg.quantity * leg.contract.lot_size
                    else:
                        payoff = (leg.entry_price - intrinsic_value) * leg.quantity * leg.contract.lot_size
                
                else:
                    payoff = 0.0
                
                total_payoff += payoff
            
            payoffs.append(total_payoff)
        
        return {
            'prices': prices.tolist(),
            'payoffs': payoffs,
            'max_profit': strategy.max_profit,
            'max_loss': strategy.max_loss,
            'breakeven_points': strategy.breakeven_points
        }

# Global instance
fo_strategy_builder = FOStrategyBuilder()
