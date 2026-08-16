"""
Claude API yordamida:
  1) Maqolalar orasidan eng muhim/qiziqarlilarini saralaydi (rank_articles)
  2) Har birini o'z so'zlari bilan qayta yozadi (rewrite_for_telegram)
  3) Media bo'yicha qaror qabul qiladi (suggest_image_query)
"""
import json
import logging
import os

import anthropic

logger = logging.getLogger("ai_pipeline")

MODEL = "claude-sonnet-4-6"

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def rank_articles(articles: list, max_select: int) -> list[dict]:
    if not articles:
        return []

    listing = "\n".join(
        f"{i}. [{a.source_name}] {a.title}\n   {a.summary[:200]}"
        for i, a in enumerate(articles)
    )

    prompt = f"""Quyida turli o'zbek axborot saytlaridan yig'ilgan {len(articles)} ta yangilik ro'yxati berilgan.

Vazifang: shu ro'yxatdan O'zbekiston auditoriyasi uchun ENG MUHIM va ENG QIZIQARLI bo'lgan
yangiliklarni tanlash. Quyidagilarga alohida e'tibor ber:
- Davlat siyosati, iqtisodiyot, ijtimoiy hayotga bevosita ta'sir qiluvchi yangiliklar
- Keng jamoatchilik qiziqishini uyg'otadigan voqealar (jamiyat, texnologiya, sport, madaniyat)
- Bir xil voqea haqida bir nechta manbada yozilgan bo'lsa — faqat bittasini tanla
- Reklama xarakteridagi, clickbait yoki ahamiyatsiz yangiliklarni chetlab o't

Ro'yxat:
{listing}

Javobni FAQAT quyidagi JSON formatda qaytar, boshqa hech qanday matn qo'shma:
{{"selected": [{{"index": <raqam>, "score": <1-100>, "reason": "<qisqa sabab, o'zbek tilida>"}}]}}

Maksimal {max_select} ta element tanla, eng muhimidan boshlab kamayish tartibida joylashtir."""

    resp = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(text)
        return data.get("selected", [])[:max_select]
    except json.JSONDecodeError:
        logger.error("Claude javobini JSON sifatida o'qib bo'lmadi: %s", text[:300])
        return []


def rewrite_for_telegram(article) -> dict:
    prompt = f"""Quyidagi yangilik matni asosida Telegram kanali uchun POST tayyorla.

Sarlavha: {article.title}
Manba: {article.source_name}
Matn:
{article.full_text[:4000]}

QOIDALAR (albatta rioya qil):
1. Matnni O'Z SO'ZLARING bilan qayta yoz — manba matnidan gap yoki jumlalarni so'zma-so'z
   ko'chirma, faqat faktlarni yetkaz (bu mualliflik huquqi talabi).
2. Sodda, tushunarli o'zbek tilida yoz. Ortiqcha bezaklarsiz, jurnalistik uslubda.
3. Umumiy uzunlik 500-800 belgi atrofida bo'lsin.
4. Kerak bo'lsa 1-2 ta mos emoji ishlatilishi mumkin.
5. Oxirida manba nomini alohida qatorga yozma — buni dastur o'zi qo'shadi.

Javobni FAQAT quyidagi JSON formatda qaytar:
{{"headline": "<qisqa, jonli sarlavha>", "body": "<qayta yozilgan matn>"}}"""

    resp = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.error("Rewrite javobini JSON sifatida o'qib bo'lmadi: %s", text[:300])
        return {"headline": article.title, "body": article.summary}


def suggest_image_query(article) -> str:
    prompt = f"""Quyidagi yangilik uchun Unsplash'dan mos, betaraf fotosurat qidirish uchun
2-4 so'zdan iborat INGLIZCHA qidiruv so'zi yoz. Faqat qidiruv so'zini yoz, boshqa hech narsa yozma.

Sarlavha: {article.title}
Mavzu: {article.summary[:200]}"""

    resp = client.messages.create(
        model=MODEL,
        max_tokens=30,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip().strip('"')
