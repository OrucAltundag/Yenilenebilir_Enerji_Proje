"""İlçe analiz raporu (PDF) üretimi — reportlab.

Rapor 02 Ek B bölümlerini içerir: kapak, özet, skorlar, girdiler, SHAP,
veri/metodoloji sürümü ve sorumluluk reddi. SHAP açıklaması ScoreService/
ShapService'ten alınır.
"""

from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DISCLAIMER = (
    "Bu rapor bir yatırım tavsiyesi veya resmî uygunluk belgesi değildir. "
    "Skorlar ilçe düzeyinde ön eleme ve karşılaştırma amaçlıdır."
)


def build_district_report(
    summary: dict,
    shap: dict | None,
    data_version: str,
    scoring_version: str,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="Buraki İlçe Raporu")
    styles = getSampleStyleSheet()
    story = []

    title = f"{summary['province']} / {summary['district']} — Yatırım Skor Raporu"
    story.append(Paragraph(title, styles["Title"]))
    story.append(Paragraph(f"Veri dönemi: {summary['year']}", styles["Normal"]))
    story.append(Spacer(1, 0.6 * cm))

    # Skor tablosu
    score_rows = [
        ["Metrik", "GES", "RES"],
        [
            "Yıllık ortalama skor",
            f"{summary['GES_YATIRIM_SKORU_mean']:.2f}",
            f"{summary['RES_YATIRIM_SKORU_mean']:.2f}",
        ],
        [
            "Ulusal sıra",
            f"{int(summary['ges_national_rank'])} / 957",
            f"{int(summary['res_national_rank'])} / 957",
        ],
        [
            "Yüzdelik",
            f"%{summary['ges_percentile']:.0f}",
            f"%{summary['res_percentile']:.0f}",
        ],
    ]
    table = Table(score_rows, colWidths=[6 * cm, 4 * cm, 4 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#13243f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.6 * cm))

    # SHAP katkıları
    if shap:
        story.append(Paragraph("Açıklama (SHAP) — GES", styles["Heading2"]))
        shap_rows = [["Özellik", "Değer", "SHAP katkısı"]]
        for c in shap["contributions"][:6]:
            shap_rows.append(
                [c["feature"], f"{c['value']:.2f}", f"{c['shap_value']:+.2f}"]
            )
        st = Table(shap_rows, colWidths=[7 * cm, 3.5 * cm, 3.5 * cm])
        st.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 9)]))
        story.append(st)
        story.append(Spacer(1, 0.5 * cm))

    story.append(
        Paragraph(
            f"Veri sürümü: {data_version} · Metodoloji sürümü: {scoring_version}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(DISCLAIMER, styles["Italic"]))

    doc.build(story)
    return buffer.getvalue()
