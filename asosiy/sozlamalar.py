import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')

SYMBOLS = [s.strip().upper() for s in os.getenv('SYMBOLS', 'BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT').split(',') if s.strip()]
INTERVAL = os.getenv('INTERVAL', '15m')
CHECK_SECONDS = int(os.getenv('CHECK_SECONDS', '900'))

BOSHLANGICH_KAPITAL = float(os.getenv('BOSHLANGICH_KAPITAL', '500'))

# Yangi xavfsiz savdo modeli
BITTA_SAVDO_USD = float(os.getenv('BITTA_SAVDO_USD', '100'))
MAKSIMAL_OCHIQ_SAVDO = int(os.getenv('MAKSIMAL_OCHIQ_SAVDO', '5'))
BIR_COIN_BIR_SAVDO = os.getenv('BIR_COIN_BIR_SAVDO', 'true').lower() == 'true'

KUNLIK_MAKSIMAL_ZARAR_USD = float(os.getenv('KUNLIK_MAKSIMAL_ZARAR_USD', '20'))
KUNLIK_MAKSIMAL_SAVDO = int(os.getenv('KUNLIK_MAKSIMAL_SAVDO', '20'))
KETMA_KET_ZARAR_LIMITI = int(os.getenv('KETMA_KET_ZARAR_LIMITI', '3'))

MIN_ISHONCH_FOIZI = float(os.getenv('MIN_ISHONCH_FOIZI', '80'))
MIN_FOYDA_XAVF_NISBATI = float(os.getenv('MIN_FOYDA_XAVF_NISBATI', '2.0'))

# Vaqt limiti va foydani himoyalash
SAVDO_MAKSIMAL_SOAT = float(os.getenv('SAVDO_MAKSIMAL_SOAT', '8'))
TRAILING_PROFIT_YOQISH = os.getenv('TRAILING_PROFIT_YOQISH', 'true').lower() == 'true'
TRAILING_TRIGGER_FOIZ = float(os.getenv('TRAILING_TRIGGER_FOIZ', '1.0'))
TRAILING_QAYTISH_FOIZ = float(os.getenv('TRAILING_QAYTISH_FOIZ', '0.5'))

SINOV_SAVDOSI = os.getenv('SINOV_SAVDOSI', 'true').lower() == 'true'
REAL_SAVDO = os.getenv('REAL_SAVDO', 'false').lower() == 'true'

KREDIT_YELKASI = int(os.getenv('KREDIT_YELKASI', '1'))
AVTOMATIK_PUL_CHIQARISH = os.getenv('AVTOMATIK_PUL_CHIQARISH', 'false').lower() == 'true'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAQLASH_DIR = os.path.join(BASE_DIR, 'saqlash')
HISOBOT_DIR = os.path.join(BASE_DIR, 'hisobotlar')

os.makedirs(SAQLASH_DIR, exist_ok=True)
os.makedirs(HISOBOT_DIR, exist_ok=True)

DATA_DIR = os.getenv("DATA_DIR", SAQLASH_DIR)
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "savdolar.db")
LOG_PATH = os.path.join(SAQLASH_DIR, 'bot.log')

# Zarar ko‘rgan coinni vaqtincha bloklash
COIN_ZARAR_BLOK_SOAT = float(os.getenv('COIN_ZARAR_BLOK_SOAT', '6'))
