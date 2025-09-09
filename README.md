# 🎯 Personal Trading Simulator

**Advanced Strategy Development & Backtesting Platform**

A comprehensive trading simulator focused on strategy development, backtesting, and preparation for real trading. No social features - just pure trading strategy development.

## 🚀 Quick Start

```bash
cd D:\Groww\trading-simulator
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501` and start developing your trading strategies!

## ✨ Features

### 📊 **Live Trading Simulation**
- ✅ **₹10,00,000 virtual capital** - Practice with realistic amounts
- ✅ **Real market data** - Uses Yahoo Finance API for Indian stocks
- ✅ **Real-time portfolio tracking** - Live P&L, positions, performance
- ✅ **Risk management** - Position sizing, stop losses, margin calculations
- ✅ **Order management** - Market/Limit orders, order history

### 📈 **Strategy Builder**
- ✅ **Pre-built strategies** - Moving Average, RSI, Breakout patterns
- ✅ **Parameter optimization** - Fine-tune strategy parameters
- ✅ **Custom indicators** - Technical analysis tools
- ✅ **Strategy templates** - Quick start with proven strategies
- ✅ **Live strategy execution** - Automated trading based on signals

### 🔄 **Advanced Backtesting**
- ✅ **Historical simulation** - Test strategies on years of data
- ✅ **Performance metrics** - Sharpe ratio, max drawdown, win rate
- ✅ **Strategy comparison** - Compare multiple strategies side-by-side
- ✅ **Parameter optimization** - Find optimal settings automatically
- ✅ **Risk analysis** - Comprehensive risk assessment

### 📋 **Performance Analysis**
- ✅ **Detailed reports** - Trade analysis, performance breakdown
- ✅ **Risk metrics** - VaR, beta, volatility analysis
- ✅ **Portfolio analytics** - Sector allocation, concentration risk
- ✅ **Export capabilities** - CSV exports for further analysis

## 🎯 **Perfect For:**

- **📚 Learning trading strategies** - Understand how different approaches work
- **🧪 Strategy development** - Build and test your own trading systems
- **📊 Performance analysis** - Analyze what works and what doesn't
- **🎮 Risk-free practice** - Perfect your skills before real trading
- **📈 Backtesting ideas** - Validate strategies on historical data

## 📊 **Available Strategies**

### 1. 📈 Moving Average Crossover
- **Logic**: Buy when fast MA crosses above slow MA
- **Parameters**: Fast period (5-50), Slow period (20-200)
- **Risk Level**: Medium
- **Best For**: Trending markets

### 2. ⚡ RSI Mean Reversion
- **Logic**: Buy oversold, sell overbought conditions
- **Parameters**: RSI period (5-30), Oversold (10-40), Overbought (60-90)
- **Risk Level**: Low-Medium
- **Best For**: Range-bound markets

### 3. 🚀 Breakout Trading
- **Logic**: Trade breakouts from support/resistance
- **Parameters**: Lookback period (10-50), Breakout threshold (1-5%)
- **Risk Level**: High
- **Best For**: Volatile markets with clear levels

## 🛠️ **Technical Architecture**

```
trading-simulator/
├── app.py                          # Main Streamlit application
├── core/
│   ├── market_data.py              # Real & mock market data
│   ├── portfolio_manager.py        # Position & P&L management
│   ├── strategy_engine.py          # Trading strategy implementations
│   ├── backtester.py              # Comprehensive backtesting engine
│   └── utils.py                   # Utility functions & calculations
├── requirements.txt               # Python dependencies
└── README.md                     # This file
```

## 📊 **Supported Instruments**

### Indian Stocks:
- **Large Cap**: RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK
- **Banking**: SBIN, KOTAKBANK, AXISBANK, INDUSINDBK
- **IT**: WIPRO, HCLTECH, TECHM
- **Auto**: MARUTI, TATAMOTORS
- **FMCG**: HINDUNILVR, ITC, NESTLEIND
- **And many more...**

### Indices:
- **NIFTY 50** - Benchmark index
- **SENSEX** - BSE benchmark
- **BANKNIFTY** - Banking sector index

### F&O Instruments:
- **Index Options** - NIFTY, BANKNIFTY options
- **Stock Options** - Individual stock options
- **Index Futures** - NIFTY, BANKNIFTY futures
- **Stock Futures** - Individual stock futures
- **Weekly Options** - Short-term options trading

## 🎯 **Strategy Development Workflow**

### 1. **Idea Generation**
- Research market patterns
- Identify trading opportunities
- Define entry/exit rules

### 2. **Strategy Building**
- Use pre-built templates
- Customize parameters
- Add risk management rules

