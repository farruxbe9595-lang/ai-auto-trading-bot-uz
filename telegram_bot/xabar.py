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
def balans_xabari():
    from saqlash.baza import balans_holati, ochiq_savdolar, bugungi_statistika
    from asosiy.sozlamalar import MAKSIMAL_OCHIQ_SAVDO

    balans = balans_holati()
    ochiq = len(ochiq_savdolar())
    stat = bugungi_statistika()

    return (
        f"💼 <b>BALANS HOLATI</b>\n"
        f"Umumiy balans: <b>{balans['umumiy']:.2f}$</b>\n"
        f"Erkin balans: <b>{balans['erkin']:.2f}$</b>\n"
        f"Band balans: <b>{balans['band']:.2f}$</b>\n"
        f"Ochiq savdolar: <b>{ochiq}/{MAKSIMAL_OCHIQ_SAVDO}</b>\n"
        f"Bugungi natija: <b>{stat['foyda_zarar']:.2f}$</b>\n"
        f"Ketma-ket zarar: <b>{stat['ketma_ket_zarar']}</b>"
    )


def savdo_ochildi_xabari(t):
    from asosiy.sozlamalar import BITTA_SAVDO_USD
    from saqlash.baza import balans_holati, ochiq_savdolar
    from asosiy.sozlamalar import MAKSIMAL_OCHIQ_SAVDO

    balans = balans_holati()
    ochiq = len(ochiq_savdolar())

    sl = 'yo‘q' if t['zararni_toxtatish'] is None else f"{t['zararni_toxtatish']:.4f}"
    tp = 'yo‘q' if t['foydani_olish'] is None else f"{t['foydani_olish']:.4f}"

    return (
        f"✅ <b>Savdo ochildi: {t['symbol']}</b>\n"
        f"💰 Tikilgan: <b>{BITTA_SAVDO_USD:.2f}$</b>\n\n"
        f"📌 Kirish narxi: <b>{t['narx']:.4f}</b>\n"
        f"🛑 Zarar chegarasi: <b>{sl}</b>\n"
        f"🎯 Foyda chegarasi: <b>{tp}</b>\n"
        f"📊 Ishonchlilik: <b>{t['ishonch_foizi']}%</b>\n"
        f"📈 Trend: <b>{t['trend']}</b>\n\n"
        f"💼 Erkin balans: <b>{balans['erkin']:.2f}$</b>\n"
        f"📦 Band balans: <b>{balans['band']:.2f}$</b>\n"
        f"📊 Ochiq savdolar: <b>{ochiq}/{MAKSIMAL_OCHIQ_SAVDO}</b>"
    )


def savdo_yopildi_xabari(trade_id, symbol, fz, sabab):
    belgi = "✅" if fz >= 0 else "❌"

    return (
        f"📌 <b>Sinov savdosi yopildi</b>\n"
        f"ID: <b>{trade_id}</b> | {symbol}\n"
        f"{belgi} Natija: <b>{fz:.4f}$</b>\n"
        f"Sabab: <b>{sabab}</b>\n\n"
        f"{balans_xabari()}"
    )
