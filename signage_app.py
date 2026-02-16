# signage_app.py
# Générateur de signalétique (zones) — Institut Imagine
# Streamlit + ReportLab (PDF direct) — design premium, simple, robuste

import io
from datetime import datetime
from pathlib import Path

import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A3, portrait, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader


# =========================
# BRAND / THEME (Imagine)
# =========================
APP_TITLE = "Générateur de signalétique — Institut Imagine"

# Charte (extraits)
IMAGINE_PINK = "#AF0073"
IMAGINE_GREY = "#414141"
WHITE = "#FFFFFF"

LOGO_PATHS = [
    "logo_rose.png",
    "LOGO ROSE.png",
    "LOGO_ROSE.png",
    "logo.png",
]

# =========================
# HELPERS
# =========================
def hex_to_rgb01(hex_color: str):
    hex_color = (hex_color or "").strip().lstrip("#")
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return (r, g, b)


def find_logo_path() -> str | None:
    for p in LOGO_PATHS:
        if Path(p).exists():
            return p
    return None


def fit_text(c: canvas.Canvas, text: str, max_width: float, font_name: str, max_font: int, min_font: int) -> int:
    """Réduit la taille de police jusqu'à ce que le texte rentre (une ligne)."""
    text = (text or "").strip()
    size = max_font
    while size >= min_font:
        c.setFont(font_name, size)
        if c.stringWidth(text, font_name, size) <= max_width:
            return size
        size -= 2
    return min_font


def draw_pictogram(c: canvas.Canvas, kind: str, cx: float, cy: float, s: float, color_hex: str):
    """
    Pictos minimalistes en vectoriel (robuste, pas d'assets).
    s = taille (en points)
    """
    c.setStrokeColorRGB(*hex_to_rgb01(color_hex))
    c.setFillColorRGB(*hex_to_rgb01(color_hex))
    c.setLineWidth(3)

    kind = (kind or "none").lower()

    if kind == "none":
        return

    if kind == "wc":
        # 2 têtes + 2 corps (simple / lisible)
        r = s * 0.12
        c.circle(cx - s*0.18, cy + s*0.18, r, stroke=1, fill=0)
        c.circle(cx + s*0.18, cy + s*0.18, r, stroke=1, fill=0)
        c.roundRect(cx - s*0.30, cy - s*0.25, s*0.22, s*0.35, 6, stroke=1, fill=0)
        c.roundRect(cx + s*0.08, cy - s*0.25, s*0.22, s*0.35, 6, stroke=1, fill=0)

    elif kind == "coat":
        # cintre stylisé
        c.line(cx - s*0.30, cy + s*0.10, cx, cy - s*0.20)
        c.line(cx + s*0.30, cy + s*0.10, cx, cy - s*0.20)
        c.line(cx - s*0.30, cy + s*0.10, cx + s*0.30, cy + s*0.10)
        c.circle(cx, cy - s*0.20, s*0.05, stroke=1, fill=0)

    elif kind == "info":
        # i dans un cercle
        c.circle(cx, cy, s*0.30, stroke=1, fill=0)
        c.setFont("Helvetica-Bold", int(s*0.45))
        c.drawCentredString(cx, cy - s*0.17, "i")

    elif kind == "coffee":
        # tasse minimaliste
        c.roundRect(cx - s*0.28, cy - s*0.10, s*0.48, s*0.24, 6, stroke=1, fill=0)
        c.circle(cx + s*0.26, cy + s*0.02, s*0.08, stroke=1, fill=0)
        c.line(cx - s*0.22, cy - s*0.18, cx + s*0.20, cy - s*0.18)

    elif kind == "exit":
        # flèche + porte
        c.roundRect(cx - s*0.30, cy - s*0.20, s*0.18, s*0.40, 4, stroke=1, fill=0)
        c.line(cx - s*0.02, cy, cx + s*0.30, cy)
        c.line(cx + s*0.18, cy + s*0.12, cx + s*0.30, cy)
        c.line(cx + s*0.18, cy - s*0.12, cx + s*0.30, cy)

    elif kind == "auditorium":
        # scène + gradins
        c.roundRect(cx - s*0.30, cy - s*0.18, s*0.60, s*0.10, 4, stroke=1, fill=0)
        c.line(cx - s*0.26, cy - s*0.02, cx + s*0.26, cy - s*0.02)
        c.line(cx - s*0.22, cy + s*0.10, cx + s*0.22, cy + s*0.10)

    elif kind == "room":
        # cadre (porte/plan)
        c.roundRect(cx - s*0.30, cy - s*0.22, s*0.60, s*0.44, 8, stroke=1, fill=0)
        c.line(cx - s*0.30, cy + s*0.08, cx + s*0.30, cy + s*0.08)


