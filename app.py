import requests
from flask import Flask, render_template_string
from datetime import datetime, timedelta

app = Flask(__name__)

# 這是妳專屬的 API 金鑰
API_KEY = '8844bf1615fcbdff71517122a6f7f53e'

def get_mlb_data():
    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
    # 我們要求抓取：美國莊家、獨贏(h2h)、讓分(spreads)、大小球(totals)
    params = {
        "apiKey": API_KEY,
        "regions": "us", 
        "markets": "h2h,spreads,totals",
        "oddsFormat": "american" # 使用美式賠率，比較符合一般看盤習慣
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# 把外國時間轉換成台灣時間的超好用小工具
def format_tw_time(utc_time_str):
    try:
        utc_dt = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ")
        tw_dt = utc_dt + timedelta(hours=8)
        return tw_dt.strftime("%m/%d %H:%M")
    except:
        return utc_time_str

# 第一層：大廳首頁 (所有今日對戰)
@app.route('/')
def index():
    games = get_mlb_data()
    html = """
    <html>
    <head>
        <title>潔米的 MLB 專業看盤大廳</title>
        <style>
            body { background-color: #1a1a1a; color: white; font-family: Arial, sans-serif; text-align: center; }
            h1 { color: #00ff00; margin-top: 30px; }
            .game-list { display: flex; flex-direction: column; align-items: center; gap: 15px; margin-top: 20px; }
            .game-card { background-color: #333; padding: 20px; width: 60%; border-radius: 10px; border-left: 6px solid #00ff00; text-decoration: none; color: white; transition: 0.2s; }
            .game-card:hover { background-color: #444; transform: scale(1.02); }
            .teams { font-size: 24px; font-weight: bold; margin-bottom: 10px; }
            .time { color: #aaa; }
        </style>
    </head>
    <body>
        <h1>⚾ MLB 賽事總覽大廳</h1>
        <p>點擊比賽進入「莊家盤口對比室」</p>
        <div class="game-list">
            {% for game in games %}
                <a href="/game/{{ game.id }}" class="game-card">
                    <div class="teams">{{ game.away_team }} @ {{ game.home_team }}</div>
                    <div class="time">開打時間: {{ format_tw_time(game.commence_time) }} (台灣時間)</div>
                </a>
            {% else %}
                <p>目前 API 沒有抓到近期的賽事資料，可能還沒開盤。</p>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html, games=games, format_tw_time=format_tw_time)

# 第二層：單場深度解析室 (各大莊家盤口)
@app.route('/game/<game_id>')
def game_detail(game_id):
    games = get_mlb_data()
    # 找出我們點擊的那場比賽
    game = next((g for g in games if g['id'] == game_id), None)
    
    if not game:
        return "<h2 style='color:white; text-align:center;'>找不到這場比賽的詳細資料</h2>"

    html = """
    <html>
    <head>
        <title>{{ game.away_team }} @ {{ game.home_team }} - 盤口對比</title>
        <style>
            body { background-color: #1a1a1a; color: white; font-family: Arial, sans-serif; text-align: center; }
            h2 { color: #00ff00; margin-top: 30px; }
            table { margin: 30px auto; border-collapse: collapse; width: 85%; }
            th, td { border: 1px solid #555; padding: 12px; text-align: center; }
            th { background-color: #222; color: #00ff00; }
            tr:nth-child(even) { background-color: #333; }
            .back-btn { display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #555; color: white; text-decoration: none; border-radius: 5px; }
            .back-btn:hover { background-color: #777; }
        </style>
    </head>
    <body>
        <h2>{{ game.away_team }} @ {{ game.home_team }}</h2>
        <p>各大莊家即時盤口 (初盤跳動追蹤功能準備中...)</p>
        
        <table>
            <tr>
                <th>莊家 (Bookmaker)</th>
                <th>更新時間</th>
            </tr>
            {% for bookie in game.bookmakers %}
            <tr>
                <td style="font-weight: bold; color: #ffeb3b;">{{ bookie.title }}</td>
                <td>{{ format_tw_time(bookie.last_update) }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <a href="/" class="back-btn">⬅ 返回賽事大廳</a>
    </body>
    </html>
    """
    return render_template_string(html, game=game, format_tw_time=format_tw_time)

if __name__ == "__main__":
    app.run(debug=True)
