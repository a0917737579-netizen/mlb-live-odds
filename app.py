import requests
from flask import Flask, render_template_string, request
from datetime import datetime, timedelta
import time

app = Flask(__name__)

# --- 設定區域 ---
# 如果安哥拿到新的免費 500 次 KEY，請把下面這行換掉：
API_KEY = '8844bf1615fcbdff71517122a6f7f53e' 

# 增加簡單的快取機制，避免太多人重複刷 API 導致額度爆炸
cache = {
    'data': None,
    'last_time': 0
}

# 輔助函式：拿取 MLB 資料 (含 10 分鐘快取機制)
def get_mlb_data():
    current_time = time.time()
    
    # 如果有舊資料且小於 10 分鐘 (600秒)，直接回傳舊資料
    if cache['data'] and (current_time - cache['last_time'] < 600):
        return cache['data']
    
    # 如果沒有或太舊，就去向 API 要資料
    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "american"
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            cache['data'] = response.json()
            cache['last_time'] = current_time
            return cache['data']
        else:
            return []
    except Exception as e:
        print(f"API Error: {e}")
        return []

# 輔助函式：將 UTC 時間轉為台灣時間格式
def format_tw_time(utc_str):
    try:
        # 解析 UTC 時間
        dt = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%SZ")
        # 加 8 小時
        dt = dt + timedelta(hours=8)
        # 格式化為 %m/%d %H:%M
        return dt.strftime("%m/%d %H:%M")
    except:
        return utc_str

# --- 網頁路由與 HTML/CSS (Jamie Makeover 版) ---

# 1. MLB 賽事總覽大廳 (美化卡片版)
@app.route('/')
def index():
    games = get_mlb_data()
    
    # 安哥，這裡就是我們升級後的 HTML/CSS，全部在裡面了！
    html = """
    <html>
    <head>
        <title>潔米 MLB 專業賽事大廳</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
        <style>
            /* 1. 基本設定：深色背景、現代字體 */
            body { 
                background-color: #1a1a1d; 
                color: #e1e1e1; 
                font-family: 'Roboto', sans-serif; 
                text-align: center; 
                margin: 0;
                padding: 0;
            }
            
            /* 2. 頁首標題 */
            .header-bar {
                background-color: #121212;
                padding: 30px;
                border-bottom: 2px solid #333;
                margin-bottom: 30px;
            }
            h1 { 
                margin: 0; 
                color: #fff; 
                font-size: 2.8rem; 
                font-weight: 700;
                letter-spacing: 2px;
            }
            p.subtitle { color: #888; font-size: 1.1rem; margin-top: 10px;}

            /* 3. 賽事清單區域 */
            .game-list {
                max-width: 900px;
                margin: 0 auto;
                padding: 0 15px;
            }

            /* 4. 賽事卡片設計：這就是變漂亮的關鍵！ */
            .game-card {
                background-color: #2c2c30; 
                border-radius: 10px; 
                margin-bottom: 20px; 
                padding: 25px; 
                text-decoration: none; 
                color: inherit; 
                display: block; 
                border: 1px solid #333;
                transition: transform 0.2s, box-shadow 0.2s; /* 增加懸停動畫 */
            }
            
            /* 5. 懸停效果 (Hover) */
            .game-card:hover { 
                background-color: #343439;
                transform: translateY(-5px); /* 輕微向上彈起 */
                box-shadow: 0 8px 25px rgba(0,0,0,0.5); /* 增加陰影，更立體 */
                border-color: #444;
            }
            
            /* 6. 卡片內的隊伍資訊 */
            .teams {
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.6rem;
                font-weight: bold;
            }
            .at-symbol {
                color: #555;
                margin: 0 20px;
                font-size: 1.3rem;
            }
            
            /* 7. 卡片內的時間顯示 */
            .commence-time {
                color: #aaa;
                margin-top: 15px;
                font-size: 0.95rem;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .time-icon { margin-right: 5px; color: #888;}
        </style>
    </head>
    <body>
        <div class="header-bar">
            <h1>MLB 賽事大廳</h1>
            <p class="subtitle">點擊比賽卡片，查看莊家賠率對比表</p>
        </div>
        
        <div class="game-list">
        {% for game in games %}
        <a href="/game/{{ game.id }}" class="game-card">
            <div class="teams">
                <span>{{ game.away_team }} (客)</span>
                <span class="at-symbol">@</span>
                <span>{{ game.home_team }} (主)</span>
            </div>
            <div class="commence-time">
                <span class="time-icon">🕒</span> 台灣時間: {{ format_tw_time(game.commence_time) }}
            </div>
        </a>
        {% endfor %}
        </div>
        
    </body>
    </html>
    """
    return render_template_string(html, games=games, format_tw_time=format_tw_time)

