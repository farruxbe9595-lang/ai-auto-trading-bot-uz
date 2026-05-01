from asosiy.sozlamalar import OPENAI_API_KEY, OPENAI_MODEL


def ai_izoh(tavsiya):
    if not OPENAI_API_KEY:
        return 'AI izoh: OpenAI API ulanmagan. Tavsiya qoidaviy tahlil va xavf boshqaruvi asosida tekshirildi.'
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        matn = f"""
O‘zbek tilida qisqa tushuntir. Bu kafolat emasligini ayt.
Tavsiya: {tavsiya['tavsiya']}
Symbol: {tavsiya['symbol']}
Narx: {tavsiya['narx']}
Trend: {tavsiya['trend']}
RSI: {tavsiya['rsi']:.2f}
Ishonch: {tavsiya['ishonch_foizi']}%
Tayanch: {tavsiya['tayanch']}
To‘siq: {tavsiya['tosiq']}
Sabablar: {', '.join(tavsiya['sabablar'])}
"""
        res = client.responses.create(model=OPENAI_MODEL, input=matn)
        return res.output_text.strip()
    except Exception as e:
        return f'AI izoh olishda xatolik: {e}'
