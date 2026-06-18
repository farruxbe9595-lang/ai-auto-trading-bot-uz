"""
Real (Binance) savdo ochish/yopish mantiqi.

ATAYLAB CHEKLOV: faqat 'SOTIB_OLISH' (long) signallari bajariladi. 'SOTISH'
signali kelsa, bu yerda RAD qilinadi va faqat log yoziladi — binarcha SPOT
hisobida marjasiz qisqa savdo qilish mumkin emas.

ATAYLAB CHEKLOV #2: trailing-profit BU MODULDA YO'Q. Sinov savdosida narx
har siklda solishtirilib, kerak bo'lsa OCO qayta joylanishi mumkin edi, lekin
buni real OCO bilan xavfsiz qilish (cancel+replace orasida pozitsiya bir zum
himoyasiz qolishi mumkin) ancha murakkab va xato qilish ehtimoli yuqori — shu
sabab hozircha real pozitsiyalar FAQAT statik SL/TP (OCO) va vaqt limiti
bilan yopiladi. Bu paper-trading bilan taqqoslaganda KAMROQ funksionallik —
buni bilib turing.

MUHIM TUZATISH (2026-06-17): Binance MARKET BUY bajarilganda komissiya
ko'pincha sotib olingan aktivning O'ZIDAN ushlanadi (masalan ETHUSDT uchun
ETH'dan). `executedQty` esa BUTUN (komissiyasiz) miqdorni ko'rsatadi. Agar
shu xom miqdor keyinchalik OCO/avariya-sotishda ishlatilsa, u hisobda
HAQIQATDA bor miqdordan ko'proq bo'lib chiqadi va Binance buni har safar
"insufficient balance" (-2010) bilan rad etadi — bu tasodifiy emas, har bir
savdoda takrorlanadigan tizimli xato edi. Shu sabab endi `fills` massividan
komissiya hisoblanadi va haqiqiy hisob balansi bilan tasdiqlanadi.

MUHIM TUZATISH #2: avval, agar OCO HAM, avariya-sotish HAM muvaffaqiyatsiz
bo'lsa, pozitsiya bazada xato ravishda "YOPILDI" deb yozilardi — aslida u
Binance'da ochiq va himoyasiz qolardi, bot esa buni butunlay unutardi. Endi
bunday holatda pozitsiya bazada OCHIQ (OCO'siz, "yalang'och") deb saqlanadi
va `real_ochiq_savdolarni_tekshir()` har siklda uni qayta yopishga urinadi,
muvaffaqiyatli bo'lguncha — jim qolib ketmaydi, har safar baqiradi.
"""

import time
import uuid
from datetime import datetime

from asosiy.logger import logger
from asosiy.sozlamalar import (
    BITTA_SAVDO_USD,
    REAL_MAKSIMAL_OCHIQ_SAVDO,
    REAL_MAKSIMAL_SLIPPAGE_FOIZ,
    MIN_FOYDA_XAVF_NISBATI,
    SAVDO_MAKSIMAL_SOAT,
    KUNLIK_MAKSIMAL_ZARAR_USD,
    KETMA_KET_ZARAR_LIMITI,
)
from saqlash.real_baza import (
    real_savdo_ochish,
    real_savdo_yopish,
    real_ochiq_savdolar,
    real_bugungi_statistika,
)
import savdo.binance_real_klient as bk


def _client_order_id(prefix: str) -> str:
    # Binance clientOrderId uzunligi cheklangan — qisqa va noyob qilamiz.
    return f"{prefix}{int(time.time())}{uuid.uuid4().hex[:6]}"


def _asosiy_aktiv(symbol: str):
    """'ETHUSDT' -> 'ETH'. Faqat USDT juftliklari qo'llab-quvvatlanadi."""
    if symbol.endswith("USDT"):
        return symbol[:-4]
    return None


