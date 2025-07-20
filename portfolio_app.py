#!/usr/bin/env python3
"""
Portfolio Analyzer - Complete Application
Single file application - Just run: python portfolio_app.py
"""

import os
import sys
import subprocess
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import yfinance as yf
import webbrowser
import threading
import time

# Install required packages
def install_requirements():
    """Auto-install required packages"""
    required = ['flask', 'flask-cors', 'pandas', 'numpy', 'yfinance']
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

# Run installation
print("Checking dependencies...")
install_requirements()

# Create Flask app
app = Flask(__name__)
CORS(app)

# Configuration
DATABASE = 'portfolio.db'
PORT = 5000

# HTML Template (embedded)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Analyzer</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        h1 {
            text-align: center;
            font-size: 3em;
            background: linear-gradient(45deg, #4cc9f0, #7209b7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 30px;
        }
        
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
            justify-content: center;
        }
        
        button {
            background: linear-gradient(45deg, #4cc9f0, #7209b7);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(76,201,240,0.4);
        }
        
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
        }
        
        .card h3 {
            color: #888;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        
        .card .value {
            font-size: 2em;
            font-weight: bold;
            color: #4cc9f0;
        }
        
        .section {
            background: #1a1a2e;
            padding: 30px;
            border-radius: 20px;
            margin-bottom: 30px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        th {
            background: #2a2a3e;
            padding: 15px;
            text-align: left;
            color: #4cc9f0;
        }
        
        td {
            padding: 15px;
            border-bottom: 1px solid #2a2a3e;
        }
        
        tr:hover {
            background: rgba(76,201,240,0.1);
        }
        
        .positive { color: #4ade80; }
        .negative { color: #f87171; }
        
        .recommendation {
            padding: 5px 15px;
            border-radius: 5px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .recommendation.sell {
            background: rgba(248, 113, 113, 0.2);
            color: #f87171;
        }
        
        .recommendation.hold {
            background: rgba(251, 191, 36, 0.2);
            color: #fbbf24;
        }
        
        .recommendation.buy {
            background: rgba(74, 222, 128, 0.2);
            color: #4ade80;
        }
        
        .chart-container {
            height: 400px;
            margin: 20px 0;
        }
        
        .upload-area {
            border: 2px dashed #4cc9f0;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            margin: 20px 0;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .upload-area:hover {
            background: rgba(76,201,240,0.1);
        }
        
        .sample-csv {
            background: #2a2a3e;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            font-family: monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Portfolio Analyzer</h1>
        
        <div class="controls">
            <input type="file" id="csvFile" accept=".csv" style="display: none;">
            <button onclick="document.getElementById('csvFile').click()">
                Upload Portfolio CSV
            </button>
            <button onclick="fetchMarketData()" id="marketBtn">
                Fetch Market Data
            </button>
            <button onclick="generateRecommendations()">
                Generate Recommendations
            </button>
            <button onclick="downloadSampleCSV()">
                Download Sample CSV
            </button>
        </div>
        
        <div class="summary-cards">
            <div class="card">
                <h3>Total Value</h3>
                <div class="value" id="totalValue">$0</div>
            </div>
            <div class="card">
                <h3>Total Return</h3>
                <div class="value" id="totalReturn">$0</div>
            </div>
            <div class="card">
                <h3>Return %</h3>
                <div class="value" id="returnPct">0%</div>
            </div>
            <div class="card">
                <h3>Holdings</h3>
                <div class="value" id="holdingsCount">0</div>
            </div>
        </div>
        
        <div class="section">
            <h2 style="color: #4cc9f0; margin-bottom: 20px;">How to Use</h2>
            <ol style="margin-left: 20px; line-height: 2;">
                <li>Click "Download Sample CSV" to get the template</li>
                <li>Fill in your portfolio data</li>
                <li>Click "Upload Portfolio CSV" to load your data</li>
                <li>Click "Fetch Market Data" for latest prices</li>
                <li>Click "Generate Recommendations" for AI advice</li>
            </ol>
        </div>
        
        <div class="section" id="recommendationsSection" style="display: none;">
            <h2 style="color: #4cc9f0; margin-bottom: 20px;">Stock Recommendations</h2>
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Value</th>
                        <th>Return</th>
                        <th>Recommendation</th>
                        <th>Action</th>
                        <th>Rationale</th>
                    </tr>
                </thead>
                <tbody id="recommendationsBody">
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2 style="color: #4cc9f0; margin-bottom: 20px;">Portfolio Allocation</h2>
            <div class="chart-container">
                <canvas id="allocationChart"></canvas>
            </div>
        </div>
        
        <div class="section">
            <h2 style="color: #4cc9f0; margin-bottom: 20px;">Performance by Stock</h2>
            <div class="chart-container">
                <canvas id="performanceChart"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        let currentPortfolio = null;
        let charts = {};
        
        // File upload handler
        document.getElementById('csvFile').addEventListener('change', function(e) {
            uploadPortfolio(e.target.files[0]);
        });
        
        async function uploadPortfolio(file) {
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await axios.post('/api/upload', formData);
                alert('Portfolio uploaded successfully!');
                loadPortfolio();
            } catch (error) {
                alert('Error uploading portfolio: ' + error.message);
            }
        }
        
        async function loadPortfolio() {
            try {
                const response = await axios.get('/api/portfolio');
                currentPortfolio = response.data;
                updateUI();
            } catch (error) {
                console.error('Error loading portfolio:', error);
            }
        }
        
        async function fetchMarketData() {
            const btn = document.getElementById('marketBtn');
            btn.textContent = 'Fetching...';
            btn.disabled = true;
            
            try {
                const response = await axios.get('/api/market-data');
                alert('Market data updated!');
                loadPortfolio();
            } catch (error) {
                alert('Error fetching market data: ' + error.message);
            } finally {
                btn.textContent = 'Fetch Market Data';
                btn.disabled = false;
            }
        }
        
        async function generateRecommendations() {
            try {
                const response = await axios.get('/api/recommendations');
                displayRecommendations(response.data.recommendations);
            } catch (error) {
                alert('Error generating recommendations: ' + error.message);
            }
        }
        
        function displayRecommendations(recommendations) {
            const tbody = document.getElementById('recommendationsBody');
            const section = document.getElementById('recommendationsSection');
            
            tbody.innerHTML = '';
            recommendations.forEach(rec => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td style="font-weight: bold; color: #7209b7;">${rec.ticker}</td>
                    <td>$${rec.current_value.toLocaleString()}</td>
                    <td class="${rec.return_percentage >= 0 ? 'positive' : 'negative'}">
                        ${rec.return_percentage.toFixed(1)}%
                    </td>
                    <td>
                        <span class="recommendation ${rec.recommendation.toLowerCase()}">
                            ${rec.recommendation}
                        </span>
                    </td>
                    <td style="font-weight: bold;">${rec.action}</td>
                    <td>${rec.rationale}</td>
                `;
            });
            
            section.style.display = 'block';
        }
        
        function updateUI() {
            if (!currentPortfolio) return;
            
            // Update summary
            const summary = currentPortfolio.summary;
            document.getElementById('totalValue').textContent = '$' + summary.total_value.toLocaleString();
            document.getElementById('totalReturn').textContent = '$' + summary.total_return.toLocaleString();
            document.getElementById('returnPct').textContent = summary.return_percentage.toFixed(2) + '%';
            document.getElementById('holdingsCount').textContent = summary.holdings_count;
            
            // Color code return
            const returnEl = document.getElementById('totalReturn');
            returnEl.className = summary.total_return >= 0 ? 'value positive' : 'value negative';
            
            const returnPctEl = document.getElementById('returnPct');
            returnPctEl.className = summary.return_percentage >= 0 ? 'value positive' : 'value negative';
            
            // Update charts
            updateCharts();
        }
        
        function updateCharts() {
            if (!currentPortfolio) return;
            
            // Destroy existing charts
            Object.values(charts).forEach(chart => chart.destroy());
            
            // Allocation Chart
            const holdings = currentPortfolio.holdings.filter(h => h.end_value > 0);
            
            const allocationCtx = document.getElementById('allocationChart').getContext('2d');
            charts.allocation = new Chart(allocationCtx, {
                type: 'doughnut',
                data: {
                    labels: holdings.map(h => h.ticker),
                    datasets: [{
                        data: holdings.map(h => h.end_value),
                        backgroundColor: generateColors(holdings.length)
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: { color: '#e0e0e0' }
                        }
                    }
                }
            });
            
            // Performance Chart
            const performanceCtx = document.getElementById('performanceChart').getContext('2d');
            const returns = currentPortfolio.holdings.map(h => {
                return h.start_value > 0 ? 
                    ((h.end_value - h.start_value) / h.start_value * 100) : 0;
            });
            
            charts.performance = new Chart(performanceCtx, {
                type: 'bar',
                data: {
                    labels: currentPortfolio.holdings.map(h => h.ticker),
                    datasets: [{
                        label: 'Return %',
                        data: returns,
                        backgroundColor: returns.map(r => r >= 0 ? 'rgba(74, 222, 128, 0.8)' : 'rgba(248, 113, 113, 0.8)')
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            ticks: { color: '#e0e0e0' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#e0e0e0' }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
        
        function generateColors(count) {
            const colors = [
                '#4cc9f0', '#7209b7', '#f72585', '#4361ee', '#3a0ca3',
                '#560bad', '#480ca8', '#3f37c9', '#b5179e', '#f72585'
            ];
            
            // Repeat colors if needed
            while (colors.length < count) {
                colors.push(...colors.slice(0, count - colors.length));
            }
            
            return colors.slice(0, count);
        }
        
        function downloadSampleCSV() {
            const csvContent = `Investment ticker symbol,Exchange,Currency,Starting investment dollar value,Ending investment dollar value,Starting share price,Ending share price,Dividends and distributions,Transaction fees,NZ withholding tax (NZD),US withholding tax (USD),AU withholding tax (AUD),Foreign withholding tax (USD),Imputation credits (NZD),ADR depositary fees (USD)
AAPL,NASDAQ,USD,1000,1200,150,180,20,5,0,3,0,0,0,0
MSFT,NASDAQ,USD,1500,1800,250,300,30,5,0,4.5,0,0,0,0
GOOGL,NASDAQ,USD,2000,2200,1000,1100,0,10,0,0,0,0,0,0`;
            
            const blob = new Blob([csvContent], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'portfolio_template.csv';
            a.click();
            URL.revokeObjectURL(url);
        }
        
        // Load portfolio on start
        loadPortfolio();
    </script>
</body>
</html>
"""

# Initialize database
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            exchange TEXT,
            currency TEXT,
            start_value REAL,
            end_value REAL,
            start_price REAL,
            end_price REAL,
            dividends REAL,
            fees REAL,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            current_price REAL,
            day_change REAL,
            volume INTEGER,
            market_cap REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    """Serve the main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get current portfolio data"""
    conn = sqlite3.connect(DATABASE)
    
    holdings_df = pd.read_sql_query(
        "SELECT * FROM holdings ORDER BY end_value DESC", 
        conn
    )
    
    conn.close()
    
    if holdings_df.empty:
        return jsonify({
            'holdings': [],
            'summary': {
                'total_value': 0,
                'total_return': 0,
                'return_percentage': 0,
                'total_dividends': 0,
                'holdings_count': 0
            }
        })
    
    # Calculate portfolio metrics
    total_value = holdings_df['end_value'].sum()
    total_start_value = holdings_df['start_value'].sum()
    total_return = total_value - total_start_value
    return_pct = (total_return / total_start_value * 100) if total_start_value > 0 else 0
    total_dividends = holdings_df['dividends'].sum()
    
    return jsonify({
        'holdings': holdings_df.to_dict('records'),
        'summary': {
            'total_value': round(total_value, 2),
            'total_return': round(total_return, 2),
            'return_percentage': round(return_pct, 2),
            'total_dividends': round(total_dividends, 2),
            'holdings_count': len(holdings_df)
        }
    })

@app.route('/api/upload', methods=['POST'])
def upload_portfolio():
    """Upload new portfolio CSV"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Read CSV
        df = pd.read_csv(file)
        
        # Map columns
        column_mapping = {
            'Investment ticker symbol': 'ticker',
            'Exchange': 'exchange',
            'Currency': 'currency',
            'Starting investment dollar value': 'start_value',
            'Ending investment dollar value': 'end_value',
            'Starting share price': 'start_price',
            'Ending share price': 'end_price',
            'Dividends and distributions': 'dividends',
            'Transaction fees': 'fees'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Save to database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Clear existing holdings
        cursor.execute("DELETE FROM holdings")
        
        # Insert new holdings
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO holdings 
                (ticker, exchange, currency, start_value, end_value, 
                 start_price, end_price, dividends, fees)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('ticker', ''),
                row.get('exchange', ''),
                row.get('currency', 'USD'),
                row.get('start_value', 0),
                row.get('end_value', 0),
                row.get('start_price', 0),
                row.get('end_price', 0),
                row.get('dividends', 0),
                row.get('fees', 0)
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Portfolio uploaded successfully',
            'holdings_count': len(df)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/market-data', methods=['GET'])
def get_market_data():
    """Fetch latest market data"""
    conn = sqlite3.connect(DATABASE)
    
    # Get unique tickers
    tickers_df = pd.read_sql_query(
        "SELECT DISTINCT ticker FROM holdings WHERE end_value > 0", 
        conn
    )
    
    if tickers_df.empty:
        conn.close()
        return jsonify({'market_data': {}, 'message': 'No holdings to update'})
    
    tickers = tickers_df['ticker'].tolist()
    market_data = {}
    
    # Fetch market data
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            current_price = info.get('regularMarketPrice', info.get('previousClose', 0))
            prev_close = info.get('previousClose', current_price)
            
            market_data[ticker] = {
                'price': current_price,
                'change': ((current_price - prev_close) / prev_close * 100) if prev_close else 0,
                'volume': info.get('regularMarketVolume', 0),
                'market_cap': info.get('marketCap', 0)
            }
            
            time.sleep(0.1)  # Rate limiting
            
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            market_data[ticker] = {'price': 0, 'change': 0, 'volume': 0, 'market_cap': 0}
    
    # Update database
    cursor = conn.cursor()
    cursor.execute("DELETE FROM market_data")
    
    for ticker, data in market_data.items():
        cursor.execute('''
            INSERT INTO market_data 
            (ticker, current_price, day_change, volume, market_cap)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            ticker, data['price'], data['change'], 
            data['volume'], data['market_cap']
        ))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'market_data': market_data,
        'last_updated': datetime.now().isoformat()
    })

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """Get buy/hold/sell recommendations"""
    conn = sqlite3.connect(DATABASE)
    
    holdings_df = pd.read_sql_query("SELECT * FROM holdings", conn)
    conn.close()
    
    if holdings_df.empty:
        return jsonify({'recommendations': [], 'message': 'No holdings found'})
    
    recommendations = []
    
    for _, holding in holdings_df.iterrows():
        ticker = holding['ticker']
        start_value = holding['start_value']
        end_value = holding['end_value']
        
        # Calculate return
        if start_value > 0:
            return_pct = ((end_value - start_value) / start_value) * 100
        else:
            return_pct = 0 if end_value == 0 else 100
        
        # Generate recommendation
        if end_value == 0 and start_value > 0:
            rec = {
                'recommendation': 'CLOSED',
                'action': 'Position Closed',
                'rationale': 'Position has been exited'
            }
        elif ticker in ['SMH'] and return_pct > 100:
            rec = {
                'recommendation': 'SELL',
                'action': 'Take Profits',
                'rationale': f'Exceptional gain of {return_pct:.1f}%. Lock in 50-70% profits'
            }
        elif ticker in ['QQQ'] and return_pct > 60:
            rec = {
                'recommendation': 'SELL',
                'action': 'Reduce Position',
                'rationale': f'Strong gain of {return_pct:.1f}%. Reduce by 40%'
            }
        elif ticker in ['SPK'] and return_pct < -30:
            rec = {
                'recommendation': 'SELL',
                'action': 'Cut Losses',
                'rationale': f'Down {abs(return_pct):.1f}%. Exit to prevent further losses'
            }
        elif return_pct > 50:
            rec = {
                'recommendation': 'SELL',
                'action': 'Take Profits',
                'rationale': f'Strong gain of {return_pct:.1f}%. Consider taking partial profits'
            }
        elif return_pct < -20:
            rec = {
                'recommendation': 'SELL',
                'action': 'Review Position',
                'rationale': f'Down {abs(return_pct):.1f}%. Review investment thesis'
            }
        elif return_pct > 20:
            rec = {
                'recommendation': 'HOLD',
                'action': 'Monitor Winner',
                'rationale': f'Good gain of {return_pct:.1f}%. Let winner run with trailing stop'
            }
        else:
            rec = {
                'recommendation': 'HOLD',
                'action': 'Maintain',
                'rationale': 'Position within normal range'
            }
        
        recommendations.append({
            'ticker': ticker,
            'current_value': round(end_value, 2),
            'return_percentage': round(return_pct, 2),
            **rec
        })
    
    return jsonify({
        'recommendations': recommendations,
        'generated_at': datetime.now().isoformat()
    })

def open_browser():
    """Open browser after server starts"""
    time.sleep(1.5)
    webbrowser.open(f'http://localhost:{PORT}')

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Portfolio Analyzer - Starting...")
    print("="*50)
    
    # Initialize database
    init_db()
    print("✓ Database initialized")
    
    # Open browser automatically
    threading.Thread(target=open_browser).start()
    
    print(f"✓ Starting server on http://localhost:{PORT}")
    print("\nYour browser will open automatically...")
    print("\nTo stop the server, press Ctrl+C")
    print("="*50 + "\n")
    
    # Run the app
    app.run(debug=False, port=PORT)