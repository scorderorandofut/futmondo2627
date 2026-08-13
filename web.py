import streamlit as st
import json
import base64
from pathlib import Path

# ---------------------------------------------------------
# 1. ARCHIVOS Y RUTAS BASE
# ---------------------------------------------------------
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_MAIN_PATH = ASSETS_DIR / "logo-futmondo.png"
STATE_PATH = BASE_DIR / "estado_liga.json"

def get_image_base64(path):
    if path and path.exists():
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return None

def cargar_estado():
    if STATE_PATH.exists():
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "jornada_actual": 1,
        "competiciones": {
            "SM": {
                "nombre": "The SuperMandingo League",
                "inicio": 1, "fin": 13, "rango_texto": "J1 a J4",
                "color_bg": "#354d47", "color_stripe": "#8affe2",
                "logo": "The-Super-Mandingo-League-Logo.png"
            },
            "CM": {
                "nombre": "Champions Mandinguera",
                "inicio": 5, "fin": 10, "rango_texto": "Inicia J5",
                "color_bg": "#0a192f", "color_stripe": "#00d2ff",
                "logo": "Champions.png"
            },
            "CS": {
                "nombre": "Copa SeCadi, Ok?",
                "inicio": 11, "fin": 21, "rango_texto": "Inicia J11",
                "color_bg": "#ff5e7e", "color_stripe": "#2d1436",
                "logo": "Logo_Copa.png"
            },
            "SC": {
                "nombre": "Supercopa de Campeones",
                "inicio": 22, "fin": 23, "rango_texto": "Inicia J22",
                "color_bg": "#37004d", "color_stripe": "#fc7e00",
                "logo": "Supercopa-Logo.png",
                "logo_vertical": "Supercopa-Logo-vertical.png",
                "logo_scale": 1.6
            },
            "GC": {
                "nombre": "The 2Girls1Cup",
                "inicio": 30, "fin": 33, "rango_texto": "Inicia J30",
                "color_bg": "#523e00", "color_stripe": "#bf9000",
                "logo": "The-2-Girls-1-Cup-Logo.png"
            }
        }
    }

estado = cargar_estado()
jornada_actual = estado.get("jornada_actual", 1)
competiciones = estado.get("competiciones", {})

comp_activa_key = None
for key, comp in competiciones.items():
    if comp["inicio"] <= jornada_actual <= comp["fin"]:
        comp_activa_key = key
        break

nombre_comp_activa = competiciones[comp_activa_key]["nombre"] if comp_activa_key else "Competición General"

# ---------------------------------------------------------
# 2. CONFIGURACIÓN DE PÁGINA Y CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Competiciones Mandingueras",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Dinámico para Hover personalizado según competición
hover_styles = ""
for idx, (code, info) in enumerate(competiciones.items()):
    col_idx = idx + 1
    stripe_color = info.get("color_stripe", "#2ecc71")
    
    hover_styles += f"""
    div[data-testid="stColumn"]:nth-child({col_idx}) div.stButton > button:hover,
    div[data-testid="column"]:nth-child({col_idx}) div.stButton > button:hover {{
        background-color: {stripe_color} !important;
        color: #000000 !important;
        border-color: {stripe_color} !important;
        box-shadow: 0 0 12px {stripe_color}80 !important;
    }}
    """

custom_css = f"""
<style>
    .stApp {{
        background-color: #000000;
        color: #FFFFFF;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }}

    #MainMenu, footer, header {{visibility: hidden;}}

    .badge-container {{
        text-align: center;
        margin-top: 10px;
        margin-bottom: 4px;
    }}

    .badge-active {{
        background-color: #2ecc71;
        color: #000000;
        font-weight: bold;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        display: inline-block;
    }}
    
    .badge-upcoming {{
        background-color: rgba(255, 255, 255, 0.15);
        color: #DCDCDC;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        display: inline-block;
    }}

    div.stButton > button {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        margin-top: 6px;
    }}

    {hover_styles}

    .sm-card-preview {{
        background-color: #111111;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
    }}

    .sm-title {{
        color: #FFFFFF;
        font-weight: 800;
        letter-spacing: 1px;
        margin-bottom: 0px;
        text-align: center;
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. ESTADO DE NAVEGACIÓN
# ---------------------------------------------------------
if 'selected_comp' not in st.session_state:
    st.session_state.selected_comp = "HUB"

# ---------------------------------------------------------
# 4. CABECERA PRINCIPAL
# ---------------------------------------------------------
if LOGO_MAIN_PATH.exists():
    img_main_b64 = get_image_base64(LOGO_MAIN_PATH)
    st.markdown(f"""
        <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 12px;'>
            <img src='data:image/png;base64,{img_main_b64}' width='130' alt='Logo Futmondo' />
        </div>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='sm-title'>COMPETICIONES MANDINGUERAS 2026/27</h1>", unsafe_allow_html=True)
