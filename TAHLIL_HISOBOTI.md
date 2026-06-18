# Haqiqiy kod tahlili — natijalar va o'zgarishlar

Bu safar taxmin emas — zip ichidagi barcha 20+ faylni o'qib, ustiga
sintetik narx ma'lumoti bilan haqiqiy kodni ishga tushirib (ta/pydantic
kutubxonalari mahalliy stub orqali) tekshirdim. Quyida — aniq topilgan
narsalar, taxmin emas.

## 1. Ijro orqali tasdiqlangan ikkita haqiqiy zaiflik

### 1.1 `savdo/sinov_savdosi.py` — `sinov_savdo_och()` o'ziga ishonmaydi
Bu funksiya `tavsiya['tavsiya'] == 'KUTISH'` yoki SL/TP `None` bo'lishi
mumkinligini o'zi tekshirmaydi — faqat chaqiruvchi (`app.py`) buni oldindan
to'g'ri filtrlab berishiga ishonadi. Buni sinab ko'rdim: funksiyani
to'g'ridan-to'g'ri `tavsiya='KUTISH'` bilan chaqirganda, u **yo'nalishni
avtomatik "SOTISH" deb hisoblab, SL/TP'siz savdo OCHDI**:

```
Natija: trade ID 1 ochildi — yonalish=SOTISH, zarar_toxtatish=None, foyda_olish=None
```

Hozirgi `app.py` oqimida bu hech qachon sodir bo'lmaydi, chunki
`xavfni_tekshir()` undan oldin `KUTISH`ni rad etadi. **Lekin** xuddi shu
sababli — agar kelajakda biror narsa (masalan, AI orqali avtomatik savdo
ochish moduli) bu funksiyani to'g'ridan-to'g'ri chaqirsa, himoya yo'q.

### 1.2 Shu singan savdo butun pozitsiya-monitoringini to'xtatadi
Yuqoridagi SL/TP=`None` bo'lgan savdo bazada qolib ketsa, keyingi siklda
`ochiq_savdolarni_tekshir()` shu savdoga yetganda **qotib qoladi**:

```
TypeError: '>=' not supported between instances of 'float' and 'NoneType'
```

Bu xato `ochiq_savdolarni_tekshir()` ichidagi `for` siklni to'xtatadi —
demak shu bitta singan yozuv tufayli **boshqa BARCHA ochiq savdolarning**
SL/TP/trailing/vaqt-limiti tekshiruvi ham har safar (har 60 soniyada)
muvaffaqiyatsiz tugaydi, toki kim DBdagi yozuvni qo'lda tuzatmaguncha.
`app.py`'dagi umumiy `try/except` botni butunlay to'xtatib qo'ymaydi, lekin
Telegram'ga doimiy xato xabari kelaveradi va ochiq savdolar yopilmay qoladi.

**Tuzatdim:** `sinov_savdosi.py`ga ikki qatorlik himoya qo'shdim — funksiya
endi o'zi ham `tavsiya` qiymatini va SL/TP `None` emasligini tekshiradi.
Patch qo'llangandan keyin qayta sinadim: noto'g'ri chaqiruv endi `None`
qaytaradi, sog'lom chaqiruv esa avvalgidek ishlayveradi.

## 2. Kod o'qishda topilgan, kamroq jiddiy narsalar

- **`ishonch_foizi` va yakuniy `tavsiya` bir-biriga bog'liq emas.**
  `tavsiya_dvigateli.py`da "ball" trend+RSI+hajm asosida alohida hisoblanadi,
  lekin SOTIB_OLISH/SOTISH faqat trend+RSI-oralig'i+tayanchga-yaqinlik+ball
  hammasi BIRGALIKDA to'g'ri kelsagina chiqadi. Sinovda buni ko'rdim: ball
  83% chiqdi, lekin yakuniy tavsiya hali ham "KUTISH" bo'lib qoldi (narx
  tayanchga yetarlicha yaqin emasligi sababli). Hozircha zarari yo'q
  (`xavfni_tekshir` "KUTISH"ni baribir rad etadi), lekin Telegram xabarida
  "ishonch: 83%" ko'rinib, aslida hech narsa ochilmagani chalkash tuyulishi
  mumkin.

