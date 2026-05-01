def tayanch_va_tosiq(df, uzunlik=40):
    qism = df.tail(uzunlik)
    tayanch = float(qism['past'].min())
    tosiq = float(qism['yuqori'].max())
    return tayanch, tosiq
