import requests
from flask import Flask, render_template_string
from datetime import datetime, timedelta

app = Flask(__name__)

# 潔米的專屬 API 金鑰
API_KEY = '8844bf1615fcbdff71517122a6f7f53e'

def get_mlb_data():
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
            return response.json()
        return []
    except:
        return []

def format_tw_time(utc_time_str):
    try:
        utc_dt = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ")
        tw_dt = utc_dt + timedelta(hours=8)
        return tw_dt.strftime("%m/%d %H:%M")
    except:
        return utc_time_str

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
                    <div class="teams">{{ game.away_team }} (客) @ {{ game.home_team }} (主)</div>
                    <div class="time">開打時間: {{ format_tw_time(game.commence_time) }}</div>
                </a>
            {% else %}
                <p>目前沒有抓到近期的賽事資料喔！</p>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html, games=games, format_tw_time=format_tw_time)

@app.route('/game/<game_id>')
def game_detail(game_id):
    games = get_mlb_data()
    game = next((g for g in games if g['id'] == game_id), None)
    
    if not game:
        return "<h2 style='color:white; text-align:center;'>找不到這場比賽的詳細資料</h2>"

    # 幫潔米把複雜的莊家數據整理乾淨
    bookies_info = []
    for bookie in game.get('bookmakers', []):
        info = {
            'name': bookie['title'],
            'time': format_tw_time(bookie['last_update']),
            'h2h': '未開盤',
            'spread': '未開盤',
            'total': '未開盤'
        }
        for market in bookie.get('markets', []):
            outcomes = market.get('outcomes', [])
            if market['key'] == 'h2h':
                info['h2h'] = "<br>".join([f"{o['name']}: <span style='color:#00ff00'>{o['price']}</span>" for o in outcomes])
            elif market['key'] == 'spreads':
                info['spread'] = "<br>".join([f"{o['name']}: {o.get('point', '')} (<span style='color:#00ff00'>{o['price']}</span>)" for o in outcomes])
            elif market['key'] == 'totals':
                info['total'] = "<br>".join([f"{o['name']}: {o.get('point', '')} (<span style='color:#00ff00'>{o['price']}</span>)" for o in outcomes])
        bookies_info.append(info)

    html = """
    <html>
    <head>
        <title>{{ game.away_team }} @ {{ game.home_team }} - 盤口對比</title>
        <style>
            body { background-color: #1a1a1a; color: white; font-family: Arial, sans-serif; text-align: center; }
            h2 { color: #00ff00; margin-top: 30px; }
            table { margin: 30px auto; border-collapse: collapse; width: 90%; background-color: #222;}
            th, td { border: 1px solid #555; padding: 15px; text-align: center; line-height: 1.5; }
            th { background-color: #111; color: #00ff00; font-size: 18px;}
            tr:hover { background-color: #333; }
            .bookie-name { font-weight: bold; color: #ffeb3b; font-size: 18px; }
            .update-time { font-size: 12px; color: #aaa; }
            .back-btn { display: inline-block; margin: 20px; padding: 10px 20px; background-color: #555; color: white; text-decoration: none; border-radius: 5px; }
            .back-btn:hover { background-color: #777; }
        </style>
    </head>
    <body>
        <h2>{{ game.away_team }} (客) @ {{ game.home_team }} (主)</h2>
        <p>各大莊家即時盤口對比</p>
        
        <table>
            <tr>
                <th>莊家</th>
                <th>獨贏 (Moneyline)</th>
                <th>讓分 (Spread)</th>
                <th>大小分 (Total)</th>
            </tr>
            {% for bookie in bookies_info %}
            <tr>
                <td>
                    <div class="bookie-name">{{ bookie.name }}</div>
                    <div class="update-time">更新: {{ bookie.time }}</div>
                </td>
                <td>{{ bookie.h2h | safe }}</td>
                <td>{{ bookie.spread | safe }}</td>
                <td>{{ bookie.total | safe }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <a href="/" class="back-btn">⬅ 返回賽事大廳</a>
    </body>
    </html>
    """
    return render_template_string(html, game=game, bookies_info=bookies_info)

if __name__ == "__main__":
    app.run(debug=True)