st.markdown(f"""
    <div style='margin-top: 10px; text-align: center;'>
        <span class='badge-active'>🔴 JORNADA {jornada_actual} ACTIVA</span> 
        <span style='margin-left: 10px; color: #E0E0E0;'>En juego: <b>{nombre_comp_activa}</b></span>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------
# 5. HUB DE TARJETAS
# ---------------------------------------------------------
st.markdown("### 🏆 Selecciona Competición")

cols = st.columns(len(competiciones))

for idx, (code, info) in enumerate(competiciones.items()):
    es_activa = (code == comp_activa_key)
    badge_class = "badge-active" if es_activa else "badge-upcoming"
    badge_text = f"J{jornada_actual} Activa" if es_activa else info["rango_texto"]

    bg_color = info.get("color_bg", "#1a2623")
    stripe_color = info.get("color_stripe", "#2ecc71")
    
    # Prioridad: usa 'logo_vertical' si está especificado; si no, usa 'logo'
    logo_filename = info.get("logo_vertical") or info.get("logo", "")
    comp_logo_path = ASSETS_DIR / logo_filename if logo_filename else None

    # Estilos de escala/filtro (si existen)
    logo_filter = info.get("logo_filter", "")
    logo_scale = info.get("logo_scale", 1.0)
    
    img_css = "max-height: 85px; max-width: 160px; object-fit: contain;"
    if logo_filter:
        img_css += f" filter: {logo_filter};"
    if logo_scale != 1.0 and not info.get("logo_vertical"): 
        # Aplica escala solo si no es el logo vertical ya adaptado
        img_css += f" transform: scale({logo_scale});"

    if comp_logo_path and comp_logo_path.exists():
        comp_logo_b64 = get_image_base64(comp_logo_path)
        logo_html = f"<div style='display: flex; justify-content: center; align-items: center; height: 95px; overflow: hidden;'><img src='data:image/png;base64,{comp_logo_b64}' style='{img_css}' alt='{info['nombre']}' /></div>"
    else:
        logo_html = f"<div style='display: flex; justify-content: center; align-items: center; height: 95px; font-weight: bold; color: #FFFFFF;'>{info['nombre']}</div>"

    card_html = (
        f"<div style='background-color: {bg_color}; border-left: 6px solid {stripe_color}; "
        f"border-radius: 12px; padding: 16px 10px 12px 10px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);'>"
        f"{logo_html}"
        f"<div class='badge-container'><span class='{badge_class}'>{badge_text}</span></div>"
        f"</div>"
    )

    with cols[idx]:
        st.markdown(card_html, unsafe_allow_html=True)
        if st.button("Entrar", key=f"btn_{code}", use_container_width=True):
            st.session_state.selected_comp = code

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. VISTA PREVIA
# ---------------------------------------------------------
comp_vista = st.session_state.selected_comp if st.session_state.selected_comp != "HUB" else (comp_activa_key or "SM")
info_vista = competiciones.get(comp_vista, competiciones["SM"])

# En la vista previa siempre se usa el logo principal horizontal
vista_logo_path = ASSETS_DIR / info_vista.get("logo", "")
if vista_logo_path.exists():
    vista_logo_b64 = get_image_base64(vista_logo_path)
    
    v_filter = info_vista.get("logo_filter", "")
    v_img_css = "max-height: 65px; max-width: 120px; object-fit: contain; margin-right: 18px;"
    if v_filter:
        v_img_css += f" filter: {v_filter};"
        
    vista_logo_html = f"<img src='data:image/png;base64,{vista_logo_b64}' style='{v_img_css}' alt='{info_vista['nombre']}' />"
else:
    vista_logo_html = ""

st.markdown(f"""
<div class='sm-card-preview' style='display: flex; align-items: center; border-left: 6px solid {info_vista.get("color_stripe", "#2ecc71")};'>
    {vista_logo_html}
    <div>
        <h3 style='margin: 0; font-size: 1.3rem;'>🔥 {info_vista['nombre']} — Jornada {jornada_actual}</h3>
        <p style='color: #DCDCDC; margin: 4px 0 0 0; font-size: 0.9rem;'>Visualizando datos y enfrentamientos asignados a la jornada {jornada_actual}.</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.info(f"💡 Listo para cargar las puntuaciones de Futmondo correspondientes a {info_vista['nombre']} en la Jornada {jornada_actual}.")