from asosiy.sozlamalar import (
    BITTA_SAVDO_USD,
    KUNLIK_MAKSIMAL_ZARAR_USD,
    KUNLIK_MAKSIMAL_SAVDO,
    KETMA_KET_ZARAR_LIMITI,
    MIN_ISHONCH_FOIZI,
    MIN_FOYDA_XAVF_NISBATI,
    MAKSIMAL_OCHIQ_SAVDO,
    BIR_COIN_BIR_SAVDO
)
from saqlash.baza import bugungi_statistika, ochiq_savdolar, balans_holati
from saqlash.baza import coin_bloklanganmi
from asosiy.sozlamalar import COIN_ZARAR_BLOK_SOAT


def xavfni_tekshir(tavsiya):
    if tavsiya is None:
        return False, 'Tavsiya hisoblanmadi.'

    if tavsiya['tavsiya'] == 'KUTISH':
        return False, 'Bot kutishni tanladi.'

    ochiq = ochiq_savdolar()

    if len(ochiq) >= MAKSIMAL_OCHIQ_SAVDO:
        return False, f'Maksimum ochiq savdo limiti: {MAKSIMAL_OCHIQ_SAVDO} ta.'

    if BIR_COIN_BIR_SAVDO:
        for s in ochiq:
            if s['symbol'] == tavsiya['symbol']:
                return False, f'{tavsiya["symbol"]} bo‘yicha savdo allaqachon ochiq.'
    # Zarar ko‘rgan coin vaqtincha blok
    if coin_bloklanganmi(tavsiya['symbol'], COIN_ZARAR_BLOK_SOAT):
        return False, f"{tavsiya['symbol']} vaqtincha bloklangan (zarar)."

    balans = balans_holati()
    if balans['erkin'] < BITTA_SAVDO_USD:
        return False, f'Erkin balans yetarli emas. Erkin: {balans["erkin"]}$'

    if tavsiya['ishonch_foizi'] < MIN_ISHONCH_FOIZI:
        return False, 'Ishonchlilik foizi past.'

    if tavsiya['zararni_toxtatish'] is None or tavsiya['foydani_olish'] is None:
        return False, 'Zararni to‘xtatish yoki foydani olish aniqlanmadi.'

    narx = tavsiya['narx']
    sl = tavsiya['zararni_toxtatish']
    tp = tavsiya['foydani_olish']

    xavf = abs(narx - sl)
    foyda = abs(tp - narx)
    nisbat = foyda / xavf if xavf else 0

    if nisbat < MIN_FOYDA_XAVF_NISBATI:
        return False, 'Foyda/xavf nisbati yetarli emas.'

    stat = bugungi_statistika()

    if stat['savdo_soni'] >= KUNLIK_MAKSIMAL_SAVDO:
        return False, 'Kunlik savdo limiti tugadi.'

    if stat['foyda_zarar'] < 0 and abs(stat['foyda_zarar']) >= KUNLIK_MAKSIMAL_ZARAR_USD:
        return False, 'Kunlik zarar limiti tugadi.'

    if stat['ketma_ket_zarar'] >= KETMA_KET_ZARAR_LIMITI:
        return False, 'Ketma-ket zarar limiti tugadi.'

    return True, 'Xavf tekshiruvidan o‘tdi.'


def savdo_hajmini_hisobla(tavsiya):
    """
    Endi har savdo $100 bilan ochiladi.
    miqdor = $100 / kirish narxi
    """
    narx = tavsiya['narx']

    if narx <= 0:
        return 0

    miqdor = BITTA_SAVDO_USD / narx
    return round(miqdor, 8)