def _sof_miqdorni_hisobla(symbol: str, order: dict) -> float:
    """
    Buyurtma javobidagi `fills`dan komissiyani ayirib, haqiqatan sotilishi
    mumkin bo'lgan sof miqdorni hisoblaydi, so'ng buni haqiqiy hisob
    balansi bilan tasdiqlaydi (ikkisidan kichigini oladi — qo'shimcha
    xavfsizlik qatlami).
    """
    xom_miqdor = float(order.get("executedQty", 0) or 0)
    asosiy_aktiv = _asosiy_aktiv(symbol)

    komissiya = 0.0
    if asosiy_aktiv:
        for f in order.get("fills", []) or []:
            if f.get("commissionAsset") == asosiy_aktiv:
                komissiya += float(f.get("commission", 0) or 0)

    sof_miqdor = xom_miqdor - komissiya
    sof_miqdor = bk.miqdorni_tayyorla(symbol, sof_miqdor)

    if asosiy_aktiv:
        try:
            haqiqiy_balans = bk.hisob_balansi(asosiy_aktiv)
            if haqiqiy_balans > 0:
                haqiqiy_balans_tayyor = bk.miqdorni_tayyorla(symbol, haqiqiy_balans)
                sof_miqdor = min(sof_miqdor, haqiqiy_balans_tayyor)
        except Exception as e:
            logger.warning(
                "%s: haqiqiy balansni tasdiqlashda xato (komissiyadan hisoblangan "
                "miqdor bilan davom etiladi): %s", symbol, e,
            )

    return sof_miqdor


def _avariya_yopishga_urin(symbol, miqdor, kirish_narxi, kirish_coid, sl_narx, tp_narx, sabab):
    """
    OCO yoki dastlabki tekshiruv (slippage/SL anomaliyasi) muvaffaqiyatsiz
    bo'lganda chaqiriladi. Pozitsiyani darhol bozor narxida yopishga
    harakat qiladi.

    - Muvaffaqiyatli bo'lsa: bazada OCHIQ deb yozilib, darhol YOPILGAN deb
      yangilanadi (to'g'ri chiqish narxi va foyda/zarar bilan).
    - Muvaffaqiyatsiz bo'lsa: bazada OCHIQ (OCO'siz, "yalang'och") holatda
      QOLDIRILADI — yolg'on "yopildi" deb yozilmaydi. Keyingi sikllarda
      `real_ochiq_savdolarni_tekshir()` buni qayta yopishga urinadi.
    """
    trade_id = real_savdo_ochish(symbol, miqdor, kirish_narxi, kirish_coid, None, sl_narx, tp_narx)

    try:
        yopish_coid = _client_order_id("avariya-yopish-")
        yopish_order = bk.market_sell_joylash(symbol, miqdor, yopish_coid)
        bajarilgan = float(yopish_order.get("executedQty", 0) or 0)
        summa = float(yopish_order.get("cummulativeQuoteQty", 0) or 0)
        chiqish_narx = summa / bajarilgan if bajarilgan > 0 else kirish_narxi
        foyda_zarar = (chiqish_narx - kirish_narxi) * miqdor
        real_savdo_yopish(trade_id, chiqish_narx, round(foyda_zarar, 6), sabab)
        logger.info("%s: avariya-yopish muvaffaqiyatli (%s).", symbol, sabab)
    except Exception as e:
        logger.error(
            "DIQQAT: %s HIMOYASIZ QOLDI (%s) — avariya-yopish HAM muvaffaqiyatsiz: %s. "
            "Pozitsiya bazada OCHIQ holatda saqlanadi, keyingi sikllarda avtomatik "
            "qayta urinilad. Zarur bo'lsa QO'LDA BINANCE'NI TEKSHIRING!",
            symbol, sabab, e,
        )

    return None


