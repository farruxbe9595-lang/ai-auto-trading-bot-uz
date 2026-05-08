import json
import re
from typing import Dict, Tuple

from asosiy.logger import logger
from asosiy.sozlamalar import (
    OPENAI_API_KEY,
    AI_SAVDO_FILTRI,
    AI_FILTR_MODEL,
    AI_MIN_ISHONCH,
    AI_RADDA_MINIMAL_BALL,
)


def _float_or_none(value):
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _fallback_ruxsat(tavsiya: Dict) -> Tuple[bool, str, Dict]:
    """
    OpenAI API ishlamasa bot to'xtab qolmasligi uchun xavfsiz fallback.
    Bu AI emas, faqat eng oddiy himoya: confidence juda past bo'lsa rad qiladi.
    """
    ishonch = _float_or_none(tavsiya.get("ishonch_foizi")) or 0
    if ishonch < AI_MIN_ISHONCH:
        return False, f"AI fallback RAD: ishonch {ishonch:.1f}% < {AI_MIN_ISHONCH:.1f}%", {
            "qaror": "RAD",
            "ball": 0,
            "sabab": "AI ishlamadi va signal minimal ishonchdan past.",
        }
    return True, "AI fallback TASDIQ: AI ishlamadi, lekin signal minimal ishonchdan yuqori.", {
        "qaror": "TASDIQ",
        "ball": 60,
        "sabab": "AI ishlamadi; xavf filtri va indikator ruxsati asosida davom etildi.",
    }


def _jsonni_ajrat(text: str) -> Dict:
    """Model javobidan JSON obyektni ehtiyotkorlik bilan ajratadi."""
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("AI javobida JSON topilmadi")
    return json.loads(match.group(0))


def ai_savdoni_tekshir(tavsiya: Dict, ochiq_savdolar_soni: int = 0) -> Tuple[bool, str, Dict]:
    """
    AI faqat ochilishi mumkin bo'lgan savdoni oxirgi bosqichda tekshiradi.
    Natija:
        (ruxsat, matn, raw_json)
    """
    if not AI_SAVDO_FILTRI:
        return True, "AI filtr o'chirilgan.", {"qaror": "OCHIRILGAN"}

    if not OPENAI_API_KEY:
        return _fallback_ruxsat(tavsiya)

    payload = {
        "symbol": tavsiya.get("symbol"),
        "tavsiya": tavsiya.get("tavsiya"),
        "narx": tavsiya.get("narx"),
        "ishonch_foizi": tavsiya.get("ishonch_foizi"),
        "trend": tavsiya.get("trend"),
        "rsi": tavsiya.get("rsi"),
        "ema50": tavsiya.get("ema50"),
        "ema200": tavsiya.get("ema200"),
        "vol_holat": tavsiya.get("vol_holat"),
        "vol_foiz": tavsiya.get("vol_foiz"),
        "tayanch": tavsiya.get("tayanch"),
        "tosiq": tavsiya.get("tosiq"),
        "zararni_toxtatish": tavsiya.get("zararni_toxtatish"),
        "foydani_olish": tavsiya.get("foydani_olish"),
        "sabablar": tavsiya.get("sabablar", []),
        "ochiq_savdolar_soni": ochiq_savdolar_soni,
    }

    system_prompt = (
        "Sen kripto trading bot uchun xavfsizlik va signal-sifat filtri sifatida ishlaysan. "
        "Maqsad: indikator signali yaxshi ko'rinsa ham, yomon market context, kech kirish, "
        "sideways bozor, resistance yaqinligi, volume tasdiqlamasligi yoki risk baland bo'lsa RAD qilish. "
        "Foyda kafolatlanmaydi. Faqat ehtiyotkor risk filtri bo'l. "
        "Javob faqat JSON bo'lsin."
    )

    user_prompt = f"""
Quyidagi savdo nomzodini analiz qil. Qaror faqat JSON bo'lsin.

JSON schema:
{{
  "qaror": "TASDIQ" yoki "RAD",
  "ball": 0-100,
  "sabab": "qisqa aniq sabab",
  "xavf_omillari": ["..."],
  "kuchli_tomonlar": ["..."]
}}

Qoidalar:
- Agar signal choppy/sideways bozorga o'xshasa RAD.
- Agar narx resistance/tosiqqa juda yaqin bo'lsa BUY uchun RAD.
- Agar trend va tavsiya mos kelmasa RAD.
- Agar ball {AI_RADDA_MINIMAL_BALL} dan past bo'lsa RAD.
- Noaniq holatda TASDIQ bermagin.

Savdo ma'lumotlari:
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""

    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=AI_FILTR_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
            timeout=30,
        )
        text = resp.choices[0].message.content or "{}"
        data = _jsonni_ajrat(text)

        qaror = str(data.get("qaror", "RAD")).upper().strip()
        ball = float(data.get("ball", 0) or 0)
        sabab = data.get("sabab", "AI sabab qaytarmadi")

        if qaror == "TASDIQ" and ball >= AI_RADDA_MINIMAL_BALL:
            return True, f"AI TASDIQ: {ball:.0f}/100 — {sabab}", data

        return False, f"AI RAD: {ball:.0f}/100 — {sabab}", data

    except Exception as e:
        logger.exception("AI savdo filtri xatosi: %s", e)
        return _fallback_ruxsat(tavsiya)
