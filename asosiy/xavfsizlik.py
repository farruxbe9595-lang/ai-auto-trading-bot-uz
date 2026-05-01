from .sozlamalar import REAL_SAVDO, KREDIT_YELKASI, AVTOMATIK_PUL_CHIQARISH

def boshlangich_xavfsizlik_tekshiruvi():
    ogohlantirishlar = []
    if REAL_SAVDO:
        ogohlantirishlar.append('DIQQAT: REAL_SAVDO=true. Real pul bilan savdo yoqilgan.')
    if KREDIT_YELKASI != 1:
        ogohlantirishlar.append('DIQQAT: Kredit yelkasi 1 emas. Bu xavfni oshiradi.')
    if AVTOMATIK_PUL_CHIQARISH:
        raise RuntimeError('AVTOMATIK_PUL_CHIQARISH xavfsizlik sababli taqiqlangan.')
    return ogohlantirishlar