def real_savdo_och(tavsiya: dict):
    """
    tavsiya: strategiya.tavsiya_dvigateli.tavsiya_hisobla() natijasi.
    Qaytaradi: trade_id (int) muvaffaqiyatli ochilsa, aks holda None.
    """
    if tavsiya.get("tavsiya") != "SOTIB_OLISH":
        logger.info(
            "%s: SOTISH/boshqa signal — real rejimda qo'llab-quvvatlanmaydi (long-only), o'tkazib yuborildi.",
            tavsiya.get("symbol"),
        )
        return None

    if tavsiya.get("zararni_toxtatish") is None or tavsiya.get("foydani_olish") is None:
        logger.warning("%s: SL/TP aniqlanmagan — real savdo ochilmadi.", tavsiya.get("symbol"))
        return None

    # Mustaqil kill-switch himoyasi — app.py buni tekshirmagan taqdirda ham,
    # bu funksiya o'zi kunlik/ketma-ket zarar limitini hurmat qiladi.
    stat = real_bugungi_statistika()
    if stat["foyda_zarar"] < 0 and abs(stat["foyda_zarar"]) >= KUNLIK_MAKSIMAL_ZARAR_USD:
        logger.warning("Real kunlik zarar limiti (%s$) tugadi — yangi real savdo ochilmadi.", KUNLIK_MAKSIMAL_ZARAR_USD)
        return None
    if stat["ketma_ket_zarar"] >= KETMA_KET_ZARAR_LIMITI:
        logger.warning("Real ketma-ket zarar limiti (%s) tugadi — yangi real savdo ochilmadi.", KETMA_KET_ZARAR_LIMITI)
        return None

    ochiq = real_ochiq_savdolar()
    if len(ochiq) >= REAL_MAKSIMAL_OCHIQ_SAVDO:
        logger.info("Real maksimal ochiq pozitsiya limiti (%s) — yangi savdo ochilmadi.", REAL_MAKSIMAL_OCHIQ_SAVDO)
        return None
    if any(s["symbol"] == tavsiya["symbol"] for s in ochiq):
        logger.info("%s bo'yicha real pozitsiya allaqachon ochiq.", tavsiya["symbol"])
        return None

    symbol = tavsiya["symbol"]
    kutilgan_narx = tavsiya["narx"]
    sl_narx = tavsiya["zararni_toxtatish"]

    rejalashtirilgan_miqdor = bk.miqdorni_tayyorla(symbol, BITTA_SAVDO_USD / kutilgan_narx)
    if rejalashtirilgan_miqdor <= 0:
        logger.warning("%s: hisoblangan miqdor 0 — savdo ochilmadi.", symbol)
        return None

    # --- 1) Kirish: MARKET BUY ---
    kirish_coid = _client_order_id("kirish-")
    try:
        order = bk.market_buy_joylash(symbol, rejalashtirilgan_miqdor, kirish_coid)
    except Exception as e:
        logger.exception("%s: real MARKET BUY xatosi: %s", symbol, e)
        return None

    xom_miqdor = float(order.get("executedQty", 0) or 0)
    kummulativ_summa = float(order.get("cummulativeQuoteQty", 0) or 0)

    if xom_miqdor <= 0 or kummulativ_summa <= 0:
        logger.error("%s: BUY buyurtmasi bajarilmadi yoki javobda miqdor yo'q: %s", symbol, order)
        return None

    haqiqiy_kirish_narxi = kummulativ_summa / xom_miqdor

    # Komissiyani hisobga olib, haqiqatan SOTILISHI mumkin bo'lgan sof
    # miqdorni aniqlaymiz (muhim tuzatish — yuqoridagi docstring'ga qarang).
    bajarilgan_miqdor = _sof_miqdorni_hisobla(symbol, order)
    if bajarilgan_miqdor <= 0:
        logger.error(
            "%s: komissiyadan/balansdan keyin sotiladigan miqdor 0 (xom=%.8f) — "
            "pozitsiya juda kichik, qo'lda BINANCE'NI TEKSHIRING (BUY allaqachon bajarilgan)!",
            symbol, xom_miqdor,
        )
        return None

    # --- 2) Slippage tekshiruvi ---
    slippage_foiz = abs(haqiqiy_kirish_narxi - kutilgan_narx) / kutilgan_narx * 100
    if slippage_foiz > REAL_MAKSIMAL_SLIPPAGE_FOIZ:
        logger.error(
            "%s: slippage %.3f%% > limit %.3f%% — pozitsiya DARHOL yopiladi.",
            symbol, slippage_foiz, REAL_MAKSIMAL_SLIPPAGE_FOIZ,
        )
        return _avariya_yopishga_urin(
            symbol, bajarilgan_miqdor, haqiqiy_kirish_narxi, kirish_coid, sl_narx, None,
            f"Ortiqcha slippage ({slippage_foiz:.2f}%) tufayli darhol yopildi",
        )

    # --- 3) TP'ni HAQIQIY kirish narxiga nisbatan qayta hisoblaymiz ---
    # (SL — texnik tayanch darajasi, o'zgarmaydi. TP shu SL'ga nisbatan
    # MIN_FOYDA_XAVF_NISBATI saqlanishi uchun haqiqiy kirish narxidan qayta
    # hisoblanadi — aks holda kichik slippage ham foyda/xavf nisbatini buzadi.)
    xavf_masofa = haqiqiy_kirish_narxi - sl_narx
    if xavf_masofa <= 0:
        logger.error(
            "%s: haqiqiy kirish narxi (%.6f) SL (%.6f) dan past/teng — mantiqsiz holat, pozitsiya darhol yopiladi.",
            symbol, haqiqiy_kirish_narxi, sl_narx,
        )
        return _avariya_yopishga_urin(
            symbol, bajarilgan_miqdor, haqiqiy_kirish_narxi, kirish_coid, sl_narx, None,
            "SL>=kirish narxi anomaliyasi tufayli darhol yopildi",
        )

    tp_narx = haqiqiy_kirish_narxi + xavf_masofa * MIN_FOYDA_XAVF_NISBATI
    sl_limit_narx = sl_narx * 0.999  # stop ishlaganda haqiqatan bajarilishi uchun bir oz pastroq limit

    # --- 4) Himoya: OCO (TP + SL birgalikda, birjaning o'zida) ---
    oco_coid = _client_order_id("oco-")
    try:
        oco = bk.oco_sell_joylash(
            symbol, bajarilgan_miqdor, tp_narx, sl_narx, sl_limit_narx, oco_coid
        )
        order_list_id = oco.get("orderListId")
    except Exception as e:
        logger.exception(
            "%s: OCO joylanmadi (%s) — pozitsiya HIMOYASIZ QOLDI, darhol yopilmoqda!",
            symbol, e,
        )
        return _avariya_yopishga_urin(
            symbol, bajarilgan_miqdor, haqiqiy_kirish_narxi, kirish_coid, sl_narx, tp_narx,
            "OCO joylanmagani uchun darhol yopildi",
        )

    trade_id = real_savdo_ochish(
        symbol, bajarilgan_miqdor, haqiqiy_kirish_narxi, kirish_coid, order_list_id, sl_narx, tp_narx
    )
    logger.info(
        "%s: REAL pozitsiya ochildi. Miqdor=%.8f Kirish=%.6f SL=%.6f TP=%.6f (slippage %.3f%%)",
        symbol, bajarilgan_miqdor, haqiqiy_kirish_narxi, sl_narx, tp_narx, slippage_foiz,
    )
    return trade_id


