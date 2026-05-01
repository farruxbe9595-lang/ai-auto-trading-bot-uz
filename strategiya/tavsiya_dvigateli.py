from tahlil.indikatorlar import indikator_qosh
from tahlil.bozor_holati import bozor_holatini_aniqla
from tahlil.tayanch_tosiq import tayanch_va_tosiq
from asosiy.sozlamalar import MIN_ISHONCH_FOIZI, MIN_FOYDA_XAVF_NISBATI


def tavsiya_hisobla(symbol: str, df):
    df = indikator_qosh(df).dropna()
    if len(df) < 50:
        return None
    oxirgi = df.iloc[-1]
    narx = float(oxirgi['yopilish'])
    rsi = float(oxirgi['rsi'])
    trend, vol_holat, vol_foiz = bozor_holatini_aniqla(oxirgi)
    tayanch, tosiq = tayanch_va_tosiq(df)
    tayanch_masofa = abs(narx - tayanch) / narx * 100
    tosiq_masofa = abs(tosiq - narx) / narx * 100
    hajm_kuchli = oxirgi['hajm'] > oxirgi['hajm_orta20']

    tavsiya = 'KUTISH'
    ball = 50
    sabablar = []

    if trend == 'YUQORIGA':
        ball += 10; sabablar.append('katta trend yuqoriga')
    else:
        ball -= 5; sabablar.append('katta trend pastga')

    if 30 <= rsi <= 45:
        ball += 15; sabablar.append('RSI past zonadan qaytishga yaqin')
    elif 55 <= rsi <= 70:
        ball += 8; sabablar.append('RSI yuqori zonada')
    elif 45 < rsi < 55:
        ball -= 10; sabablar.append('RSI noaniq zonada')

    if tayanch_masofa <= 1.5:
        ball += 15; sabablar.append('narx tayanchga yaqin')
    if tosiq_masofa <= 1.5:
        ball -= 8; sabablar.append('narx tosiqqa yaqin')

    if hajm_kuchli:
        ball += 8; sabablar.append('hajm o‘rtachadan yuqori')
    if vol_holat == 'JUDA_YUQORI':
        ball -= 20; sabablar.append('bozor juda keskin harakatda')

    if trend == 'YUQORIGA' and 30 <= rsi <= 45 and tayanch_masofa <= 1.5 and ball >= MIN_ISHONCH_FOIZI:
        tavsiya = 'SOTIB_OLISH'
    elif trend == 'PASTGA' and 55 <= rsi <= 70 and tosiq_masofa <= 1.5 and ball >= MIN_ISHONCH_FOIZI:
        tavsiya = 'SOTISH'
    else:
        tavsiya = 'KUTISH'

    if tavsiya == 'SOTIB_OLISH':
        zarar_toxtatish = tayanch * 0.995
        foyda_olish = narx + ((narx - zarar_toxtatish) * MIN_FOYDA_XAVF_NISBATI)
    elif tavsiya == 'SOTISH':
        zarar_toxtatish = tosiq * 1.005
        foyda_olish = narx - ((zarar_toxtatish - narx) * MIN_FOYDA_XAVF_NISBATI)
    else:
        zarar_toxtatish = None
        foyda_olish = None

    return {
        'symbol': symbol,
        'narx': narx,
        'rsi': rsi,
        'ema50': float(oxirgi['ema50']),
        'ema200': float(oxirgi['ema200']),
        'trend': trend,
        'vol_holat': vol_holat,
        'vol_foiz': vol_foiz,
        'tayanch': tayanch,
        'tosiq': tosiq,
        'tavsiya': tavsiya,
        'ishonch_foizi': max(0, min(100, round(ball, 1))),
        'zararni_toxtatish': zarar_toxtatish,
        'foydani_olish': foyda_olish,
        'sabablar': sabablar
    }
