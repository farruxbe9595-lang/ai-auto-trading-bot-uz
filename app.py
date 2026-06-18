import time

from asosiy.sozlamalar import (
    SYMBOLS,
    INTERVAL,
    CHECK_SECONDS,
    SINOV_SAVDOSI,
    REAL_SAVDO,
    REAL_SAVDO_XAVFNI_QABUL_QILDIM,
    MAKSIMAL_OCHIQ_SAVDO,
    KUNLIK_MAKSIMAL_ZARAR_USD,
)
from asosiy.logger import logger
from asosiy.xavfsizlik import boshlangich_xavfsizlik_tekshiruvi
from malumot.binance_malumot import shamlarni_ol
from strategiya.tavsiya_dvigateli import tavsiya_hisobla
from strategiya.ai_tekshiruvchi import ai_izoh
from strategiya.ai_savdo_filtri import ai_savdoni_tekshir
from xavf.xavf_boshqaruvchisi import xavfni_tekshir
from savdo.sinov_savdosi import sinov_savdo_och, ochiq_savdolarni_tekshir
from saqlash.baza import bazani_tayyorla, tavsiyani_saqlash, ochiq_savdolar
from saqlash.real_baza import real_bazani_tayyorla, real_ochiq_savdolar, real_bugungi_statistika
from savdo.real_savdosi import real_savdo_och, real_ochiq_savdolarni_tekshir, real_barchasini_majburiy_yop
from telegram_bot.xabar import (
    telegramga_yubor,
    tavsiya_xabari,
    savdo_ochildi_xabari,
    savdo_yopildi_xabari,
)
from hisobotlar.hisobot_yaratish import oylik_hisobot_yarat