def _soat_farqi(vaqt_str):
    try:
        return (datetime.now() - datetime.fromisoformat(vaqt_str)).total_seconds() / 3600
    except Exception:
        return 0


def real_ochiq_savdolarni_tekshir():
    """
    Har bir ochiq real pozitsiyaning OCO holatini Binance'dan so'raydi.
    Trailing-profit YO'Q (yuqoridagi modul docstringga qarang) — faqat
    OCO natijasi (SL/TP) va vaqt limiti orqali yopiladi.

    Agar pozitsiya OCO'siz ("yalang'och", oco_order_list_id=None) bo'lsa —
    bu avval OCO/avariya-yopish muvaffaqiyatsiz bo'lgani uchun shunday
    qolgan, va endi har siklda qayta yopishga harakat qilinadi, jim
    o'tkazib yuborilmaydi.
    """
    yopilganlar = []

    for s in real_ochiq_savdolar():
        symbol = s["symbol"]
        order_list_id = s["oco_order_list_id"]

        if order_list_id is None:
            # Himoyasiz ("yalang'och") pozitsiya — har safar qayta yopishga harakat qilamiz.
            try:
                yopish_coid = _client_order_id("retry-yopish-")
                yopish_order = bk.market_sell_joylash(symbol, s["miqdor"], yopish_coid)
                bajarilgan = float(yopish_order.get("executedQty", 0) or 0)
                summa = float(yopish_order.get("cummulativeQuoteQty", 0) or 0)
                chiqish_narx = summa / bajarilgan if bajarilgan > 0 else s["kirish_narxi"]
                foyda_zarar = (chiqish_narx - s["kirish_narxi"]) * s["miqdor"]
                sabab = "Oldin himoyasiz qolgan pozitsiya keyinroq muvaffaqiyatli yopildi"
                real_savdo_yopish(s["id"], chiqish_narx, round(foyda_zarar, 6), sabab)
                yopilganlar.append((s["id"], symbol, foyda_zarar, sabab))
                logger.info("%s: oldin himoyasiz qolgan pozitsiya endi muvaffaqiyatli yopildi.", symbol)
            except Exception as e:
                logger.error(
                    "DIQQAT: %s hali himoyasiz, qayta yopish yana muvaffaqiyatsiz: %s — "
                    "QO'LDA BINANCE'NI TEKSHIRING!", symbol, e,
                )
            continue

        try:
            holat = bk.oco_holatini_olish(symbol, order_list_id)
        except Exception as e:
            logger.exception("%s: OCO holatini olishda xato: %s", symbol, e)
            continue

        list_status = holat.get("listOrderStatus")

        if list_status == "ALL_DONE":
            bajarilgan = next(
                (o for o in holat.get("orderReports", holat.get("orders", []))
                 if o.get("status") == "FILLED"),
                None,
            )
            if bajarilgan and bajarilgan.get("price"):
                chiqish_narx = float(bajarilgan["price"])
            else:
                chiqish_narx = s["sl_narx"]  # taxminiy fallback, holat noaniq bo'lsa

            foyda_zarar = (chiqish_narx - s["kirish_narxi"]) * s["miqdor"]
            sabab = "TP/SL (OCO) ishladi"
            real_savdo_yopish(s["id"], chiqish_narx, round(foyda_zarar, 6), sabab)
            yopilganlar.append((s["id"], symbol, foyda_zarar, sabab))
            continue

        # Vaqt limiti — OCO hali EXECUTING bo'lsa ham majburan yopamiz
        if _soat_farqi(s["ochilish_vaqti"]) >= SAVDO_MAKSIMAL_SOAT:
            try:
                bk.oco_bekor_qilish(symbol, order_list_id)
                yopish_coid = _client_order_id("vaqt-limit-")
                yopish_order = bk.market_sell_joylash(symbol, s["miqdor"], yopish_coid)
                chiqish_narx = float(yopish_order.get("cummulativeQuoteQty", 0)) / max(
                    float(yopish_order.get("executedQty", 1)), 1e-12
                )
                foyda_zarar = (chiqish_narx - s["kirish_narxi"]) * s["miqdor"]
                sabab = f"Vaqt limiti ({SAVDO_MAKSIMAL_SOAT} soat) tufayli majburan yopildi"
                real_savdo_yopish(s["id"], chiqish_narx, round(foyda_zarar, 6), sabab)
                yopilganlar.append((s["id"], symbol, foyda_zarar, sabab))
            except Exception as e:
                logger.exception("%s: vaqt limiti bo'yicha majburan yopishda xato: %s — QO'LDA TEKSHIRING!", symbol, e)

    return yopilganlar


