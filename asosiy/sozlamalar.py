import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')

SYMBOLS = [s.strip().upper() for s in os.getenv('SYMBOLS', 'BTCUSDT,ETHUSDT').split(',') if s.strip()]
INTERVAL = os.getenv('INTERVAL', '15m')
CHECK_SECONDS = int(os.getenv('CHECK_SECONDS', '900'))

BOSHLANGICH_KAPITAL = float(os.getenv('BOSHLANGICH_KAPITAL', '500'))
BITTA_SAVDO_XAVFI_USD = float(os.getenv('BITTA_SAVDO_XAVFI_USD', '7'))
KUNLIK_MAKSIMAL_ZARAR_USD = float(os.getenv('KUNLIK_MAKSIMAL_ZARAR_USD', '20'))
KUNLIK_MAKSIMAL_SAVDO = int(os.getenv('KUNLIK_MAKSIMAL_SAVDO', '5'))
KETMA_KET_ZARAR_LIMITI = int(os.getenv('KETMA_KET_ZARAR_LIMITI', '3'))
MIN_ISHONCH_FOIZI = float(os.getenv('MIN_ISHONCH_FOIZI', '80'))
MIN_FOYDA_XAVF_NISBATI = float(os.getenv('MIN_FOYDA_XAVF_NISBATI', '2.0'))

SINOV_SAVDOSI = os.getenv('SINOV_SAVDOSI', 'true').lower() == 'true'
REAL_SAVDO = os.getenv('REAL_SAVDO', 'false').lower() == 'true'
KREDIT_YELKASI = int(os.getenv('KREDIT_YELKASI', '1'))
AVTOMATIK_PUL_CHIQARISH = os.getenv('AVTOMATIK_PUL_CHIQARISH', 'false').lower() == 'true'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAQLASH_DIR = os.path.join(BASE_DIR, 'saqlash')
HISOBOT_DIR = os.path.join(BASE_DIR, 'hisobotlar')
DB_PATH = os.path.join(SAQLASH_DIR, 'savdolar.db')
LOG_PATH = os.path.join(SAQLASH_DIR, 'bot.log')
