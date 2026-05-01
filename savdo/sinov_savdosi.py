from saqlash.baza import savdo_ochish, savdo_yopish, ochiq_savdolar
from xavf.xavf_boshqaruvchisi import savdo_hajmini_hisobla


def sinov_savdo_och(tavsiya):
    yonalish = 'SOTIB_OLISH' if tavsiya['tavsiya'] == 'SOTIB_OLISH' else 'SOTISH'
    miqdor = savdo_hajmini_hisobla(tavsiya)
    if miqdor <= 0:
        return None
    return savdo_ochish(
        symbol=tavsiya['symbol'], yonalish=yonalish, kirish=tavsiya['narx'], miqdor=miqdor,
        sl=tavsiya['zararni_toxtatish'], tp=tavsiya['foydani_olish'],
        izoh='Sinov savdosi avtomatik ochildi.'
    )


def ochiq_savdolarni_tekshir(joriy_narxlar: dict):
    yopilganlar = []
    for s in ochiq_savdolar():
        symbol = s['symbol']
        if symbol not in joriy_narxlar:
            continue
        narx = joriy_narxlar[symbol]
        yon = s['yonalish']
        sl = s['zarar_toxtatish']; tp = s['foyda_olish']; kirish = s['kirish_narxi']; miqdor = s['miqdor']
        yopish = False; sabab = ''
        if yon == 'SOTIB_OLISH':
            if narx <= sl: yopish=True; sabab='Zararni to‘xtatish ishladi.'
            elif narx >= tp: yopish=True; sabab='Foydani olish ishladi.'
            foyda_zarar = (narx - kirish) * miqdor
        else:
            if narx >= sl: yopish=True; sabab='Zararni to‘xtatish ishladi.'
            elif narx <= tp: yopish=True; sabab='Foydani olish ishladi.'
            foyda_zarar = (kirish - narx) * miqdor
        if yopish:
            savdo_yopish(s['id'], narx, round(foyda_zarar, 4), sabab)
            yopilganlar.append((s['id'], symbol, foyda_zarar, sabab))
    return yopilganlar
