"""
User Authentication and Data Persistence System
"""

import json
import os
import hashlib
import streamlit as st
import traceback
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class UserAuth:
    def __init__(self, data_dir: str = "user_data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Create users file if it doesn't exist
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, password: str, email: str = "") -> tuple[bool, str]:
        """Register a new user"""
        try:
            # Load existing users
            with open(self.users_file, 'r') as f:
                users = json.load(f)
            
            # Check if user already exists
            if username in users:
                return False, "Username already exists"
            
            # Create new user
            users[username] = {
                'password': self.hash_password(password),
                'email': email,
                'created_at': datetime.now().isoformat(),
                'last_login': None
            }
            
            # Save users
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2)
            
            # Create user data directory
            user_data_dir = os.path.join(self.data_dir, username)
            if not os.path.exists(user_data_dir):
                os.makedirs(user_data_dir)
            
            # Initialize user portfolio data
            self.initialize_user_data(username)
            
            return True, "User registered successfully"
            
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
    def login_user(self, username: str, password: str) -> tuple[bool, str]:
        """Login user"""
        try:
            # Load users
            with open(self.users_file, 'r') as f:
                users = json.load(f)
            
            # Check if user exists
            if username not in users:
                return False, "Username not found"
            
            # Verify password
            if users[username]['password'] != self.hash_password(password):
                return False, "Invalid password"
            
            # Update last login
            users[username]['last_login'] = datetime.now().isoformat()
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2)
            
            return True, "Login successful"
            
        except Exception as e:
            return False, f"Login failed: {str(e)}"
    
    def initialize_user_data(self, username: str):
        """Initialize default portfolio data for new user"""
        user_data = {
            'portfolio': {
                'cash': 1000000.0,  # 10L starting capital
                'positions': {},
                'trade_history': [],
                'fo_positions': {},
                'fo_trade_history': [],
                'total_pnl': 0.0,
                'day_pnl': 0.0
            },
            'settings': {
                'trading_mode': 'virtual',
                'risk_tolerance': 'medium',
                'auto_square_off': True
            },
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        
        user_file = os.path.join(self.data_dir, username, 'portfolio.json')
        with open(user_file, 'w') as f:
            json.dump(user_data, f, indent=2)
    
    def save_user_data(self, username: str, data: Dict[str, Any]) -> bool:
        """Save user portfolio data"""
        try:
            user_file = os.path.join(self.data_dir, username, 'portfolio.json')
            data['last_updated'] = datetime.now().isoformat()
            
            # Serialize the entire data structure to handle any remaining non-JSON types
            serialized_data = self._serialize_dict_values(data)
            
            # Validate JSON by attempting to serialize to string first
            json_string = json.dumps(serialized_data, indent=2, default=str)
            
            # Write to a temporary file first, then move to final location
            temp_file = user_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(json_string)
            
            # Verify the temp file is valid JSON
            with open(temp_file, 'r', encoding='utf-8') as f:
                json.load(f)  # This will raise an error if JSON is invalid
            
            # If we get here, the JSON is valid, so move temp to final location
            shutil.move(temp_file, user_file)
            return True
            
        except Exception as e:
            st.error(f"Failed to save data: {str(e)}")
            st.error(f"Full error: {traceback.format_exc()}")
            
            # Clean up temp file if it exists
            temp_file = os.path.join(self.data_dir, username, 'portfolio.json.tmp')
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass  # Ignore cleanup errors
            
            return False
    
    def load_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Load user portfolio data"""
        try:
            user_file = os.path.join(self.data_dir, username, 'portfolio.json')
            
            if not os.path.exists(user_file):
                self.initialize_user_data(username)
            
            with open(user_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Validate JSON before parsing
            if not content.strip():
                st.warning(f"Empty data file for user {username}, reinitializing...")
                self.initialize_user_data(username)
                return self.load_user_data(username)
            
            try:
                return json.loads(content)
            except json.JSONDecodeError as json_error:
                st.error(f"Corrupted data file for user {username}: {str(json_error)}")
                st.info("Creating backup and reinitializing data...")
                
                # Create backup of corrupted file
                backup_file = user_file + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(user_file, backup_file)
                st.info(f"Backup created: {backup_file}")
                
                # Reinitialize with fresh data
                self.initialize_user_data(username)
                return self.load_user_data(username)
                
        except Exception as e:
            st.error(f"Failed to load data: {str(e)}")
            st.error(f"Full error: {traceback.format_exc()}")
            
            # Try to reinitialize as last resort
            try:
                st.info("Attempting to reinitialize user data...")
                self.initialize_user_data(username)
                return self.load_user_data(username)
            except:
                return None
    
    def render_auth_page(self):
        """Render Groww-like homepage with sign in/sign up"""
        
        # Remove default Streamlit styling and add custom CSS
        st.markdown("""
        <style>
        .stApp {
            background: #ffffff;
        }
        .main .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Hero Section with proper Groww styling
        st.markdown("""
        <div style="background: linear-gradient(135deg, #00d09c 0%, #00b386 100%); color: white; padding: 4rem 2rem; text-align: center;">
            <div style="font-size: 4rem; font-weight: 900; margin-bottom: 1rem; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                ✨ Manira Trading ✨
            </div>
            <div style="font-size: 1.4rem; opacity: 0.9; margin-bottom: 2rem; font-weight: 500;">
                Where Smart Investors Begin Their Journey
            </div>
            <div style="font-size: 1.1rem; opacity: 0.8; max-width: 600px; margin: 0 auto; line-height: 1.6;">
                Practice trading with virtual money, master F&O strategies, and build confidence before investing real capital. 
                Experience professional-grade tools in a completely risk-free environment.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Features Section with proper container
        st.markdown("""
        <div style="background: #f8f9fa; padding: 3rem 2rem; margin: 0;">
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div style="background: white; padding: 2rem; border-radius: 12px; text-align: center; 
                 box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin: 0; height: 300px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🎯</div>
                <h3 style="color: #1f2937; margin-bottom: 1rem;">Risk-Free Trading</h3>
                <p style="color: #6b7280; line-height: 1.5;">Practice with ₹10 Lakh virtual capital. No real money at risk while you learn.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: white; padding: 2rem; border-radius: 12px; text-align: center; 
                 box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin: 0; height: 300px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📈</div>
                <h3 style="color: #1f2937; margin-bottom: 1rem;">F&O Mastery</h3>
                <p style="color: #6b7280; line-height: 1.5;">Master Futures & Options with real-time options chain and Greeks.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="background: white; padding: 2rem; border-radius: 12px; text-align: center; 
                 box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin: 0; height: 300px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🧠</div>
                <h3 style="color: #1f2937; margin-bottom: 1rem;">Smart Strategies</h3>
                <p style="color: #6b7280; line-height: 1.5;">Create, backtest, and optimize trading strategies with advanced analytics.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div style="background: white; padding: 2rem; border-radius: 12px; text-align: center; 
                 box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin: 0; height: 300px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                <h3 style="color: #1f2937; margin-bottom: 1rem;">Live Market Data</h3>
                <p style="color: #6b7280; line-height: 1.5;">Experience real market conditions with live price feeds and data.</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Authentication Section with inline styles
        st.markdown("""
        <div style="background: white; padding: 3rem 2rem; max-width: 500px; margin: 2rem auto; 
             border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.15);">
        """, unsafe_allow_html=True)
        
        # Tab selection using session state
        if 'auth_tab' not in st.session_state:
            st.session_state.auth_tab = 'signin'
        
        # Custom tab buttons with Groww colors
        col1, col2 = st.columns(2)
        with col1:
            signin_style = "primary" if st.session_state.auth_tab == 'signin' else "secondary"
            if st.button("🔑 Sign In", key="signin_tab", use_container_width=True, type=signin_style):
                st.session_state.auth_tab = 'signin'
        with col2:
            signup_style = "primary" if st.session_state.auth_tab == 'signup' else "secondary"
            if st.button("📝 Sign Up", key="signup_tab", use_container_width=True, type=signup_style):
                st.session_state.auth_tab = 'signup'
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Render appropriate form
        if st.session_state.auth_tab == 'signin':
            self.render_groww_login_form()
        else:
            self.render_groww_register_form()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Stats Section with inline styles
        st.markdown("""
        <div style="background: #1f2937; color: white; padding: 3rem 2rem; text-align: center;">
            <h2 style="margin-bottom: 1rem; color: white;">Join Thousands of Smart Traders</h2>
            <p style="opacity: 0.8; margin-bottom: 2rem; color: white;">Building wealth through intelligent trading simulation</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Stats grid using columns with proper background
        st.markdown("""
        <div style="background: #1f2937; padding: 2rem 0;">
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div style="color: white; padding: 1rem; text-align: center;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #00d09c;">10L+</div>
                <div style="opacity: 0.8; margin-top: 0.5rem;">Virtual Capital</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="color: white; padding: 1rem; text-align: center;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #00d09c;">1000+</div>
                <div style="opacity: 0.8; margin-top: 0.5rem;">Active Traders</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="color: white; padding: 1rem; text-align: center;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #00d09c;">50+</div>
                <div style="opacity: 0.8; margin-top: 0.5rem;">Trading Strategies</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div style="color: white; padding: 1rem; text-align: center;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #00d09c;">24/7</div>
                <div style="opacity: 0.8; margin-top: 0.5rem;">Market Access</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    def render_groww_login_form(self):
        """Render Groww-style login form"""
        st.markdown("### Welcome Back! 👋")
        st.markdown("Sign in to continue your trading journey")
        
        with st.form("groww_login_form", clear_on_submit=False):
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                help="Your unique username"
            )
            password = st.text_input(
                "Password", 
                type="password",
                placeholder="Enter your password",
                help="Your account password"
            )
            
            # Custom styled submit button
            submitted = st.form_submit_button(
                "🚀 Enter Manira Trading",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                if not username or not password:
                    st.error("🚨 Please fill in all fields")
                    return
                
                success, message = self.login_user(username, password)
                
                if success:
                    # Set session state
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    
                    # Create persistent session file
                    self.create_session_file(username)
                    
                    # Load user data
                    user_data = self.load_user_data(username)
                    if user_data:
                        # Restore portfolio data to session state
                        portfolio = user_data.get('portfolio', {})
                        st.session_state.current_capital = portfolio.get('cash', 1000000.0)
                        st.session_state.positions = portfolio.get('positions', {})
                        st.session_state.trade_history = portfolio.get('trade_history', [])
                        # Restore F&O positions (need to convert back to objects)
                        fo_positions_data = portfolio.get('fo_positions', {})
                        st.session_state.fo_positions = self._restore_fo_positions(fo_positions_data)
                        
                        st.session_state.fo_trade_history = portfolio.get('fo_trade_history', [])
                        st.session_state.fo_margin_used = portfolio.get('fo_margin_used', 0.0)
                    
                    st.success(f"🎉 Welcome back, {username}!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    def render_groww_register_form(self):
        """Render Groww-style registration form"""
        st.markdown("### Join Manira Trading! 🚀")
        st.markdown("Start your trading journey with ₹10 Lakh virtual capital")
        
        with st.form("groww_register_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input(
                    "First Name",
                    placeholder="John",
                    help="Your first name"
                )
            
            with col2:
                last_name = st.text_input(
                    "Last Name", 
                    placeholder="Trader",
                    help="Your last name"
                )
            
            username = st.text_input(
                "Username",
                placeholder="john_trader",
                help="Choose a unique username (3-20 characters)"
            )
            
            email = st.text_input(
                "Email Address",
                placeholder="john@example.com",
                help="We'll send you trading insights and updates"
            )
            
            col3, col4 = st.columns(2)
            
            with col3:
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Strong password",
                    help="Minimum 6 characters"
                )
            
            with col4:
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Repeat password",
                    help="Must match your password"
                )
            
            # Terms and conditions
            terms_accepted = st.checkbox(
                "I agree to the Terms of Service and Privacy Policy",
                help="Required to create an account"
            )
            
            # Custom styled submit button
            submitted = st.form_submit_button(
                "🎯 Join Manira Trading with ₹10L",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                # Validation
                if not all([first_name, last_name, username, password]):
                    st.error("🚨 Please fill in all required fields")
                    return
                
                if not terms_accepted:
                    st.error("🚨 Please accept the Terms of Service to continue")
                    return
                
                if password != confirm_password:
                    st.error("🚨 Passwords don't match")
                    return
                
                if len(password) < 6:
                    st.error("🚨 Password must be at least 6 characters")
                    return
                
                if len(username) < 3:
                    st.error("🚨 Username must be at least 3 characters")
                    return
                
                # Create full name for display
                full_name = f"{first_name} {last_name}"
                
                success, message = self.register_user(username, password, email)
                
                if success:
                    st.success(f"🎉 Welcome to Manira Trading, {full_name}!")
                    st.success("💰 Your ₹10 Lakh virtual capital is ready!")
                    st.info("👈 Please sign in with your new account")
                    st.balloons()
                    # Switch to sign in tab
                    st.session_state.auth_tab = 'signin'
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    def render_login_form(self):
        """Render login form"""
        st.markdown("### Welcome Back!")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            if st.form_submit_button("🔑 Login", use_container_width=True):
                if not username or not password:
                    st.error("Please fill in all fields")
                    return
                
                success, message = self.login_user(username, password)
                
                if success:
                    # Set session state
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    
                    # Load user data
                    user_data = self.load_user_data(username)
                    if user_data:
                        # Restore portfolio data to session state
                        portfolio = user_data.get('portfolio', {})
                        st.session_state.current_capital = portfolio.get('cash', 1000000.0)
                        st.session_state.positions = portfolio.get('positions', {})
                        st.session_state.trade_history = portfolio.get('trade_history', [])
                        st.session_state.fo_positions = portfolio.get('fo_positions', {})
                        st.session_state.fo_trade_history = portfolio.get('fo_trade_history', [])
                    
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    def render_register_form(self):
        """Render registration form"""
        st.markdown("### Create New Account")
        
        with st.form("register_form"):
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email (Optional)", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password", placeholder="Choose a strong password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            
            if st.form_submit_button("📝 Register", use_container_width=True):
                if not username or not password:
                    st.error("Username and password are required")
                    return
                
                if password != confirm_password:
                    st.error("Passwords don't match")
                    return
                
                if len(password) < 6:
                    st.error("Password must be at least 6 characters")
                    return
                
                success, message = self.register_user(username, password, email)
                
                if success:
                    st.success(f"✅ {message}")
                    st.info("Please login with your new account")
                else:
                    st.error(f"❌ {message}")
    
    def logout(self):
        """Logout user and clear session"""
        # Save current data before logout
        if hasattr(st.session_state, 'username'):
            self.save_current_session_data()
        
        # Clear persistent session file
        self.clear_session_file()
        
        # Clear session state
        for key in ['authenticated', 'username', 'current_capital', 'positions', 'trade_history', 'fo_positions', 'fo_trade_history']:
            if key in st.session_state:
                del st.session_state[key]
        
        st.rerun()
    
    def save_current_session_data(self):
        """Save current session data to user file"""
        if not hasattr(st.session_state, 'username'):
            return
        
        username = st.session_state.username
        
        # Collect current portfolio data with proper serialization
        fo_positions = st.session_state.get('fo_positions', {})
        serialized_fo_positions = {}
        
        # Serialize F&O positions properly
        for pos_id, position in fo_positions.items():
            if hasattr(position, 'to_dict'):
                pos_dict = position.to_dict()
                # Convert any enum objects to strings
                pos_dict = self._serialize_dict_values(pos_dict)
                serialized_fo_positions[pos_id] = pos_dict
            else:
                # If already a dict, serialize it too
                serialized_fo_positions[pos_id] = self._serialize_dict_values(position)
        
        portfolio_data = {
            'portfolio': {
                'cash': st.session_state.get('current_capital', 1000000.0),
                'positions': st.session_state.get('positions', {}),
                'trade_history': st.session_state.get('trade_history', []),
                'fo_positions': serialized_fo_positions,
                'fo_trade_history': st.session_state.get('fo_trade_history', []),
                'fo_margin_used': st.session_state.get('fo_margin_used', 0.0),
                'total_pnl': 0.0,  # Calculate this based on positions
                'day_pnl': 0.0     # Calculate this based on today's trades
            },
            'settings': {
                'trading_mode': 'virtual',
                'risk_tolerance': 'medium',
                'auto_square_off': True
            }
        }
        
        self.save_user_data(username, portfolio_data)
    
    def _serialize_dict_values(self, data):
        """Recursively serialize dict values to handle enums and other non-JSON types"""
        if isinstance(data, dict):
            serialized = {}
            for key, value in data.items():
                serialized[key] = self._serialize_dict_values(value)
            return serialized
        elif isinstance(data, list):
            return [self._serialize_dict_values(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        elif hasattr(data, 'value'):  # Enum objects
            return data.value
        elif hasattr(data, '__str__') and not isinstance(data, (str, int, float, bool, type(None))):
            # Convert complex objects to strings
            return str(data)
        else:
            return data
    
    def _restore_fo_positions(self, fo_positions_data: dict) -> dict:
        """Restore F&O positions from saved data back to FOPosition objects"""
        restored_positions = {}
        
        try:
            # Import here to avoid circular imports
            from core.fo_portfolio_manager import FOPosition
            from core.fo_instruments import OptionsContract, FuturesContract, OptionType
            from datetime import datetime
            
            for position_id, position_data in fo_positions_data.items():
                if isinstance(position_data, dict):
                    try:
                        # Reconstruct the contract
                        contract_data = position_data.get('contract_data', {})
                        contract_type = position_data.get('contract_type', '')
                        
                        if contract_type == 'OptionsContract':
                            # Reconstruct OptionType enum
                            option_type_str = contract_data.get('option_type', 'CALL')
                            option_type = OptionType.CALL if option_type_str == 'CALL' else OptionType.PUT
                            
                            # Create proper OptionsContract instance
                            contract = OptionsContract(
                                symbol=contract_data.get('symbol', f"{contract_data.get('underlying', 'UNK')}OPT"),
                                underlying=contract_data.get('underlying', ''),
                                strike_price=contract_data.get('strike_price', 0),
                                option_type=option_type,
                                expiry_date=datetime.fromisoformat(contract_data.get('expiry_date', datetime.now().isoformat())),
                                lot_size=contract_data.get('lot_size', 50),
                                tick_size=contract_data.get('tick_size', 0.05),
                                premium=contract_data.get('premium', 0)
                            )
                        elif contract_type == 'FuturesContract':
                            # Create proper FuturesContract instance
                            contract = FuturesContract(
                                symbol=contract_data.get('symbol', f"{contract_data.get('underlying', 'UNK')}FUT"),
                                underlying=contract_data.get('underlying', ''),
                                expiry_date=datetime.fromisoformat(contract_data.get('expiry_date', datetime.now().isoformat())),
                                lot_size=contract_data.get('lot_size', 50),
                                tick_size=contract_data.get('tick_size', 0.05),
                                contract_size=contract_data.get('contract_size', contract_data.get('lot_size', 50))
                            )
                        else:
                            # For other contract types, create a simple object with string representation
                            class SimpleContract:
                                def __init__(self, data):
                                    for key, value in data.items():
                                        setattr(self, key, value)
                                
                                def __str__(self):
                                    return f"{getattr(self, 'underlying', 'Unknown')} Contract"
                            
                            contract = SimpleContract(contract_data)
                        
                        # Reconstruct FOPosition
                        position = FOPosition(
                            contract=contract,
                            position_type=position_data.get('position_type', 'BUY'),
                            quantity=position_data.get('quantity', 1),
                            entry_price=position_data.get('entry_price', 0),
                            entry_time=datetime.fromisoformat(position_data.get('entry_time', datetime.now().isoformat()))
                        )
                        
                        # Restore additional attributes
                        position.current_price = position_data.get('current_price', position.entry_price)
                        position.unrealized_pnl = position_data.get('unrealized_pnl', 0.0)
                        position.margin_used = position_data.get('margin_used', 0.0)
                        
                        restored_positions[position_id] = position
                        
                    except Exception as e:
                        st.warning(f"Could not restore F&O position {position_id}: {str(e)}")
                        # Keep as dict if restoration fails
                        restored_positions[position_id] = position_data
                else:
                    # Already an object, keep as is
                    restored_positions[position_id] = position_data
                    
        except ImportError as e:
            st.warning(f"Could not import F&O classes for position restoration: {str(e)}")
            # Return as-is if we can't import the classes
            return fo_positions_data
        except Exception as e:
            st.warning(f"Error restoring F&O positions: {str(e)}")
            return fo_positions_data
        
        return restored_positions
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        # First check session state
        if st.session_state.get('authenticated', False):
            return True
        
        # If not in session state, check if user has a persistent login
        return self.check_persistent_login()
    
    def get_current_user(self) -> Optional[str]:
        """Get current logged in user"""
        return st.session_state.get('username', None)
    
    def create_session_file(self, username: str):
        """Create a session file for persistent login"""
        try:
            session_file = os.path.join(self.data_dir, '.current_session')
            session_data = {
                'username': username,
                'login_time': datetime.now().isoformat(),
                'expires': (datetime.now() + timedelta(days=7)).isoformat()  # 7 days expiry
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f)
                
        except Exception as e:
            st.error(f"Failed to create session: {str(e)}")
    
    def check_persistent_login(self) -> bool:
        """Check if user has a valid persistent session"""
        try:
            session_file = os.path.join(self.data_dir, '.current_session')
            
            if not os.path.exists(session_file):
                return False
            
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check if session is expired
            expires = datetime.fromisoformat(session_data['expires'])
            if datetime.now() > expires:
                # Session expired, remove it
                os.remove(session_file)
                return False
            
            # Session is valid, restore user data
            username = session_data['username']
            st.session_state.authenticated = True
            st.session_state.username = username
            
            # Load user data
            user_data = self.load_user_data(username)
            if user_data:
                portfolio = user_data.get('portfolio', {})
                st.session_state.current_capital = portfolio.get('cash', 1000000.0)
                st.session_state.positions = portfolio.get('positions', {})
                st.session_state.trade_history = portfolio.get('trade_history', [])
                
                # Restore F&O positions (need to convert back to objects)
                fo_positions_data = portfolio.get('fo_positions', {})
                st.session_state.fo_positions = self._restore_fo_positions(fo_positions_data)
                
                st.session_state.fo_trade_history = portfolio.get('fo_trade_history', [])
                st.session_state.fo_margin_used = portfolio.get('fo_margin_used', 0.0)
            
            return True
            
        except Exception as e:
            # If there's any error, remove the session file and return False
            session_file = os.path.join(self.data_dir, '.current_session')
            if os.path.exists(session_file):
                os.remove(session_file)
            return False
    
    def clear_session_file(self):
        """Clear the persistent session file"""
        try:
            session_file = os.path.join(self.data_dir, '.current_session')
            if os.path.exists(session_file):
                os.remove(session_file)
        except Exception:
            pass  # Ignore errors when clearing session
