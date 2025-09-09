"""
Personal Trading Simulator & Strategy Tester
Focus on strategy development and backtesting for real trading
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os
import logging

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from core.strategy_engine import StrategyEngine
from core.portfolio_manager import PortfolioManager
from core.market_data import MarketDataProvider
from core.backtester import Backtester
from core.trading_modes import TradingModeManager
from core.fo_market_data import FOMarketDataProvider
from core.fo_portfolio_manager import FOPortfolioManager
from core.fo_strategies import FOStrategyBuilder, StrategyType
from core.utils import setup_logging, format_currency, format_percentage
from core.user_auth import UserAuth

# Configure Streamlit
st.set_page_config(
    page_title="Trading Simulator - Strategy Tester",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Groww-inspired design
st.markdown("""
<style>
    /* Import Groww-like fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .stApp {
        background-color: #f7f8fa;
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #ffffff;
        border-right: 1px solid #e8e8e8;
    }
    
    /* Main content area */
    .main .block-container {
        padding: 2rem 1.5rem;
        max-width: 1200px;
    }
    
    /* Groww-style metric cards */
    .groww-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e8e8e8;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 1.5rem;
        transition: all 0.2s ease;
    }
    
    .groww-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        transform: translateY(-1px);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0.5rem 0;
        line-height: 1.2;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #6b7280;
        font-weight: 500;
        margin-bottom: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-change {
        font-size: 0.875rem;
        font-weight: 600;
        margin-top: 0.25rem;
    }
    
    /* Groww color scheme */
    .profit { 
        color: #00d09c; 
        background-color: rgba(0, 208, 156, 0.1);
        padding: 2px 8px;
        border-radius: 4px;
    }
    
    .loss { 
        color: #eb5757; 
        background-color: rgba(235, 87, 87, 0.1);
        padding: 2px 8px;
        border-radius: 4px;
    }
    
    .neutral { 
        color: #6b7280; 
    }
    
    /* Primary button styling */
    .stButton > button {
        background: linear-gradient(135deg, #00d09c 0%, #00b386 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0, 208, 156, 0.2);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #00b386 0%, #009970 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 208, 156, 0.3);
    }
    
    /* Sidebar header */
    .sidebar-header {
        background: linear-gradient(135deg, #00d09c 0%, #00b386 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 16px rgba(0, 208, 156, 0.2);
    }
    
    .sidebar-header h3 {
        margin: 0;
        font-weight: 700;
        font-size: 1.25rem;
    }
    
    .sidebar-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 0.875rem;
    }
    
    /* Portfolio section cards */
    .portfolio-section {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid #e8e8e8;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Table styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e8e8e8;
    }
    
    /* Navigation tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f9fafb;
        color: #6b7280;
        border-radius: 8px;
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        border: 1px solid #e5e7eb;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #00d09c;
        color: white;
        border-color: #00d09c;
    }
    
    /* Input styling */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 1px solid #d1d5db;
    }
    
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #d1d5db;
    }
    
    /* Alert styling */
    .stAlert {
        border-radius: 8px;
        border: none;
    }
    
    /* Success alert */
    .stAlert[data-baseweb="notification"] {
        background-color: rgba(0, 208, 156, 0.1);
        border-left: 4px solid #00d09c;
    }
    
    /* Warning alert */
    .stAlert[kind="warning"] {
        background-color: rgba(251, 191, 36, 0.1);
        border-left: 4px solid #fbbf24;
    }
    
    /* Error alert */
    .stAlert[kind="error"] {
        background-color: rgba(235, 87, 87, 0.1);
        border-left: 4px solid #eb5757;
    }
    
    /* Clean button styling like Groww */
    .stButton > button {
        background-color: #ffffff;
        border: 1px solid #e8e8e8;
        border-radius: 6px;
        color: #1f2937;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #f8f9fa;
        border-color: #00d09c;
        color: #00d09c;
    }
    
    .stButton > button:active {
        background-color: #00d09c;
        color: white;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
        }
        
        .groww-card {
            padding: 1rem;
        }
        
        .metric-value {
            font-size: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

class TradingSimulatorApp:
    def __init__(self):
        self.auth = UserAuth()
        self.setup_session_state()
        self.market_data = MarketDataProvider()
        self.portfolio = PortfolioManager()
        self.strategy_engine = StrategyEngine()
        self.backtester = Backtester()
        self.trading_manager = TradingModeManager()
        self.fo_market_data = FOMarketDataProvider()
        self.fo_portfolio = FOPortfolioManager()
        self.fo_strategy_builder = FOStrategyBuilder()
        
        setup_logging()
    
    def setup_session_state(self):
        """Initialize session state"""
        if 'current_capital' not in st.session_state:
            st.session_state.current_capital = 1000000.0  # 10L starting capital
        
        if 'positions' not in st.session_state:
            st.session_state.positions = {}
        
        if 'trade_history' not in st.session_state:
            st.session_state.trade_history = []
        
        if 'selected_strategy' not in st.session_state:
            st.session_state.selected_strategy = None
        
        if 'strategy_params' not in st.session_state:
            st.session_state.strategy_params = {}
    
    def render_sidebar(self):
        """Render sidebar with navigation and controls - Groww-style"""
        # Professional Header with User Info
        if self.auth.is_authenticated():
            current_user = self.auth.get_current_user()
            st.sidebar.markdown(f"""
            <div style="background: #ffffff; padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; 
                 border: 1px solid #e5e7eb; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
                    <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #00d09c, #00b386); 
                         border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                         color: white; font-weight: 700; font-size: 1.1rem;">
                        {current_user[0].upper()}
                    </div>
                    <div>
                        <div style="font-weight: 600; color: #1f2937; font-size: 0.95rem;">✨ Manira Trading</div>
                        <div style="color: #6b7280; font-size: 0.8rem;">Welcome, {current_user}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.sidebar.markdown("""
            <div style="background: #ffffff; padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; 
                 border: 1px solid #e5e7eb; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #00d09c, #00b386); 
                         border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                         color: white; font-weight: 700; font-size: 1.1rem;">
                        M
                    </div>
                    <div>
                        <div style="font-weight: 600; color: #1f2937; font-size: 0.95rem;">✨ Manira Trading</div>
                        <div style="color: #6b7280; font-size: 0.8rem;">Smart Trading Platform</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Initialize selected page in session state
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = "📊 Dashboard"
        
        # Navigation options with clean icons (Groww style)
        nav_options = [
            ("📊", "Dashboard", "Dashboard"),
            ("🎯", "Trade", "Live Trading"), 
            ("🎲", "F&O", "F&O Trading"),
            ("📈", "Strategies", "Strategy Builder"),
            ("🔄", "Backtest", "Backtesting"),
            ("📊", "Analytics", "Analytics"),
            ("📋", "Reports", "Reports"),
            ("⚙️", "Settings", "Settings")
        ]
        
        # Groww-style navigation with minimal gaps
        st.sidebar.markdown("""
        <style>
        /* Override Streamlit's default button styling */
        div[data-testid="stSidebar"] .stButton > button {
            background-color: transparent !important;
            border: none !important;
            border-radius: 0 !important;
            color: #374151 !important;
            font-weight: 500 !important;
            padding: 0.75rem 1rem !important;
            margin: 0 !important;
            width: 100% !important;
            text-align: left !important;
            font-size: 0.9rem !important;
            box-shadow: none !important;
            border-left: 3px solid transparent !important;
            transition: all 0.15s ease !important;
        }
        
        div[data-testid="stSidebar"] .stButton > button:hover {
            background-color: #f8f9fa !important;
            color: #1f2937 !important;
            border-left: 3px solid #e5e7eb !important;
        }
        
        div[data-testid="stSidebar"] .stButton > button:focus {
            box-shadow: none !important;
            border: none !important;
            outline: none !important;
        }
        
        /* Selected state styling - Groww style */
        .nav-selected {
            background-color: #f0f9ff !important;
            color: #00d09c !important;
            font-weight: 600 !important;
            border-left: 3px solid #00d09c !important;
        }
        
        /* Remove gaps between buttons */
        div[data-testid="stSidebar"] .stButton {
            margin-bottom: 0 !important;
        }
        
        /* Navigation container */
        .nav-container {
            background: #ffffff;
            border-radius: 0;
            margin: 0;
            padding: 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Clean navigation without gaps
        page = None
        for icon, label, internal_name in nav_options:
            display_name = f"{icon} {label}"
            is_selected = st.session_state.selected_page == display_name
            
            button_key = f"nav_{internal_name}"
            
            # Create clickable navigation item
            if is_selected:
                # Selected state - show selected styling
                st.sidebar.markdown(f"""
                <div style="padding: 0.75rem 1rem; margin: 0; 
                     background-color: #f0f9ff; color: #00d09c; font-weight: 600; 
                     border-left: 3px solid #00d09c; font-size: 0.9rem;">
                    {icon} {label}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Regular clickable button
                if st.sidebar.button(
                    f"{icon} {label}",
                    key=button_key,
                    use_container_width=True
                ):
                    st.session_state.selected_page = display_name
                    page = display_name
                    st.rerun()
        
        # Use current selected page if no button was clicked
        if page is None:
            page = st.session_state.selected_page
        
        # Trading Mode Selector
        self.trading_manager.render_mode_selector()
        
        # Portfolio Summary Card
        st.sidebar.markdown("### 💼 Portfolio")
        portfolio_summary = self.trading_manager.get_portfolio_summary()
        
        total_value = portfolio_summary.get('total_portfolio_value', portfolio_summary.get('total_value', 1000000))
        day_pnl = portfolio_summary.get('day_pnl', 0)
        total_pnl = portfolio_summary.get('total_pnl', total_value - 1000000.0)
        
        pnl_color = "#00d09c" if total_pnl >= 0 else "#eb5757"
        
        st.sidebar.markdown(f"""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid {pnl_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">Portfolio Value</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #1f2937; margin: 0.25rem 0;">{format_currency(total_value)}</div>
            <div style="font-size: 0.875rem; color: {pnl_color}; font-weight: 600;">
                {format_currency(total_pnl)} ({format_percentage(total_pnl/1000000*100)})
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Today's Performance
        day_pnl_color = "#00d09c" if day_pnl >= 0 else "#eb5757"
        st.sidebar.markdown(f"""
        <div style="background: #ffffff; padding: 0.75rem; border-radius: 8px; margin: 0.5rem 0; border: 1px solid #e5e7eb;">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">Today's P&L</div>
            <div style="font-size: 1rem; font-weight: 600; color: {day_pnl_color}; margin: 0.25rem 0;">
                {format_currency(day_pnl)} ({format_percentage(day_pnl/1000000*100)})
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick Actions section with minimal spacing
        st.sidebar.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)  # Small spacer
        
        # Professional action buttons (Groww style)
        action_buttons = [
            ("🔄", "Reset Portfolio", "reset_portfolio"),
            ("📤", "Export Data", "export_data"),
        ]
        
        # Add logout button for authenticated users
        if self.auth.is_authenticated():
            action_buttons.append(("🔓", "Logout", "logout"))
        
        # Action buttons with clean styling - no gaps
        for icon, label, action in action_buttons:
            if st.sidebar.button(
                f"{icon} {label}",
                key=f"action_{action}",
                use_container_width=True,
                type="primary" if action == "logout" else "secondary"
            ):
                if action == "reset_portfolio":
                    self.reset_portfolio()
                elif action == "export_data":
                    self.export_portfolio_data()
                elif action == "logout":
                    self.auth.logout()
        
        # Map page names for routing
        page_mapping = {
            "📊 Dashboard": "Dashboard",
            "🎯 Trade": "Live Trading", 
            "📈 Strategies": "Strategy Builder",
            "🔄 Backtest": "Backtesting",
            "📊 Analytics": "Performance Analysis",
            "🎲 F&O": "F&O Trading",
            "📋 Reports": "Reports",
            "⚙️ Settings": "Settings"
        }
        
        return page_mapping.get(page, "Dashboard")
    
    def render_dashboard(self):
        """Main dashboard with portfolio overview - Groww-style"""
        # Clean header without emoji clutter
        st.markdown('<div class="section-title">📊 Portfolio Overview</div>', unsafe_allow_html=True)
        
        # Trading mode warning
        self.trading_manager.render_mode_warning()
        
        # Portfolio metrics in Groww-style cards
        portfolio_data = self.trading_manager.get_portfolio_summary()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            unrealized_pnl = portfolio_data['unrealized_pnl']
            pnl_color = "#00d09c" if unrealized_pnl >= 0 else "#eb5757"
            pnl_change = f"{(unrealized_pnl/portfolio_data['cash']*100):+.2f}%" if portfolio_data['cash'] > 0 else "0%"
            
            st.markdown(f"""
            <div class="groww-card">
                <div class="metric-label">Current Value</div>
                <div class="metric-value" style="color: #1f2937;">{format_currency(portfolio_data['cash'] + unrealized_pnl)}</div>
                <div class="metric-change" style="color: {pnl_color};">
                    {format_currency(unrealized_pnl)} ({pnl_change})
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_invested = portfolio_data['total_invested']
            st.markdown(f"""
            <div class="groww-card">
                <div class="metric-label">Invested</div>
                <div class="metric-value" style="color: #1f2937;">{format_currency(total_invested)}</div>
                <div class="metric-change neutral">Total Amount Invested</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            available_cash = portfolio_data['cash']
            st.markdown(f"""
            <div class="groww-card">
                <div class="metric-label">Available Cash</div>
                <div class="metric-value" style="color: #1f2937;">{format_currency(available_cash)}</div>
                <div class="metric-change neutral">Ready to Invest</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            total_orders = portfolio_data.get('total_orders', 0)
            st.markdown(f"""
            <div class="groww-card">
                <div class="metric-label">Total Orders</div>
                <div class="metric-value" style="color: #1f2937;">{total_orders}</div>
                <div class="metric-change neutral">All Time</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Portfolio Performance Chart in a card
        st.markdown("""
        <div class="portfolio-section">
            <div class="section-title">📈 Portfolio Performance</div>
        """, unsafe_allow_html=True)
        self.render_portfolio_chart()
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Holdings and Recent Orders in two columns
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("""
            <div class="portfolio-section">
                <div class="section-title">💼 Holdings</div>
            """, unsafe_allow_html=True)
            self.render_positions_table()
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="portfolio-section">
                <div class="section-title">📋 Recent Orders</div>
            """, unsafe_allow_html=True)
            self.render_recent_trades()
            st.markdown("</div>", unsafe_allow_html=True)
    
    def render_live_trading(self):
        """Live trading interface - Groww-style"""
        st.markdown('<div class="section-title">🎯 Place Order</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Order Placement Card
            st.markdown("""
            <div class="portfolio-section">
                <div class="section-title">📊 Order Details</div>
            """, unsafe_allow_html=True)
            
            # Symbol selection with search-like interface
            symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "HINDUNILVR", "LT", "ITC", "TATAMOTORS"]
            symbol = st.selectbox("🔍 Search & Select Stock", symbols, help="Type to search stocks")
            
            # Current price display
            current_price = self.market_data.get_current_price(symbol)
            change = self.market_data.get_price_change(symbol)
            change_pct = (change / current_price) * 100 if current_price > 0 else 0
            price_color = "#00d09c" if change >= 0 else "#eb5757"
            
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 1rem 0; border-left: 4px solid {price_color};">
                <div style="font-size: 0.875rem; color: #6b7280; margin-bottom: 0.25rem;">Current Price</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #1f2937;">₹{current_price:.2f}</div>
                <div style="font-size: 0.875rem; color: {price_color}; font-weight: 600;">
                    {change:+.2f} ({change_pct:+.2f}%)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Buy/Sell tabs
            order_type = st.radio("Order Type", ["BUY", "SELL"], horizontal=True, key="order_type_radio", label_visibility="collapsed")
            
            # Order details in clean layout
            col_qty, col_price = st.columns(2)
            
            with col_qty:
                quantity = st.number_input("Quantity", min_value=1, value=1, help="Number of shares")
            
            with col_price:
                price_type = st.selectbox("Order Type", ["MARKET", "LIMIT"], help="Market order executes immediately")
                
                if price_type == "LIMIT":
                    limit_price = st.number_input("Price", value=current_price, step=0.05, format="%.2f")
                else:
                    limit_price = current_price
            
            # Order summary
            order_value = quantity * limit_price
            st.markdown(f"""
            <div style="background: #f0f9ff; padding: 1rem; border-radius: 8px; margin: 1rem 0; border: 1px solid #bfdbfe;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span>Order Value:</span>
                    <span style="font-weight: 600;">₹{order_value:,.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.875rem; color: #6b7280;">
                    <span>Brokerage:</span>
                    <span>₹0 (Free)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Place order button - Groww style
            button_color = "#00d09c" if order_type == "BUY" else "#eb5757"
            button_text = f"{order_type} {symbol}"
            
            if st.button(button_text, type="primary", use_container_width=True, key="place_order_btn"):
                if self.trading_manager.is_live_mode():
                    st.warning(f"⚠️ **LIVE ORDER**: This will place a real order for {quantity} shares of {symbol} at ₹{limit_price:.2f}")
                    
                    if st.button("✅ Confirm Live Order", type="secondary"):
                        success, message = self.trading_manager.place_order(
                            symbol=symbol,
                            order_type=order_type,
                            quantity=quantity,
                            price=limit_price
                        )
                        
                        if success:
                            st.success(f"✅ Order placed successfully!")
                            self.auto_save_user_data()
                            st.rerun()
                        else:
                            st.error(f"❌ Order failed: {message}")
                else:
                    success, message = self.trading_manager.place_order(
                        symbol=symbol,
                        order_type=order_type,
                        quantity=quantity,
                        price=limit_price
                    )
                    
                    if success:
                        st.success(f"✅ Order placed successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Order failed: {message}")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            # Market Watch Card
            st.markdown("""
            <div class="portfolio-section">
                <div class="section-title">📈 Market Watch</div>
            """, unsafe_allow_html=True)
            
            watchlist = ["NIFTY 50", "SENSEX", "RELIANCE", "TCS", "HDFCBANK"]
            
            for sym in watchlist:
                display_sym = sym.replace(" 50", "")
                price = self.market_data.get_current_price(display_sym)
                change = self.market_data.get_price_change(display_sym)
                change_pct = (change / price) * 100 if price > 0 else 0
                
                color = "#00d09c" if change >= 0 else "#eb5757"
                bg_color = "rgba(0, 208, 156, 0.05)" if change >= 0 else "rgba(235, 87, 87, 0.05)"
                
                st.markdown(f"""
                <div style="padding: 0.75rem; margin: 0.5rem 0; border-radius: 8px; background: {bg_color}; border-left: 3px solid {color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 600; color: #1f2937;">{sym}</div>
                            <div style="font-size: 0.875rem; color: #6b7280;">NSE</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-weight: 600; color: #1f2937;">₹{price:.2f}</div>
                            <div style="font-size: 0.875rem; color: {color}; font-weight: 600;">
                                {change:+.2f} ({change_pct:+.2f}%)
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Quick Actions Card
            st.markdown("""
            <div class="portfolio-section">
                <div class="section-title">⚡ Quick Actions</div>
            """, unsafe_allow_html=True)
            
            if st.button("📊 View Portfolio", use_container_width=True, key="view_portfolio_btn"):
                st.rerun()
            
            if st.button("🔄 Square Off All", use_container_width=True, key="square_off_btn"):
                self.square_off_all_positions()
            
            if st.button("📈 Analysis", use_container_width=True, key="analysis_btn"):
                st.info("Navigate to Performance Analysis from sidebar")
                
            st.markdown("</div>", unsafe_allow_html=True)
    
    def render_strategy_builder(self):
        """Strategy builder interface"""
        st.title("📈 Strategy Builder")
        
        # Strategy Templates
        st.markdown("### 🎯 Strategy Templates")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="strategy-card">
                <h4>📊 Moving Average Crossover</h4>
                <p>Buy when fast MA crosses above slow MA</p>
                <p><strong>Risk:</strong> Medium | <strong>Timeframe:</strong> Daily</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Use MA Strategy", key="ma_strategy"):
                st.session_state.selected_strategy = "MA_Crossover"
        
        with col2:
            st.markdown("""
            <div class="strategy-card">
                <h4>⚡ RSI Mean Reversion</h4>
                <p>Buy oversold, sell overbought conditions</p>
                <p><strong>Risk:</strong> Low | <strong>Timeframe:</strong> Intraday</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Use RSI Strategy", key="rsi_strategy"):
                st.session_state.selected_strategy = "RSI_MeanReversion"
        
        with col3:
            st.markdown("""
            <div class="strategy-card">
                <h4>📈 Breakout Trading</h4>
                <p>Trade breakouts from support/resistance</p>
                <p><strong>Risk:</strong> High | <strong>Timeframe:</strong> Swing</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Use Breakout Strategy", key="breakout_strategy"):
                st.session_state.selected_strategy = "Breakout"
        
        # Strategy Parameters
        if st.session_state.selected_strategy:
            st.markdown(f"### ⚙️ Configure {st.session_state.selected_strategy} Strategy")
            
            if st.session_state.selected_strategy == "MA_Crossover":
                self.render_ma_strategy_params()
            elif st.session_state.selected_strategy == "RSI_MeanReversion":
                self.render_rsi_strategy_params()
            elif st.session_state.selected_strategy == "Breakout":
                self.render_breakout_strategy_params()
        
        # Live Strategy Execution
        if st.session_state.selected_strategy and st.session_state.strategy_params:
            st.markdown("### 🚀 Strategy Execution")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Start Strategy", type="primary", use_container_width=True):
                    self.start_strategy_execution()
            
            with col2:
                if st.button("Stop Strategy", use_container_width=True):
                    self.stop_strategy_execution()
    
    def render_backtesting(self):
        """Backtesting interface"""
        st.title("🔄 Backtesting")
        
        # Backtest Parameters
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Backtest Configuration")
            
            # Strategy selection
            strategy = st.selectbox(
                "Strategy:",
                ["MA_Crossover", "RSI_MeanReversion", "Breakout", "Custom"]
            )
            
            # Symbol selection
            symbol = st.selectbox(
                "Stock:",
                ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]
            )
            
            # Time period
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=365))
            end_date = st.date_input("End Date", value=datetime.now())
            
            # Capital
            initial_capital = st.number_input("Initial Capital:", value=1000000, step=10000)
        
        with col2:
            st.markdown("### ⚙️ Strategy Parameters")
            
            if strategy == "MA_Crossover":
                fast_ma = st.slider("Fast MA Period:", 5, 50, 10)
                slow_ma = st.slider("Slow MA Period:", 20, 200, 50)
                params = {"fast_ma": fast_ma, "slow_ma": slow_ma}
            
            elif strategy == "RSI_MeanReversion":
                rsi_period = st.slider("RSI Period:", 5, 30, 14)
                oversold = st.slider("Oversold Level:", 10, 40, 30)
                overbought = st.slider("Overbought Level:", 60, 90, 70)
                params = {"rsi_period": rsi_period, "oversold": oversold, "overbought": overbought}
            
            else:
                params = {}
        
        # Run Backtest
        if st.button("🚀 Run Backtest", type="primary", use_container_width=True):
            with st.spinner("Running backtest..."):
                results = self.backtester.run_backtest(
                    strategy=strategy,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=initial_capital,
                    params=params
                )
                
                self.display_backtest_results(results)
    
    def render_performance_analysis(self):
        """Performance analysis dashboard"""
        st.title("📋 Performance Analysis")
        
        # Performance Metrics
        metrics = self.portfolio.get_performance_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Return", f"{metrics['total_return']:.2f}%")
        
        with col2:
            st.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
        
        with col3:
            st.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}")
        
        with col4:
            st.metric("Max Drawdown", f"{metrics['max_drawdown']:.2f}%")
        
        # Detailed Analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Trade Analysis")
            self.render_trade_analysis()
        
        with col2:
            st.markdown("### 📈 Risk Metrics")
            self.render_risk_analysis()
    
    def render_fo_trading(self):
        """F&O Trading dashboard - Frontpage app style"""
        
        # Groww-style clean header
        st.markdown("""
        <div style="background: linear-gradient(135deg, #00d09c 0%, #00b386 100%); color: white; 
             padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem; text-align: center;">
            <h2 style="margin: 0; font-weight: 700; font-size: 1.8rem;">F&O Trading</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1rem;">Futures & Options Trading Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        # F&O Portfolio Summary
        fo_summary = self.fo_portfolio.get_fo_portfolio_summary()
        
        # Groww-style dashboard cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="groww-card">
                <div class="metric-label">Available Margin</div>
                <div class="metric-value" style="color: #00d09c;">{format_currency(fo_summary['available_margin'])}</div>
                <div class="metric-change positive">Ready to Trade</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            margin_used_pct = (fo_summary['total_margin_used'] / fo_summary['available_margin'] * 100) if fo_summary['available_margin'] > 0 else 0
            st.markdown(f"""
            <div class="groww-card">
                <div class="metric-label">Margin Used</div>
                <div class="metric-value" style="color: #1f2937;">{format_currency(fo_summary['total_margin_used'])}</div>
                <div class="metric-change neutral">{margin_used_pct:.1f}% Utilized</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            pnl_color = "#00d09c" if fo_summary['total_pnl'] >= 0 else "#eb5757"
            st.markdown(f"""
            <div class="groww-card">
                <div class="metric-label">Total P&L</div>
                <div class="metric-value" style="color: {pnl_color};">{format_currency(fo_summary['total_pnl'])}</div>
                <div class="metric-change" style="color: {pnl_color};">
                    {"Profit" if fo_summary['total_pnl'] >= 0 else "Loss"}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="groww-card">
                <div class="metric-label">Active Positions</div>
                <div class="metric-value" style="color: #1f2937;">{fo_summary['total_positions']}</div>
                <div class="metric-change neutral">Open Contracts</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Groww-style navigation tabs
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Custom tab styling with Groww colors
        st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 1.5rem;
            background: #ffffff;
            padding: 0.75rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border: 1px solid #e8e8e8;
        }
        .stTabs [data-baseweb="tab"] {
            background: #f8f9fa;
            color: #6b7280;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            border: 1px solid #e8e8e8;
            transition: all 0.2s ease;
        }
        .stTabs [aria-selected="true"] {
            background: #00d09c;
            color: white;
            box-shadow: 0 2px 8px rgba(0, 208, 156, 0.3);
            border: 1px solid #00d09c;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Simplified tabs - removed Quick Trade
        tab1, tab2, tab3 = st.tabs(["📊 Options Chain & Trading", "📈 Strategy Builder", "💼 Positions"])
        
        with tab1:
            self.render_options_chain()
        
        with tab2:
            self.render_fo_strategy_builder()
        
        with tab3:
            self.render_fo_positions()
    
    def render_options_chain(self):
        """Render mobile-first options chain exactly like the screenshot"""
        
        # Simple clean header
        st.markdown("""
        <div style="padding: 1rem 0; margin-bottom: 1rem;">
            <h2 style="margin: 0; color: #1f2937; font-weight: 600; font-size: 1.4rem;">Option Chain</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Index selector card (like NIFTY dropdown)
        fo_symbols = self.fo_market_data.get_fo_watchlist()
        selected_symbol = st.selectbox("Select Index", fo_symbols, index=0, key="options_chain_symbol", label_visibility="collapsed")
        
        if selected_symbol:
            spot_price = self.fo_market_data.get_spot_price(selected_symbol)
            change_pct = 0.35  # Simulated change like +0.35%
            change_value = 86.80  # Simulated change value
            change_color = "#22c55e" if change_pct > 0 else "#ef4444"
            
            # Index card exactly like screenshot
            st.markdown(f"""
            <div style="background: #f8f9fa; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1rem; margin: 1rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="color: #6b7280; font-size: 0.9rem; margin-bottom: 0.25rem;">Index</div>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span style="font-size: 1.1rem; font-weight: 600; color: #1f2937;">{selected_symbol}</span>
                            <span style="color: #6b7280; font-size: 1rem;">▼</span>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.3rem; font-weight: 700; color: #1f2937; margin-bottom: 0.25rem;">{spot_price:.2f}</div>
                        <div style="color: {change_color}; font-size: 0.9rem; font-weight: 500;">+{change_value:.2f} (+{change_pct:.2f}%)</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Expiry and LTP/OI tabs
            col1, col2 = st.columns([2, 1])
            
            with col1:
                expiry_dates = self.fo_market_data.get_expiry_dates(selected_symbol)
            if expiry_dates:
                selected_expiry = st.selectbox(
                        "Select Expiry Date",
                    expiry_dates,
                        format_func=lambda x: x.strftime("%d-%b-%Y"),
                        key="options_chain_expiry",
                        label_visibility="collapsed"
                )
        
            with col2:
                # LTP/OI toggle using radio buttons
                view_mode = st.radio("View Mode", ["LTP", "OI"], horizontal=True, key="view_mode", label_visibility="collapsed")
            
        
            # Options chain data
            if expiry_dates:
                options_chain = self.fo_market_data.get_options_chain(selected_symbol, selected_expiry)
                
                if options_chain:
                    calls = options_chain.get('calls', [])
                    puts = options_chain.get('puts', [])
                    
                    if calls and puts:
                        # Mobile-style 3-column table header - changes based on view mode
                        if view_mode == "LTP":
                            call_header = "Call LTP (Chng%)"
                            put_header = "Put LTP (Chng%)"
                        else:  # OI mode
                            call_header = "Call OI (Chng%)"
                            put_header = "Put OI (Chng%)"
                        
                        st.markdown(f"""
                        <div style="background: #ffffff; margin: 1rem 0;">
                            <div style="display: grid; grid-template-columns: 1fr auto 1fr; gap: 0; background: #f8f9fa; padding: 0.75rem 1rem; border-bottom: 1px solid #e5e7eb; font-size: 0.9rem; font-weight: 500; color: #6b7280;">
                                <div style="text-align: left;">{call_header}</div>
                                <div style="text-align: center; padding: 0 2rem;">Strike</div>
                                <div style="text-align: right;">{put_header}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                        # Generate dynamic strike range around spot price
                        # For NIFTY 24858.90, show strikes from 24800 to 25900 (around ±500 points)
                        atm_strike = round(spot_price / 50) * 50  # Round to nearest 50
                        strike_range_start = max(0, atm_strike - 500)
                        strike_range_end = atm_strike + 500
                    
                        # Filter options to show only strikes in our range
                        filtered_calls = [c for c in calls if strike_range_start <= c['contract'].strike_price <= strike_range_end]
                        filtered_puts = [p for p in puts if strike_range_start <= p['contract'].strike_price <= strike_range_end]
                        
                        # Show up to 15 strikes around ATM
                        strike_range = min(len(filtered_calls), len(filtered_puts), 15)
                        
                        # Find the ATM strike index for price bar placement
                        atm_index = None
                        for idx in range(strike_range):
                            if idx < len(filtered_calls):
                                strike_price = filtered_calls[idx]['contract'].strike_price
                                if abs(spot_price - strike_price) < 50:
                                    atm_index = idx
                                    break
                        
                        for i in range(strike_range):
                            if i >= len(filtered_calls) or i >= len(filtered_puts):
                                continue
                                
                            call_data = filtered_calls[i]
                            put_data = filtered_puts[i]
                            
                            call_contract = call_data['contract']
                            put_contract = put_data['contract']
                            strike = call_contract.strike_price
                            
                            # Market status
                            call_itm = spot_price > strike
                            put_itm = spot_price < strike
                            atm = abs(spot_price - strike) < 50
                            
                            # Check if this is the ATM row to insert the price bar
                            is_atm_row = atm
                        
                            # Insert price bar before ATM row
                            if i == atm_index:  # Show price bar at the ATM strike position
                                st.markdown(f"""
                                <div style="display: flex; align-items: center; margin: 0; padding: 0;">
                                    <div style="flex: 1; height: 1px; background: linear-gradient(to right, transparent, #3b82f6); 
                                        border-top: 1px dashed #3b82f6; opacity: 0.7;"></div>
                                    <div style="background: #3b82f6; color: white; padding: 0.15rem 0.5rem; 
                                        border-radius: 8px; font-weight: 600; font-size: 0.75rem; 
                                        box-shadow: 0 1px 2px rgba(59, 130, 246, 0.3); margin: 0 0.2rem;
                                        border: 1px solid #ffffff; white-space: nowrap;">
                                        {selected_symbol} {spot_price:.2f}
                                    </div>
                                    <div style="flex: 1; height: 1px; background: linear-gradient(to left, transparent, #3b82f6); 
                                        border-top: 1px dashed #3b82f6; opacity: 0.7;"></div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Get values based on view mode
                            if view_mode == "LTP":
                                call_value = call_data.get('last_price', call_contract.premium)
                                put_value = put_data.get('last_price', put_contract.premium)
                                # Calculate percentage changes (simulated) with proper red/green colors
                                call_change = 4.11 if call_itm else -0.19  # Simulated changes
                                put_change = -21.57 if put_itm else -22.02
                            else:  # OI mode
                                call_value = call_data.get('open_interest', 15420)  # Simulated OI
                                put_value = put_data.get('open_interest', 12850)    # Simulated OI
                                # Calculate OI percentage changes (simulated)
                                call_change = 8.45 if call_itm else -2.31  # Simulated OI changes
                                put_change = -15.67 if put_itm else 12.44
                            
                            # Color coding for percentage changes
                            call_change_color = "#22c55e" if call_change > 0 else "#ef4444"  # Green/Red
                            put_change_color = "#22c55e" if put_change > 0 else "#ef4444"    # Green/Red
                            
                            # Row background - green for positive, red for negative changes
                            if call_change > 0:
                                call_bg = "#dcfce7"  # Light green for positive
                            elif call_change < 0:
                                call_bg = "#fef2f2"  # Light red for negative
                            else:
                                call_bg = "#ffffff"  # White for neutral
                            
                            if put_change > 0:
                                put_bg = "#dcfce7"   # Light green for positive
                            elif put_change < 0:
                                put_bg = "#fef2f2"   # Light red for negative
                            else:
                                put_bg = "#ffffff"   # White for neutral
                            
                            strike_bg = "#dcfce7" if atm else "#ffffff"    # Light green for ATM
                            
                            # Use Streamlit columns for proper rendering
                            col_call, col_strike, col_put = st.columns([1, 0.6, 1])
                            
                            with col_call:
                                # Call section with proper background (LTP or OI)
                                call_style = f"background-color: {call_bg}; padding: 0.2rem 0.3rem; border-radius: 0; border-bottom: 1px solid #f0f0f0;"
                                value_format = f"{call_value:.2f}" if view_mode == "LTP" else f"{call_value:,}"
                                st.markdown(f"""
                                <div style="{call_style}">
                                    <div style="font-size: 0.9rem; font-weight: 500; color: #1f2937; margin: 0; line-height: 1.1;">{value_format}</div>
                                    <div style="font-size: 0.75rem; color: {call_change_color}; font-weight: 500; margin: 0; line-height: 1;">{'+'if call_change > 0 else ''}{call_change:.2f}%</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Call trading button with direct dialog
                                button_text = f"CE {call_value:.2f}" if view_mode == "LTP" else f"CE {call_value:,}"
                                with st.popover(button_text, use_container_width=True):
                                    st.markdown(f"**Trade {selected_symbol} {strike:.0f} CALL**")
                                    if view_mode == "LTP":
                                        st.markdown(f"Price: ₹{call_value:.2f}")
                                    else:
                                        st.markdown(f"Open Interest: {call_value:,}")
                                        st.markdown(f"Price: ₹{call_data.get('last_price', call_contract.premium):.2f}")
                                    
                                    # Quick order form
                                    col_a, col_b = st.columns(2)
                                    with col_a:
                                        action = st.selectbox("Action", ["BUY", "SELL"], key=f"call_action_{i}")
                                    with col_b:
                                        lots = st.number_input("Lots", min_value=1, value=1, key=f"call_lots_{i}")
                                    
                                    # Timeframe (mandatory)
                                    timeframe = st.selectbox("Timeframe", ["Intraday", "CNC", "NRML"], key=f"call_timeframe_{i}", help="Mandatory field")
                                    
                                    # Advanced options
                                    with st.expander("🎯 Stop Loss & Target"):
                                        col_sl, col_tgt = st.columns(2)
                                        with col_sl:
                                            enable_sl = st.checkbox("Stop Loss", key=f"call_enable_sl_{i}")
                                            if enable_sl:
                                                sl_price = st.number_input("SL Price", min_value=0.05, value=call_value*0.9, step=0.05, key=f"call_sl_{i}")
                                        with col_tgt:
                                            enable_tgt = st.checkbox("Target", key=f"call_enable_tgt_{i}")
                                            if enable_tgt:
                                                tgt_price = st.number_input("Target Price", min_value=0.05, value=call_value*1.2, step=0.05, key=f"call_tgt_{i}")
                                    
                                    if st.button("Place Order", key=f"call_confirm_{i}", use_container_width=True):
                                        actual_price = call_data.get('last_price', call_contract.premium)
                                        self.handle_option_trade(
                                            selected_symbol, strike, "CALL", action, actual_price, selected_expiry, lots
                                        )
                                        # Show comprehensive order confirmation
                                        order_details = f"✅ {action} {lots} lot(s) - {timeframe}"
                                        if 'enable_sl' in locals() and enable_sl:
                                            order_details += f" | SL: ₹{sl_price:.2f}"
                                        if 'enable_tgt' in locals() and enable_tgt:
                                            order_details += f" | TGT: ₹{tgt_price:.2f}"
                                        
                                        st.success(order_details)
                                        self.auto_save_user_data()
                                        st.rerun()
                            
                            with col_strike:
                                # Strike price section
                                strike_style = f"background-color: {strike_bg}; padding: 0.2rem 0.3rem; border-radius: 0; text-align: center; border-bottom: 1px solid #f0f0f0;"
                                st.markdown(f"""
                                <div style="{strike_style}">
                                    <div style="font-size: 0.9rem; font-weight: 600; color: #1f2937;">{strike:.0f}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col_put:
                                # Put section with proper background (LTP or OI)
                                put_style = f"background-color: {put_bg}; padding: 0.2rem 0.3rem; border-radius: 0; text-align: right; border-bottom: 1px solid #f0f0f0;"
                                put_value_format = f"{put_value:.2f}" if view_mode == "LTP" else f"{put_value:,}"
                                st.markdown(f"""
                                <div style="{put_style}">
                                    <div style="font-size: 0.9rem; font-weight: 500; color: #1f2937; margin: 0; line-height: 1.1;">{put_value_format}</div>
                                    <div style="font-size: 0.75rem; color: {put_change_color}; font-weight: 500; margin: 0; line-height: 1;">{'+'if put_change > 0 else ''}{put_change:.2f}%</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Put trading button with direct dialog
                                put_button_text = f"PE {put_value:.2f}" if view_mode == "LTP" else f"PE {put_value:,}"
                                with st.popover(put_button_text, use_container_width=True):
                                    st.markdown(f"**Trade {selected_symbol} {strike:.0f} PUT**")
                                    if view_mode == "LTP":
                                        st.markdown(f"Price: ₹{put_value:.2f}")
                                    else:
                                        st.markdown(f"Open Interest: {put_value:,}")
                                        st.markdown(f"Price: ₹{put_data.get('last_price', put_contract.premium):.2f}")
                                    
                                    # Quick order form
                                    col_a, col_b = st.columns(2)
                                    with col_a:
                                        action = st.selectbox("Action", ["BUY", "SELL"], key=f"put_action_{i}")
                                    with col_b:
                                        lots = st.number_input("Lots", min_value=1, value=1, key=f"put_lots_{i}")
                                    
                                    # Timeframe (mandatory)
                                    timeframe = st.selectbox("Timeframe", ["Intraday", "CNC", "NRML"], key=f"put_timeframe_{i}", help="Mandatory field")
                                    
                                    # Advanced options
                                    with st.expander("🎯 Stop Loss & Target"):
                                        col_sl, col_tgt = st.columns(2)
                                        with col_sl:
                                            enable_sl = st.checkbox("Stop Loss", key=f"put_enable_sl_{i}")
                                            if enable_sl:
                                                sl_price = st.number_input("SL Price", min_value=0.05, value=put_value*0.9, step=0.05, key=f"put_sl_{i}")
                                        with col_tgt:
                                            enable_tgt = st.checkbox("Target", key=f"put_enable_tgt_{i}")
                                            if enable_tgt:
                                                tgt_price = st.number_input("Target Price", min_value=0.05, value=put_value*1.2, step=0.05, key=f"put_tgt_{i}")
                                    
                                    if st.button("Place Order", key=f"put_confirm_{i}", use_container_width=True):
                                        actual_put_price = put_data.get('last_price', put_contract.premium)
                                        self.handle_option_trade(
                                            selected_symbol, strike, "PUT", action, actual_put_price, selected_expiry, lots
                                        )
                                        # Show comprehensive order confirmation
                                        order_details = f"✅ {action} {lots} lot(s) - {timeframe}"
                                        if 'enable_sl' in locals() and enable_sl:
                                            order_details += f" | SL: ₹{sl_price:.2f}"
                                        if 'enable_tgt' in locals() and enable_tgt:
                                            order_details += f" | TGT: ₹{tgt_price:.2f}"
                                        
                                        st.success(order_details)
                                        self.auto_save_user_data()
                                        st.rerun()
                        
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            # No bottom space needed
                            
                    else:
                        st.error("❌ No options data available for this symbol")
                else:
                    st.error("❌ Unable to load options chain")
            else:
                st.warning("⚠️ No expiry dates available for this symbol")
            
            # Show order dialog if triggered
            if hasattr(st.session_state, 'order_dialog') and st.session_state.order_dialog.get('show', False):
                self.show_order_dialog()
        
    
    def show_order_dialog(self):
        """Show Frontpage/Groww style order placement dialog"""
        dialog_data = st.session_state.order_dialog
        
        # Simple dialog container with border
        st.markdown("""
        <div style="border: 2px solid #3b82f6; background: white; border-radius: 12px; padding: 1rem; margin: 2rem 0; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        """, unsafe_allow_html=True)
        
        # Order dialog content
        with st.container():
            # Header
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid #f0f0f0;">
                <h3 style="color: #1f2937; margin: 0; font-weight: 600;">Place Order</h3>
                <p style="color: #6b7280; margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                    {dialog_data['symbol']} {dialog_data['strike']:.0f} {dialog_data['option_type']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Order form
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Order Type**")
                order_type = st.selectbox("Order Type", ["Market", "Limit"], key="order_type_dialog", label_visibility="collapsed")
                
                st.markdown("**Quantity (Lots)**")
                # Use default lots from options chain if available
                default_value = st.session_state.get('default_lots', 1)
                lots = st.number_input("Quantity", min_value=1, max_value=100, value=default_value, key="lots_dialog", label_visibility="collapsed")
                
                st.markdown("**Validity**")
                validity = st.selectbox("Validity", ["DAY", "IOC"], key="validity_dialog", label_visibility="collapsed")
            
            with col2:
                # Action display
                action_color = "#00b386" if dialog_data['action'] == 'BUY' else "#eb5757"
                action_bg = "#e8f5e8" if dialog_data['action'] == 'BUY' else "#fef2f2"
                
                st.markdown("**Action**")
                st.markdown(f"""
                <div style="padding: 0.75rem; background: {action_bg}; border-radius: 8px; text-align: center; 
                     color: {action_color}; font-weight: 600; font-size: 1.1rem; margin-bottom: 1rem;">
                    {dialog_data['action']}
                </div>
                """, unsafe_allow_html=True)
                
                # Price input
                st.markdown("**Price**")
                if order_type == "Market":
                    st.markdown(f"""
                    <div style="padding: 0.75rem; background: #f8f9fa; border-radius: 8px; text-align: center; 
                         font-weight: 600; color: #1f2937;">₹{dialog_data['price']:.2f}</div>
                    """, unsafe_allow_html=True)
                    order_price = dialog_data['price']
                else:
                    order_price = st.number_input("Price", min_value=0.05, value=dialog_data['price'], 
                                                step=0.05, key="price_dialog", label_visibility="collapsed")
            
            # Calculate order summary
            lot_size = self.fo_instruments.get_lot_size(dialog_data['symbol'])
            contract_value = order_price * lots * lot_size
            margin_required = contract_value * 0.20  # Approximate margin
            brokerage = min(contract_value * 0.0003, 20) * lots  # Max ₹20 per lot
            total_cost = margin_required + brokerage
            
            # Order summary card
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); 
                 padding: 1.25rem; border-radius: 10px; margin: 1.5rem 0; 
                 border: 1px solid #e8e8e8;">
                <h4 style="margin: 0 0 1rem 0; color: #1f2937; font-size: 1rem;">Order Summary</h4>
            """, unsafe_allow_html=True)
            
            # Summary details
            summary_items = [
                ("Quantity", f"{lots} lot(s) × {lot_size} = {lots * lot_size} shares"),
                ("Price per share", f"₹{order_price:.2f}"),
                ("Contract Value", f"₹{contract_value:,.2f}"),
                ("Margin Required", f"₹{margin_required:,.2f}"),
                ("Brokerage", f"₹{brokerage:.2f}"),
            ]
            
            for label, value in summary_items:
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; 
                     font-size: 0.9rem;">
                    <span style="color: #6b7280;">{label}:</span>
                    <span style="font-weight: 500; color: #1f2937;">{value}</span>
                </div>
                """, unsafe_allow_html=True)
            
            # Total
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; padding-top: 0.75rem; 
                 border-top: 2px solid #e8e8e8; font-weight: 600; font-size: 1rem;">
                <span style="color: #1f2937;">Total Required:</span>
                <span style="color: {action_color};">₹{total_cost:,.2f}</span>
            </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if st.button("❌ Cancel", key="cancel_order", use_container_width=True, 
                           help="Cancel this order"):
                    st.session_state.order_dialog = {'show': False}
                    st.rerun()
            
            with col2:
                button_style = f"background: {action_color}; color: white; border: none; font-weight: 600;"
                action_emoji = "🟢" if dialog_data['action'] == 'BUY' else "🔴"
                
                if st.button(f"{action_emoji} {dialog_data['action']} Order", key="confirm_order", 
                           use_container_width=True, help=f"Place {dialog_data['action']} order"):
                    # Execute the trade
                    self.handle_option_trade(
                        dialog_data['symbol'], 
                        dialog_data['strike'], 
                        dialog_data['option_type'], 
                        dialog_data['action'], 
                        order_price, 
                        dialog_data['expiry'],
                        lots
                    )
                    st.session_state.order_dialog = {'show': False}
                    self.auto_save_user_data()
                    st.rerun()
        
        # Close dialog container
        st.markdown("</div>", unsafe_allow_html=True)
    
    def render_fo_quick_trade(self):
        """Quick F&O trading interface"""
        st.markdown("### 🚀 Quick F&O Trade")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Trade Setup")
            
            # Instrument type
            instrument_type = st.selectbox("Instrument Type:", ["Options", "Futures"], key="quick_trade_instrument")
            
            # Symbol selection
            fo_symbols = self.fo_market_data.get_fo_watchlist()
            symbol = st.selectbox("Symbol:", fo_symbols, key="quick_trade_symbol")
            
            # Get current price
            spot_price = self.fo_market_data.get_spot_price(symbol)
            st.info(f"Spot Price: ₹{spot_price:.2f}")
            
            # Expiry selection
            expiry_dates = self.fo_market_data.get_expiry_dates(symbol)
            if expiry_dates:
                expiry_date = st.selectbox(
                    "Expiry Date:",
                    expiry_dates,
                    format_func=lambda x: x.strftime("%d %b %Y"),
                    key="quick_trade_expiry"
                )
                
                if instrument_type == "Options":
                    # Options specific inputs
                    option_type = st.selectbox("Option Type:", ["CALL", "PUT"], key="quick_trade_option_type")
                    
                    # Strike price selection
                    strike_prices = self.fo_market_data.fo_manager.generate_strike_prices(
                        symbol, spot_price, expiry_date
                    )
                    
                    if strike_prices:
                        # Find ATM strike
                        atm_strike = min(strike_prices, key=lambda x: abs(x - spot_price))
                        atm_index = strike_prices.index(atm_strike)
                        
                        strike_price = st.selectbox(
                            "Strike Price:",
                            strike_prices,
                            index=atm_index,
                            format_func=lambda x: f"₹{x:.0f}",
                            key="quick_trade_strike"
                        )
                        
                        # Create option contract to get premium
                        from core.fo_instruments import OptionType
                        opt_type = OptionType.CALL if option_type == "CALL" else OptionType.PUT
                        
                        option_contract = self.fo_market_data.fo_manager.create_options_contract(
                            symbol, strike_price, opt_type, expiry_date, spot_price
                        )
                        
                        st.info(f"Premium: ₹{option_contract.premium:.2f}")
                        
                        # Greeks display
                        greeks = self.fo_market_data.fo_manager.bs_calculator.calculate_greeks(
                            spot_price, strike_price, option_contract.time_to_expiry,
                            self.fo_market_data.fo_manager.risk_free_rate,
                            self.fo_market_data.fo_manager.default_volatility,
                            opt_type
                        )
                        
                        col_delta, col_gamma, col_theta, col_vega = st.columns(4)
                        col_delta.metric("Delta", f"{greeks['delta']:.3f}")
                        col_gamma.metric("Gamma", f"{greeks['gamma']:.4f}")
                        col_theta.metric("Theta", f"{greeks['theta']:.2f}")
                        col_vega.metric("Vega", f"{greeks['vega']:.2f}")
                        
                        contract = option_contract
                        current_price = option_contract.premium
                        
                    else:
                        st.error("No strike prices available")
                        return
                
                else:  # Futures
                    futures_contract = self.fo_market_data.fo_manager.create_futures_contract(
                        symbol, spot_price, expiry_date
                    )
                    futures_price = self.fo_market_data.get_futures_price(symbol, expiry_date)
                    
                    st.info(f"Futures Price: ₹{futures_price:.2f}")
                    
                    contract = futures_contract
                    current_price = futures_price
                
                # Trading inputs
                position_type = st.selectbox("Position:", ["BUY", "SELL"], key="quick_trade_position")
                quantity = st.number_input("Quantity (Lots):", min_value=1, value=1, key="quick_trade_quantity")
                
                # Calculate margin requirement
                margin_required = self.fo_market_data.get_margin_requirement(
                    contract, quantity, position_type
                )
                
                st.info(f"Margin Required: ₹{margin_required:,.2f}")
                
                # Available margin check
                available_margin = self.fo_portfolio.get_available_margin()
                st.info(f"Available Margin: ₹{available_margin:,.2f}")
                
                # Place order button
                if st.button("Place F&O Order", type="primary", use_container_width=True, key="place_fo_order_button"):
                    if margin_required <= available_margin:
                        success, message = self.fo_portfolio.place_fo_order(
                            contract, position_type, quantity, current_price
                        )
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("❌ Insufficient margin for this trade")
            
            else:
                st.error("No expiry dates available")
        
        with col2:
            st.markdown("#### Position Calculator")
            
            if 'contract' in locals():
                # P&L scenarios
                st.markdown("**P&L at Different Prices:**")
                
                price_scenarios = [
                    spot_price * 0.95,
                    spot_price * 0.98,
                    spot_price,
                    spot_price * 1.02,
                    spot_price * 1.05
                ]
                
                scenario_data = []
                for scenario_price in price_scenarios:
                    if instrument_type == "Options":
                        # Calculate option value at scenario price
                        scenario_premium = self.fo_market_data.fo_manager.bs_calculator.calculate_option_price(
                            spot_price=scenario_price,
                            strike_price=strike_price if 'strike_price' in locals() else spot_price,
                            time_to_expiry=option_contract.time_to_expiry if 'option_contract' in locals() else 0.1,
                            risk_free_rate=self.fo_market_data.fo_manager.risk_free_rate,
                            volatility=self.fo_market_data.fo_manager.default_volatility,
                            option_type=opt_type if 'opt_type' in locals() else OptionType.CALL
                        )
                        
                        if position_type == "BUY":
                            pnl = (scenario_premium - current_price) * quantity * contract.lot_size
                        else:
                            pnl = (current_price - scenario_premium) * quantity * contract.lot_size
                    
                    else:  # Futures
                        if position_type == "BUY":
                            pnl = (scenario_price - current_price) * quantity * contract.lot_size
                        else:
                            pnl = (current_price - scenario_price) * quantity * contract.lot_size
                    
                    scenario_data.append({
                        'Price': f"₹{scenario_price:.2f}",
                        'P&L': f"₹{pnl:,.2f}",
                        'P&L %': f"{(pnl/margin_required)*100:.1f}%"
                    })
                
                df_scenarios = pd.DataFrame(scenario_data)
                st.dataframe(df_scenarios, use_container_width=True)
    
    def render_fo_strategy_builder(self):
        """F&O Strategy builder"""
        st.markdown("### 📈 F&O Strategy Builder")
        
        strategy_type = st.selectbox(
            "Select Strategy:",
            [
                "Bull Call Spread",
                "Bear Put Spread", 
                "Long Straddle",
                "Short Straddle",
                "Iron Condor",
                "Covered Call",
                "Protective Put"
            ],
            key="strategy_builder_type"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Strategy parameters
            symbol = st.selectbox("Symbol:", self.fo_market_data.get_fo_watchlist(), key="strategy_builder_symbol")
            
            expiry_dates = self.fo_market_data.get_expiry_dates(symbol)
            if expiry_dates:
                expiry_date = st.selectbox(
                    "Expiry:",
                    expiry_dates,
                    format_func=lambda x: x.strftime("%d %b %Y"),
                    key="strategy_builder_expiry"
                )
                
                spot_price = self.fo_market_data.get_spot_price(symbol)
                st.info(f"Spot Price: ₹{spot_price:.2f}")
                
                # Strategy specific inputs
                if strategy_type in ["Bull Call Spread", "Bear Put Spread"]:
                    lower_strike = st.number_input("Lower Strike:", value=spot_price - 100, step=50.0, key="spread_lower_strike")
                    upper_strike = st.number_input("Upper Strike:", value=spot_price + 100, step=50.0, key="spread_upper_strike")
                    quantity = st.number_input("Quantity (Lots):", min_value=1, value=1, key="spread_quantity")
                    
                    if st.button("Create Spread Strategy", key="create_spread_button"):
                        if strategy_type == "Bull Call Spread":
                            strategy = self.fo_strategy_builder.create_bull_call_spread(
                                symbol, spot_price, expiry_date, lower_strike, upper_strike, quantity
                            )
                        else:
                            strategy = self.fo_strategy_builder.create_bear_put_spread(
                                symbol, spot_price, expiry_date, lower_strike, upper_strike, quantity
                            )
                        
                        success, message = self.fo_portfolio.create_strategy_position(strategy)
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                
                elif strategy_type in ["Long Straddle", "Short Straddle"]:
                    strike = st.number_input("Strike Price:", value=spot_price, step=50.0, key="straddle_strike")
                    quantity = st.number_input("Quantity (Lots):", min_value=1, value=1, key="straddle_quantity")
                    
                    if st.button("Create Straddle", key="create_straddle_button"):
                        position_type = "BUY" if strategy_type == "Long Straddle" else "SELL"
                        strategy = self.fo_strategy_builder.create_straddle(
                            symbol, spot_price, expiry_date, strike, quantity, position_type
                        )
                        
                        success, message = self.fo_portfolio.create_strategy_position(strategy)
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
        
        with col2:
            st.markdown("#### Strategy Information")
            
            if strategy_type == "Bull Call Spread":
                st.info("""
                **Bull Call Spread**
                - Buy lower strike call
                - Sell higher strike call
                - Limited profit, limited risk
                - Bullish outlook
                """)
            
            elif strategy_type == "Bear Put Spread":
                st.info("""
                **Bear Put Spread**
                - Buy higher strike put
                - Sell lower strike put
                - Limited profit, limited risk
                - Bearish outlook
                """)
            
            elif strategy_type == "Long Straddle":
                st.info("""
                **Long Straddle**
                - Buy call + Buy put (same strike)
                - Unlimited profit potential
                - Limited risk (premium paid)
                - Expects high volatility
                """)
            
            elif strategy_type == "Short Straddle":
                st.info("""
                **Short Straddle**
                - Sell call + Sell put (same strike)
                - Limited profit (premium received)
                - Unlimited risk
                - Expects low volatility
                """)
    
    def render_fo_positions(self):
        """Render F&O positions"""
        st.markdown("### 💼 F&O Positions")
        
        positions = self.fo_portfolio.get_fo_positions_details()
        
        if positions:
            # Convert to DataFrame for better display
            df_data = []
            for pos in positions:
                df_data.append({
                    'Contract': pos['contract_name'],
                    'Type': pos['position_type'],
                    'Qty': pos['quantity'],
                    'Entry': f"₹{pos['entry_price']:.2f}",
                    'Current': f"₹{pos['current_price']:.2f}",
                    'P&L': f"₹{pos['unrealized_pnl']:,.2f}",
                    'P&L %': f"{pos['pnl_percent']:+.1f}%",
                    'Margin': f"₹{pos['margin_used']:,.0f}",
                    'Days': pos['days_held']
                })
            
            df = pd.DataFrame(df_data)
            
            # Color code P&L
            def color_pnl(val):
                if '₹' in str(val):
                    try:
                        pnl_value = float(str(val).replace('₹', '').replace(',', ''))
                        if pnl_value > 0:
                            return 'color: green'
                        elif pnl_value < 0:
                            return 'color: red'
                    except (ValueError, AttributeError):
                        pass
                return ''
            
            styled_df = df.style.map(color_pnl)
            st.dataframe(styled_df, use_container_width=True)
            
            # Position management buttons
            st.markdown("#### Position Management")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Refresh Positions", use_container_width=True, key="refresh_fo_positions"):
                    self.fo_portfolio.update_fo_positions()
                    st.rerun()
            
            with col2:
                if st.button("📊 Export F&O Data", use_container_width=True, key="export_fo_data"):
                    export_data = self.fo_portfolio.export_fo_data()
                    st.download_button(
                        label="Download F&O Data",
                        data=export_data,
                        file_name=f"fo_portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key="download_fo_data"
                    )
            
            with col3:
                if st.button("⚠️ Close All Positions", type="secondary", use_container_width=True, key="close_all_fo_positions"):
                    st.warning("This will close all F&O positions. This action cannot be undone.")
                    
                    if st.button("Confirm Close All", type="primary", key="confirm_close_all_fo"):
                        closed_count = 0
                        for pos in positions:
                            success, message = self.fo_portfolio.close_fo_position(
                                pos['position_id'], pos['current_price']
                            )
                            if success:
                                closed_count += 1
                        
                        st.success(f"Closed {closed_count} positions")
                        self.auto_save_user_data()
                        st.rerun()
        
        else:
            st.info("No F&O positions currently held")
            
            # Quick links to start trading
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Start F&O Trading", type="primary", use_container_width=True, key="start_fo_trading"):
                    st.info("💡 Navigate to '🎲 F&O Trading' from the sidebar to start trading!")
            
            with col2:
                if st.button("📊 View Options Chain", use_container_width=True, key="view_options_chain"):
                    st.info("💡 Navigate to '🎲 F&O Trading' from the sidebar to view options chain!")

    def render_settings(self):
        """Settings and configuration"""
        st.title("⚙️ Settings")
        
        # Trading Settings
        st.markdown("### 🎯 Trading Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Risk Management
            st.markdown("#### Risk Management")
            max_position_size = st.slider("Max Position Size (%):", 1, 50, 10)
            stop_loss_pct = st.slider("Default Stop Loss (%):", 1, 20, 5)
            take_profit_pct = st.slider("Default Take Profit (%):", 1, 50, 10)
        
        with col2:
            # Data Settings
            st.markdown("#### Data Configuration")
            use_real_data = st.checkbox("Use Real Market Data", value=True)
            auto_refresh = st.checkbox("Auto Refresh Prices", value=True)
            refresh_interval = st.slider("Refresh Interval (seconds):", 5, 60, 15)
        
        # Strategy Settings
        st.markdown("### 📈 Strategy Configuration")
        
        # Paper Trading vs Real Trading Toggle
        st.markdown("#### Trading Mode")
        trading_mode = st.radio(
            "Select Trading Mode:",
            ["Paper Trading", "Real Trading (Future)"],
            help="Paper trading uses virtual money for practice"
        )
        
        if trading_mode == "Real Trading (Future)":
            st.info("🔄 Real trading integration coming soon! Currently in paper trading mode.")
        
        # F&O Settings
        st.markdown("### 🎲 F&O Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### F&O Risk Management")
            max_fo_exposure = st.slider("Max F&O Exposure (%):", 10, 80, 50)
            auto_square_off = st.checkbox("Auto Square-off on Expiry", value=True)
            margin_buffer = st.slider("Margin Buffer (%):", 10, 50, 20)
        
        with col2:
            st.markdown("#### Options Settings")
            default_volatility = st.slider("Default IV (%):", 10, 50, 25)
            greeks_update_freq = st.slider("Greeks Update (seconds):", 5, 60, 15)
            show_payoff_diagram = st.checkbox("Show Payoff Diagrams", value=True)
        
        # Save Settings
        if st.button("💾 Save Settings", type="primary", key="save_settings_button"):
            # Save settings to session state or config file
            st.success("Settings saved successfully!")
    
    def render_portfolio_chart(self):
        """Render portfolio performance chart"""
        # Generate sample portfolio history
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        
        # Mock portfolio values
        portfolio_values = []
        base_value = 1000000
        
        for i, date in enumerate(dates):
            # Add some random walk
            change = np.random.normal(0, 0.02)  # 2% daily volatility
            base_value *= (1 + change)
            portfolio_values.append(base_value)
        
        df = pd.DataFrame({
            'Date': dates,
            'Portfolio Value': portfolio_values
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Portfolio Value'],
            mode='lines',
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=2)
        ))
        
        fig.update_layout(
            title="Portfolio Performance (Last 30 Days)",
            xaxis_title="Date",
            yaxis_title="Value (₹)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_positions_table(self):
        """Render current positions table"""
        positions = self.trading_manager.get_positions()
        
        if not positions:
            st.info("No current positions")
            return
        
        positions_data = []
        for position in positions:
            if isinstance(position, dict):
                # Handle both virtual and live position formats
                symbol = position.get('symbol')
                quantity = position.get('quantity', 0)
                avg_price = position.get('avg_price', position.get('average_price', 0))
                current_price = position.get('current_price', self.market_data.get_current_price(symbol))
                pnl = position.get('pnl', (current_price - avg_price) * quantity)
                pnl_pct = position.get('pnl_pct', (pnl / (avg_price * quantity) * 100) if avg_price * quantity > 0 else 0)
                
                positions_data.append({
                    'Symbol': symbol,
                    'Quantity': quantity,
                    'Avg Price': f"₹{avg_price:.2f}",
                    'Current Price': f"₹{current_price:.2f}",
                    'P&L': f"₹{pnl:,.2f}",
                    'P&L %': f"{pnl_pct:+.2f}%"
                })
        
        if positions_data:
            df = pd.DataFrame(positions_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No current positions")
    
    def render_recent_trades(self):
        """Render recent trades table"""
        if not st.session_state.trade_history:
            st.info("No trades yet")
            return
        
        # Show last 10 trades
        recent_trades = st.session_state.trade_history[-10:]
        df = pd.DataFrame(recent_trades)
        
        if not df.empty:
            # Format the dataframe
            df['Timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            df = df[['Timestamp', 'symbol', 'type', 'quantity', 'price', 'pnl']]
            df.columns = ['Time', 'Symbol', 'Type', 'Qty', 'Price', 'P&L']
            
            st.dataframe(df, use_container_width=True)
    
    def reset_portfolio(self):
        """Reset portfolio to initial state"""
        # Reset regular portfolio
        st.session_state.current_capital = 1000000.0
        st.session_state.positions = {}
        st.session_state.trade_history = []
        
        # Reset F&O portfolio using the dedicated method
        self.fo_portfolio.reset_fo_portfolio()
        
        # Auto-save the reset state
        if self.auth.is_authenticated():
            self.auth.save_current_session_data()
        
        st.success("🔄 Portfolio reset successfully! All positions and trades cleared.")
        st.balloons()  # Add celebration effect
        st.rerun()
    
    def export_portfolio_data(self):
        """Export portfolio data to CSV"""
        # Get both regular and F&O trade history
        regular_trades = st.session_state.get('trade_history', [])
        fo_trades = st.session_state.get('fo_trade_history', [])
        
        # Combine all trades
        all_trades = []
        
        # Add regular trades with trade_type indicator
        for trade in regular_trades:
            trade_copy = trade.copy()
            trade_copy['trade_category'] = 'Equity'
            all_trades.append(trade_copy)
        
        # Add F&O trades with trade_type indicator
        for trade in fo_trades:
            trade_copy = trade.copy()
            trade_copy['trade_category'] = 'F&O'
            # Ensure consistent column names
            if 'position_type' in trade_copy:
                trade_copy['type'] = trade_copy.pop('position_type')
            if 'price' not in trade_copy and 'entry_price' in trade_copy:
                trade_copy['price'] = trade_copy.pop('entry_price')
            all_trades.append(trade_copy)
        
        if all_trades:
            df = pd.DataFrame(all_trades)
            
            # Sort by timestamp
            if 'timestamp' in df.columns:
                df = df.sort_values('timestamp', ascending=False)
            
            # Reorder columns for better readability
            preferred_columns = ['timestamp', 'trade_category', 'symbol', 'type', 'quantity', 'price', 'margin_used', 'trade_type']
            available_columns = [col for col in preferred_columns if col in df.columns]
            other_columns = [col for col in df.columns if col not in preferred_columns]
            df = df[available_columns + other_columns]
            
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Complete Trade History",
                data=csv,
                file_name=f"complete_trade_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help=f"Download all {len(all_trades)} trades (Equity: {len(regular_trades)}, F&O: {len(fo_trades)})"
            )
            
            # Just show the download button without preview
            st.success(f"✅ Ready to export {len(all_trades)} trades (Equity: {len(regular_trades)}, F&O: {len(fo_trades)})")
        else:
            st.info("📭 No trade history to export. Start trading to generate data!")
    
    def render_reports(self):
        """Comprehensive Reports and Export Page"""
        st.markdown("# 📋 Reports & Analytics")
        st.markdown("---")
        
        # Get trade data
        regular_trades = st.session_state.get('trade_history', [])
        fo_trades = st.session_state.get('fo_trade_history', [])
        all_trades = regular_trades + fo_trades
        
        # Summary cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="groww-card">
                <div class="metric-label">Total Trades</div>
                <div class="metric-value" style="color: #1f2937;">{len(all_trades)}</div>
                <div class="metric-change neutral">All Time</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="groww-card">
                <div class="metric-label">Equity Trades</div>
                <div class="metric-value" style="color: #3b82f6;">{len(regular_trades)}</div>
                <div class="metric-change neutral">Stock Orders</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="groww-card">
                <div class="metric-label">F&O Trades</div>
                <div class="metric-value" style="color: #8b5cf6;">{len(fo_trades)}</div>
                <div class="metric-change neutral">Derivatives</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            fo_margin = st.session_state.get('fo_margin_used', 0.0)
            st.markdown(f"""
            <div class="groww-card">
                <div class="metric-label">Margin Used</div>
                <div class="metric-value" style="color: #ef4444;">{format_currency(fo_margin)}</div>
                <div class="metric-change neutral">F&O Exposure</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Export Section
        st.markdown("## 📥 Export Data")
        
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            st.markdown("### Complete Trade History")
            if all_trades:
                # Prepare combined data
                combined_trades = []
                
                # Add regular trades
                for trade in regular_trades:
                    trade_copy = trade.copy()
                    trade_copy['trade_category'] = 'Equity'
                    combined_trades.append(trade_copy)
                
                # Add F&O trades
                for trade in fo_trades:
                    trade_copy = trade.copy()
                    trade_copy['trade_category'] = 'F&O'
                    if 'position_type' in trade_copy:
                        trade_copy['type'] = trade_copy.pop('position_type')
                    combined_trades.append(trade_copy)
                
                df = pd.DataFrame(combined_trades)
                if 'timestamp' in df.columns:
                    df = df.sort_values('timestamp', ascending=False)
                
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Download All Trades",
                    data=csv,
                    file_name=f"complete_trade_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                st.info(f"📊 {len(all_trades)} total trades ready for export")
            else:
                st.warning("No trades to export yet")
        
        with col_export2:
            st.markdown("### Portfolio Summary")
            portfolio_data = self.trading_manager.get_portfolio_summary()
            
            summary_data = {
                'Metric': ['Current Capital', 'Available Cash', 'Total Invested', 'Unrealized P&L', 'F&O Margin Used', 'Total Orders'],
                'Value': [
                    f"₹{portfolio_data.get('total_portfolio_value', 0):,.2f}",
                    f"₹{portfolio_data.get('cash', 0):,.2f}",
                    f"₹{portfolio_data.get('total_invested', 0):,.2f}",
                    f"₹{portfolio_data.get('unrealized_pnl', 0):,.2f}",
                    f"₹{portfolio_data.get('fo_margin_used', 0):,.2f}",
                    str(portfolio_data.get('total_orders', 0))
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_csv = summary_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Portfolio Summary",
                data=summary_csv,
                file_name=f"portfolio_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            st.info("📈 Current portfolio metrics")
        
        # Trade History Table
        if all_trades:
            st.markdown("## 📊 Recent Trades")
            
            # Filter options
            col_filter1, col_filter2 = st.columns(2)
            
            with col_filter1:
                trade_filter = st.selectbox(
                    "Filter by Category:",
                    ["All Trades", "Equity Only", "F&O Only"],
                    key="trade_filter"
                )
            
            with col_filter2:
                show_count = st.selectbox(
                    "Show:",
                    [10, 25, 50, "All"],
                    key="show_count"
                )
            
            # Prepare display data
            display_trades = []
            
            for trade in regular_trades:
                if trade_filter in ["All Trades", "Equity Only"]:
                    trade_copy = trade.copy()
                    trade_copy['Category'] = 'Equity'
                    display_trades.append(trade_copy)
            
            for trade in fo_trades:
                if trade_filter in ["All Trades", "F&O Only"]:
                    trade_copy = trade.copy()
                    trade_copy['Category'] = 'F&O'
                    display_trades.append(trade_copy)
            
            if display_trades:
                df = pd.DataFrame(display_trades)
                
                # Sort by timestamp
                if 'timestamp' in df.columns:
                    df = df.sort_values('timestamp', ascending=False)
                
                # Limit rows
                if show_count != "All":
                    df = df.head(show_count)
                
                # Clean up display columns
                display_columns = []
                if 'timestamp' in df.columns:
                    df['Time'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                    display_columns.append('Time')
                
                if 'Category' in df.columns:
                    display_columns.append('Category')
                
                for col in ['symbol', 'type', 'position_type', 'quantity', 'price', 'margin_used']:
                    if col in df.columns:
                        display_columns.append(col)
                
                # Display the table
                if display_columns:
                    st.dataframe(df[display_columns], use_container_width=True)
                else:
                    st.dataframe(df, use_container_width=True)
            else:
                st.info(f"No {trade_filter.lower()} found")
        else:
            st.info("No trades yet. Start trading to see your history here!")
    
    def render_ma_strategy_params(self):
        """Render Moving Average strategy parameters"""
        col1, col2 = st.columns(2)
        
        with col1:
            fast_ma = st.slider("Fast MA Period:", 5, 50, 10)
        
        with col2:
            slow_ma = st.slider("Slow MA Period:", 20, 200, 50)
        
        st.session_state.strategy_params = {
            "fast_ma": fast_ma,
            "slow_ma": slow_ma
        }
        
        st.info(f"Strategy: Buy when {fast_ma}-period MA crosses above {slow_ma}-period MA")
    
    def render_rsi_strategy_params(self):
        """Render RSI strategy parameters"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            rsi_period = st.slider("RSI Period:", 5, 30, 14)
        
        with col2:
            oversold = st.slider("Oversold Level:", 10, 40, 30)
        
        with col3:
            overbought = st.slider("Overbought Level:", 60, 90, 70)
        
        st.session_state.strategy_params = {
            "rsi_period": rsi_period,
            "oversold": oversold,
            "overbought": overbought
        }
        
        st.info(f"Strategy: Buy when RSI < {oversold}, Sell when RSI > {overbought}")
    
    def render_breakout_strategy_params(self):
        """Render Breakout strategy parameters"""
        col1, col2 = st.columns(2)
        
        with col1:
            lookback_period = st.slider("Lookback Period:", 10, 50, 20)
        
        with col2:
            breakout_threshold = st.slider("Breakout Threshold (%):", 1.0, 5.0, 2.0)
        
        st.session_state.strategy_params = {
            "lookback_period": lookback_period,
            "breakout_threshold": breakout_threshold / 100  # Convert to decimal
        }
        
        st.info(f"Strategy: Trade breakouts from {lookback_period}-day high/low with {breakout_threshold}% threshold")
    
    def start_strategy_execution(self):
        """Start strategy execution"""
        st.success("🚀 Strategy execution started! (Demo mode)")
        st.info("In a real implementation, this would start monitoring markets and placing orders based on strategy signals.")
    
    def stop_strategy_execution(self):
        """Stop strategy execution"""
        st.warning("⏹️ Strategy execution stopped!")
    
    def square_off_all_positions(self):
        """Square off all positions"""
        success, message = self.portfolio.square_off_all_positions()
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)
    
    def auto_save_user_data(self):
        """Auto-save user data after trades"""
        if self.auth.is_authenticated():
            try:
                self.auth.save_current_session_data()
            except Exception as e:
                logging.error(f"Auto-save failed: {e}")
    
    def handle_option_trade(self, symbol: str, strike: float, option_type: str, action: str, price: float, expiry_date, lots: int = 1):
        """Handle option trade execution"""
        try:
            # Create option contract
            from core.fo_instruments import OptionType
            opt_type = OptionType.CALL if option_type == "CALL" else OptionType.PUT
            
            # Get spot price
            spot_price = self.fo_market_data.get_spot_price(symbol)
            
            # Create contract
            contract = self.fo_market_data.fo_manager.create_options_contract(
                symbol, strike, opt_type, expiry_date, spot_price
            )
            
            # Use the lots parameter
            quantity = lots
            
            # Calculate margin requirement
            margin_required = self.fo_market_data.get_margin_requirement(contract, quantity, action)
            
            # Check available margin
            available_margin = self.fo_portfolio.get_available_margin()
            
            if margin_required <= available_margin:
                # Place the order
                success, message = self.fo_portfolio.place_fo_order(
                    contract, action, quantity, price
                )
                
                if success:
                    # Create contract display name
                    contract_name = f"{symbol} {strike:.0f} {option_type}"
                    action_text = "Bought" if action == "BUY" else "Sold"
                    lot_text = "lot" if quantity == 1 else "lots"
                    
                    st.success(f"✅ {action_text} {quantity} {lot_text} of {contract_name} at ₹{price:.2f}")
                    
                    # Show margin info
                    st.info(f"💰 Margin Used: ₹{margin_required:,.2f} | Available: ₹{available_margin - margin_required:,.2f}")
                    
                    # Auto-save data after successful trade
                    self.auto_save_user_data()
                    
                    # Refresh the page to show updated positions
                    st.rerun()
                else:
                    st.error(f"❌ Order failed: {message}")
            else:
                st.error(f"❌ Insufficient margin! Required: ₹{margin_required:,.2f}, Available: ₹{available_margin:,.2f}")
                
        except Exception as e:
            st.error(f"❌ Trade execution failed: {str(e)}")
            logging.error(f"Option trade error: {e}")
    
    def display_backtest_results(self, results):
        """Display backtest results"""
        if "error" in results:
            st.error(f"Backtest failed: {results['error']}")
            return
        
        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Return", f"{results.get('total_return', 0):.2f}%")
        
        with col2:
            st.metric("Max Drawdown", f"{results.get('max_drawdown', 0):.2f}%")
        
        with col3:
            st.metric("Total Trades", results.get('total_trades', 0))
        
        with col4:
            st.metric("Final Value", f"₹{results.get('final_value', 0):,.0f}")
        
        # Portfolio value chart
        if 'portfolio_value' in results and results['portfolio_value']:
            st.markdown("### 📈 Portfolio Performance")
            
            portfolio_values = results['portfolio_value']
            dates = pd.date_range(start=datetime.now() - timedelta(days=len(portfolio_values)), 
                                 periods=len(portfolio_values), freq='D')
            
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=portfolio_values,
                mode='lines',
                name='Portfolio Value',
                line=dict(color='#1f77b4', width=2)
            ))
            
            fig.update_layout(
                title="Backtest Portfolio Performance",
                xaxis_title="Date",
                yaxis_title="Portfolio Value (₹)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Trade signals
        if 'signals' in results and results['signals']:
            st.markdown("### 📊 Trade Signals")
            signals_df = pd.DataFrame(results['signals'])
            st.dataframe(signals_df, use_container_width=True)
    
    def render_trade_analysis(self):
        """Render trade analysis"""
        trade_history = self.get_trade_history()
        
        if not trade_history:
            st.info("No trades to analyze")
            return
        
        df = pd.DataFrame(trade_history)
        
        # Trade statistics
        total_trades = len(df)
        profitable_trades = len(df[df['pnl'] > 0]) if 'pnl' in df.columns else 0
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Trades", total_trades)
        
        with col2:
            st.metric("Profitable Trades", profitable_trades)
        
        with col3:
            st.metric("Win Rate", f"{win_rate:.1f}%")
        
        # Recent trades table
        st.dataframe(df.tail(10), use_container_width=True)
    
    def render_risk_analysis(self):
        """Render risk analysis"""
        portfolio_summary = self.portfolio.get_portfolio_summary()
        risk_metrics = self.portfolio.calculate_risk_metrics()
        
        # Risk metrics
        st.metric("Portfolio Concentration", f"{risk_metrics.get('concentration_risk', 0):.1f}%")
        st.metric("Diversification Score", f"{risk_metrics.get('diversification_score', 0):.1f}%")
        
        # Sector allocation
        if risk_metrics.get('sector_risk'):
            st.markdown("#### Sector Allocation")
            sector_data = risk_metrics['sector_risk']
            
            for sector, allocation in sector_data.items():
                st.write(f"**{sector}**: {allocation:.1f}%")
    
    def get_trade_history(self):
        """Get trade history from session state"""
        return st.session_state.get('trade_history', [])
    
    def run(self):
        """Main application entry point"""
        # Check authentication first
        if not self.auth.is_authenticated():
            self.auth.render_auth_page()
            return
        
        # Auto-save data periodically
        self.auth.save_current_session_data()
        
        page = self.render_sidebar()
        
        # Route to appropriate page
        if page == "Dashboard":
            self.render_dashboard()
        elif page == "Live Trading":
            self.render_live_trading()
        elif page == "Strategy Builder":
            self.render_strategy_builder()
        elif page == "Backtesting":
            self.render_backtesting()
        elif page == "Performance Analysis":
            self.render_performance_analysis()
        elif page == "F&O Trading":
            self.render_fo_trading()
        elif page == "Reports":
            self.render_reports()
        elif page == "Settings":
            self.render_settings()

if __name__ == "__main__":
    app = TradingSimulatorApp()
    app.run()
