from flask import Flask, render_template_string
import requests
import json
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

@app.route('/')
def index():
    url = "https://www.sportsbookreview.com/betting-odds/mlb-baseball/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        script_tag = soup.find('script', id='__NEXT_DATA__')
        
        if not script_tag:
            return "<h1>暫時抓不到資料，請重新整理網頁。</h1>"

        data = json.loads(script_tag.text)
        game_rows = data['props']['pageProps']['oddsTables'][0]['oddsTableModel']['gameRows']
        
        html_content = ""
        for game in game_rows:
            away = game['gameView']['awayTeam']['shortName']
            home = game['gameView']['homeTeam']['shortName']
            time = game['gameView'].get('startDate', '').split('T')[-1][:5]
            
            odds_views = game.get('oddsViews', {})
            # 抓取第一個莊家的盤口
            odds_list = list(odds_views.values()) if isinstance(odds_views, dict) else odds_views
            odds_item = odds_list[0] if odds_list else None
            
            if odds_item:
                curr = odds_item.get('currentLine', {})
                open_l = odds_item.get('openingLine', {})
                c_a, c_h = curr.get('awayOdds'), curr.get('homeOdds')
                o_a, o_h = open_l.get('awayOdds') if isinstance(open_l, dict) else None, open_l.get('homeOdds') if isinstance(open_l, dict) else None
                
                alert = "⚠️ 跳盤" if str(c_a) != str(o_a) else ""
                bg_color = "bg-red-900/20" if alert else "bg-gray-800"
                
                html_content += f"""
                <tr class="border-b border-gray-700 {bg_color}">
                    <td class="p-3 text-blue-400 font-bold">{time}<br><span class="text-white">{away}@{home}</span></td>
                    <td class="p-3 text-gray-400">客{o_a} | 主{o_h}</td>
                    <td class="p-3 text-white font-bold text-lg">客{c_a} | 主{c_h}</td>
                    <td class="p-3 text-red-400 animate-pulse">{alert}</td>
                </tr>
                """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.tailwindcss.com"></script>
            <title>MLB 即時看盤</title>
        </head>
        <body class="bg-gray-900 text-gray-100 p-4">
            <h1 class="text-2xl font-bold mb-4 text-center text-blue-500">⚡ MLB 專業跳盤監視器</h1>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <tr class="bg-gray-800 text-gray-400 text-sm">
                        <th class="p-3">時間/對戰</th><th class="p-3">初盤</th><th class="p-3">現盤</th><th class="p-3">狀態</th>
                    </tr>
                    {html_content}
                </table>
            </div>
            <p class="text-center text-gray-500 text-xs mt-4 font-bold">下拉或手動重新整理網頁即可更新數據</p>
        </body>
        </html>
        """
    except Exception as e:
        return f"<h1>系統讀取中，請稍候再試。</h1><p>{str(e)}</p>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