def draw_sign_page(
    c: canvas.Canvas,
    w: float,
    h: float,
    *,
    event_title: str,
    event_subtitle: str | None,
    zone_title: str,
    zone_subtitle: str | None,
    icon_kind: str,
    logo_path: str | None,
    theme_variant: str,
):
    """
    Design A — Affiche premium :
    - Nom événement grand en haut
    - Bloc rose central + texte blanc énorme
    - Sous-texte optionnel
    - Picto
    - Logo en bas discret
    """
    m = 16 * mm
    event_title = (event_title or "").strip()
    event_subtitle = (event_subtitle or "").strip() if event_subtitle else ""
    zone_title = (zone_title or "").strip().upper()
    zone_subtitle = (zone_subtitle or "").strip() if zone_subtitle else ""

    # Fond
    c.setFillColorRGB(*hex_to_rgb01(WHITE))
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Header event (grand)
    # On garde beaucoup d'air -> premium + lisible
    header_y = h - 26 * mm

    # Ligne fine rose (signature)
    c.setStrokeColorRGB(*hex_to_rgb01(IMAGINE_PINK))
    c.setLineWidth(2)
    c.line(m, h - 16 * mm, w - m, h - 16 * mm)

    # Event title
    if event_title:
        max_w = w - 2 * m
        max_font = 40 if w < 700 else 54  # A4 vs A3
        fs = fit_text(c, event_title, max_w, "Helvetica-Bold", max_font=max_font, min_font=18)
        c.setFillColorRGB(*hex_to_rgb01(IMAGINE_GREY))
        c.setFont("Helvetica-Bold", fs)
        c.drawCentredString(w / 2, header_y, event_title)

        if event_subtitle:
            c.setFillColorRGB(*hex_to_rgb01(IMAGINE_PINK))
            c.setFont("Helvetica-Bold", 14 if w < 700 else 16)
            c.drawCentredString(w / 2, header_y - 10 * mm, event_subtitle)

    # Bloc central rose
    # Si event_title vide -> on remonte le bloc pour garder équilibre
    block_top = h * 0.70 if event_title else h * 0.78
    block_h = h * (0.40 if w < 700 else 0.42)
    block_w = w - 2 * m
    block_x = m
    block_y = block_top - block_h

    # Variante "encre" (plus ou moins rempli)
    if theme_variant == "eco":
        # Bande rose + grand texte gris (plus économe)
        c.setFillColorRGB(*hex_to_rgb01(WHITE))
        c.roundRect(block_x, block_y, block_w, block_h, 18, stroke=1, fill=0)
        c.setStrokeColorRGB(*hex_to_rgb01(IMAGINE_PINK))
        c.setLineWidth(6)
        c.line(block_x, block_y + block_h, block_x + block_w, block_y + block_h)
        zone_color = IMAGINE_GREY
        text_color = IMAGINE_GREY
    else:
        # Full rose (premium signage)
        c.setFillColorRGB(*hex_to_rgb01(IMAGINE_PINK))
        c.roundRect(block_x, block_y, block_w, block_h, 18, stroke=0, fill=1)
        zone_color = IMAGINE_PINK
        text_color = WHITE

    # Zone title (énorme)
    max_text_width = block_w - 24 * mm
    max_font_zone = 78 if w < 700 else 104
    min_font_zone = 34
    fs_zone = fit_text(c, zone_title, max_text_width, "Helvetica-Bold", max_font=max_font_zone, min_font=min_font_zone)
    c.setFillColorRGB(*hex_to_rgb01(text_color))
    c.setFont("Helvetica-Bold", fs_zone)
    c.drawCentredString(w / 2, block_y + block_h / 2 - fs_zone * 0.35, zone_title)

    # Zone subtitle (optionnel) sous le bloc
    # (utile pour EN / étage / indication)
    below_y = block_y - 18 * mm

    # Picto (au-dessus du sous-texte, centré)
    if icon_kind and icon_kind.lower() != "none":
        draw_pictogram(c, icon_kind, w / 2, below_y + 10 * mm, 44 if w < 700 else 52, zone_color)

    if zone_subtitle:
        c.setFillColorRGB(*hex_to_rgb01(IMAGINE_GREY))
        c.setFont("Helvetica-Bold", 16 if w < 700 else 20)
        c.drawCentredString(w / 2, below_y - 4 * mm, zone_subtitle)

    # Bas de page : ligne fine + logo centré
    c.setStrokeColorRGB(*hex_to_rgb01(IMAGINE_PINK))
    c.setLineWidth(1)
    c.line(m, 18 * mm, w - m, 18 * mm)

    if logo_path:
        try:
            img = ImageReader(logo_path)
            logo_w = 44 * mm
            logo_h = 18 * mm
            y = 24 * mm
            c.drawImage(img, (w - logo_w) / 2, y, width=logo_w, height=logo_h, mask="auto")
        except Exception:
            pass


