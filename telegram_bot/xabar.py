import requests
from asosiy.sozlamalar import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def telegramga_yubor(matn):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(matn)
        return
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    try:
        requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'text': matn, 'parse_mode': 'HTML'}, timeout=15)
    except Exception as e:
        print('Telegram xabar xatosi:', e)


def tavsiya_xabari(t, xavf_matni, ai_matni):
    sl = 'yo‘q' if t['zararni_toxtatish'] is None else f"{t['zararni_toxtatish']:.4f}"
    tp = 'yo‘q' if t['foydani_olish'] is None else f"{t['foydani_olish']:.4f}"
    return f"""
📊 <b>{t['symbol']} — BOT TAVSIYASI</b>

Tavsiya: <b>{t['tavsiya']}</b>
Ishonchlilik: <b>{t['ishonch_foizi']}%</b>
Narx: <b>{t['narx']:.4f}</b>
Trend: <b>{t['trend']}</b>
RSI: <b>{t['rsi']:.2f}</b>
Bozor keskinligi: <b>{t['vol_holat']}</b>

Tayanch: <b>{t['tayanch']:.4f}</b>
To‘siq: <b>{t['tosiq']:.4f}</b>
Zararni to‘xtatish: <b>{sl}</b>
Foydani olish: <b>{tp}</b>

Xavf tekshiruvi: <b>{xavf_matni}</b>

🧠 {ai_matni}
"""
