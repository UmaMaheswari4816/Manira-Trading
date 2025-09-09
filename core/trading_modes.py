"""
Trading Mode Manager
Handles switching between virtual and live trading
"""

import streamlit as st
from typing import Dict, List, Tuple, Optional
import logging

from core.portfolio_manager import PortfolioManager
from core.groww_integration import RealTradingManager

logger = logging.getLogger(__name__)

class TradingModeManager:
    """Manages virtual and live trading modes"""
    
    def __init__(self):
        self.virtual_portfolio = PortfolioManager()
        self.real_trading = RealTradingManager()
        
    def get_current_mode(self) -> str:
        """Get current trading mode"""
        return st.session_state.get('trading_mode', 'virtual')
    
    def is_live_mode(self) -> bool:
        """Check if live trading is enabled"""
        return (self.get_current_mode() == 'live' and 
                st.session_state.get('live_trading_enabled', False))
    
    def switch_to_virtual(self):
        """Switch to virtual trading mode"""
        st.session_state.trading_mode = 'virtual'
        st.success("✅ Switched to Virtual Trading Mode")
        st.info("🎮 You are now trading with virtual money - completely risk-free!")
    
    def switch_to_live(self, api_key: str, access_token: str) -> Tuple[bool, str]:
        """Switch to live trading mode"""
        # Authenticate with Groww
        success, message = self.real_trading.enable_live_trading(api_key, access_token)
        
        if success:
            st.session_state.trading_mode = 'live'
            return True, "✅ Live Trading Mode Enabled - You are now trading with real money!"
        else:
            return False, f"❌ Failed to enable live trading: {message}"
    
    def disable_live_trading(self):
        """Disable live trading and switch to virtual"""
        self.real_trading.disable_live_trading()
        st.session_state.trading_mode = 'virtual'
        st.warning("⚠️ Live trading disabled. Switched to virtual mode.")
    
    def place_order(self, symbol: str, order_type: str, quantity: int, 
                   price: float) -> Tuple[bool, str]:
        """Place order based on current mode"""
        
        if self.is_live_mode():
            # Live trading
            return self.real_trading.place_live_order(symbol, order_type, quantity, price)
        else:
            # Virtual trading
            return self.virtual_portfolio.place_order(symbol, order_type, quantity, price)
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary based on current mode"""
        
        if self.is_live_mode():
            # Get real portfolio from Groww
            live_portfolio = self.real_trading.sync_portfolio_from_groww()
            if live_portfolio:
                return live_portfolio
            else:
                # Fallback to virtual if API fails
                st.warning("⚠️ Could not fetch live portfolio. Showing virtual portfolio.")
                return self.virtual_portfolio.get_portfolio_summary()
        else:
            # Virtual portfolio
            return self.virtual_portfolio.get_portfolio_summary()
    
    def get_positions(self) -> List[Dict]:
        """Get positions based on current mode"""
        
        if self.is_live_mode():
            # Get real positions from Groww
            live_portfolio = self.real_trading.sync_portfolio_from_groww()
            if live_portfolio and 'positions' in live_portfolio:
                return live_portfolio['positions']
            else:
                return []
        else:
            # Virtual positions
            return self.virtual_portfolio.get_position_details()
    
    def get_orders(self) -> List[Dict]:
        """Get orders based on current mode"""
        
        if self.is_live_mode():
            # Get real orders from Groww
            live_orders = self.real_trading.get_live_orders()
            return live_orders if live_orders else []
        else:
            # Virtual orders (from trade history)
            return self.virtual_portfolio.get_trade_history()
    
    def render_mode_selector(self):
        """Render trading mode selector in sidebar"""
        st.sidebar.markdown("### 🎯 Trading Mode")
        
        current_mode = self.get_current_mode()
        
        # Mode indicator
        if current_mode == 'live' and self.is_live_mode():
            st.sidebar.markdown("""
            <div style="background: linear-gradient(135deg, #eb5757 0%, #dc2626 100%); color: white; padding: 0.75rem; border-radius: 8px; text-align: center; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(235, 87, 87, 0.2);">
                🔴 <strong>LIVE TRADING</strong><br>
                <small>Real Money - Real Risk</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.sidebar.markdown("""
            <div style="background: linear-gradient(135deg, #00d09c 0%, #00b386 100%); color: white; padding: 0.75rem; border-radius: 8px; text-align: center; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0, 208, 156, 0.2);">
                🎮 <strong>VIRTUAL TRADING</strong><br>
                <small>Practice Mode - No Risk</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Mode switching buttons
        if current_mode == 'virtual':
            if st.sidebar.button("🔴 Enable Live Trading", use_container_width=True):
                self.render_live_trading_setup()
        else:
            if st.sidebar.button("🎮 Switch to Virtual", use_container_width=True):
                self.switch_to_virtual()
                st.rerun()
    
    def render_live_trading_setup(self):
        """Render live trading setup modal"""
        with st.sidebar.expander("🔐 Live Trading Setup", expanded=True):
            st.warning("⚠️ **WARNING**: Live trading uses real money!")
            
            api_key = st.text_input(
                "Groww API Key:", 
                type="password",
                placeholder="Enter your Groww API key",
                help="Get this from your Groww account settings"
            )
            
            access_token = st.text_input(
                "Access Token:", 
                type="password",
                placeholder="Enter your access token",
                help="Generate this from Groww API dashboard"
            )
            
            if st.button("🚀 Enable Live Trading", type="primary", use_container_width=True):
                if api_key and access_token:
                    success, message = self.switch_to_live(api_key, access_token)
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter both API key and access token")
            
            st.markdown("---")
            st.markdown("### 📚 How to get Groww API credentials:")
            st.markdown("""
            1. Login to [groww.in](https://groww.in)
            2. Go to Settings → API Settings
            3. Generate API Key and Access Token
            4. Copy and paste them above
            
            **Note**: Keep your credentials secure!
            """)
    
    def render_mode_warning(self):
        """Render warning based on current mode"""
        if self.is_live_mode():
            st.markdown("""
            <div style="background: rgba(235, 87, 87, 0.1); border-left: 4px solid #eb5757; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                <div style="color: #eb5757; font-weight: 600; margin-bottom: 0.5rem;">
                    🔴 <strong>LIVE TRADING MODE ACTIVE</strong>
                </div>
                <div style="color: #1f2937; margin-bottom: 0.75rem;">
                    You are trading with <strong>real money</strong>. All orders will be placed on your actual Groww account.
                </div>
                <div style="color: #6b7280; font-size: 0.9rem;">
                    • Real profits and losses<br>
                    • Actual money at risk<br>
                    • Orders execute on live market<br><br>
                    <strong style="color: #eb5757;">Trade carefully!</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: rgba(0, 208, 156, 0.1); border-left: 4px solid #00d09c; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                <div style="color: #00b386; font-weight: 600; margin-bottom: 0.5rem;">
                    🎮 <strong>Virtual Trading Mode</strong>
                </div>
                <div style="color: #1f2937; margin-bottom: 0.75rem;">
                    You are practicing with virtual money (₹10,00,000). Perfect for:
                </div>
                <div style="color: #6b7280; font-size: 0.9rem;">
                    • Learning trading strategies<br>
                    • Testing new approaches<br>
                    • Risk-free practice<br><br>
                    <strong>Switch to Live Trading when ready!</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Global instance
trading_mode_manager = TradingModeManager()