- **`malumot/binance_malumot.py`** narxni `api.binance.us`'dan oladi — bu
  global `binance.com` emas, AQSh fuqarolari uchun alohida tartibga
  solinadigan birja. Agar real savdoni keyinchalik global Binance orqali
  qilish niyatida bo'lsangiz, signal bir bozordan, ijro boshqa bozordan
  bo'lib qoladi — narx odatda yaqin, lekin bu ataylab tanlangan qaror emas,
  ehtimol shunchaki nazardan chetda qolgan.

- **Kunlik zarar/ketma-ket-zarar limiti** (`xavf_boshqaruvchisi.py`) faqat
  YANGI savdo ochilishini to'xtatadi — limitga yetganda ALLAQACHON ochiq
  turgan savdolarni majburan yopmaydi. Bu avvalgi suhbatda aytganim
  taxminim edi, endi kodda tasdiqlandi.

- **`AVTOMATIK_PUL_CHIQARISH=true`** bo'lsa bot ishga tushishidan oldin
  `RuntimeError` bilan to'xtaydi — bu yaxshi, ataylab qilingan xavfsizlik
  qarori, o'zgartirmadim.

## 3. AI filtr — Claude'ga moslab qayta yozdim

Avvalgi javobimda taxminiy maydon nomlari (`rsi`, `ema`, `macd`...) bilan
yozgan edim — endi haqiqiy `tavsiya_hisobla()` natijasidagi aniq nomlarga
(`rsi`, `ema50`, `ema200`, `trend`, `vol_holat`, `vol_foiz`, `tayanch`,
`tosiq`, `zararni_toxtatish`, `foydani_olish`, `sabablar`) moslab qayta
yozdim. Tashqi interfeys (`ai_savdoni_tekshir`) va fallback mantiqi asl
OpenAI-versiyasi bilan bir xil saqlangan — faqat Claude API ishlatadi.

Buni mahalliy stub kutubxonalar bilan sinadim: `AI_SAVDO_FILTRI=false`,
`AI_SAVDO_FILTRI=true` + kalit yo'q (fallback) holatlarini tasdiqladim.
**Claude API'ning o'ziga haqiqiy chaqiruvni sinay olmadim** — bu yerda
internet yo'q va sizning shaxsiy `ANTHROPIC_API_KEY`ingiz yo'q. Shuning
uchun bu qism — kodi to'g'ri yozilgan, lekin haqiqiy API javobi bilan hali
sinalmagan.

## 4. O'rnatish

1. `strategiya/ai_savdo_filtri.py`ni shu fayl bilan almashtiring.
2. `savdo/sinov_savdosi.py`ni shu fayl bilan almashtiring (yuqoridagi
   1.1-1.2 patch shu yerda).
3. `requirements.txt`ga qo'shing: `anthropic` (so'ng
   `pip install -U anthropic --break-system-packages`).
4. `.env`ga qo'shing:
   ```
   ANTHROPIC_API_KEY=sk-ant-...sizning-shaxsiy-kalitingiz...
   AI_FILTR_MODEL=claude-haiku-4-5-20251001
   AI_SAVDO_FILTRI=true
   AI_KUNLIK_LIMIT=200
   ```
   (Kalitni console.anthropic.com'da o'zingiz yaratasiz — bu pullik xizmat,
   menda sizga beradigan umumiy kalit yo'q.)

## 5. Hali ham ochiq qolgan narsalar

- Bu hamon faqat **sinov savdosi**. `REAL_SAVDO` ataylab bloklangan holida
  qoldi — buyurtma yuborish moduli umuman yozilmagan.
- Strategiyaning o'zi (RSI+EMA+tayanch/to'siq qoidalari) tarixiy ma'lumotda
  hali sinalmagan — ball/qoidalar qog'ozda mantiqiy ko'rinadi, lekin foyda
  keltirishi isbotlanmagan.
- Yuqoridagi 1.1/1.2 patch — qo'lda qo'shilgan, sizning haqiqiy faylingiz
  ustida emas (men uni faylga to'g'ridan-to'g'ri yoza olmayman, faqat
  natijani qaytarib beraman) — shuning uchun joylashtirgandan keyin o'zingiz
  bir marta ko'zdan kechiring.
