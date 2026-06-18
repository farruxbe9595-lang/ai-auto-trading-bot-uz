"""
Binance SPOT uchun signed (autentifikatsiyalangan) REST klient.

Narx ma'lumotlari hamon malumot/binance_malumot.py orqali keladi (ochiq/public
API). Bu fayl FAQAT order yuborish/bekor qilish/holatini so'rash uchun va
ANTHROPIC yoki boshqa AI bilan aloqasi yo'q — bu sof Binance integratsiyasi.

MUHIM ARXITEKTURA QARORI: bu modul faqat LONG (SOTIB_OLISH) pozitsiyalarni
ochadi. Binance SPOT'da marjasiz qisqa (short) pozitsiya ochish mumkin emas —
buning uchun avval aktivni egallab turish kerak, aks holda buyurtma "balans
yetarli emas" xatosi bilan rad etiladi. Shu sabab SOTISH signallari bu modulda
ATAYLAB qo'llab-quvvatlanmaydi (hamon faqat sinov savdosida simulyatsiya
qilinadi). Qisqa savdo kerak bo'lsa — bu Binance Margin/Futures API talab
qiladi, butunlay boshqa (yuqori xavfli: likvidatsiya, foiz to'lovi) modul.

Endpoint manbalari (2026 holatiga tekshirilgan):
- Eski POST /api/v3/order/oco DEPRECATED. Yangi: POST /api/v3/orderList/oco
  (boshqa parametr sxemasi: aboveType/belowType, eskisi: price/stopPrice).
"""

import time
import hmac
import hashlib
import decimal
import urllib.parse

import requests

from asosiy.logger import logger
from asosiy.sozlamalar import (
    BINANCE_API_KEY,
    BINANCE_API_SECRET,
    BINANCE_TESTNET,
)

BASE_URL = "https://testnet.binance.vision" if BINANCE_TESTNET else "https://api.binance.com"

_exchange_info_keshi = {}


class BinanceXatosi(Exception):
    pass


