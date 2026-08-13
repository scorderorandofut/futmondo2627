# =========================================================
# ARCHIVO: web.py
# VERSIÓN: v2.18
# DESCRIPCIÓN: Código completo de la aplicación.
#              - Clasificación inicializada a 0 (sin simulación automática).
#              - Cabecera FORMA centrada sobre 5 columnas dinámicas.
#              - Liguilla SM Round-Robin (13 jornadas) con fila de descanso.
# =========================================================

import base64
import json
from pathlib import Path
import requests
import streamlit as st

# ---------------------------------------------------------
# 1. ARCHIVOS Y RUTAS BASE
# ---------------------------------------------------------
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
ESCUDOS_DIR = ASSETS_DIR / "escudos"
LOGO_MAIN_PATH = ASSETS_DIR / "logo-futmondo.png"
STATE_PATH = BASE_DIR / "estado_liga.json"


def get_image_base64(path_str_or_path):
    """Convierte una ruta de archivo local a cadena Base64 para HTML."""
    if not path_str_or_path:
        return None
    p = Path(path_str_or_path)
    if p.exists() and p.is_file():
        with open(p, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return None


def obtener_ruta_escudo(team_id, escudo_url_api=None):
    """Busca primero el escudo localmente en assets/escudos/{team_id}.*
    Si no lo encuentra, usa la URL de la API.
    """
    if ESCUDOS_DIR.exists():
        for ext in [".png", ".jpg", ".jpeg", ".webp", ".svg"]:
            escudo_local = ESCUDOS_DIR / f"{team_id}{ext}"
            if escudo_local.exists():
                return str(escudo_local)
    return escudo_url_api


def cargar_estado():
    if STATE_PATH.exists():
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "jornada_actual": 11,
        "competiciones": {
            "SM": {
                "nombre": "The SuperMandingo League",
                "inicio": 1,
                "fin": 13,
                "rango_texto": "J1 a J13",
                "color_bg": "#354d47",
                "color_stripe": "#8affe2",
                "logo": "The-Super-Mandingo-League-Logo.png",
            },
            "CM": {
                "nombre": "Champions Mandinguera",
                "inicio": 5,
                "fin": 10,
                "rango_texto": "Inicia J5",
                "color_bg": "#0a192f",
                "color_stripe": "#00d2ff",
                "logo": "Champions-Mandinguera-Logo.png",
            },
            "CS": {
                "nombre": "Copa SeCadi, Ok?",
                "inicio": 11,
                "fin": 21,
                "rango_texto": "Inicia J11",
                "color_bg": "#2d1436",
                "color_stripe": "#ff5e7e",
                "logo": "Copa-SeCadi-Logo.png",
            },
            "SC": {
                "nombre": "Supercopa de Campeones",
                "inicio": 22,
                "fin": 23,
                "rango_texto": "Inicia J22",
                "color_bg": "#3a2d0c",
                "color_stripe": "#ffd700",
                "logo": "Supercopa-Logo.png",
            },
            "GC": {
                "nombre": "The 2Girls1Cup",
                "inicio": 30,
                "fin": 33,
                "rango_texto": "Inicia J30",
                "color_bg": "#3b1a1a",
                "color_stripe": "#ff4d4d",
                "logo": "2Girls1Cup-Logo.png",
            },
        },
    }


