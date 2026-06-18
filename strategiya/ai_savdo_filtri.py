"""
Claude (Anthropic) yordamida ishlaydigan ikkinchi bosqich AI savdo filtri.

strategiya/ai_savdo_filtri.py o'rnini bosadi (OpenAI -> Claude). Maydon nomlari
loyihangizdagi strategiya/tavsiya_dvigateli.py (tavsiya_hisobla) qaytaradigan
HAQIQIY lug'atga mos: symbol, narx, rsi, ema50, ema200, trend, vol_holat,
vol_foiz, tayanch, tosiq, tavsiya, ishonch_foizi, zararni_toxtatish,
foydani_olish, sabablar.

Tashqi interfeys avvalgisi bilan bir xil:
    ai_savdoni_tekshir(tavsiya: dict, ochiq_savdolar_soni: int = 0)
    -> (ruxsat: bool, matn: str, data: dict)
"""

import os
import json
import datetime
from typing import Dict, List, Tuple

from pydantic import BaseModel, Field

from asosiy.logger import logger
from asosiy.sozlamalar import (
    AI_SAVDO_FILTRI,
    AI_FILTR_MODEL,
    AI_MIN_ISHONCH,
    AI_RADDA_MINIMAL_BALL,
)

# ---------------------------------------------------------------------------
_client = None
_kunlik_chaqiruv_soni = 0
_kunlik_sana = None


def _client_olish():
    """Anthropic mijozini yaratadi; kalit bo'lmasa None qaytaradi (xato emas)."""
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        from anthropic import Anthropic
        _client = Anthropic(api_key=api_key)
    return _client


def _kunlik_limitni_tekshir() -> bool:
    """Kunlik AI chaqiruvlar sonini cheklab, kutilmagan xarajatdan himoya qiladi."""
    global _kunlik_chaqiruv_soni, _kunlik_sana
    bugun = datetime.date.today()
    if _kunlik_sana != bugun:
        _kunlik_sana = bugun
        _kunlik_chaqiruv_soni = 0
    limit = int(os.getenv("AI_KUNLIK_LIMIT", "200"))
    if _kunlik_chaqiruv_soni >= limit:
        return False
    _kunlik_chaqiruv_soni += 1
    return True


def _float_or_none(value):
    try:
        return None if value is None else float(value)
    except Exception:
        return None


def _fallback_ruxsat(tavsiya: Dict) -> Tuple[bool, str, Dict]:
    """
    Claude ishlamasa (kalit yo'q, tarmoq xatosi, limit) bot to'xtab qolmasin,
    lekin xavfsiz tomonga: faqat asosiy ishonch foizi yetarli bo'lsa o'tkazadi.
    (Asl OpenAI-versiyadagi bilan bir xil mantiq.)
    """
    ishonch = _float_or_none(tavsiya.get("ishonch_foizi")) or 0
    if ishonch < AI_MIN_ISHONCH:
        return (
            False,
            f"AI fallback RAD: ishonch {ishonch:.1f}% < {AI_MIN_ISHONCH:.1f}%",
            {"qaror": "RAD", "ball": 0, "sabab": "AI ishlamadi va signal minimal ishonchdan past."},
        )
    return (
        True,
        "AI fallback TASDIQ: AI ishlamadi, lekin signal minimal ishonchdan yuqori.",
        {"qaror": "TASDIQ", "ball": 60, "sabab": "AI ishlamadi; xavf filtri va indikator ruxsati asosida davom etildi."},
    )


class SavdoBaholash(BaseModel):
    qaror: str = Field(description="Aniq qiymat: 'TASDIQ' yoki 'RAD'")
    ball: float = Field(description="0 dan 100 gacha ishonch bali")
    sabab: str = Field(description="Qisqa, aniq sabab, o'zbek tilida")
    xavf_omillari: List[str] = Field(default_factory=list, description="Topilgan xavf belgilari")
    kuchli_tomonlar: List[str] = Field(default_factory=list, description="Signalni qo'llab-quvvatlovchi omillar")


TIZIM_PROMPTI = (
    "Sen kripto trading bot uchun IKKINCHI BOSQICH xavfsizlik va signal-sifat "
    "filtrisan. Maqsad: indikator signali yaxshi ko'rinsa ham, yomon market "
    "context, kech kirish, sideways/choppy bozor, qarshilik (resistance) "
    "yaqinligi, hajm tasdiqlamasligi yoki risk baland bo'lsa RAD qilish. "
    "Foyda hech qachon kafolatlanmaydi — sen moliyaviy maslahat bermaysan, "
    "faqat texnik signal sifatini ehtiyotkorlik bilan baholaysan. "
    "Noaniq holatda TASDIQ bermagin — shubhada qolsang RAD qil."
)


def ai_savdoni_tekshir(tavsiya: Dict, ochiq_savdolar_soni: int = 0) -> Tuple[bool, str, Dict]:
    if not AI_SAVDO_FILTRI:
        return True, "AI filtr o'chirilgan.", {"qaror": "OCHIRILGAN"}

    client = _client_olish()
    if client is None:
        return _fallback_ruxsat(tavsiya)

    if not _kunlik_limitni_tekshir():
        return (
            False,
            "Kunlik AI chaqiruv limitiga yetildi — xavfsizlik uchun RAD qilindi",
            {"qaror": "RAD"},
        )

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

    qoidalar = (
        f"Qoidalar:\n"
        f"- Signal choppy/sideways bozorga o'xshasa RAD.\n"
        f"- Narx resistance/to'siqqa juda yaqin bo'lsa BUY uchun RAD.\n"
        f"- Trend va tavsiya mos kelmasa RAD.\n"
        f"- Ball {AI_RADDA_MINIMAL_BALL} dan past bo'lsa RAD.\n\n"
        f"Savdo ma'lumotlari:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )

    try:
        javob = client.messages.parse(
            model=AI_FILTR_MODEL,
            max_tokens=500,
            system=TIZIM_PROMPTI,
            messages=[{"role": "user", "content": qoidalar}],
            output_format=SavdoBaholash,
        )
        baho: SavdoBaholash = javob.parsed_output
    except Exception as e:
        logger.exception("Claude AI savdo filtri xatosi: %s", e)
        return _fallback_ruxsat(tavsiya)

    qaror = baho.qaror.upper().strip()
    data = baho.model_dump()

    if qaror == "TASDIQ" and baho.ball >= AI_RADDA_MINIMAL_BALL:
        return True, f"AI TASDIQ: {baho.ball:.0f}/100 — {baho.sabab}", data

    return False, f"AI RAD: {baho.ball:.0f}/100 — {baho.sabab}", data
