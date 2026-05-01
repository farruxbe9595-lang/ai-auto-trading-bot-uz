import requests
import pandas as pd

BINANCE_URL = 'https://api.binance.com/api/v3/klines'

def shamlarni_ol(symbol: str, interval: str = '15m', limit: int = 250) -> pd.DataFrame:
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    r = requests.get(BINANCE_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data, columns=[
        'ochilish_vaqti','ochilish','yuqori','past','yopilish','hajm',
        'yopilish_vaqti','quote_hajm','savdolar_soni','taker_base','taker_quote','ignore'
    ])
    for col in ['ochilish','yuqori','past','yopilish','hajm']:
        df[col] = df[col].astype(float)
    df['ochilish_vaqti'] = pd.to_datetime(df['ochilish_vaqti'], unit='ms')
    df['yopilish_vaqti'] = pd.to_datetime(df['yopilish_vaqti'], unit='ms')
    return df