# 2. 賽事詳細賠率對比頁面 (內頁美化版)
@app.route('/game/<game_id>')
def game_detail(game_id):
    # 這裡可以預設一個 market (例如：獨贏 h2h)
    selected_market = request.args.get('market', 'h2h')
    
    games = get_mlb_data()
    # 尋找特定 ID 的比賽
    game = next((g for g in games if g['id'] == game_id), None)
    
    if not game:
        return "資料讀取失敗，可能是 API 額度滿了"
        
    rows = []
    market_names = {'h2h': '獨贏 (Moneyline)', 'spreads': '讓分 (Spread)', 'totals': '大小球 (Totals)'}
    
    # 迴圈每個莊家
    for bookie in game.get('bookmakers', []):
        market_data = next((m for m in bookie['markets'] if m['key'] == selected_market), None)
        
        if market_data:
            odds_str = " | ".join([f"{o['name']} (<span style='color:#fcfcfc;'>{o['price']}</span>)" for o in market_data['outcomes']])
            rows.append(f"<tr><td style='color:#aaa; font-weight:bold;'>{bookie['title']}</td><td>{odds_str}</td></tr>")
            
    html = f"""
    <html>
    <head>
        <title>{game['away_team']} @ {game['home_team']} 賠率對比</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {{ background-color: #1a1a1d; color: #e1e1e1; font-family: 'Roboto', sans-serif; text-align: center; }}
            h2 {{ font-size: 2.2rem; margin-bottom: 5px;}}
            p.detail-subtitle {{ color: #888; font-size: 1rem; margin-top: 0;}}
            
            /* 按鈕樣式 */
            .market-selector {{ margin: 20px; }}
            .btn {{ padding: 10px 20px; margin: 5px; cursor: pointer; background: #333; color: white; border: none; border-radius: 5px; text-decoration: none; display: inline-block;}}
            .btn:hover {{ background: #444; }}
            .active {{ background: #444; border: 2px solid #555; font-weight: bold; }}
            
            /* 表格樣式：現代簡約 */
            table {{ width: 90%; margin: 20px auto; border-collapse: collapse; background-color: #2c2c30; border-radius: 8px; overflow: hidden; }}
            th, td {{ border: 1px solid #333; padding: 15px; text-align: center; }}
            th {{ background: #121212; color: #fff; font-size: 1.1rem;}}
            
            /* 返回按鈕 */
            .back-link {{ color: #aaa; text-decoration: none; margin-top: 20px; display: inline-block;}}
            .back-link:hover {{ color: #fff; text-decoration: underline;}}
        </style>
    </head>
    <body>
        <h2>{game['away_team']} (客) @ {game['home_team']} (主)</h2>
        <p class="detail-subtitle">各大莊家即時賠率對比</p>
        
        <div class="market-selector">
            <a href="?market=h2h" class="btn {'active' if selected_market=='h2h' else ''}">獨贏</a>
            <a href="?market=spreads" class="btn {'active' if selected_market=='spreads' else ''}">讓分</a>
            <a href="?market=totals" class="btn {'active' if selected_market=='totals' else ''}">大小球</a>
        </div>
        
        <table>
            <tr>
                <th style="width: 25%;">莊家 (Bookie)</th>
                <th>{market_names.get(selected_market)} 賠率</th>
            </tr>
            {"".join(rows)}
        </table>
        
        <br>
        <a href="/" class="back-link">⬅ 返回大廳</a>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    app.run(debug=True)
