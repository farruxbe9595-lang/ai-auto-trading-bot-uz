import os, json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from saqlash.baza import barcha_savdolar
from asosiy.sozlamalar import HISOBOT_DIR, BOSHLANGICH_KAPITAL


def oylik_hisobot_yarat():
    savdolar = barcha_savdolar()
    yopilgan = [s for s in savdolar if s['holat'] == 'YOPILGAN']
    foyda_zararlar = [float(s['foyda_zarar'] or 0) for s in yopilgan]
    jami = sum(foyda_zararlar)
    foydali = sum(1 for x in foyda_zararlar if x > 0)
    zararli = sum(1 for x in foyda_zararlar if x < 0)
    yutuq_foizi = (foydali / len(yopilgan) * 100) if yopilgan else 0
    kapital = BOSHLANGICH_KAPITAL
    eng_past = kapital
    kapital_qatori = []
    for x in foyda_zararlar:
        kapital += x
        kapital_qatori.append(kapital)
        eng_past = min(eng_past, kapital)
    maksimal_pasayish = BOSHLANGICH_KAPITAL - eng_past
    hisobot = {
        'yaratilgan_vaqt': datetime.now().isoformat(),
        'boshlangich_kapital': BOSHLANGICH_KAPITAL,
        'yakuniy_kapital': round(BOSHLANGICH_KAPITAL + jami, 4),
        'umumiy_foyda_zarar': round(jami, 4),
        'foyda_foiz': round(jami / BOSHLANGICH_KAPITAL * 100, 2) if BOSHLANGICH_KAPITAL else 0,
        'jami_yopilgan_savdo': len(yopilgan),
        'foydali_savdo': foydali,
        'zararli_savdo': zararli,
        'yutuq_foizi': round(yutuq_foizi, 2),
        'eng_katta_foyda': max(foyda_zararlar) if foyda_zararlar else 0,
        'eng_katta_zarar': min(foyda_zararlar) if foyda_zararlar else 0,
        'maksimal_kapital_pashayishi_usd': round(maksimal_pasayish, 4),
        'savdolar': yopilgan
    }
    oy_dir = os.path.join(HISOBOT_DIR, 'oylik')
    os.makedirs(oy_dir, exist_ok=True)
    name = datetime.now().strftime('hisobot_%Y_%m.json')
    path = os.path.join(oy_dir, name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(hisobot, f, ensure_ascii=False, indent=2)

    csv_path = os.path.join(oy_dir, datetime.now().strftime('savdolar_%Y_%m.csv'))
    pd.DataFrame(yopilgan).to_csv(csv_path, index=False, encoding='utf-8-sig')

    if kapital_qatori:
        png_path = os.path.join(oy_dir, datetime.now().strftime('kapital_grafigi_%Y_%m.png'))
        plt.figure()
        plt.plot(kapital_qatori)
        plt.title('Kapital o‘zgarishi')
        plt.xlabel('Savdo tartib raqami')
        plt.ylabel('Kapital, USD')
        plt.savefig(png_path, dpi=160, bbox_inches='tight')
        plt.close()
    return path
