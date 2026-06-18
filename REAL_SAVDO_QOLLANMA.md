# Real savdo (Binance) moduli — qo'llanma

## Nima qurildi

Uchta yangi fayl + `app.py`ga ulanish:

- `savdo/binance_real_klient.py` — Binance'ga signed (imzolangan) so'rov
  yuboradigan pastki daraja: order joylash, OCO (stop-loss+take-profit
  birgalikda), miqdor/narxni Binance qoidalariga moslab dumalash.
- `savdo/real_savdosi.py` — savdo ochish/yopish mantiqi: slippage tekshiruvi,
  OCO orqali himoya, vaqt limiti, kunlik/ketma-ket zarar kill-switch.
- `saqlash/real_baza.py` — real savdolar uchun ALOHIDA jadval
  (`real_savdolar.db`). Sinov savdosining `savdolar.db`siga sira tegmaydi.
- `app.py` — `REAL_SAVDO` blokini haqiqiy ishlaydigan chaqiruvga almashtirdim.

## Muhim arxitektura qarori: faqat LONG (SOTIB_OLISH)

Binance SPOT'da marjasiz qisqa pozitsiya ochib bo'lmaydi. Strategiyangiz
"SOTISH" signali bersa, real rejimda bu **o'tkazib yuboriladi** (faqat log
yoziladi) — sinov savdosida hamon simulyatsiya qilinadi. Qisqa savdo kerak
bo'lsa, bu Binance Margin/Futures API talab qiladi (likvidatsiya xavfi,
foiz to'lovi) — butunlay boshqa, ancha xavfli modul, alohida so'rang.

## Ikkita mustaqil xavfsizlik bayrog'i

Real order yuborilishi uchun IKKISI HAM `true` bo'lishi kerak:
```
REAL_SAVDO=true
REAL_SAVDO_XAVFNI_QABUL_QILDIM=true
```
Faqat bittasi `true` bo'lsa, bot Telegram'ga ogohlantirish yuboradi va real
order yubormaydi. Bu ataylab — bitta o'zgaruvchini noto'g'ri qo'yib
qo'yishdan himoya.

## Nima tekshirildi, nima tekshirilmadi

**Tekshirilgan (haqiqiy kodni ishlatib, mock javoblar bilan):**
- Imzolash (HMAC-SHA256) deterministik va mustaqil hisoblash bilan mos.
- Miqdor/narxni LOT_SIZE/PRICE_FILTER qadamiga dumalash — turli holatlar.
- API kalit yo'qligida darhol, tarmoqqa chiqmasdan xato berishi.
- Savdo ochish: muvaffaqiyatli holat, SOTISH rad etilishi, max-pozitsiya
  limiti, ortiqcha slippage'da darhol xavfsiz yopilish, OCO joylanmasa
  darhol xavfsiz yopilish — barchasi alohida-alohida sinaldi.
- Savdo yopish: OCO ALL_DONE to'g'ri aniqlanishi, vaqt limiti bo'yicha
  majburan yopish, kill-switch orqali barcha pozitsiyalarni yopish.
- `app.py`ning to'liq aylanishi (`bitta_aylanish()`) — risk filtri →
  AI filtr → real savdo ochish → Telegram xabari — boshidan oxirigacha bir
  marta to'liq ishlatib ko'rildi.

**TEKSHIRILMAGAN (bu konteynerda internet yo'q, shu sababli mumkin emas):**
- Binance Testnet/production serverining o'ziga haqiqiy so'rov. Hamma narsa
  mock (soxta) javoblar bilan sinaldi — bu mantiqning to'g'riligini
  tasdiqlaydi, lekin Binance API'sining haqiqiy xatti-harakati bilan 100%
  bir xilligini KAFOLATLAMAYDI (masalan, OCO parametrlarining haqiqiy
  qabul qilinishi, recvWindow/timestamp sinxronligi haqiqiy serverda).
- Shu sababli — **avval testnet'da, real pulga tegmasdan, o'zingiz sinab
  ko'rishingiz SHART**, quyidagi qadamlar bilan.

## Bilinmagan cheklovlar (paper trading bilan solishtirsangiz)

- **Trailing-profit real rejimda YO'Q.** Buni xavfsiz qilish uchun OCO'ni
  doimiy bekor qilib qayta joylash kerak bo'lardi — bu jarayonda pozitsiya
  bir zum himoyasiz qolishi mumkin. Hozircha real pozitsiyalar faqat statik
  SL/TP (OCO) va vaqt limiti bilan yopiladi.
- Strategiyaning o'zi hamon tarixiy ma'lumotda sinalmagan (backtest yo'q).

## Testnet bilan sinash — qadamlar

1. https://testnet.binance.vision ga kiring (GitHub orqali login),
   API Key yaratasiz — bu HAQIQIY Binance hisobingizdan BUTUNLAY ALOHIDA,
   sox pul avtomatik beriladi.
2. `.env`da:
   ```
   BINANCE_API_KEY=<testnet kaliti>
   BINANCE_API_SECRET=<testnet siri>
   BINANCE_TESTNET=true
   REAL_SAVDO=true
   REAL_SAVDO_XAVFNI_QABUL_QILDIM=true
   ```
3. Ishga tushirishdan oldin server vaqt farqini tekshiring (terminalda):
   ```python
   from savdo.binance_real_klient import server_vaqt_farqi_ms
   print(server_vaqt_farqi_ms())
   ```
   Bir necha soniyadan ko'p farq bo'lsa, serveringiz soatini NTP bilan
   sinxronlang — aks holda "timestamp outside of recvWindow" xatosi chiqadi.
4. `python app.py` — Telegram'da "🟥 REAL SAVDO" xabarini ko'rishingiz kerak.
5. Bir necha kun kuzating: testnet.binance.vision saytida buyurtmalar
   to'g'ri ko'rinayotganini, OCO joylanayotganini, yopilganda to'g'ri
   yopilayotganini tasdiqlang.
6. Faqat shundan keyin, va faqat juda kichik summa bilan,
   `BINANCE_TESTNET=false` + haqiqiy Binance API kalitlari bilan o'tasiz.

## Qolgan ochiq narsa

Strategiyaning o'zi — bu kod qanchalik to'g'ri ishlasa ham — daromadli
ekanligi hali isbotlanmagan. Backtest hamon tavsiya etiladi, real
kapitalni asta-sekin oshirish oldidan.
