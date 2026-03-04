import requests
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jamie_secret_key'
# 啟動即時通訊引擎
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

API_KEY = '8844bf1615fcbdff71517122a6f7f53e' 

cache = {'data': None, 'last_time': 0}

def get_mlb_data():
    current_time = time.time()
    if cache['data'] and (current_time - cache['last_time'] < 600):
        return cache['data']
    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
    params = {"apiKey": API_KEY, "regions": "us", "markets": "h2h,spreads,totals", "oddsFormat": "american"}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            cache['data'] = response.json()
            cache['last_time'] = current_time
            return cache['data']
        return []
    except: return []

def format_tw_time(utc_str):
    try:
        dt = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)
        return dt.strftime("%m/%d %H:%M")
    except: return utc_str

# --- 聊天室的廣播中心 ---
@socketio.on('send_message')
def handle_message(data):
    # 當有人傳訊息來，立刻廣播給所有人 (包含傳送者自己)
    emit('receive_message', data, broadcast=True)

@app.route('/')
def index():
    games = get_mlb_data()
    html = """
    <html>
    <head>
        <title>潔米 MLB 專業大廳 ＋ 即時討論區</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <style>
            body { background-color: #121212; color: white; font-family: sans-serif; text-align: center; margin: 0; padding-bottom: 300px; }
            .card { background: #333; margin: 10px auto; padding: 20px; width: 80%; border-radius: 10px; border-left: 5px solid #00ff00; cursor: pointer; text-decoration: none; color: white; display: block; }
            .card:hover { background: #444; }
            
            /* 聊天室介面設計 */
            #chat-container { position: fixed; bottom: 0; right: 10%; width: 350px; height: 400px; background: #222; border: 2px solid #00ff00; border-radius: 10px 10px 0 0; display: flex; flex-direction: column; box-shadow: 0px 0px 15px rgba(0,255,0,0.2); z-index: 1000;}
            #chat-header { background: #00ff00; color: black; padding: 10px; font-weight: bold; border-radius: 8px 8px 0 0; }
            #chat-messages { flex-grow: 1; padding: 10px; overflow-y: auto; text-align: left; font-size: 14px; }
            .msg { margin-bottom: 8px; }
            .msg-name { color: #ffeb3b; font-weight: bold; margin-right: 5px; }
            #chat-input-area { display: flex; padding: 10px; background: #111; border-top: 1px solid #444;}
            #chat-name { width: 30%; padding: 5px; border-radius: 3px; border: none; margin-right: 5px; }
            #chat-input { flex-grow: 1; padding: 5px; border-radius: 3px; border: none; }
            #send-btn { background: #00ff00; color: black; border: none; padding: 5px 10px; margin-left: 5px; cursor: pointer; font-weight: bold; border-radius: 3px;}
        </style>
    </head>
    <body>
        <h1 style="color:#00ff00;">⚾ MLB 賽事大廳 (附設即時討論區)</h1>
        {% for game in games %}
        <a href="/game/{{ game.id }}?market=totals" class="card">
            <div style="font-size: 20px;">{{ game.away_team }} @ {{ game.home_team }}</div>
            <div style="color:#aaa;">開打時間：{{ format_tw_time(game.commence_time) }}</div>
        </a>
        {% endfor %}

        <div id="chat-container">
            <div id="chat-header">💬 賽事即時大廳</div>
            <div id="chat-messages"></div>
            <div id="chat-input-area">
                <input type="text" id="chat-name" placeholder="你的暱稱" value="匿名玩家">
                <input type="text" id="chat-input" placeholder="輸入訊息...">
                <button id="send-btn">傳送</button>
            </div>
        </div>

        <script>
            var socket = io();
            var messagesDiv = document.getElementById('chat-messages');
            var inputBtn = document.getElementById('send-btn');
            var inputMsg = document.getElementById('chat-input');
            var inputName = document.getElementById('chat-name');

            // 接收到新訊息時的動作
            socket.on('receive_message', function(data) {
                var newMsg = document.createElement('div');
                newMsg.className = 'msg';
                newMsg.innerHTML = '<span class="msg-name">' + data.name + ':</span> ' + data.message;
                messagesDiv.appendChild(newMsg);
                messagesDiv.scrollTop = messagesDiv.scrollHeight; // 自動捲動到底部
            });

            // 按下傳送按鈕的動作
            inputBtn.onclick = function() {
                if(inputMsg.value.trim() !== '') {
                    socket.emit('send_message', { name: inputName.value, message: inputMsg.value });
                    inputMsg.value = ''; // 清空輸入框
                }
            };
            
            // 支援按下 Enter 鍵傳送
            inputMsg.addEventListener("keypress", function(event) {
                if (event.key === "Enter") { event.preventDefault(); inputBtn.click(); }
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html, games=games, format_tw_time=format_tw_time)

# --- 內頁邏輯保持不變 ---
@app.route('/game/<game_id>')
def game_detail(game_id):
    selected_market = request.args.get('market', 'h2h')
    games = get_mlb_data()
    game = next((g for g in games if g['id'] == game_id), None)
    if not game: return "資料讀取失敗，可能是 API 額度滿了"
    rows = []
    market_names = {'h2h': '獨贏 (Moneyline)', 'spreads': '讓分 (Spread)', 'totals': '大小球 (Totals)'}
    for bookie in game.get('bookmakers', []):
        market_data = next((m for m in bookie['markets'] if m['key'] == selected_market), None)
        if market_data:
            odds_str = " | ".join([f"{o['name']} {o.get('point', '')} (<span style='color:#00ff00'>{o['price']}</span>)" for o in market_data['outcomes']])
            rows.append(f"<tr><td style='color:#ffeb3b; font-weight:bold;'>{bookie['title']}</td><td>{odds_str}</td></tr>")
    html = f"""
    <html>
    <head>
        <style>
            body {{ background-color: #121212; color: white; font-family: sans-serif; text-align: center; }}
            .btn {{ padding: 10px 20px; margin: 5px; cursor: pointer; background: #444; color: white; border: none; border-radius: 5px; text-decoration: none; display: inline-block; }}
            .active {{ background: #00ff00; color: black; font-weight: bold; }}
            table {{ width: 90%; margin: 20px auto; border-collapse: collapse; }}
            th, td {{ border: 1px solid #555; padding: 12px; text-align: center; }}
            th {{ background: #222; color: #00ff00; }}
        </style>
    </head>
    <body>
        <h2>{game['away_team']} @ {game['home_team']}</h2>
        <div>
            <a href="?market=h2h" class="btn {'active' if selected_market=='h2h' else ''}">獨贏</a>
            <a href="?market=spreads" class="btn {'active' if selected_market=='spreads' else ''}">讓分</a>
            <a href="?market=totals" class="btn {'active' if selected_market=='totals' else ''}">大小球</a>
        </div>
        <table>
            <tr><th>莊家</th><th>{market_names.get(selected_market)} 賠率</th></tr>
            {"".join(rows)}
        </table>
        <br><a href="/" style="color:#aaa;">⬅ 返回大廳</a>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    socketio.run(app, debug=True)
