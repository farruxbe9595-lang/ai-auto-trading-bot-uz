from datetime import datetime, date
from asosiy.sozlamalar import (
    BITTA_SAVDO_XAVFI_USD, KUNLIK_MAKSIMAL_ZARAR_USD,
    KUNLIK_MAKSIMAL_SAVDO, KETMA_KET_ZARAR_LIMITI,
    MIN_ISHONCH_FOIZI, MIN_FOYDA_XAVF_NISBATI
)
from saqlash.baza import bugungi_statistika


def xavfni_tekshir(tavsiya):
    if tavsiya is None:
        return False, 'Tavsiya hisoblanmadi.'
    if tavsiya['tavsiya'] == 'KUTISH':
        return False, 'Bot kutishni tanladi.'
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
    if abs(stat['foyda_zarar']) >= KUNLIK_MAKSIMAL_ZARAR_USD and stat['foyda_zarar'] < 0:
        return False, 'Kunlik zarar limiti tugadi.'
    if stat['ketma_ket_zarar'] >= KETMA_KET_ZARAR_LIMITI:
        return False, 'Ketma-ket zarar limiti tugadi.'
    return True, 'Xavf tekshiruvidan o‘tdi.'


def savdo_hajmini_hisobla(tavsiya):
    narx = tavsiya['narx']
    sl = tavsiya['zararni_toxtatish']
    bir_dona_xavfi = abs(narx - sl)
    if bir_dona_xavfi <= 0:
        return 0
    miqdor = BITTA_SAVDO_XAVFI_USD / bir_dona_xavfi
    return round(miqdor, 6)