### 3. **Backtesting**
- Test on historical data
- Analyze performance metrics
- Optimize parameters

### 4. **Live Simulation**
- Deploy strategy with virtual money
- Monitor real-time performance
- Refine based on results

### 5. **Real Trading Preparation**
- Validate strategy robustness
- Set up risk management
- Prepare for live deployment

## 📈 **Performance Metrics**

### Return Metrics:
- **Total Return** - Overall strategy performance
- **Annual Return** - Annualized returns
- **Sharpe Ratio** - Risk-adjusted returns
- **Sortino Ratio** - Downside risk-adjusted returns

### Risk Metrics:
- **Maximum Drawdown** - Worst peak-to-trough decline
- **Volatility** - Price movement variability
- **Value at Risk (VaR)** - Potential losses
- **Beta** - Market correlation

### Trade Metrics:
- **Win Rate** - Percentage of profitable trades
- **Profit Factor** - Gross profit / Gross loss
- **Average Win/Loss** - Average profit per winning/losing trade
- **Maximum Consecutive Losses** - Risk assessment

## 🔧 **Configuration**

### Market Data:
- **Real Data**: Uses Yahoo Finance API (default)
- **Mock Data**: Simulated data for testing
- **Update Frequency**: Configurable refresh intervals

### Risk Management:
- **Position Sizing**: Percentage of capital per trade
- **Stop Loss**: Automatic loss limitation
- **Take Profit**: Profit booking levels
- **Maximum Positions**: Portfolio concentration limits

## 🚀 **Getting Started Guide**

### Step 1: Installation
```bash
git clone <repository>
cd trading-simulator
pip install -r requirements.txt
```

### Step 2: Launch Application
```bash
streamlit run app.py
```

### Step 3: Explore Dashboard
- View portfolio overview
- Check market data
- Review performance metrics

### Step 4: Build Your First Strategy
- Go to "Strategy Builder"
- Select "Moving Average Crossover"
- Set parameters: Fast MA = 10, Slow MA = 50
- Click "Start Strategy"

### Step 5: Backtest Your Strategy
- Go to "Backtesting"
- Select your strategy and stock
- Set date range (1 year recommended)
- Click "Run Backtest"

### Step 6: Analyze Results
- Review performance metrics
- Check trade history
- Optimize parameters if needed

## 📚 **Learning Resources**

### Strategy Guides:
- **Moving Averages** - Trend following basics
- **RSI Trading** - Momentum oscillator strategies
- **Breakout Systems** - Volatility-based approaches
- **Risk Management** - Position sizing and stops

### Market Analysis:
- **Technical Indicators** - RSI, MACD, Bollinger Bands
- **Chart Patterns** - Support/resistance, breakouts
- **Market Timing** - Entry and exit techniques
- **Portfolio Management** - Diversification and allocation

### 🎲 **F&O Trading (NEW!)**
- ✅ **Options Chain** - Real-time options data with Greeks
- ✅ **Futures Trading** - Complete futures trading simulation
- ✅ **Options Strategies** - Bull/Bear spreads, Straddles, Iron Condor
- ✅ **Greeks Calculator** - Delta, Gamma, Theta, Vega calculations
- ✅ **Margin Management** - Accurate F&O margin calculations
- ✅ **Strategy Builder** - Multi-leg options strategies
- ✅ **P&L Scenarios** - Position calculator and risk analysis

## 🔮 **Future Enhancements**

- **Algorithmic Trading** - Automated execution systems
- **Machine Learning** - AI-powered strategy generation
- **Real Broker Integration** - Live trading connectivity
- **Advanced Analytics** - Monte Carlo simulations
- **Custom Indicators** - Build your own technical indicators
- **Advanced F&O** - Exotic options and complex derivatives

## 🆘 **Support & Troubleshooting**

### Common Issues:

**Q: Market data not loading?**
A: Check internet connection. App uses Yahoo Finance API.

**Q: Strategy not generating signals?**
A: Ensure sufficient historical data and correct parameters.

**Q: Backtest taking too long?**
A: Reduce date range or use simpler strategies for faster results.

**Q: How to export results?**
A: Use the "Export Data" button in Settings or Performance Analysis.

## 🚀 **Start Your Trading Journey**

```bash
streamlit run app.py
```

**🎯 Strategy Development** - Build and test your ideas  
**📊 Performance Analysis** - Understand what works  
**🎮 Risk-Free Practice** - Perfect your skills  
**📈 Real Trading Preparation** - Get ready for live markets  

**Master Your Strategies, Master The Markets!** 🚀📈
