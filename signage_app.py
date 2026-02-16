import io
from datetime import datetime

import streamlit as st
from reportlab.lib.pagesizes import A4, A3, landscape, portrait
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader


# =========================
# BRAND (Imagine)
# =========================
IMAGINE_PINK = "#AF0073"   # charte \ue202turn0file0
IMAGINE_DARK = "#414141"   # charte \ue202turn0file0
BG = "#FFFFFF"

LOGO_PATHS = ["logo_rose.png", "LOGO ROSE.png", "LOGO_ROSE.png", "logo.png"]


def find_logo():
    import os
    for p in LOGO_PATHS:
        if os.path.exists(p):
            return p
    return None


def hex_to_rgb01(hex_color: str):
    hex_color = hex_color.strip().lstrip("#")
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return (r, g, b)


def draw_sign_page(c: canvas.Canvas, w: float, h: float, *,
                   title: str,
                   subtitle: str | None = None,
                   footer: str | None = None,
                   logo_path: str | None = None):
    # Marges
    m = 18 * mm

    # Fond blanc
    c.setFillColorRGB(*hex_to_rgb01(BG))
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Bandeau haut (fin, premium)
    band_h = 10 * mm
    c.setFillColorRGB(*hex_to_rgb01(IMAGINE_PINK))
    c.rect(0, h - band_h, w, band_h, fill=1, stroke=0)

    # Logo (en haut à gauche, sous bandeau)
    if logo_path:
        try:
            img = ImageReader(logo_path)
            logo_w = 38 * mm
            logo_h = 16 * mm
            c.drawImage(img, m, h - band_h - logo_h - 6*mm, width=logo_w, height=logo_h, mask="auto")
        except Exception:
            pass

    # Titre principal (très lisible)
    # (on reste sur Helvetica-Bold pour éviter la gestion de polices côté serveur)
    c.setFillColorRGB(*hex_to_rgb01(IMAGINE_DARK))
    c.setFont("Helvetica-Bold", 54 if w < 600 else 70)

    # Centrage vertical sur zone utile
    y_title = h * 0.55
    c.drawCentredString(w / 2, y_title, title.upper())

    # Sous-titre (option)
    if subtitle:
        c.setFillColorRGB(*hex_to_rgb01(IMAGINE_PINK))
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(w / 2, y_title - 30*mm, subtitle)

    # Footer discret
    if footer:
        c.setFillColorRGB(*hex_to_rgb01(IMAGINE_DARK))
        c.setFont("Helvetica", 10)
        c.drawString(m, 10*mm, footer)

    # Petit repère (optionnel) : ligne fine en bas (style charte PPT)
    c.setStrokeColorRGB(*hex_to_rgb01(IMAGINE_PINK))
    c.setLineWidth(1)
    c.line(m, 16*mm, w - m, 16*mm)


def build_pdf(pages: list[dict], *, page_size):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=page_size)
    w, h = page_size

    logo = find_logo()

    for p in pages:
        draw_sign_page(
            c, w, h,
            title=p["title"],
            subtitle=p.get("subtitle"),
            footer=p.get("footer"),
            logo_path=logo
        )
        c.showPage()

    c.save()
    return buf.getvalue()


# =========================
# APP
# =========================
st.set_page_config(page_title="Signalétique — Institut Imagine", layout="centered")
st.title("Générateur de signalétique (zones)")

st.caption("Génère un PDF multi-pages prêt à imprimer, avec un rendu simple et premium.")

col1, col2, col3 = st.columns(3)
with col1:
    fmt = st.selectbox("Format", ["A4", "A3"], index=0)
with col2:
    orient = st.selectbox("Orientation", ["Portrait", "Paysage"], index=0)
with col3:
    lang = st.selectbox("Langue", ["FR", "EN"], index=0)

event_name = st.text_input("Nom événement (optionnel)", placeholder="Ex : Séminaire XYZ — 12/03/2026")

st.markdown("### Panneaux à générer")
zone_options_fr = [
    "ACCUEIL", "AUDITORIUM", "SALLE (personnalisée)", "TOILETTES", "VESTIAIRE", "PAUSE", "SORTIE"
]
zone_options_en = [
    "REGISTRATION", "AUDITORIUM", "ROOM (custom)", "RESTROOMS", "CLOAKROOM", "COFFEE BREAK", "EXIT"
]
zone_options = zone_options_fr if lang == "FR" else zone_options_en

selected = st.multiselect("Sélection", zone_options, default=zone_options[:4])

custom_room = None
if ("SALLE (personnalisée)" in selected) or ("ROOM (custom)" in selected):
    custom_room = st.text_input("Texte salle / room", value="Salle 1" if lang == "FR" else "Room 1")

# Page size
size = A4 if fmt == "A4" else A3
size = portrait(size) if orient == "Portrait" else landscape(size)

# Build pages
pages = []
footer = event_name.strip() if event_name.strip() else None
ts = datetime.now().strftime("%Y-%m-%d_%H%M")

for z in selected:
    if z in ("SALLE (personnalisée)", "ROOM (custom)"):
        title = (custom_room or "").strip() or ("SALLE" if lang == "FR" else "ROOM")
    else:
        title = z

    # Sous-titre optionnel (ex: "INSTITUT IMAGINE" ou rien)
    pages.append({
        "title": title,
        "subtitle": None,
        "footer": footer
    })

if st.button("Générer le PDF", type="primary", use_container_width=True, disabled=(len(pages) == 0)):
    pdf_bytes = build_pdf(pages, page_size=size)
    st.success("PDF généré.")
    st.download_button(
        "Télécharger la signalétique (PDF)",
        data=pdf_bytes,
        file_name=f"signaletique_zones_{fmt}_{orient}_{ts}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