def real_barchasini_majburiy_yop(sabab: str):
    """
    Kill-switch uchun: kunlik zarar limiti yoki boshqa jiddiy holatda
    BARCHA ochiq real pozitsiyalarni darhol yopadi. app.py'dan chaqiriladi.
    """
    yopilganlar = []
    for s in real_ochiq_savdolar():
        symbol = s["symbol"]
        try:
            if s["oco_order_list_id"] is not None:
                bk.oco_bekor_qilish(symbol, s["oco_order_list_id"])
            yopish_coid = _client_order_id("killswitch-")
            yopish_order = bk.market_sell_joylash(symbol, s["miqdor"], yopish_coid)
            chiqish_narx = float(yopish_order.get("cummulativeQuoteQty", 0)) / max(
                float(yopish_order.get("executedQty", 1)), 1e-12
            )
            foyda_zarar = (chiqish_narx - s["kirish_narxi"]) * s["miqdor"]
            real_savdo_yopish(s["id"], chiqish_narx, round(foyda_zarar, 6), sabab)
            yopilganlar.append((s["id"], symbol, foyda_zarar, sabab))
        except Exception as e:
            logger.exception("%s: kill-switch majburiy yopishda xato: %s — QO'LDA BINANCE'NI TEKSHIRING!", symbol, e)
    return yopilganlar