def generar_partidos_jornada(equipos_list, jornada):
    """Genera los emparejamientos dinámicos por jornada (Round-Robin a solo ida)
    y detecta qué equipo descansa cuando el número de equipos es impar.
    """
    if not equipos_list or len(equipos_list) < 2:
        return [], None

    teams = list(equipos_list)
    if len(teams) % 2 != 0:
        teams.append(None)

    n = len(teams)
    shift = (jornada - 1) % (n - 1)
    rotated = [teams[0]] + teams[1 + shift :] + teams[1 : 1 + shift]

    partidos = []
    equipo_descansa = None

    for i in range(n // 2):
        eq1 = rotated[i]
        eq2 = rotated[n - 1 - i]

        if eq1 is None:
            equipo_descansa = eq2
        elif eq2 is None:
            equipo_descansa = eq1
        else:
            if jornada % 2 == 0:
                partidos.append((eq2, eq1))
            else:
                partidos.append((eq1, eq2))

    return partidos, equipo_descansa


def calcular_tabla_real(equipos_dict, jornada_actual_tope):
    """Inicializa la tabla a 0 para reflejar datos reales de los partidos."""
    lista_eq = list(equipos_dict.values())
    if not lista_eq:
        return []

    stats = {}
    for eq in lista_eq:
        eq_id = eq["id"]
        stats[eq_id] = {
            "id": eq_id,
            "Equipo": eq["nombre_equipo"],
            "escudo": obtener_ruta_escudo(eq_id, eq.get("escudo_url")),
            "J": 0,
            "G": 0,
            "E": 0,
            "P": 0,
            "GF": 0,
            "GC": 0,
            "DG": 0,
            "Puntos": 0,
            "forma": [],  # Sin partidos jugados todavía
        }

    resultado_final = list(stats.values())
    
    # Ordenar por Puntos, Diferencia de Goles, Goles a Favor
    resultado_final.sort(key=lambda x: (x["Puntos"], x["DG"], x["GF"]), reverse=True)

    # Asignar posiciones
    for idx, row in enumerate(resultado_final):
        row["Pos"] = idx + 1

    return resultado_final


# ---------------------------------------------------------
# 2. FUNCIONES API FUTMONDO
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def login_futmondo(email, password):
    url_login = "https://api.futmondo.com/5/login/with_mail"
    payload = {
        "header": {"token": "null", "userid": ""},
        "query": {"mail": email, "pwd": password},
        "answer": {},
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(
            url_login, json=payload, headers=headers, timeout=10
        )
        response.raise_for_status()
        data = response.json()

        mobile_data = data.get("answer", {}).get("mobile", {})
        token = mobile_data.get("token")
        userid = mobile_data.get("userid")

        if token and userid:
            return token, userid
        else:
            st.error("❌ Error de credenciales o token no recibido de Futmondo.")
            return None, None
    except Exception as e:
        st.error(f"❌ Error en la autenticación con Futmondo: {e}")
        return None, None


@st.cache_data(ttl=600)
def obtener_equipos_liga(token, userid, championship_id):
    url = "https://api.futmondo.com/2/championship/teams"
    payload = {
        "header": {"token": token, "userid": userid},
        "query": {"championshipId": championship_id},
        "answer": {},
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        teams_list = data.get("answer", {}).get("teams", [])

        equipos_map = {}
        for team in teams_list:
            team_id = team.get("id") or team.get("teamid")
            equipos_map[team_id] = {
                "id": team_id,
                "nombre_equipo": team.get("teamname"),
                "escudo_url": team.get("photo"),
            }

        return equipos_map
    except Exception as e:
        st.error(f"❌ Error al obtener los equipos de Futmondo: {e}")
        return {}


# ---------------------------------------------------------
# 3. RENDERIZADOR DE CLASIFICACIÓN TIPO EXCEL
# ---------------------------------------------------------
def render_tabla_clasificacion(datos_clasificacion, jornada_act):
    """Calcula las últimas 5 jornadas disputadas antes de la jornada actual y
    construye la tabla en HTML puro continuo para evitar fallos de formato.
    """
    if jornada_act <= 5:
        jornadas_forma = [f"J{j}" for j in range(1, 6)]
    else:
        jornadas_forma = [f"J{j}" for j in range(jornada_act - 5, jornada_act)]

    css_style = """
<style>
.excel-table-container {
    width: fit-content;
    max-width: 100%;
    overflow-x: auto;
    margin: 10px auto 0 auto;
    background: rgba(18, 28, 25, 0.95);
    border-radius: 10px;
    padding: 6px 10px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.excel-table {
    width: auto;
    border-collapse: collapse;
    font-family: 'Segoe UI', Roboto, sans-serif;
    color: #FFFFFF;
    font-size: 0.85rem;
}
.excel-table th {
    color: #8da198;
    font-weight: 700;
    text-align: center;
    padding: 4px 2px;
    font-size: 0.72rem;
    letter-spacing: 0.3px;
    text-transform: uppercase;
    white-space: nowrap;
}
.excel-table th.th-forma {
    border-bottom: 1px solid rgba(255, 255, 255, 0.15);
    text-align: center;
}
.excel-table td {
    padding: 2px 2px;
    text-align: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    vertical-align: middle;
    white-space: nowrap;
}
.excel-table .col-stat {
    width: 36px;
    min-width: 36px;
    max-width: 36px;
    box-sizing: border-box;
    text-align: center;
}
.excel-table tr:hover {
    background: rgba(255, 255, 255, 0.04);
}
.excel-table .td-pos {
    color: #8da198;
    font-weight: 600;
    padding: 2px 6px;
    width: 28px;
}
.excel-table .td-equipo {
    text-align: left;
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 0.3px;
    padding-left: 4px;
    padding-right: 12px;
}
.excel-table .team-wrapper {
    display: flex;
    align-items: center;
    gap: 10px;
}
.excel-table .team-logo {
    width: 38px;
    height: 38px;
    object-fit: contain;
}
.excel-table .pts-green {
    background-color: #277e3c !important;
    color: #ffffff !important;
    font-weight: 800 !important;
    font-size: 0.95rem !important;
    border-radius: 3px;
    padding: 3px 0px !important;
}
.excel-table .pts-gold {
    background-color: #b58100 !important;
    color: #ffffff !important;
    font-weight: 800 !important;
    font-size: 0.95rem !important;
    border-radius: 3px;
    padding: 3px 0px !important;
}
.dot {
    height: 12px;
    width: 12px;
    border-radius: 50%;
    display: inline-block;
    margin: 0 auto;
}
.dot-w { background-color: #2ecc71; box-shadow: 0 0 5px rgba(46, 204, 113, 0.5); }
.dot-d { background-color: #f1c40f; box-shadow: 0 0 5px rgba(241, 196, 15, 0.5); }
.dot-l { background-color: #e74c3c; box-shadow: 0 0 5px rgba(231, 76, 60, 0.5); }
</style>
"""

    sub_headers = "".join([f'<th class="col-stat">{j}</th>' for j in jornadas_forma])

    html_body = f'{css_style}<div class="excel-table-container"><table class="excel-table"><thead>'
    html_body += f'<tr><th rowspan="2">POS</th><th rowspan="2" style="text-align: left; padding-left: 4px;">EQUIPO</th><th rowspan="2" class="col-stat">J</th><th rowspan="2" class="col-stat">G</th><th rowspan="2" class="col-stat">E</th><th rowspan="2" class="col-stat">P</th><th rowspan="2" class="col-stat">GF</th><th rowspan="2" class="col-stat">GC</th><th rowspan="2" class="col-stat">DG</th><th rowspan="2" class="col-stat">PTS</th><th colspan="5" class="th-forma">FORMA</th></tr>'
    html_body += f'<tr>{sub_headers}</tr></thead><tbody>'

    for row in datos_clasificacion:
        pts_class = "pts-green" if row["Pos"] <= 8 else "pts-gold"

        forma_dots_html = ""
        forma_list = row.get("forma", [])
        for jj in range(len(jornadas_forma)):
            if jj < len(forma_list):
                resultado = forma_list[jj]
                if resultado == "G":
                    forma_dots_html += '<td class="col-stat"><span class="dot dot-w" title="Victoria"></span></td>'
                elif resultado == "E":
                    forma_dots_html += '<td class="col-stat"><span class="dot dot-d" title="Empate"></span></td>'
                else:
                    forma_dots_html += '<td class="col-stat"><span class="dot dot-l" title="Derrota"></span></td>'
            else:
                forma_dots_html += '<td class="col-stat"><span style="color: rgba(255,255,255,0.2);">-</span></td>'

        escudo_val = row.get("escudo")
        if escudo_val:
            if str(escudo_val).startswith("http"):
                img_src = escudo_val
            else:
                b64 = get_image_base64(escudo_val)
                img_src = f"data:image/png;base64,{b64}" if b64 else ""

            img_html = f'<img src="{img_src}" class="team-logo"/>' if img_src else "⚽"
        else:
            img_html = "⚽"

        html_body += f'<tr><td class="td-pos">{row["Pos"]}</td><td class="td-equipo"><div class="team-wrapper">{img_html}<span>{row["Equipo"].upper()}</span></div></td><td class="col-stat">{row["J"]}</td><td class="col-stat">{row["G"]}</td><td class="col-stat">{row["E"]}</td><td class="col-stat">{row["P"]}</td><td class="col-stat">{row["GF"]}</td><td class="col-stat">{row["GC"]}</td><td class="col-stat">{row["DG"]}</td><td class="col-stat {pts_class}">{row["Puntos"]}</td>{forma_dots_html}</tr>'

    html_body += '</tbody></table></div>'
    return html_body


# ---------------------------------------------------------
# 4. CARGA DE ESTADO Y CONFIGURACIÓN PÁGINA
# ---------------------------------------------------------
estado = cargar_estado()
jornada_actual = int(estado.get("jornada_actual", 11))
competiciones = estado.get("competiciones", {})

comp_activa_key = None
for key, comp in competiciones.items():
    if comp["inicio"] <= jornada_actual <= comp["fin"]:
        comp_activa_key = key
        break

nombre_comp_activa = (
    competiciones[comp_activa_key]["nombre"]
    if comp_activa_key
    else "Competición General"
)

st.set_page_config(
    page_title="Competiciones Mandingueras",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos globales CSS
custom_css = """
<style>
    .stApp {
        background-color: #000000;
        color: #FFFFFF;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }

    #MainMenu, footer, header {visibility: hidden;}

    .badge-container {
        text-align: center;
        margin-top: 10px;
        margin-bottom: 4px;
    }

    .badge-active {
        background-color: #2ecc71;
        color: #000000;
        font-weight: bold;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        display: inline-block;
    }

    .badge-upcoming {
        background-color: rgba(255, 255, 255, 0.15);
        color: #DCDCDC;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        display: inline-block;
    }

    div.stButton > button {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }

    div.stButton > button:hover {
        background-color: #2ecc71 !important;
        color: #000000 !important;
        border-color: #2ecc71 !important;
        box-shadow: 0 0 10px rgba(46, 204, 113, 0.5) !important;
    }

    .sm-title {
        color: #FFFFFF;
        font-weight: 800;
        letter-spacing: 1px;
        margin-bottom: 0px;
        text-align: center;
    }

    .matches-wrapper {
        max-width: 500px;
        margin: 0 auto;
    }

    .match-row {
        background: rgba(22, 33, 29, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 8px 12px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .team-box {
        display: flex;
        align-items: center;
        gap: 8px;
        width: 42%;
    }

    .team-box.home {
        justify-content: flex-end;
        text-align: right;
    }

    .team-box.away {
        justify-content: flex-start;
        text-align: left;
    }

    .vs-box {
        width: 16%;
        text-align: center;
        font-weight: 800;
        color: #8affe2;
        font-size: 0.85rem;
    }

    .match-logo {
        width: 28px;
        height: 28px;
        object-fit: contain;
    }

    .team-name-text {
        font-size: 0.82rem;
        font-weight: 600;
        color: #ffffff;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. CABECERA PRINCIPAL
# ---------------------------------------------------------
if "selected_comp" not in st.session_state:
    st.session_state.selected_comp = "HUB"

if LOGO_MAIN_PATH.exists():
    img_main_b64 = get_image_base64(LOGO_MAIN_PATH)
    st.markdown(
        f"""
        <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 12px;'>
            <img src='data:image/png;base64,{img_main_b64}' width='130' alt='Logo Futmondo' />
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    "<h1 class='sm-title'>COMPETICIONES MANDINGUERAS 2026/27</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    f"""
    <div style='margin-top: 10px; text-align: center;'>
        <span class='badge-active'>🔴 JORNADA {jornada_actual} ACTIVA</span> 
        <span style='margin-left: 10px; color: #E0E0E0;'>En juego: <b>{nombre_comp_activa}</b></span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# ---------------------------------------------------------
# 6. HUB DE TARJETAS (SELECCIÓN DE COMPETICIÓN)
# ---------------------------------------------------------
st.markdown("### 🏆 Selecciona Competición")

cols = st.columns(len(competiciones))

for idx, (code, info) in enumerate(competiciones.items()):
    es_activa = code == comp_activa_key
    badge_class = "badge-active" if es_activa else "badge-upcoming"
    badge_text = f"J{jornada_actual} Activa" if es_activa else info["rango_texto"]

    bg_color = info.get("color_bg", "#1a2623")
    stripe_color = info.get("color_stripe", "#2ecc71")
    logo_filename = info.get("logo", "")
    nombre_comp = info.get("nombre", "")

    comp_logo_path = (
        (ASSETS_DIR / logo_filename)
        if logo_filename and (ASSETS_DIR / logo_filename).exists()
        else (BASE_DIR / logo_filename if logo_filename else None)
    )

    if comp_logo_path and comp_logo_path.exists():
        comp_logo_b64 = get_image_base64(comp_logo_path)
        logo_html = (
            f"<div style='display: flex; justify-content: center; align-items: center; height: 95px;'>"
            f"<img src='data:image/png;base64,{comp_logo_b64}' style='max-height: 85px; max-width: 130px; object-fit: contain;' alt='{nombre_comp}' />"
            f"</div>"
        )
    else:
        logo_html = (
            f"<div style='display: flex; justify-content: center; align-items: center; height: 95px; font-weight: bold; color: #FFFFFF; text-align: center; font-size: 0.9rem;'>"
            f"{nombre_comp}</div>"
        )

    card_html = (
        f"<div style='background-color: {bg_color}; border-left: 6px solid {stripe_color}; border-radius: 12px; padding: 16px 10px 12px 10px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);'>"
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
# 7. AUTENTICACIÓN Y CARGA DE DATOS DE FUTMONDO
# ---------------------------------------------------------
email = (
    st.secrets.get("FUTMONDO_USER")
    or st.secrets.get("futmondo", {}).get("email")
    or "scorderorando@gmail.com"
)
password = st.secrets.get("FUTMONDO_PASS") or st.secrets.get(
    "futmondo", {}
).get("password")
championship_id = (
    st.secrets.get("FUTMONDO_CHAMPIONSHIP_ID")
    or st.secrets.get("futmondo", {}).get("championship_id")
    or "5b56e918529e47fd32faea09"
)

equipos = {}
if email and password:
    token, userid = login_futmondo(email, password)
    if token and userid:
        equipos = obtener_equipos_liga(token, userid, championship_id)

# ---------------------------------------------------------
# 8. PANEL PRINCIPAL: CLASIFICACIÓN Y PARTIDOS
# ---------------------------------------------------------
st.markdown("---")

# --- SECCIÓN 1: CLASIFICACIÓN TIPO EXCEL ---
st.markdown(
    "<h3 style='text-align: center; margin-bottom: 12px;'>📊 Clasificación</h3>",
    unsafe_allow_html=True,
)

if equipos:
    datos_clasificacion = calcular_tabla_real(equipos, jornada_actual)
    html_tabla = render_tabla_clasificacion(datos_clasificacion, jornada_actual)
    st.markdown(html_tabla, unsafe_allow_html=True)
else:
    st.warning("Inicia sesión o sube tus datos para renderizar la tabla.")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# --- SECCIÓN 2: ENFRENTAMIENTOS DE LA JORNADA Y EQUIPO QUE DESCANSA ---
if "jornada_seleccionada" not in st.session_state:
    st.session_state.jornada_seleccionada = (
        jornada_actual if jornada_actual <= 13 else 13
    )

j_sel = st.session_state.jornada_seleccionada
lista_equipos = list(equipos.values()) if equipos else []

_, c_center, _ = st.columns([1, 1.2, 1])

with c_center:
    nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])

    with nav_col1:
        if st.button("◀", key="btn_j_prev", disabled=(j_sel <= 1), use_container_width=True):
            st.session_state.jornada_seleccionada -= 1
            st.rerun()

    with nav_col2:
        st.markdown(
            f"<h3 style='text-align: center; margin: 0; padding-top: 2px; font-size: 1.25rem;'>⚽ Jornada {j_sel} / 13</h3>",
            unsafe_allow_html=True,
        )

    with nav_col3:
        if st.button("▶", key="btn_j_next", disabled=(j_sel >= 13), use_container_width=True):
            st.session_state.jornada_seleccionada += 1
            st.rerun()

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    partidos_jornada, equipo_descansa = generar_partidos_jornada(lista_equipos, j_sel)

    if partidos_jornada or equipo_descansa:
        matches_html = "<div class='matches-wrapper'>"

        for eq1, eq2 in partidos_jornada:
            escudo1 = obtener_ruta_escudo(eq1["id"], eq1.get("escudo_url"))
            escudo2 = obtener_ruta_escudo(eq2["id"], eq2.get("escudo_url"))

            img_src1 = ""
            if escudo1:
                if str(escudo1).startswith("http"):
                    img_src1 = escudo1
                else:
                    b64 = get_image_base64(escudo1)
                    if b64:
                        img_src1 = f"data:image/png;base64,{b64}"

            img_src2 = ""
            if escudo2:
                if str(escudo2).startswith("http"):
                    img_src2 = escudo2
                else:
                    b64 = get_image_base64(escudo2)
                    if b64:
                        img_src2 = f"data:image/png;base64,{b64}"

            logo_html1 = f'<img src="{img_src1}" class="match-logo"/>' if img_src1 else "⚽"
            logo_html2 = f'<img src="{img_src2}" class="match-logo"/>' if img_src2 else "⚽"

            row_html = f"<div class='match-row'><div class='team-box home'><span class='team-name-text'>{eq1['nombre_equipo']}</span>{logo_html1}</div><div class='vs-box'>VS</div><div class='team-box away'>{logo_html2}<span class='team-name-text'>{eq2['nombre_equipo']}</span></div></div>"
            matches_html += row_html

        if equipo_descansa:
            escudo_desc = obtener_ruta_escudo(equipo_descansa["id"], equipo_descansa.get("escudo_url"))
            img_src_desc = ""
            if escudo_desc:
                if str(escudo_desc).startswith("http"):
                    img_src_desc = escudo_desc
                else:
                    b64 = get_image_base64(escudo_desc)
                    if b64:
                        img_src_desc = f"data:image/png;base64,{b64}"

            logo_desc_html = f'<img src="{img_src_desc}" class="match-logo"/>' if img_src_desc else "☕"

            descanso_html = f"<div class='match-row' style='background: rgba(255, 255, 255, 0.03); border: 1px dashed rgba(255, 255, 255, 0.2); justify-content: center; gap: 10px;'><span style='font-size: 0.82rem; color: #8da198; font-weight: 700;'>☕ DESCANSA:</span>{logo_desc_html}<span class='team-name-text' style='color: #8da198;'>{equipo_descansa['nombre_equipo']}</span></div>"
            matches_html += descanso_html

        matches_html += "</div>"
        st.markdown(matches_html, unsafe_allow_html=True)
    else:
        st.info("No hay emparejamientos disponibles para esta jornada.")
