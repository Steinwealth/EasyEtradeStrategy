#!/usr/bin/env python3
"""
Prime Rank Dashboard
===================

A simple web dashboard to view prime rankings after market hours.
This creates a local web server to display rankings in a browser.

Usage:
    python3 prime_rank_dashboard.py
    python3 prime_rank_dashboard.py --port 8080
    python3 prime_rank_dashboard.py --host 0.0.0.0
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

class PrimeRankHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.data_file = Path("symbol_scores.json")
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.serve_dashboard()
        elif self.path == '/api/rankings':
            self.serve_rankings_api()
        elif self.path.startswith('/api/symbol/'):
            symbol = self.path.split('/')[-1]
            self.serve_symbol_api(symbol)
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        html = self.get_dashboard_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_rankings_api(self):
        """Serve rankings as JSON API"""
        try:
            data = self.load_data()
            rankings = self.get_rankings(data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(rankings).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def serve_symbol_api(self, symbol):
        """Serve specific symbol data as JSON API"""
        try:
            data = self.load_data()
            symbol_data = data.get('symbol_ranks', {}).get(symbol.upper())
            
            if not symbol_data:
                self.send_error(404, f"Symbol {symbol} not found")
                return
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(symbol_data).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def load_data(self):
        """Load symbol score data"""
        if not self.data_file.exists():
            return {}
        
        with open(self.data_file, 'r') as f:
            return json.load(f)
    
    def get_rankings(self, data):
        """Get sorted rankings"""
        symbol_ranks = data.get('symbol_ranks', {})
        sorted_symbols = sorted(
            symbol_ranks.items(),
            key=lambda x: x[1].get('avg_prime_score', 0),
            reverse=True
        )
        
        return [
            {
                'rank': rank,
                'symbol': symbol,
                'avg_prime_score': data.get('avg_prime_score', 0),
                'total_trades': data.get('total_trades', 0),
                'win_rate': data.get('win_rate', 0),
                'total_profit': data.get('total_profit', 0),
                'avg_trade_size': data.get('avg_trade_size', 0)
            }
            for rank, (symbol, data) in enumerate(sorted_symbols, 1)
        ]
    
    def get_dashboard_html(self):
        """Generate dashboard HTML"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Prime Symbol Rankings</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 5px; }}
        .stat {{ text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        .refresh-btn {{ background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 10px 0; }}
        .refresh-btn:hover {{ background: #0056b3; }}
        .loading {{ text-align: center; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 Prime Symbol Rankings</h1>
        <div class="stats" id="stats">
            <div class="stat">
                <div class="stat-value" id="total-symbols">-</div>
                <div class="stat-label">Total Symbols</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="total-trades">-</div>
                <div class="stat-label">Total Trades</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="last-updated">-</div>
                <div class="stat-label">Last Updated</div>
            </div>
        </div>
        
        <button class="refresh-btn" onclick="loadRankings()">🔄 Refresh Data</button>
        
        <div id="rankings-container">
            <div class="loading">Loading rankings...</div>
        </div>
    </div>

    <script>
        function loadRankings() {{
            document.getElementById('rankings-container').innerHTML = '<div class="loading">Loading rankings...</div>';
            
            fetch('/api/rankings')
                .then(response => response.json())
                .then(data => {{
                    displayRankings(data);
                    updateStats(data);
                }})
                .catch(error => {{
                    document.getElementById('rankings-container').innerHTML = 
                        '<div style="color: red;">Error loading data: ' + error + '</div>';
                }});
        }}
        
        function displayRankings(rankings) {{
            if (rankings.length === 0) {{
                document.getElementById('rankings-container').innerHTML = 
                    '<div style="text-align: center; color: #666; padding: 40px;">No data available yet. The system needs to complete some trades.</div>';
                return;
            }}
            
            let html = `
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Symbol</th>
                            <th>Avg Prime Score</th>
                            <th>Trades</th>
                            <th>Win Rate</th>
                            <th>Total Profit</th>
                            <th>Avg Trade Size</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            rankings.forEach(item => {{
                const profitClass = item.total_profit >= 0 ? 'positive' : 'negative';
                html += `
                    <tr>
                        <td>${{item.rank}}</td>
                        <td><strong>${{item.symbol}}</strong></td>
                        <td>${{item.avg_prime_score.toFixed(2)}}</td>
                        <td>${{item.total_trades}}</td>
                        <td>${{item.win_rate.toFixed(1)}}%</td>
                        <td class="${{profitClass}}">$${{item.total_profit.toFixed(2)}}</td>
                        <td>$${{item.avg_trade_size.toFixed(2)}}</td>
                    </tr>
                `;
            }});
            
            html += '</tbody></table>';
            document.getElementById('rankings-container').innerHTML = html;
        }}
        
        function updateStats(rankings) {{
            document.getElementById('total-symbols').textContent = rankings.length;
            document.getElementById('total-trades').textContent = 
                rankings.reduce((sum, item) => sum + item.total_trades, 0);
            document.getElementById('last-updated').textContent = 
                new Date().toLocaleTimeString();
        }}
        
        // Load data on page load
        loadRankings();
        
        // Auto-refresh every 30 seconds
        setInterval(loadRankings, 30000);
    </script>
</body>
</html>
        """
    
    def log_message(self, format, *args):
        """Override to reduce log noise"""
        pass

def main():
    parser = argparse.ArgumentParser(description='Prime Rank Dashboard')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    
    args = parser.parse_args()
    
    server_address = (args.host, args.port)
    httpd = HTTPServer(server_address, PrimeRankHandler)
    
    print(f"🌐 Prime Rank Dashboard starting...")
    print(f"   URL: http://{args.host}:{args.port}")
    print(f"   Press Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")
        httpd.shutdown()

if __name__ == "__main__":
    main()