def bitta_aylanish():
    joriy_narxlar = {}

    for symbol in SYMBOLS:
        df = shamlarni_ol(symbol, INTERVAL)
        t = tavsiya_hisobla(symbol, df)

        if not t:
            continue

        joriy_narxlar[symbol] = t['narx']
        tavsiyani_saqlash(t)

        ruxsat, xavf_matni = xavfni_tekshir(t)
        ai_matni = ai_izoh(t)  # hozircha izoh uchun, AI filtr alohida pastda ishlaydi

        logger.info('%s | %s | %.1f%% | %s', symbol, t['tavsiya'], t['ishonch_foizi'], xavf_matni)

        if ruxsat and SINOV_SAVDOSI and not REAL_SAVDO:
            ochiq = ochiq_savdolar()

            if t["symbol"] in [s["symbol"] for s in ochiq]:
                logger.info(f"{t['symbol']} allaqachon ochiq — skip")
                continue

            if len(ochiq) >= MAKSIMAL_OCHIQ_SAVDO:
                logger.info(f"Max savdo limiti: {MAKSIMAL_OCHIQ_SAVDO} ta — skip")
                continue

            # AI faqat riskdan o'tgan va ochilishi mumkin bo'lgan savdoni tekshiradi.
            ai_ruxsat, ai_filtr_matni, ai_data = ai_savdoni_tekshir(
                t,
                ochiq_savdolar_soni=len(ochiq),
            )
            logger.info("%s | AI filtr | %s", symbol, ai_filtr_matni)

            if not ai_ruxsat:
                telegramga_yubor(f"🤖 AI filtr RAD qildi: {t['symbol']}\n{ai_filtr_matni}")
                continue

            trade_id = sinov_savdo_och(t)

            if trade_id:
                telegramga_yubor(savdo_ochildi_xabari(t, trade_id) + f"\n\n🤖 AI filtr: {ai_filtr_matni}")
            else:
                logger.info("Savdo ochilmadi (limit yoki coin band)")

        if ruxsat and REAL_SAVDO and REAL_SAVDO_XAVFNI_QABUL_QILDIM:
            # Real rejimda ham xuddi shu AI filtr ishlatiladi (sinov savdosidagi
            # bilan bir xil chaqiruv), lekin ochiq hisob real_ochiq_savdolar()'dan.
            real_ai_ruxsat, real_ai_matni, _ = ai_savdoni_tekshir(
                t, ochiq_savdolar_soni=len(real_ochiq_savdolar())
            )
            logger.info("%s | REAL AI filtr | %s", symbol, real_ai_matni)

            if not real_ai_ruxsat:
                telegramga_yubor(f"🤖 REAL AI filtr RAD qildi: {t['symbol']}\n{real_ai_matni}")
            else:
                real_trade_id = real_savdo_och(t)
                if real_trade_id:
                    telegramga_yubor(
                        f"💵 <b>REAL savdo ochildi: {t['symbol']}</b>\n"
                        f"ID: {real_trade_id}\n🤖 AI: {real_ai_matni}"
                    )
                else:
                    logger.info("%s: real savdo ochilmadi (limit/balans/long-only/kill-switch).", symbol)

        elif ruxsat and REAL_SAVDO and not REAL_SAVDO_XAVFNI_QABUL_QILDIM:
            telegramga_yubor(
                "⚠️ REAL_SAVDO=true, lekin REAL_SAVDO_XAVFNI_QABUL_QILDIM=false — "
                "real order moduli ikkinchi tasdiqlash bayrog'i kutilmoqda, hali bloklangan."
            )

    yopilganlar = ochiq_savdolarni_tekshir(joriy_narxlar)
    for trade_id, symbol, fz, sabab in yopilganlar:
        telegramga_yubor(savdo_yopildi_xabari(trade_id, symbol, fz, sabab))

    if REAL_SAVDO and REAL_SAVDO_XAVFNI_QABUL_QILDIM:
        real_yopilganlar = real_ochiq_savdolarni_tekshir()
        for trade_id, symbol, fz, sabab in real_yopilganlar:
            belgi = "✅" if fz >= 0 else "❌"
            telegramga_yubor(f"💵 <b>REAL savdo yopildi: {symbol}</b>\nID: {trade_id}\n{belgi} Natija: {fz:.4f}$\nSabab: {sabab}")

        # Kunlik kill-switch: limitga yetilgan bo'lsa, ochiq qolgan REAL
        # pozitsiyalarning hammasini ham majburan yopamiz (faqat yangi
        # ochilishini bloklash yetarli emas — allaqachon ochiqlar ham xavf).
        real_stat = real_bugungi_statistika()
        if real_stat['foyda_zarar'] < 0 and abs(real_stat['foyda_zarar']) >= KUNLIK_MAKSIMAL_ZARAR_USD and real_ochiq_savdolar():
            logger.warning('Real kunlik zarar limiti tugadi — barcha real pozitsiyalar majburan yopilmoqda.')
            majburiy = real_barchasini_majburiy_yop('Kunlik zarar limiti — kill-switch')
            for trade_id, symbol, fz, sabab in majburiy:
                telegramga_yubor(f"🛑 <b>KILL-SWITCH: {symbol} majburan yopildi</b>\nID: {trade_id}\nNatija: {fz:.4f}$\n{sabab}")


def main():
    bazani_tayyorla()
    real_bazani_tayyorla()

    for ogoh in boshlangich_xavfsizlik_tekshiruvi():
        telegramga_yubor('⚠️ ' + ogoh)

    if REAL_SAVDO and REAL_SAVDO_XAVFNI_QABUL_QILDIM:
        rejim_xabari = '🟥 REAL SAVDO (Binance, faqat long/SOTIB_OLISH signallari)'
    elif REAL_SAVDO:
        rejim_xabari = '🟧 REAL_SAVDO=true, lekin ikkinchi tasdiqlash yo‘q — REAL ORDER BLOKLANGAN'
    else:
        rejim_xabari = '🟩 SINOV SAVDOSI (real pul ishlatilmaydi)'

    telegramga_yubor(f'🤖 AI Avto Trading Bot UZ ishga tushdi. Rejim: {rejim_xabari}')
    logger.info(
        'Bot ishga tushdi. REAL_SAVDO=%s REAL_SAVDO_XAVFNI_QABUL_QILDIM=%s SINOV_SAVDOSI=%s',
        REAL_SAVDO, REAL_SAVDO_XAVFNI_QABUL_QILDIM, SINOV_SAVDOSI,
    )

    while True:
        try:
            bitta_aylanish()
        except KeyboardInterrupt:
            path = oylik_hisobot_yarat()
            logger.info('Bot to‘xtatildi. Hisobot: %s', path)
            break
        except Exception as e:
            logger.exception('Umumiy xatolik: %s', e)
            telegramga_yubor(f'❌ Bot xatosi: {e}')

        time.sleep(CHECK_SECONDS)


if __name__ == '__main__':
    main()
