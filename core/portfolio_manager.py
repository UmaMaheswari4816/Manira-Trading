"""
Portfolio Manager
Handles positions, orders, and portfolio calculations
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

from core.market_data import MarketDataProvider

logger = logging.getLogger(__name__)

class PortfolioManager:
    """Manages portfolio positions and calculations"""
    
    def __init__(self, initial_capital: float = 1000000.0):
        self.initial_capital = initial_capital
        self.market_data = MarketDataProvider()
    
    def get_current_cash(self) -> float:
        """Get current available cash (accounting for F&O margin used)"""
        base_cash = st.session_state.get('current_capital', self.initial_capital)
        fo_margin_used = st.session_state.get('fo_margin_used', 0.0)
        return base_cash - fo_margin_used
    
    def get_positions(self) -> Dict:
        """Get current positions"""
        return st.session_state.get('positions', {})
    
    def get_trade_history(self) -> List[Dict]:
        """Get trade history"""
        return st.session_state.get('trade_history', [])
    
    def place_order(self, symbol: str, order_type: str, quantity: int, price: float) -> Tuple[bool, str]:
        """Place a buy/sell order"""
        try:
            current_cash = self.get_current_cash()
            positions = self.get_positions()
            
            if order_type == "BUY":
                # Check if enough cash
                order_value = quantity * price
                if order_value > current_cash:
                    return False, f"Insufficient cash. Required: ₹{order_value:,.2f}, Available: ₹{current_cash:,.2f}"
                
                # Execute buy order
                self._execute_buy_order(symbol, quantity, price)
                return True, f"Bought {quantity} shares of {symbol} at ₹{price:.2f}"
            
            elif order_type == "SELL":
                # Check if enough shares
                current_qty = positions.get(symbol, {}).get('quantity', 0)
                if quantity > current_qty:
                    return False, f"Insufficient shares. Required: {quantity}, Available: {current_qty}"
                
                # Execute sell order
                self._execute_sell_order(symbol, quantity, price)
                return True, f"Sold {quantity} shares of {symbol} at ₹{price:.2f}"
            
            else:
                return False, "Invalid order type"
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return False, f"Order failed: {str(e)}"
    
    def _execute_buy_order(self, symbol: str, quantity: int, price: float):
        """Execute buy order"""
        positions = self.get_positions()
        trade_history = self.get_trade_history()
        
        order_value = quantity * price
        
        # Update cash
        current_cash = self.get_current_cash()
        st.session_state.current_capital = current_cash - order_value
        
        # Update position
        if symbol in positions:
            # Average down/up
            existing_qty = positions[symbol]['quantity']
            existing_avg = positions[symbol]['avg_price']
            
            total_qty = existing_qty + quantity
            total_cost = (existing_qty * existing_avg) + (quantity * price)
            new_avg_price = total_cost / total_qty
            
            positions[symbol] = {
                'quantity': total_qty,
                'avg_price': new_avg_price,
                'last_updated': datetime.now()
            }
        else:
            # New position
            positions[symbol] = {
                'quantity': quantity,
                'avg_price': price,
                'last_updated': datetime.now()
            }
        
        # Record trade
        trade_history.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'type': 'BUY',
            'quantity': quantity,
            'price': price,
            'value': order_value,
            'pnl': 0  # No P&L on buy
        })
        
        # Update session state
        st.session_state.positions = positions
        st.session_state.trade_history = trade_history
    
    def _execute_sell_order(self, symbol: str, quantity: int, price: float):
        """Execute sell order"""
        positions = self.get_positions()
        trade_history = self.get_trade_history()
        
        order_value = quantity * price
        
        # Calculate P&L
        avg_price = positions[symbol]['avg_price']
        pnl = (price - avg_price) * quantity
        
        # Update cash
        current_cash = self.get_current_cash()
        st.session_state.current_capital = current_cash + order_value
        
        # Update position
        remaining_qty = positions[symbol]['quantity'] - quantity
        
        if remaining_qty == 0:
            # Close position
            del positions[symbol]
        else:
            # Reduce position
            positions[symbol]['quantity'] = remaining_qty
            positions[symbol]['last_updated'] = datetime.now()
        
        # Record trade
        trade_history.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'type': 'SELL',
            'quantity': quantity,
            'price': price,
            'value': order_value,
            'pnl': pnl
        })
        
        # Update session state
        st.session_state.positions = positions
        st.session_state.trade_history = trade_history
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        positions = self.get_positions()
        current_cash = self.get_current_cash()
        
        total_invested = 0
        total_current_value = 0
        unrealized_pnl = 0
        
        # Calculate position values
        for symbol, position in positions.items():
            current_price = self.market_data.get_current_price(symbol)
            
            invested_amount = position['quantity'] * position['avg_price']
            current_value = position['quantity'] * current_price
            position_pnl = current_value - invested_amount
            
            total_invested += invested_amount
            total_current_value += current_value
            unrealized_pnl += position_pnl
        
        # Add F&O margin and P&L
        fo_margin_used = st.session_state.get('fo_margin_used', 0.0)
        fo_positions = st.session_state.get('fo_positions', {})
        fo_pnl = 0.0
        
        for position in fo_positions.values():
            if hasattr(position, 'unrealized_pnl'):
                fo_pnl += position.unrealized_pnl
            elif isinstance(position, dict):
                fo_pnl += position.get('unrealized_pnl', 0.0)
        
        # Total includes cash + equity value + F&O P&L
        total_portfolio_value = current_cash + total_current_value + fo_pnl + fo_margin_used
        
        # Calculate total orders from both regular and F&O trades
        trade_history = st.session_state.get('trade_history', [])
        fo_trade_history = st.session_state.get('fo_trade_history', [])
        total_orders = len(trade_history) + len(fo_trade_history)
        
        return {
            'cash': current_cash,
            'total_invested': total_invested + fo_margin_used,
            'current_value': total_current_value,
            'unrealized_pnl': unrealized_pnl + fo_pnl,
            'total_portfolio_value': total_portfolio_value,
            'total_return_pct': ((total_portfolio_value - self.initial_capital) / self.initial_capital) * 100,
            'fo_margin_used': fo_margin_used,
            'fo_pnl': fo_pnl,
            'total_orders': total_orders
        }
    
    def get_position_details(self) -> List[Dict]:
        """Get detailed position information"""
        positions = self.get_positions()
        position_details = []
        
        for symbol, position in positions.items():
            current_price = self.market_data.get_current_price(symbol)
            
            invested_amount = position['quantity'] * position['avg_price']
            current_value = position['quantity'] * current_price
            pnl = current_value - invested_amount
            pnl_pct = (pnl / invested_amount) * 100 if invested_amount > 0 else 0
            
            position_details.append({
                'symbol': symbol,
                'quantity': position['quantity'],
                'avg_price': position['avg_price'],
                'current_price': current_price,
                'invested_amount': invested_amount,
                'current_value': current_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'last_updated': position['last_updated']
            })
        
        return position_details
    
    def get_total_value(self) -> float:
        """Get total portfolio value"""
        summary = self.get_portfolio_summary()
        return summary['total_portfolio_value']
    
    def get_day_pnl(self) -> float:
        """Get day's P&L (simplified calculation)"""
        # For simplicity, calculate as a percentage of unrealized P&L
        summary = self.get_portfolio_summary()
        return summary['unrealized_pnl'] * 0.1  # Mock daily P&L
    
    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics"""
        trade_history = self.get_trade_history()
        summary = self.get_portfolio_summary()
        
        if not trade_history:
            return {
                'total_return': 0,
                'win_rate': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'total_trades': 0,
                'profitable_trades': 0
            }
        
        # Calculate metrics from trade history
        total_trades = len([t for t in trade_history if t['type'] == 'SELL'])
        profitable_trades = len([t for t in trade_history if t['type'] == 'SELL' and t['pnl'] > 0])
        
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        total_return = summary['total_return_pct']
        
        # Simplified Sharpe ratio calculation
        returns = [t['pnl'] for t in trade_history if t['type'] == 'SELL']
        if returns:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Simplified max drawdown
        portfolio_values = self._calculate_portfolio_history()
        if len(portfolio_values) > 1:
            peak = portfolio_values[0]
            max_drawdown = 0
            
            for value in portfolio_values:
                if value > peak:
                    peak = value
                
                drawdown = (peak - value) / peak * 100
                max_drawdown = max(max_drawdown, drawdown)
        else:
            max_drawdown = 0
        
        return {
            'total_return': total_return,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'profitable_trades': profitable_trades
        }
    
    def _calculate_portfolio_history(self) -> List[float]:
        """Calculate historical portfolio values"""
        # Simplified calculation based on trade history
        trade_history = self.get_trade_history()
        
        portfolio_values = [self.initial_capital]
        current_value = self.initial_capital
        
        for trade in trade_history:
            if trade['type'] == 'BUY':
                # No immediate P&L impact
                pass
            elif trade['type'] == 'SELL':
                current_value += trade['pnl']
                portfolio_values.append(current_value)
        
        return portfolio_values
    
    def square_off_all_positions(self) -> Tuple[bool, str]:
        """Square off all positions at current market price"""
        positions = self.get_positions()
        
        if not positions:
            return False, "No positions to square off"
        
        try:
            total_pnl = 0
            squared_positions = []
            
            for symbol, position in positions.items():
                current_price = self.market_data.get_current_price(symbol)
                quantity = position['quantity']
                
                # Execute sell order
                success, message = self.place_order(symbol, "SELL", quantity, current_price)
                
                if success:
                    pnl = (current_price - position['avg_price']) * quantity
                    total_pnl += pnl
                    squared_positions.append(symbol)
                else:
                    logger.warning(f"Failed to square off {symbol}: {message}")
            
            return True, f"Squared off {len(squared_positions)} positions. Total P&L: ₹{total_pnl:,.2f}"
            
        except Exception as e:
            logger.error(f"Error squaring off positions: {e}")
            return False, f"Failed to square off positions: {str(e)}"
    
    def get_sector_allocation(self) -> Dict[str, float]:
        """Get portfolio allocation by sector (simplified)"""
        positions = self.get_positions()
        
        # Simplified sector mapping
        sector_mapping = {
            'RELIANCE': 'Energy',
            'TCS': 'IT',
            'INFY': 'IT',
            'HDFCBANK': 'Banking',
            'ICICIBANK': 'Banking',
            'SBIN': 'Banking',
            'HINDUNILVR': 'FMCG',
            'LT': 'Infrastructure',
            'ITC': 'FMCG',
            'TATAMOTORS': 'Auto'
        }
        
        sector_allocation = {}
        total_value = 0
        
        for symbol, position in positions.items():
            current_price = self.market_data.get_current_price(symbol)
            position_value = position['quantity'] * current_price
            
            sector = sector_mapping.get(symbol, 'Others')
            sector_allocation[sector] = sector_allocation.get(sector, 0) + position_value
            total_value += position_value
        
        # Convert to percentages
        if total_value > 0:
            for sector in sector_allocation:
                sector_allocation[sector] = (sector_allocation[sector] / total_value) * 100
        
        return sector_allocation
    
    def calculate_risk_metrics(self) -> Dict:
        """Calculate portfolio risk metrics"""
        positions = self.get_positions()
        portfolio_summary = self.get_portfolio_summary()
        
        if not positions:
            return {'concentration_risk': 0, 'sector_risk': {}, 'position_risk': {}}
        
        total_value = portfolio_summary['current_value']
        
        # Position concentration risk
        position_risk = {}
        max_position_pct = 0
        
        for symbol, position in positions.items():
            current_price = self.market_data.get_current_price(symbol)
            position_value = position['quantity'] * current_price
            position_pct = (position_value / total_value) * 100 if total_value > 0 else 0
            
            position_risk[symbol] = position_pct
            max_position_pct = max(max_position_pct, position_pct)
        
        # Sector risk
        sector_allocation = self.get_sector_allocation()
        
        return {
            'concentration_risk': max_position_pct,
            'sector_risk': sector_allocation,
            'position_risk': position_risk,
            'diversification_score': 100 - max_position_pct  # Simple diversification score
        }
