import time
from asosiy.sozlamalar import SYMBOLS, INTERVAL, CHECK_SECONDS, SINOV_SAVDOSI, REAL_SAVDO
from asosiy.logger import logger
from asosiy.xavfsizlik import boshlangich_xavfsizlik_tekshiruvi
from malumot.binance_malumot import shamlarni_ol
from strategiya.tavsiya_dvigateli import tavsiya_hisobla
from strategiya.ai_tekshiruvchi import ai_izoh
from xavf.xavf_boshqaruvchisi import xavfni_tekshir
from savdo.sinov_savdosi import ochiq_savdolar_royxati
from savdo.sinov_savdosi import sinov_savdo_och, ochiq_savdolarni_tekshir
from telegram_bot.xabar import telegramga_yubor, tavsiya_xabari, savdo_ochildi_xabari, savdo_yopildi_xabari
from saqlash.baza import bazani_tayyorla, tavsiyani_saqlash
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
        ai_matni = ai_izoh(t)
        logger.info('%s | %s | %.1f%% | %s', symbol, t['tavsiya'], t['ishonch_foizi'], xavf_matni)

        
        if ruxsat and SINOV_SAVDOSI and not REAL_SAVDO:
            ochiq = ochiq_savdolar_royxati()
        
            if t["symbol"] in [s["symbol"] for s in ochiq]:
                logger.info(f"{t['symbol']} allaqachon ochiq — skip")
                continue
        
            if len(ochiq) >= 4:
                logger.info("Max savdo limiti — skip")
                continue
        
            trade_id = sinov_savdo_och(t)
        
            if trade_id:
                telegramga_yubor(savdo_ochildi_xabari(t["symbol"]))
            else:
                logger.info("Savdo ochilmadi (limit yoki coin band)")
                            
        if ruxsat and REAL_SAVDO:
            # Xavfsizlik uchun real order kodi bu versiyada ataylab faollashtirilmagan.
            telegramga_yubor('⚠️ REAL_SAVDO yoqilgan, lekin real order moduli xavfsizlik uchun bloklangan. Avval alohida tekshiruv kerak.')

    yopilganlar = ochiq_savdolarni_tekshir(joriy_narxlar)
    for trade_id, symbol, fz, sabab in yopilganlar:
        telegramga_yubor(savdo_yopildi_xabari(trade_id, symbol, fz, sabab))


def main():
    bazani_tayyorla()
    for ogoh in boshlangich_xavfsizlik_tekshiruvi():
        telegramga_yubor('⚠️ ' + ogoh)
    telegramga_yubor('🤖 AI Avto Trading Bot UZ ishga tushdi. Boshlanish rejimi: SINOV SAVDOSI.')
    logger.info('Bot ishga tushdi. REAL_SAVDO=%s SINOV_SAVDOSI=%s', REAL_SAVDO, SINOV_SAVDOSI)
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
