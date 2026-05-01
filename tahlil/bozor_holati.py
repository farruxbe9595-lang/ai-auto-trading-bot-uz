def bozor_holatini_aniqla(oxirgi):
    if oxirgi['ema50'] > oxirgi['ema200']:
        trend = 'YUQORIGA'
    else:
        trend = 'PASTGA'
    vol_foiz = (oxirgi['atr'] / oxirgi['yopilish']) * 100 if oxirgi['yopilish'] else 0
    if vol_foiz > 3:
        vol = 'JUDA_YUQORI'
    elif vol_foiz > 1.2:
        vol = 'ORTACHA'
    else:
        vol = 'PAST'
    return trend, vol, vol_foiz
