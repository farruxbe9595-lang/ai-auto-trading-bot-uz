from datetime import datetime
from saqlash.baza import (
    savdo_ochish,
    savdo_yopish,
    ochiq_savdolar,
    eng_yaxshi_foiz_yangilash,
    balans_holati
)
from xavf.xavf_boshqaruvchisi import savdo_hajmini_hisobla
from asosiy.sozlamalar import (
    BITTA_SAVDO_USD,
    MAKSIMAL_OCHIQ_SAVDO,
    BIR_COIN_BIR_SAVDO,
    SAVDO_MAKSIMAL_SOAT,
    TRAILING_PROFIT_YOQISH,
    TRAILING_TRIGGER_FOIZ,
    TRAILING_QAYTISH_FOIZ
)


def sinov_savdo_och(tavsiya):
    ochiq = ochiq_savdolar()

    if len(ochiq) >= MAKSIMAL_OCHIQ_SAVDO:
        return None

    if BIR_COIN_BIR_SAVDO:
        for s in ochiq:
            if s['symbol'] == tavsiya['symbol']:
                return None

    balans = balans_holati()
    if balans['erkin'] < BITTA_SAVDO_USD:
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
        izoh=f'Sinov savdosi. Hajm: {BITTA_SAVDO_USD}$',
        savdo_hajmi_usd=BITTA_SAVDO_USD
    )


def _foyda_zarar_hisobla(s, narx):
    yon = s['yonalish']
    kirish = s['kirish_narxi']
    miqdor = s['miqdor']

    if yon == 'SOTIB_OLISH':
        return (narx - kirish) * miqdor

    return (kirish - narx) * miqdor


def _foiz_hisobla(s, narx):
    yon = s['yonalish']
    kirish = s['kirish_narxi']

    if kirish <= 0:
        return 0

    if yon == 'SOTIB_OLISH':
        return ((narx - kirish) / kirish) * 100

    return ((kirish - narx) / kirish) * 100


def _soat_farqi(ochilish_vaqti):
    try:
        start = datetime.fromisoformat(ochilish_vaqti)
        return (datetime.now() - start).total_seconds() / 3600
    except Exception:
        return 0


def ochiq_savdolarni_tekshir(joriy_narxlar: dict):
    yopilganlar = []

    for s in ochiq_savdolar():
        symbol = s['symbol']

        if symbol not in joriy_narxlar:
            continue

        narx = joriy_narxlar[symbol]
        yon = s['yonalish']
        sl = s['zarar_toxtatish']
        tp = s['foyda_olish']

        foyda_zarar = _foyda_zarar_hisobla(s, narx)
        joriy_foiz = _foiz_hisobla(s, narx)

        yopish = False
        sabab = ''

        # 1. Oddiy TP / SL
        if yon == 'SOTIB_OLISH':
            if narx <= sl:
                yopish = True
                sabab = 'Zararni to‘xtatish ishladi.'
            elif narx >= tp:
                yopish = True
                sabab = 'Foydani olish ishladi.'
        else:
            if narx >= sl:
                yopish = True
                sabab = 'Zararni to‘xtatish ishladi.'
            elif narx <= tp:
                yopish = True
                sabab = 'Foydani olish ishladi.'

        # 2. Trailing profit
        if not yopish and TRAILING_PROFIT_YOQISH:
            eski_eng_yaxshi = s.get('eng_yaxshi_foiz') or 0
            yangi_eng_yaxshi = max(eski_eng_yaxshi, joriy_foiz)

            if yangi_eng_yaxshi != eski_eng_yaxshi:
                eng_yaxshi_foiz_yangilash(s['id'], round(yangi_eng_yaxshi, 4))

            if yangi_eng_yaxshi >= TRAILING_TRIGGER_FOIZ:
                qaytish_chegarasi = yangi_eng_yaxshi - TRAILING_QAYTISH_FOIZ

                if joriy_foiz <= qaytish_chegarasi:
                    yopish = True
                    sabab = (
                        f'Trailing profit ishladi. '
                        f'Eng yaxshi: {yangi_eng_yaxshi:.2f}%, '
                        f'joriy: {joriy_foiz:.2f}%.'
                    )

        # 3. Vaqt limiti
        if not yopish:
            davomiylik_soat = _soat_farqi(s['ochilish_vaqti'])

            if davomiylik_soat >= SAVDO_MAKSIMAL_SOAT:
                yopish = True
                sabab = (
                    f'Vaqt limiti tugadi: {davomiylik_soat:.1f} soat. '
                    f'Joriy natija bilan yopildi.'
                )

        if yopish:
            savdo_yopish(s['id'], narx, round(foyda_zarar, 4), sabab)
            yopilganlar.append((s['id'], symbol, foyda_zarar, sabab))

    return yopilganlar