# ---------------------------------------------------------------------------
# Pastki daraja: imzolash va so'rov yuborish
# ---------------------------------------------------------------------------
def _imzo(params: dict) -> str:
    qs = urllib.parse.urlencode(params)
    return hmac.new(
        BINANCE_API_SECRET.encode("utf-8"), qs.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def _imzolangan_sorov(method: str, path: str, params: dict = None, urinishlar: int = 3):
    if not BINANCE_API_KEY or not BINANCE_API_SECRET:
        raise BinanceXatosi(
            "BINANCE_API_KEY / BINANCE_API_SECRET .env faylida yo'q. "
            "Testnet kaliti uchun: https://testnet.binance.vision"
        )

    # MUHIM: signature aynan shu dict ustida hisoblanadi va keyin requests
    # ham AYNAN shu dict'ni yuboradi — tartib (insertion order) buzilmasligi
    # kerak, aks holda Binance "Signature for this request is not valid" deb
    # qaytaradi. Shu sabab dict'ga signature qo'shilgandan keyin uni
    # o'zgartirmang.
    params = dict(params or {})
    params["timestamp"] = int(time.time() * 1000)
    params.setdefault("recvWindow", 10000)
    params["signature"] = _imzo(params)

    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    url = BASE_URL + path

    oxirgi_xato = None
    for urinish in range(1, urinishlar + 1):
        try:
            if method == "GET":
                r = requests.get(url, headers=headers, params=params, timeout=15)
            elif method == "POST":
                r = requests.post(url, headers=headers, data=params, timeout=15)
            elif method == "DELETE":
                r = requests.delete(url, headers=headers, params=params, timeout=15)
            else:
                raise ValueError(f"Noma'lum method: {method}")

            if r.status_code == 200:
                return r.json()

            # 4xx (masalan filtr xatosi, balans yetarli emas) — qayta urinish
            # foydasiz, darrov chiqamiz.
            if 400 <= r.status_code < 500:
                raise BinanceXatosi(f"Binance 4xx xatosi: {r.status_code} {r.text}")

            oxirgi_xato = BinanceXatosi(f"Binance {r.status_code}: {r.text}")
        except requests.RequestException as e:
            oxirgi_xato = e

        logger.warning(
            "Binance so'rovi muvaffaqiyatsiz (%s/%s urinish): %s",
            urinish, urinishlar, oxirgi_xato,
        )
        if urinish < urinishlar:
            time.sleep(1.5 * urinish)

    raise oxirgi_xato


def server_vaqt_farqi_ms() -> int:
    """
    Mahalliy va Binance server vaqti orasidagi farq (ms). Katta farq
    "Timestamp for this request is outside of the recvWindow" xatosining
    eng keng tarqalgan sababi — botni ishga tushirishdan oldin buni
    tekshiring (server soatini NTP bilan sinxronlang).
    """
    r = requests.get(BASE_URL + "/api/v3/time", timeout=10)
    r.raise_for_status()
    server_vaqt = r.json()["serverTime"]
    mahalliy_vaqt = int(time.time() * 1000)
    return abs(server_vaqt - mahalliy_vaqt)


# ---------------------------------------------------------------------------
# Exchange filtrlari — miqdor/narxni Binance qoidalariga moslab dumalash
# ---------------------------------------------------------------------------
def exchange_info_olish(symbol: str) -> dict:
    if symbol in _exchange_info_keshi:
        return _exchange_info_keshi[symbol]

    r = requests.get(BASE_URL + "/api/v3/exchangeInfo", params={"symbol": symbol}, timeout=15)
    r.raise_for_status()
    info = r.json()["symbols"][0]

    natija = {"step_size": 0.0, "tick_size": 0.0, "min_notional": 0.0, "min_qty": 0.0}
    for f in info["filters"]:
        if f["filterType"] == "LOT_SIZE":
            natija["step_size"] = float(f["stepSize"])
            natija["min_qty"] = float(f["minQty"])
        elif f["filterType"] == "PRICE_FILTER":
            natija["tick_size"] = float(f["tickSize"])
        elif f["filterType"] in ("MIN_NOTIONAL", "NOTIONAL"):
            natija["min_notional"] = float(f.get("minNotional", f.get("notional", 0)))

    _exchange_info_keshi[symbol] = natija
    return natija


def _qadamga_dumalash(qiymat: float, qadam: float) -> float:
    """Qiymatni PASTGA, eng yaqin 'qadam' (step/tick) ga dumalaydi (decimal bilan, float xatosiz)."""
    if not qadam:
        return qiymat
    d_qiymat = decimal.Decimal(str(qiymat))
    d_qadam = decimal.Decimal(str(qadam))
    dumalangan = (d_qiymat // d_qadam) * d_qadam
    return float(dumalangan)


def _decimal_satr(qiymat: float, qadam: float) -> str:
    """Binance kutgan formatda satr — ortiqcha o'nlik xona/ilmiy belgi (1e-05) bo'lmasligi kerak."""
    qadam_str = format(decimal.Decimal(str(qadam)).normalize(), "f") if qadam else "0.00000001"
    o_n = max(0, -qadam_str.find(".") + len(qadam_str) - 1) if "." in qadam_str else 0
    return f"{qiymat:.{o_n}f}"


def miqdorni_tayyorla(symbol: str, miqdor: float) -> float:
    info = exchange_info_olish(symbol)
    return _qadamga_dumalash(miqdor, info["step_size"])


def narxni_tayyorla(symbol: str, narx: float) -> float:
    info = exchange_info_olish(symbol)
    return _qadamga_dumalash(narx, info["tick_size"])


def min_notional_yetarlimi(symbol: str, miqdor: float, narx: float) -> bool:
    info = exchange_info_olish(symbol)
    return (miqdor * narx) >= info["min_notional"]


# ---------------------------------------------------------------------------
# Order amallari
# ---------------------------------------------------------------------------
def _kalitlarni_tekshir():
    if not BINANCE_API_KEY or not BINANCE_API_SECRET:
        raise BinanceXatosi(
            "BINANCE_API_KEY / BINANCE_API_SECRET .env faylida yo'q. "
            "Testnet kaliti uchun: https://testnet.binance.vision"
        )


def market_buy_joylash(symbol: str, miqdor: float, client_order_id: str) -> dict:
    _kalitlarni_tekshir()
    info = exchange_info_olish(symbol)
    params = {
        "symbol": symbol,
        "side": "BUY",
        "type": "MARKET",
        "quantity": _decimal_satr(miqdor, info["step_size"]),
        "newClientOrderId": client_order_id,
        "newOrderRespType": "FULL",
    }
    return _imzolangan_sorov("POST", "/api/v3/order", params)


def market_sell_joylash(symbol: str, miqdor: float, client_order_id: str) -> dict:
    """Pozitsiyani majburan (vaqt limiti yoki kill-switch tufayli) yopish uchun."""
    _kalitlarni_tekshir()
    info = exchange_info_olish(symbol)
    params = {
        "symbol": symbol,
        "side": "SELL",
        "type": "MARKET",
        "quantity": _decimal_satr(miqdor, info["step_size"]),
        "newClientOrderId": client_order_id,
        "newOrderRespType": "FULL",
    }
    return _imzolangan_sorov("POST", "/api/v3/order", params)


def oco_sell_joylash(
    symbol: str,
    miqdor: float,
    tp_narx: float,
    sl_stop_narx: float,
    sl_limit_narx: float,
    list_client_order_id: str,
) -> dict:
    """
    Long pozitsiyani himoyalash uchun OCO (SELL tomonda): yuqorida
    Take-Profit (LIMIT_MAKER), pastda Stop-Loss (STOP_LOSS_LIMIT). Ikkisidan
    biri ishlasa, ikkinchisi avtomatik bekor bo'ladi. Bu Binance serverining
    o'zida ishlaydi — bot o'chib qolsa ham kuchda qoladi.

    (Yangi /api/v3/orderList/oco endpointi, eski /api/v3/order/oco emas —
    eskisi deprecated.)
    """
    _kalitlarni_tekshir()
    info = exchange_info_olish(symbol)
    miqdor_str = _decimal_satr(miqdor, info["step_size"])

    params = {
        "symbol": symbol,
        "side": "SELL",
        "quantity": miqdor_str,
        "aboveType": "LIMIT_MAKER",
        "abovePrice": _decimal_satr(tp_narx, info["tick_size"]),
        "belowType": "STOP_LOSS_LIMIT",
        "belowPrice": _decimal_satr(sl_limit_narx, info["tick_size"]),
        "belowStopPrice": _decimal_satr(sl_stop_narx, info["tick_size"]),
        "belowTimeInForce": "GTC",
        "listClientOrderId": list_client_order_id,
        "newOrderRespType": "FULL",
    }
    return _imzolangan_sorov("POST", "/api/v3/orderList/oco", params)


def oco_holatini_olish(symbol: str, order_list_id: int) -> dict:
    # MUHIM: GET /api/v3/orderList 'symbol' parametrini QABUL QILMAYDI — faqat
    # orderListId (yoki origClientOrderId). 'symbol' yuborilsa Binance -1104
    # ("Not all sent parameters were read") bilan rad etadi. `symbol` argumenti
    # bu yerda faqat chaqiruvchi tomonda log/xato xabarlarida ishlatish uchun
    # qabul qilinadi, so'rovga qo'shilmaydi.
    return _imzolangan_sorov(
        "GET", "/api/v3/orderList", {"orderListId": order_list_id}
    )


def oco_bekor_qilish(symbol: str, order_list_id: int) -> dict:
    return _imzolangan_sorov(
        "DELETE", "/api/v3/orderList", {"symbol": symbol, "orderListId": order_list_id}
    )


def hisob_balansi(asset: str) -> float:
    data = _imzolangan_sorov("GET", "/api/v3/account", {})
    for b in data.get("balances", []):
        if b["asset"] == asset:
            return float(b["free"])
    return 0.0