def build_pdf(pages: list[dict], *, page_size):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=page_size)
    w, h = page_size

    logo_path = find_logo_path()

    for p in pages:
        draw_sign_page(
            c,
            w,
            h,
            event_title=p["event_title"],
            event_subtitle=p.get("event_subtitle"),
            zone_title=p["zone_title"],
            zone_subtitle=p.get("zone_subtitle"),
            icon_kind=p.get("icon_kind", "none"),
            logo_path=logo_path,
            theme_variant=p.get("theme_variant", "premium"),
        )
        c.showPage()

    c.save()
    return buf.getvalue()


# =========================
# STREAMLIT APP
# =========================
st.set_page_config(page_title=APP_TITLE, layout="centered")

# CSS léger (premium)
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');

html, body, .stApp, [class*="css"] {{
  font-family: 'Montserrat', sans-serif !important;
}}

header[data-testid="stHeader"] {{
  display: none;
}}

.stApp {{
  background: #F6F7FB;
}}

[data-testid="stHorizontalBlock"] {{
  background: white;
  border-radius: 16px;
  padding: 0.50rem 0.75rem;
  margin-bottom: 0.50rem;
  box-shadow: 0 1px 12px rgba(0,0,0,0.06);
}}

.stButton > button {{
  background-color: {IMAGINE_PINK} !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 14px !important;
  padding: 0.85rem 1.05rem !important;
  font-weight: 900 !important;
  min-height: 52px !important;
  white-space: nowrap !important;
}}
</style>
""",
    unsafe_allow_html=True,
)

# Header app
logo = find_logo_path()
c1, c2 = st.columns([1, 6], vertical_alignment="center")
with c1:
    if logo:
        st.image(logo, width=86)
with c2:
    st.markdown(f"## {APP_TITLE}")
    st.caption("Crée en quelques clics un PDF multi-pages (A4/A3) prêt à imprimer : accueil, auditorium, toilettes, vestiaire, etc.")
st.divider()

# ---- Controls
left, right = st.columns([1.2, 1], vertical_alignment="top")

with left:
    st.subheader("Paramètres")
    col1, col2 = st.columns(2)
    with col1:
        fmt = st.selectbox("Format", ["A4", "A3"], index=1)  # A3 par défaut (signalétique)
    with col2:
        orient = st.selectbox("Orientation", ["Portrait", "Paysage"], index=0)

    lang = st.selectbox("Langue", ["FR", "EN"], index=0)

    theme_variant = st.radio(
        "Style",
        ["premium", "eco"],
        index=0,
        help="Premium = bloc rose très lisible. Eco = plus économe en encre (cadre + liseré).",
        horizontal=True,
    )

    st.markdown("### Nom de l’événement")
    event_title = st.text_input("Titre (affiché en haut sur toutes les pages)", placeholder="Ex : Séminaire International — 2026")
    event_subtitle = st.text_input("Sous-titre (optionnel)", placeholder="Ex : Institut Imagine • 24 bd du Montparnasse")

with right:
    st.subheader("Panneaux")
    st.caption("Sélectionne des panneaux, puis personnalise le texte si besoin.")

    # Templates + pictos
    if lang == "FR":
        templates = [
            {"key": "accueil", "label": "Accueil", "default": "ACCUEIL", "icon": "info"},
            {"key": "auditorium", "label": "Auditorium", "default": "AUDITORIUM", "icon": "auditorium"},
            {"key": "wc", "label": "Toilettes", "default": "TOILETTES", "icon": "wc"},
            {"key": "vestiaire", "label": "Vestiaire", "default": "VESTIAIRE", "icon": "coat"},
            {"key": "pause", "label": "Pause", "default": "PAUSE", "icon": "coffee"},
            {"key": "sortie", "label": "Sortie", "default": "SORTIE", "icon": "exit"},
            {"key": "salle", "label": "Salle (personnalisée)", "default": "SALLE 1", "icon": "room"},
        ]
        subtitle_suggest = {
            "accueil": "Registration",
            "auditorium": "",
            "wc": "Restrooms",
            "vestiaire": "Cloakroom",
            "pause": "Coffee break",
            "sortie": "Exit",
            "salle": "",
        }
    else:
        templates = [
            {"key": "accueil", "label": "Registration", "default": "REGISTRATION", "icon": "info"},
            {"key": "auditorium", "label": "Auditorium", "default": "AUDITORIUM", "icon": "auditorium"},
            {"key": "wc", "label": "Restrooms", "default": "RESTROOMS", "icon": "wc"},
            {"key": "vestiaire", "label": "Cloakroom", "default": "CLOAKROOM", "icon": "coat"},
            {"key": "pause", "label": "Coffee break", "default": "COFFEE BREAK", "icon": "coffee"},
            {"key": "sortie", "label": "Exit", "default": "EXIT", "icon": "exit"},
            {"key": "salle", "label": "Room (custom)", "default": "ROOM 1", "icon": "room"},
        ]
        subtitle_suggest = {
            "accueil": "",
            "auditorium": "",
            "wc": "",
            "vestiaire": "",
            "pause": "",
            "sortie": "",
            "salle": "",
        }

    labels = [t["label"] for t in templates]
    default_sel = labels[:4]
    selected_labels = st.multiselect("Sélection", labels, default=default_sel)

    # Edition (override) par panneau sélectionné
    pages = []
    for t in templates:
        if t["label"] not in selected_labels:
            continue

        with st.container(border=True):
            st.markdown(f"**{t['label']}**")

            override = st.toggle("Texte personnalisé", value=(t["key"] == "salle"), key=f"ov_{t['key']}")
            zone_text = st.text_input(
                "Texte affiché",
                value=t["default"],
                disabled=(not override and t["key"] != "salle"),
                key=f"txt_{t['key']}",
            )

            # Sous-texte : utile pour bilingue / étage / précision
            suggested = subtitle_suggest.get(t["key"], "")
            zone_sub = st.text_input(
                "Sous-texte (optionnel)",
                value=suggested,
                key=f"sub_{t['key']}",
                placeholder="Ex : Restrooms / Niveau 0 / etc.",
            )

            icon_choice = st.selectbox(
                "Picto",
                ["auto", "none", "info", "auditorium", "wc", "coat", "coffee", "exit", "room"],
                index=0,
                key=f"ico_{t['key']}",
            )
            icon_kind = t["icon"] if icon_choice == "auto" else icon_choice

            pages.append(
                {
                    "event_title": event_title.strip(),
                    "event_subtitle": event_subtitle.strip() if event_subtitle.strip() else None,
                    "zone_title": (zone_text or t["default"]).strip(),
                    "zone_subtitle": zone_sub.strip() if zone_sub.strip() else None,
                    "icon_kind": icon_kind,
                    "theme_variant": theme_variant,
                }
            )

st.divider()

# ---- Page size
size = A4 if fmt == "A4" else A3
page_size = portrait(size) if orient == "Portrait" else landscape(size)

# ---- Guardrails (client-ready)
if not pages:
    st.warning("Sélectionne au moins un panneau.")
else:
    # Quick preview (textual)
    st.markdown("### Récap")
    recap_lines = [f"- {p['zone_title']}" + (f" — {p['zone_subtitle']}" if p.get("zone_subtitle") else "") for p in pages]
    st.markdown("\n".join(recap_lines))

# ---- Generate
colA, colB = st.columns([1, 1], vertical_alignment="center")
with colA:
    st.caption("Conseil : A3 pour couloirs/accueil ; A4 pour portes.")
with colB:
    disabled = len(pages) == 0
    if st.button("Générer le PDF", type="primary", use_container_width=True, disabled=disabled):
        pdf_bytes = build_pdf(pages, page_size=page_size)
        ts = datetime.now().strftime("%Y-%m-%d_%H%M")
        fname = f"signaletique_{fmt}_{orient}_{ts}.pdf"
        st.download_button(
            "⬇️ Télécharger le PDF",
            data=pdf_bytes,
            file_name=fname,
            mime="application/pdf",
            use_container_width=True,
        )

# ---- Product polish: footer
st.markdown("---")
st.caption(
    "Astuce terrain : imprime en couleur (premium) pour les points clés (Accueil, Auditorium). "
    "En cas de contrainte d’encre, passe en style Eco."
)
