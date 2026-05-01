import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange

def indikator_qosh(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    close = df['yopilish']
    high = df['yuqori']
    low = df['past']
    df['rsi'] = RSIIndicator(close=close, window=14).rsi()
    df['ema50'] = EMAIndicator(close=close, window=50).ema_indicator()
    df['ema200'] = EMAIndicator(close=close, window=200).ema_indicator()
    macd = MACD(close=close)
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    atr = AverageTrueRange(high=high, low=low, close=close, window=14)
    df['atr'] = atr.average_true_range()
    df['hajm_orta20'] = df['hajm'].rolling(20).mean()
    return df
