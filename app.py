import requests
from bs4 import BeautifulSoup
import json
from flask import Flask, render_template_string

app = Flask(__name__)

# 這裡是我們要抓的 MLB 網址
URL = "https://www.sportsbookreview.com/betting-odds/mlb-baseball/"

def get_mlb_odds():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(URL, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 抓取網頁內部的 JSON 資料
        script = soup.find('script', id='__NEXT_DATA__')
        data = json.loads(script.string)
        
        # 解析賽事資料
        events = data['props']['pageProps']['oddsListData']['events']
        all_games = []
        
        for event in events:
            home_team = event['homeTeam']['fullName']
            away_team = event['awayTeam']['fullName']
            
            # 抓取賠率（包含讓分、獨贏、大小球）
            odds_list = event.get('lines', {}).get('20', {}) # 預設抓 Pinnacle 或常用盤口
            
            game = {
                'teams': f"{away_team} @ {home_team}",
                'moneyline': f"{odds_list.get('moneyline', {}).get('awayLine', 'N/A')} / {odds_list.get('moneyline', {}).get('homeLine', 'N/A')}",
                'spread': f"{odds_list.get('pointspread', {}).get('awayLine', 'N/A')} / {odds_list.get('pointspread', {}).get('homeLine', 'N/A')}",
                # 這裡就是你要的大小球！
                'total': f"O {odds_list.get('total', {}).get('totalLine', 'N/A')} / U {odds_list.get('total', {}).get('totalLine', 'N/A')}"
            }
            all_games.append(game)
        return all_games
    except Exception as e:
        return [{"teams": "錯誤", "moneyline": str(e), "spread": "-", "total": "-"}]

@app.route('/')
def index():
    games = get_mlb_odds()
    # 這裡設計網頁表格，加入了「大小球」欄位
    html = """
    <html>
    <head>
        <title>潔米的 MLB 看盤神器</title>
        <style>
            body { font-family: Arial; background-color: #1a1a1a; color: white; text-align: center; }
            table { margin: auto; border-collapse: collapse; width: 80%; }
            th, td { border: 1px solid #444; padding: 12px; }
            th { background-color: #333; color: #00ff00; }
            tr:nth-child(even) { background-color: #222; }
        </style>
    </head>
    <body>
        <h2>⚾ MLB 即時賠率表 (含大小球)</h2>
        <table>
            <tr>
                <th>對戰組合 (客 @ 主)</th>
                <th>獨贏盤 (Moneyline)</th>
                <th>讓分盤 (Spread)</th>
                <th>大小球 (Total)</th>
            </tr>
            {% for game in games %}
            <tr>
                <td>{{ game.teams }}</td>
                <td>{{ game.moneyline }}</td>
                <td>{{ game.spread }}</td>
                <td>{{ game.total }}</td>
            </tr>
            {% endfor %}
        </table>
        <p>資料每幾分鐘自動更新</p>
    </body>
    </html>
    """
    return render_template_string(html, games=games)

if __name__ == "__main__":
    app.run(debug=True)
