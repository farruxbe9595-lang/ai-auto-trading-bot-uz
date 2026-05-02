from saqlash.baza import savdo_ochish, savdo_yopish, ochiq_savdolar
from xavf.xavf_boshqaruvchisi import savdo_hajmini_hisobla

MAX_OCHIQ_SAVDO = 5

def sinov_savdo_och(tavsiya):
    ochiq = ochiq_savdolar()

    # 1. maksimal savdo limiti
    if len(ochiq) >= MAX_OCHIQ_SAVDO:
        return None

    # 2. bir coin = 1 savdo
    for s in ochiq:
        if s['symbol'] == tavsiya['symbol']:
            return None

    yonalish = 'SOTIB_OLISH' if tavsiya['tavsiya'] == 'SOTIB_OLISH' else 'SOTISH'
    miqdor = savdo_hajmini_hisobla(tavsiya)

    if miqdor <= 0:
        return None

    return savdo_ochish(
        symbol=tavsiya['symbol'],
        yonalish=yonalish,
        kirish=tavsiya['narx'],
        miqdor=miqdor,
        sl=tavsiya['zararni_toxtatish'],
        tp=tavsiya['foydani_olish'],
        izoh='Sinov savdosi (limit bilan)'
    )
