"""
F&O Portfolio Manager
Handles F&O positions, margin calculations, and P&L tracking
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
import json

from .fo_instruments import FOInstrumentManager, FuturesContract, OptionsContract, OptionType
from .fo_market_data import FOMarketDataProvider
from .fo_strategies import FOStrategy, FOStrategyBuilder, StrategyLeg

logger = logging.getLogger(__name__)

class FOPosition:
    """Represents a F&O position"""
    
    def __init__(self, contract: Any, position_type: str, quantity: int, 
                 entry_price: float, entry_time: datetime):
        self.contract = contract
        self.position_type = position_type  # "BUY" or "SELL"
        self.quantity = quantity
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.current_price = entry_price
        self.unrealized_pnl = 0.0
        self.margin_used = 0.0
        
    def update_current_price(self, current_price: float):
        """Update current price and calculate unrealized P&L"""
        self.current_price = current_price
        
        if isinstance(self.contract, (FuturesContract, OptionsContract)):
            lot_size = self.contract.lot_size
        else:
            lot_size = 1  # For stocks
        
        if self.position_type == "BUY":
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity * lot_size
        else:
            self.unrealized_pnl = (self.entry_price - current_price) * self.quantity * lot_size
    
    def to_dict(self) -> Dict:
        """Convert position to dictionary for storage"""
        contract_data = {}
        if hasattr(self.contract, '__dict__'):
            contract_data = {k: v for k, v in self.contract.__dict__.items() 
                           if not k.startswith('_')}
            # Handle datetime serialization
            for key, value in contract_data.items():
                if isinstance(value, datetime):
                    contract_data[key] = value.isoformat()
        
        return {
            'contract_type': type(self.contract).__name__,
            'contract_data': contract_data,
            'position_type': self.position_type,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time.isoformat(),
            'current_price': self.current_price,
            'unrealized_pnl': self.unrealized_pnl,
            'margin_used': self.margin_used
        }

class FOPortfolioManager:
    """Enhanced portfolio manager for F&O trading"""
    
    def __init__(self, initial_capital: float = 1000000.0):
        self.initial_capital = initial_capital
        self.fo_manager = FOInstrumentManager()
        self.market_data = FOMarketDataProvider()
        self.strategy_builder = FOStrategyBuilder()
        
        # Initialize session state for F&O
        self._initialize_fo_session_state()
    
    def _initialize_fo_session_state(self):
        """Initialize F&O-specific session state"""
        if 'fo_positions' not in st.session_state:
            st.session_state.fo_positions = {}
        
        if 'fo_strategies' not in st.session_state:
            st.session_state.fo_strategies = {}
        
        if 'fo_margin_used' not in st.session_state:
            st.session_state.fo_margin_used = 0.0
        
        if 'fo_trade_history' not in st.session_state:
            st.session_state.fo_trade_history = []
    
    def get_available_margin(self) -> float:
        """Get available margin for F&O trading"""
        current_cash = st.session_state.get('current_capital', self.initial_capital)
        margin_used = st.session_state.get('fo_margin_used', 0.0)
        return current_cash - margin_used
    
    def place_fo_order(self, contract: Any, position_type: str, quantity: int, 
                       price: float) -> Tuple[bool, str]:
        """Place F&O order"""
        try:
            # Calculate margin requirement
            margin_required = self.market_data.get_margin_requirement(
                contract, quantity, position_type
            )
            
            available_margin = self.get_available_margin()
            
            # Check margin availability
            if margin_required > available_margin:
                return False, f"Insufficient margin. Required: ₹{margin_required:,.2f}, Available: ₹{available_margin:,.2f}"
            
            # Create position
            position = FOPosition(
                contract=contract,
                position_type=position_type,
                quantity=quantity,
                entry_price=price,
                entry_time=datetime.now()
            )
            position.margin_used = margin_required
            
            # Generate position ID
            if isinstance(contract, FuturesContract):
                position_id = f"FUT_{contract.underlying}_{contract.expiry_date.strftime('%y%m%d')}_{position_type}_{datetime.now().strftime('%H%M%S')}"
            elif isinstance(contract, OptionsContract):
                option_suffix = "CE" if contract.option_type == OptionType.CALL else "PE"
                position_id = f"OPT_{contract.underlying}_{contract.expiry_date.strftime('%y%m%d')}_{int(contract.strike_price)}{option_suffix}_{position_type}_{datetime.now().strftime('%H%M%S')}"
            else:
                position_id = f"POS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Store position
            st.session_state.fo_positions[position_id] = position
            st.session_state.fo_margin_used += margin_required
            
            # Record trade
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'position_id': position_id,
                'symbol': getattr(contract, 'underlying', 'UNKNOWN'),
                'contract_type': type(contract).__name__,
                'position_type': position_type,
                'quantity': quantity,
                'price': price,
                'margin_used': margin_required,
                'trade_type': 'OPEN'
            }
            
            st.session_state.fo_trade_history.append(trade_record)
            
            return True, f"F&O order placed successfully. Position ID: {position_id}"
            
        except Exception as e:
            logger.error(f"Error placing F&O order: {e}")
            return False, f"Order failed: {str(e)}"
    
    def close_fo_position(self, position_id: str, close_price: float) -> Tuple[bool, str]:
        """Close F&O position"""
        try:
            if position_id not in st.session_state.fo_positions:
                return False, "Position not found"
            
            position = st.session_state.fo_positions[position_id]
            
            # Calculate final P&L
            position.update_current_price(close_price)
            realized_pnl = position.unrealized_pnl
            
            # Update cash and margin
            st.session_state.current_capital += realized_pnl
            st.session_state.fo_margin_used -= position.margin_used
            
            # Record closing trade
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'position_id': position_id,
                'symbol': getattr(position.contract, 'underlying', 'UNKNOWN'),
                'contract_type': type(position.contract).__name__,
                'position_type': 'SELL' if position.position_type == 'BUY' else 'BUY',
                'quantity': position.quantity,
                'price': close_price,
                'pnl': realized_pnl,
                'trade_type': 'CLOSE'
            }
            
            st.session_state.fo_trade_history.append(trade_record)
            
            # Remove position
            del st.session_state.fo_positions[position_id]
            
            return True, f"Position closed. P&L: ₹{realized_pnl:,.2f}"
            
        except Exception as e:
            logger.error(f"Error closing F&O position: {e}")
            return False, f"Failed to close position: {str(e)}"
    
    def create_strategy_position(self, strategy: FOStrategy) -> Tuple[bool, str]:
        """Create a multi-leg strategy position"""
        try:
            total_margin = strategy.margin_required
            available_margin = self.get_available_margin()
            
            if total_margin > available_margin:
                return False, f"Insufficient margin for strategy. Required: ₹{total_margin:,.2f}, Available: ₹{available_margin:,.2f}"
            
            # Create strategy ID
            strategy_id = f"STRATEGY_{strategy.strategy_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Execute all legs
            leg_position_ids = []
            total_margin_used = 0.0
            
            for i, leg in enumerate(strategy.legs):
                if isinstance(leg.contract, str):  # Stock position
                    # Handle stock positions (simplified)
                    continue
                
                # Calculate individual leg margin
                leg_margin = self.market_data.get_margin_requirement(
                    leg.contract, leg.quantity, leg.position_type
                )
                
                # Create individual position for each leg
                position = FOPosition(
                    contract=leg.contract,
                    position_type=leg.position_type,
                    quantity=leg.quantity,
                    entry_price=leg.entry_price,
                    entry_time=datetime.now()
                )
                position.margin_used = leg_margin
                
                # Generate leg position ID
                leg_position_id = f"{strategy_id}_LEG_{i}"
                st.session_state.fo_positions[leg_position_id] = position
                leg_position_ids.append(leg_position_id)
                total_margin_used += leg_margin
            
            # Store strategy
            strategy_data = {
                'strategy': strategy,
                'leg_position_ids': leg_position_ids,
                'created_time': datetime.now(),
                'total_margin_used': total_margin_used
            }
            
            st.session_state.fo_strategies[strategy_id] = strategy_data
            st.session_state.fo_margin_used += total_margin_used
            
            # Record strategy trade
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'strategy_id': strategy_id,
                'strategy_name': strategy.name,
                'strategy_type': strategy.strategy_type.value,
                'underlying': strategy.underlying,
                'margin_used': total_margin_used,
                'trade_type': 'STRATEGY_OPEN'
            }
            
            st.session_state.fo_trade_history.append(trade_record)
            
            return True, f"Strategy '{strategy.name}' created successfully. Strategy ID: {strategy_id}"
            
        except Exception as e:
            logger.error(f"Error creating strategy: {e}")
            return False, f"Strategy creation failed: {str(e)}"
    
    def close_strategy_position(self, strategy_id: str) -> Tuple[bool, str]:
        """Close entire strategy position"""
        try:
            if strategy_id not in st.session_state.fo_strategies:
                return False, "Strategy not found"
            
            strategy_data = st.session_state.fo_strategies[strategy_id]
            total_realized_pnl = 0.0
            
            # Close all leg positions
            for leg_position_id in strategy_data['leg_position_ids']:
                if leg_position_id in st.session_state.fo_positions:
                    position = st.session_state.fo_positions[leg_position_id]
                    
                    # Get current market price
                    if isinstance(position.contract, FuturesContract):
                        current_price = self.market_data.get_futures_price(
                            position.contract.underlying, position.contract.expiry_date
                        )
                    elif isinstance(position.contract, OptionsContract):
                        spot_price = self.market_data.get_spot_price(position.contract.underlying)
                        current_price = self.fo_manager.bs_calculator.calculate_option_price(
                            spot_price=spot_price,
                            strike_price=position.contract.strike_price,
                            time_to_expiry=position.contract.time_to_expiry,
                            risk_free_rate=self.fo_manager.risk_free_rate,
                            volatility=self.fo_manager.default_volatility,
                            option_type=position.contract.option_type
                        )
                    else:
                        current_price = position.entry_price
                    
                    # Close individual position
                    success, message = self.close_fo_position(leg_position_id, current_price)
                    if success:
                        total_realized_pnl += position.unrealized_pnl
            
            # Update margin
            st.session_state.fo_margin_used -= strategy_data['total_margin_used']
            
            # Record strategy close
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'strategy_id': strategy_id,
                'strategy_name': strategy_data['strategy'].name,
                'total_pnl': total_realized_pnl,
                'trade_type': 'STRATEGY_CLOSE'
            }
            
            st.session_state.fo_trade_history.append(trade_record)
            
            # Remove strategy
            del st.session_state.fo_strategies[strategy_id]
            
            return True, f"Strategy closed. Total P&L: ₹{total_realized_pnl:,.2f}"
            
        except Exception as e:
            logger.error(f"Error closing strategy: {e}")
            return False, f"Failed to close strategy: {str(e)}"
    
    def update_fo_positions(self):
        """Update all F&O positions with current market prices"""
        try:
            for position_id, position in st.session_state.fo_positions.items():
                if isinstance(position.contract, FuturesContract):
                    current_price = self.market_data.get_futures_price(
                        position.contract.underlying, position.contract.expiry_date
                    )
                elif isinstance(position.contract, OptionsContract):
                    spot_price = self.market_data.get_spot_price(position.contract.underlying)
                    current_price = self.fo_manager.bs_calculator.calculate_option_price(
                        spot_price=spot_price,
                        strike_price=position.contract.strike_price,
                        time_to_expiry=position.contract.time_to_expiry,
                        risk_free_rate=self.fo_manager.risk_free_rate,
                        volatility=self.fo_manager.default_volatility,
                        option_type=position.contract.option_type
                    )
                else:
                    continue
                
                position.update_current_price(current_price)
                
        except Exception as e:
            logger.error(f"Error updating F&O positions: {e}")
    
    def get_fo_portfolio_summary(self) -> Dict:
        """Get F&O portfolio summary"""
        self.update_fo_positions()
        
        total_unrealized_pnl = 0.0
        total_margin_used = st.session_state.get('fo_margin_used', 0.0)
        position_count = len(st.session_state.fo_positions)
        strategy_count = len(st.session_state.fo_strategies)
        
        # Calculate total unrealized P&L
        for position in st.session_state.fo_positions.values():
            total_unrealized_pnl += position.unrealized_pnl
        
        # Get realized P&L from trade history
        total_realized_pnl = 0.0
        for trade in st.session_state.fo_trade_history:
            if trade.get('trade_type') == 'CLOSE':
                total_realized_pnl += trade.get('pnl', 0.0)
        
        current_cash = st.session_state.get('current_capital', self.initial_capital)
        available_margin = current_cash - total_margin_used
        
        return {
            'total_positions': position_count,
            'total_strategies': strategy_count,
            'total_margin_used': total_margin_used,
            'available_margin': available_margin,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_realized_pnl': total_realized_pnl,
            'total_pnl': total_unrealized_pnl + total_realized_pnl,
            'current_cash': current_cash,
            'margin_utilization': (total_margin_used / current_cash * 100) if current_cash > 0 else 0
        }
    
    def get_fo_positions_details(self) -> List[Dict]:
        """Get detailed F&O positions"""
        self.update_fo_positions()
        
        positions_details = []
        
        for position_id, position in st.session_state.fo_positions.items():
            if isinstance(position.contract, FuturesContract):
                contract_name = f"{position.contract.underlying} {position.contract.expiry_date.strftime('%d%b%y')} FUT"
                strike_price = None
                option_type = None
                
            elif isinstance(position.contract, OptionsContract):
                option_suffix = "CE" if position.contract.option_type == OptionType.CALL else "PE"
                contract_name = f"{position.contract.underlying} {position.contract.expiry_date.strftime('%d%b%y')} {int(position.contract.strike_price)} {option_suffix}"
                strike_price = position.contract.strike_price
                option_type = position.contract.option_type.value
                
            else:
                contract_name = str(position.contract)
                strike_price = None
                option_type = None
            
            positions_details.append({
                'position_id': position_id,
                'contract_name': contract_name,
                'underlying': getattr(position.contract, 'underlying', 'N/A'),
                'contract_type': type(position.contract).__name__,
                'strike_price': strike_price,
                'option_type': option_type,
                'position_type': position.position_type,
                'quantity': position.quantity,
                'entry_price': position.entry_price,
                'current_price': position.current_price,
                'unrealized_pnl': position.unrealized_pnl,
                'margin_used': position.margin_used,
                'entry_time': position.entry_time,
                'days_held': (datetime.now() - position.entry_time).days,
                'pnl_percent': (position.unrealized_pnl / position.margin_used * 100) if position.margin_used > 0 else 0
            })
        
        return positions_details
    
    def get_fo_trade_history(self) -> List[Dict]:
        """Get F&O trade history"""
        return st.session_state.get('fo_trade_history', [])
    
    def export_fo_data(self) -> str:
        """Export F&O data to JSON"""
        export_data = {
            'positions': {pid: pos.to_dict() for pid, pos in st.session_state.fo_positions.items()},
            'trade_history': st.session_state.fo_trade_history,
            'portfolio_summary': self.get_fo_portfolio_summary(),
            'export_timestamp': datetime.now().isoformat()
        }
        
        return json.dumps(export_data, indent=2, default=str)
    
    def reset_fo_portfolio(self):
        """Reset F&O portfolio"""
        st.session_state.fo_positions = {}
        st.session_state.fo_strategies = {}
        st.session_state.fo_margin_used = 0.0
        st.session_state.fo_trade_history = []

# Global instance
fo_portfolio_manager = FOPortfolioManager()
