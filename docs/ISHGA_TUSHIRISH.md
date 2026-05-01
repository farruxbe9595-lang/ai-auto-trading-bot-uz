# AI Avto Trading Bot UZ — ishga tushirish yo‘riqnomasi

## 1. Python o‘rnating
Python 3.10 yoki 3.11 tavsiya qilinadi.

## 2. Loyihani oching
```bash
cd ai_auto_trading_bot_uz
```

## 3. Kutubxonalarni o‘rnating
```bash
pip install -r requirements.txt
```

## 4. .env fayl yarating
`.env.example` faylini nusxalab `.env` deb nomlang.

Windows CMD:
```bash
copy .env.example .env
```

Keyin `.env` ichiga Telegram token va chat id kiriting.

## 5. Botni ishga tushiring
```bash
python app.py
```

## 6. Hisobot yaratish
Botni to‘xtatgandan keyin yoki istalgan payt:
```bash
python hisobot_olish.py
```

Hisobot joylashuvi:
```text
hisobotlar/oylik/hisobot_YYYY_MM.json
hisobotlar/oylik/savdolar_YYYY_MM.csv
hisobotlar/oylik/kapital_grafigi_YYYY_MM.png
```

## Xavfsizlik
Boshlanishida:
```env
SINOV_SAVDOSI=true
REAL_SAVDO=false
```

Bu real pul tikmaydi. Faqat virtual sinov savdosi qiladi.

Real savdo moduli bu ZIP ichida ataylab bloklangan. Avval 1 oy sinov natijasi ko‘riladi.
