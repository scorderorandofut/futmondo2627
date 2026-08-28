# =========================================================
# ARCHIVO: web.py
# VERSIÓN: v2.66.0
# DESCRIPCIÓN: Tabla estilo Champions, caché TTL nativa y 
#              mapeo exacto de jornadas de SM con la liga real.
# =========================================================

import base64
import json
import re
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

# Diccionario de abreviaturas oficiales
ABREVIATURAS = {
    "Maccabi de Levantá": "MCL",
    "Bass-T-Nation United": "BTN",
    "Rayo Malayo": "RAY",
    "LA MERIDA GUSTO FC": "LMG",
    "Al-larik-apapa": "ALP",
    "Estrella Galicia CF": "ESG",
    "La casa de la Juventus": "JUV",
    "AC Poniente": "ACP",
    "Apoel Barceló C.F.": "APO",
    "Olympique de Mamársella": "OLM",
    "Emerita Adisgusta!": "EMD",
    "Wine & Horses": "W&H",
    "Cskalaropa": "CSK",
    "CSKAlaropa": "CSK"
}

# Equivalencias entre el nombre del calendario y el nombre devuelto por la API de Futmondo
EQUIVALENCIAS_NOMBRES = {
    "Cskalaropa": "CSKAlaropa"
}

def normalizar_nombre_equipo(nombre):
    """Traduce el nombre del calendario al nombre oficial de la API si existe equivalencia."""
    return EQUIVALENCIAS_NOMBRES.get(nombre, nombre)


# ---------------------------------------------------------
# MAPEO DE JORNADAS SUPERMANDINGO CON LA LIGA REAL
# ---------------------------------------------------------
MAPEO_LIGA_REAL = {
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 6,
    6: 7,
    7: 8,
    8: 13,
    9: 18,
    10: 19,
    11: 21,
    12: 25,
    13: 26
}


# ---------------------------------------------------------
# CALENDARIO OFICIAL DE ENFRENTAMIENTOS POR JORNADA
# ---------------------------------------------------------
CALENDARIO_JORNADAS = {
    1: [
        ("Rayo Malayo", "Emerita Adisgusta!"),
        ("AC Poniente", "Olympique de Mamársella"),
        ("Al-larik-apapa", "Maccabi de Levantá"),
        ("Wine & Horses", "Cskalaropa"),
        ("Bass-T-Nation United", "Estrella Galicia CF"),
        ("LA MERIDA GUSTO FC", "Apoel Barceló C.F.")
    ],
    2: [
        ("Rayo Malayo", "La casa de la Juventus"),
        ("Emerita Adisgusta!", "Al-larik-apapa"),
        ("Olympique de Mamársella", "Wine & Horses"),
        ("Maccabi de Levantá", "Bass-T-Nation United"),
        ("Cskalaropa", "LA MERIDA GUSTO FC"),
        ("Estrella Galicia CF", "Apoel Barceló C.F.")
    ],
    3: [
        ("La casa de la Juventus", "AC Poniente"),
        ("Al-larik-apapa", "Rayo Malayo"),
        ("Bass-T-Nation United", "Emerita Adisgusta!"),
        ("LA MERIDA GUSTO FC", "Olympique de Mamársella"),
        ("Apoel Barceló C.F.", "Maccabi de Levantá"),
        ("Estrella Galicia CF", "Cskalaropa")
    ],
    4: [
        ("Al-larik-apapa", "La casa de la Juventus"),
        ("AC Poniente", "Wine & Horses"),
        ("Rayo Malayo", "Bass-T-Nation United"),
        ("Emerita Adisgusta!", "Apoel Barceló C.F."),
        ("Olympique de Mamársella", "Estrella Galicia CF"),
        ("Maccabi de Levantá", "Cskalaropa")
    ],
    5: [
        ("La casa de la Juventus", "Wine & Horses"),
        ("Bass-T-Nation United", "Al-larik-apapa"),
        ("LA MERIDA GUSTO FC", "AC Poniente"),
        ("Apoel Barceló C.F.", "Rayo Malayo"),
        ("Cskalaropa", "Emerita Adisgusta!"),
        ("Maccabi de Levantá", "Olympique de Mamársella")
    ],
    6: [
        ("Bass-T-Nation United", "La casa de la Juventus"),
        ("Wine & Horses", "LA MERIDA GUSTO FC"),
        ("Al-larik-apapa", "Apoel Barceló C.F."),
        ("AC Poniente", "Estrella Galicia CF"),
        ("Rayo Malayo", "Cskalaropa"),
        ("Emerita Adisgusta!", "Olympique de Mamársella")
    ],
    7: [
        ("La casa de la Juventus", "LA MERIDA GUSTO FC"),
        ("Apoel Barceló C.F.", "Bass-T-Nation United"),
        ("Estrella Galicia CF", "Wine & Horses"),
        ("Cskalaropa", "Al-larik-apapa"),
        ("Maccabi de Levantá", "AC Poniente"),
        ("Olympique de Mamársella", "Rayo Malayo")
    ],
    8: [
        ("Apoel Barceló C.F.", "La casa de la Juventus"),
        ("LA MERIDA GUSTO FC", "Estrella Galicia CF"),
        ("Bass-T-Nation United", "Cskalaropa"),
        ("Wine & Horses", "Maccabi de Levantá"),
        ("Al-larik-apapa", "Olympique de Mamársella"),
        ("AC Poniente", "Emerita Adisgusta!")
    ],
    9: [
        ("La casa de la Juventus", "Estrella Galicia CF"),
        ("Cskalaropa", "Apoel Barceló C.F."),
        ("Maccabi de Levantá", "LA MERIDA GUSTO FC"),
        ("Olympique de Mamársella", "Bass-T-Nation United"),
        ("Emerita Adisgusta!", "Wine & Horses"),
        ("Rayo Malayo", "AC Poniente")
    ],
    10: [
        ("Cskalaropa", "La casa de la Juventus"),
        ("Estrella Galicia CF", "Maccabi de Levantá"),
        ("Apoel Barceló C.F.", "Olympique de Mamársella"),
        ("LA MERIDA GUSTO FC", "Emerita Adisgusta!"),
        ("Wine & Horses", "Rayo Malayo"),
        ("Al-larik-apapa", "AC Poniente")
    ],
    11: [
        ("La casa de la Juventus", "Maccabi de Levantá"),
        ("Olympique de Mamársella", "Cskalaropa"),
        ("Emerita Adisgusta!", "Estrella Galicia CF"),
        ("Rayo Malayo", "LA MERIDA GUSTO FC"),
        ("AC Poniente", "Bass-T-Nation United"),
        ("Al-larik-apapa", "Wine & Horses")
    ],
    12: [
        ("Olympique de Mamársella", "La casa de la Juventus"),
        ("Maccabi de Levantá", "Emerita Adisgusta!"),
        ("Estrella Galicia CF", "Rayo Malayo"),
        ("Apoel Barceló C.F.", "AC Poniente"),
        ("LA MERIDA GUSTO FC", "Al-larik-apapa"),
        ("Bass-T-Nation United", "Wine & Horses")
    ],
    13: [
        ("La casa de la Juventus", "Emerita Adisgusta!"),
        ("Rayo Malayo", "Maccabi de Levantá"),
        ("AC Poniente", "Cskalaropa"),
        ("Al-larik-apapa", "Estrella Galicia CF"),
        ("Wine & Horses", "Apoel Barceló C.F."),
        ("Bass-T-Nation United", "LA MERIDA GUSTO FC")
    ]
}


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
    if ESCUDOS_DIR.exists() and team_id:
        for ext in [".png", ".jpg", ".jpeg", ".webp", ".svg"]:
            escudo_local = ESCUDOS_DIR / f"{team_id}{ext}"
            if escudo_local.exists():
                return str(escudo_local)
    return escudo_url_api


def buscar_equipo_info(nombre_calendario, equipos_dict):
    """Busca de forma flexible la información de un equipo manejando 
    diferencias de mayúsculas, acentos o espacios entre el calendario y la API.
    """
    if not equipos_dict:
        return {}
    
    nombre_busq = normalizar_nombre_equipo(nombre_calendario)
    
    if nombre_busq in equipos_dict:
        return equipos_dict[nombre_busq]
    
    for k, v in equipos_dict.items():
        if k.lower() == nombre_busq.lower():
            return v
            
    def normalizar(s):
        return re.sub(r'[^a-zA-Z0-9]', '', s).lower()
        
    norm_buscado = normalizar(nombre_busq)
    for k, v in equipos_dict.items():
        if normalizar(k) == norm_buscado:
            return v
            
    return {}


# ---------------------------------------------------------
# REGLA OFICIAL DE CONVERSIÓN DE PUNTOS A GOLES
# ---------------------------------------------------------
def puntos_a_goles_base(pts):
    """Calcula los goles base según la tabla oficial de rangos."""
    if pts <= 99:
        return 0
    elif 100 <= pts <= 119:
        return 1
    elif 120 <= pts <= 129:
        return 2
    elif 130 <= pts <= 139:
        return 3
    elif 140 <= pts <= 149:
        return 4
    elif 150 <= pts <= 159:
        return 5
    elif 160 <= pts <= 169:
        return 6
    elif 170 <= pts <= 179:
        return 7
    elif 180 <= pts <= 189:
        return 8
    else:
        return 8 + (pts - 180) // 10


def calcular_goles_partido(pts1, pts2):
    """Calcula los goles de ambos equipos aplicando la tabla base 
    y la regla especial de +1 gol si hay 10 o más puntos de diferencia 
    estando en el mismo intervalo.
    """
    g1 = puntos_a_goles_base(pts1)
    g2 = puntos_a_goles_base(pts2)

    if g1 == g2:
        if pts1 > pts2 and (pts1 - pts2) >= 10:
            g1 += 1
        elif pts2 > pts1 and (pts2 - pts1) >= 10:
            g2 += 1

    return g1, g2


# ---------------------------------------------------------
# 2. FUNCIONES API FUTMONDO & CACHÉ NATIVA (STREAMLIT)
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
        response = requests.post(url_login, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        mobile_data = data.get("answer", {}).get("mobile", {})
        token = mobile_data.get("token")
        userid = mobile_data.get("userid")
        return (token, userid) if (token and userid) else (None, None)
    except Exception:
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
            nombre = team.get("teamname")
            equipos_map[nombre] = {
                "id": team_id,
                "nombre_equipo": nombre,
                "escudo_url": team.get("photo"),
            }
        return equipos_map
    except Exception:
        return {}


@st.cache_data(ttl=600)
def obtener_jornadas_usuario(token, userid, championship_id, userteam_id):
    url = "https://api.futmondo.com/1/userteam/rounds"
    payload = {
        "header": {"token": token, "userid": userid},
        "query": {"championshipId": championship_id, "userteamId": userteam_id},
        "answer": {}
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json().get("answer", [])
    except Exception:
        return []


@st.cache_data(ttl=600)
def obtener_ranking_jornada(token, userid, championship_id, userteam_id, round_id):
    url = "https://api.futmondo.com/1/ranking/round"
    payload = {
        "header": {"token": token, "userid": userid},
        "query": {
            "championshipId": championship_id,
            "roundNumber": round_id,
            "userteamId": userteam_id
        },
        "answer": {}
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json().get("answer", {}).get("ranking", [])
    except Exception:
        return []


# ---------------------------------------------------------
# 3. CÁLCULO DINÁMICO DE CLASIFICACIÓN
# ---------------------------------------------------------
def calcular_clasificacion_real(equipos_map, rounds_info, token, userid, championship_id, userteam_id):
    stats = {}
    for nombre_eq in equipos_map.keys():
        stats[nombre_eq] = {
            "Equipo": nombre_eq,
            "id": equipos_map[nombre_eq]["id"],
            "escudo": obtener_ruta_escudo(equipos_map[nombre_eq]["id"], equipos_map[nombre_eq].get("escudo_url")),
            "J": 0, "G": 0, "E": 0, "P": 0, "GF": 0, "GC": 0, "DG": 0, "Puntos": 0, "SUM": 0,
            "forma": {}
        }

    jornadas_cerradas = [r for r in rounds_info if r.get("status") == "closed"]
    jornadas_cerradas = sorted(jornadas_cerradas, key=lambda x: x.get("number", 0))
    jornadas_jugadas_count = len(jornadas_cerradas)

    for r in jornadas_cerradas:
        num_jornada = r.get("number")
        round_id = r.get("id")
        
        ranking_data = obtener_ranking_jornada(token, userid, championship_id, userteam_id, round_id)
        
        puntos_fantasy = {}
        for item in ranking_data:
            nombre_api = item.get("name")
            pts = item.get("points", 0)
            info_eq = buscar_equipo_info(nombre_api, equipos_map)
            if info_eq and "nombre_equipo" in info_eq:
                puntos_fantasy[info_eq["nombre_equipo"]] = pts

        partidos = CALENDARIO_JORNADAS.get(num_jornada, [])

        for eq1_cal, eq2_cal in partidos:
            eq1 = normalizar_nombre_equipo(eq1_cal)
            eq2 = normalizar_nombre_equipo(eq2_cal)

            if eq1 in stats and eq2 in stats:
                pts1 = puntos_fantasy.get(eq1, 0)
                pts2 = puntos_fantasy.get(eq2, 0)

                stats[eq1]["SUM"] += pts1
                stats[eq2]["SUM"] += pts2

                gf1, gf2 = calcular_goles_partido(pts1, pts2)

                if gf1 > gf2:
                    res1, res2, res_letra1, res_letra2 = "G", "P", "G", "P"
                elif gf1 < gf2:
                    res1, res2, res_letra1, res_letra2 = "P", "G", "P", "G"
                else:
                    res1, res2, res_letra1, res_letra2 = "E", "E", "E", "E"

                stats[eq1]["J"] += 1
                stats[eq1]["GF"] += gf1
                stats[eq1]["GC"] += gf2
                if res1 == "G":
                    stats[eq1]["G"] += 1
                    stats[eq1]["Puntos"] += 3
                elif res1 == "E":
                    stats[eq1]["E"] += 1
                    stats[eq1]["Puntos"] += 1
                else:
                    stats[eq1]["P"] += 1
                stats[eq1]["forma"][num_jornada] = res_letra1

                stats[eq2]["J"] += 1
                stats[eq2]["GF"] += gf2
                stats[eq2]["GC"] += gf1
                if res2 == "G":
                    stats[eq2]["G"] += 1
                    stats[eq2]["Puntos"] += 3
                elif res2 == "E":
                    stats[eq2]["E"] += 1
                    stats[eq2]["Puntos"] += 1
                else:
                    stats[eq2]["P"] += 1
                stats[eq2]["forma"][num_jornada] = res_letra2

    lista_clasif = []
    for eq, data in stats.items():
        data["DG"] = data["GF"] - data["GC"]
        lista_clasif.append(data)

    lista_clasif = sorted(
        lista_clasif, 
        key=lambda x: (x["Puntos"], x["DG"], x["GF"], x["SUM"]), 
        reverse=True
    )

    for idx, row in enumerate(lista_clasif):
        row["Pos"] = idx + 1

    return lista_clasif, jornadas_jugadas_count


# ---------------------------------------------------------
# 4. RENDERIZADOR DE CLASIFICACIÓN TIPO EXCEL (CHAMPIONS STYLE)
# ---------------------------------------------------------
def render_tabla_clasificacion(datos_clasificacion, jornada_sel):
    jornadas_forma = []
    for i in range(5):
        j = jornada_sel - i
        jornadas_forma.append(j if j >= 1 else None)

    total_equipos = len(datos_clasificacion)

    css_style = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&display=swap');

.excel-table-container {
    width: 100%;
    overflow-x: auto;
    margin-top: -3px;
    background: #354d47;
    border-radius: 8px;
    padding: 8px;
    border: 1px solid #8aa4ae;
}
.excel-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Montserrat', 'Segoe UI', Roboto, sans-serif;
    color: #ffffff;
    font-size: 0.95rem;
    letter-spacing: 0.5px;
}
.excel-table th {
    color: #8aa4ae;
    font-weight: 800;
    text-align: center;
    padding: 5px 4px;
    font-size: 0.85rem;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.excel-table th.th-forma {
    border-bottom: 1px solid rgba(138, 164, 174, 0.3);
}
.excel-table td {
    padding: 9px 6px;
    text-align: center;
    border-bottom: 1px solid rgba(138, 164, 174, 0.15);
    vertical-align: middle;
}
.excel-table tr:hover {
    background: rgba(138, 164, 174, 0.1);
}
.excel-table .td-pos {
    color: #8aa4ae;
    font-weight: 700;
    width: 35px;
    font-size: 0.95rem;
    letter-spacing: 1px;
}
.excel-table .td-equipo {
    text-align: left;
    font-weight: 800;
    font-size: 1.02rem;
    letter-spacing: 0.8px;
    white-space: nowrap;
}
.excel-table .team-wrapper {
    display: flex;
    align-items: center;
    gap: 8px;
}
.excel-table .team-logo {
    width: 26px;
    height: 26px;
    object-fit: contain;
}
.excel-table .pts-green {
    background-color: #277e3c !important;
    color: #ffffff !important;
    font-weight: 900 !important;
    font-size: 1.1rem !important;
    letter-spacing: 0.5px;
    border-radius: 4px;
}
.excel-table .pts-gold {
    background-color: #b58100 !important;
    color: #ffffff !important;
    font-weight: 900 !important;
    font-size: 1.1rem !important;
    letter-spacing: 0.5px;
    border-radius: 4px;
}
.excel-table .pts-red {
    background-color: #c0392b !important;
    color: #ffffff !important;
    font-weight: 900 !important;
    font-size: 1.1rem !important;
    letter-spacing: 0.5px;
    border-radius: 4px;
}
.dot {
    height: 13px;
    width: 13px;
    border-radius: 50%;
    display: inline-block;
    margin: 0 1px;
}
.dot-w { background-color: #2ecc71; box-shadow: 0 0 4px rgba(46, 204, 113, 0.5); }
.dot-d { background-color: #f1c40f; box-shadow: 0 0 4px rgba(241, 196, 15, 0.5); }
.dot-l { background-color: #e74c3c; box-shadow: 0 0 4px rgba(231, 76, 60, 0.5); }
</style>
"""

    html_body = f"""{css_style}
<div class="excel-table-container">
<table class="excel-table">
<thead>
<tr>
    <th rowspan="2">POS</th>
    <th rowspan="2" style="text-align: left; padding-left: 28px;">EQUIPO</th>
    <th rowspan="2">J</th>
    <th rowspan="2">G</th>
    <th rowspan="2">E</th>
    <th rowspan="2">P</th>
    <th rowspan="2">GF</th>
    <th rowspan="2">GC</th>
    <th rowspan="2">DG</th>
    <th rowspan="2">PTS</th>
    <th colspan="{len(jornadas_forma)}" class="th-forma">FORMA</th>
</tr>
<tr>
"""
    for j in jornadas_forma:
        if j is not None:
            html_body += f"<th>J{j}</th>"
        else:
            html_body += "<th>-</th>"
    html_body += "\n</tr>\n</thead>\n<tbody>\n"

    for row in datos_clasificacion:
        if row["Pos"] == total_equipos:
            pts_class = "pts-red"
            border_color = "#c0392b"
        elif row["Pos"] <= 8:
            pts_class = "pts-green"
            border_color = "#277e3c"
        else:
            pts_class = "pts-gold"
            border_color = "#b58100"

        forma_dots_html = ""
        for j in jornadas_forma:
            if j is None:
                forma_dots_html += '<td><span style="color: #8aa4ae; font-size: 0.8rem;">-</span></td>'
            else:
                resultado = row.get("forma", {}).get(j)
                if resultado == "G":
                    forma_dots_html += '<td><span class="dot dot-w" title="Victoria"></span></td>'
                elif resultado == "E":
                    forma_dots_html += '<td><span class="dot dot-d" title="Empate"></span></td>'
                elif resultado == "P":
                    forma_dots_html += '<td><span class="dot dot-l" title="Derrota"></span></td>'
                else:
                    forma_dots_html += '<td><span style="color: #8aa4ae; font-size: 0.8rem;">-</span></td>'

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

        html_body += f"""<tr>
<td class="td-pos" style="border-right: 3px solid {border_color};">{row['Pos']}</td>
<td class="td-equipo"><div class="team-wrapper">{img_html}<span>{row['Equipo'].upper()}</span></div></td>
<td>{row['J']}</td>
<td>{row['G']}</td>
<td>{row['E']}</td>
<td>{row['P']}</td>
<td>{row['GF']}</td>
<td>{row['GC']}</td>
<td>{row['DG']}</td>
<td class="{pts_class}">{row['Puntos']}</td>
{forma_dots_html}
</tr>
"""

    html_body += "</tbody>\n</table>\n</div>"
    return html_body


# ---------------------------------------------------------
# 5. CONFIGURACIÓN PÁGINA Y ESTADO
# ---------------------------------------------------------
st.set_page_config(
    page_title="The SuperMandingo League",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

INICIO_SM = 1
FIN_SM = 13
NOMBRE_COMP = "The SuperMandingo League"
LOGO_COMP = ASSETS_DIR / "The-Super-Mandingo-League-Logo.png"

custom_css = """
<style>
    .stApp {
        background-color: #11191d;
        color: #ffffff;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    #MainMenu, footer, header {visibility: hidden;}
    .sm-title {
        color: #ffffff;
        font-weight: 800;
        letter-spacing: 1px;
        margin-bottom: 0px;
        text-align: center;
    }
    .match-box {
        background: #354d47;
        border-radius: 8px;
        padding: 8px 12px;
        border: 1px solid #8aa4ae;
        margin-bottom: 8px;
    }
    @media (max-width: 768px) {
        .mobile-spacer {
            height: 25px;
            display: block;
        }
    }
    @media (min-width: 769px) {
        .mobile-spacer {
            height: 0px;
            display: none;
        }
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. CABECERA PRINCIPAL
# ---------------------------------------------------------
if LOGO_COMP.exists():
    img_comp_b64 = get_image_base64(LOGO_COMP)
    st.markdown(
        f"""
        <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 12px;'>
            <img src='data:image/png;base64,{img_comp_b64}' width='140' alt='Logo SuperMandingo' />
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(f"<h1 class='sm-title'>{NOMBRE_COMP.upper()}</h1>", unsafe_allow_html=True)
st.markdown(
    f"<h3 class='sm-title' style='font-size: 1.1rem; color: #8aa4ae; margin-top: 4px;'>FASE DE LIGA</h3>", 
    unsafe_allow_html=True
)
st.markdown("---")

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
rounds_info = []
jornada_actual = 11
userteam_id = None

if email and password:
    token, userid = login_futmondo(email, password)
    if token and userid:
        equipos = obtener_equipos_liga(token, userid, championship_id)
        if equipos:
            userteam_id = next(iter(equipos.values()))["id"]
            rounds_info = obtener_jornadas_usuario(token, userid, championship_id, userteam_id)
            
            running_rounds = [r.get("number") for r in rounds_info if r.get("status") == "running"]
            closed_rounds = [r.get("number") for r in rounds_info if r.get("status") == "closed"]
            if running_rounds:
                jornada_actual = running_rounds[0]
            elif closed_rounds:
                jornada_actual = min(FIN_SM, max(closed_rounds) + 1)

# ---------------------------------------------------------
# 8. GESTIÓN DE ESTADO PARA LA JORNADA SELECCIONADA
# ---------------------------------------------------------
jornada_key_state = "jornada_supermandingo"
if jornada_key_state not in st.session_state:
    st.session_state[jornada_key_state] = max(
        INICIO_SM, min(jornada_actual, FIN_SM)
    )

jornada_seleccionada = st.session_state[jornada_key_state]

# ---------------------------------------------------------
# 9. VISTA PRINCIPAL: CLASIFICACIÓN (IZQ) Y ENFRENTAMIENTOS (DER)
# ---------------------------------------------------------
col_clasif, col_enf = st.columns([1.6, 1])

with col_clasif:
    st.markdown(f"### 📊 CLASIFICACIÓN")

    if equipos and rounds_info and token and userid:
        datos_clasificacion, jornadas_jugadas_count = calcular_clasificacion_real(
            equipos, rounds_info, token, userid, championship_id, userteam_id
        )
        html_tabla = render_tabla_clasificacion(datos_clasificacion, max(1, jornadas_jugadas_count))
        st.markdown(html_tabla, unsafe_allow_html=True)
    else:
        st.warning("Cargando datos reales de la API de Futmondo...")

with col_enf:
    st.markdown("<div class='mobile-spacer'></div>", unsafe_allow_html=True)
    
    jornada_elegida = st.selectbox(
        "Selecciona la Jornada",
        options=list(range(INICIO_SM, FIN_SM + 1)),
        index=st.session_state[jornada_key_state] - INICIO_SM,
        format_func=lambda x: f"⚽ JORNADA {x} — J{MAPEO_LIGA_REAL.get(x, x)} de Liga",
        key="combo_jornada_selector",
        label_visibility="collapsed"
    )

    if jornada_elegida != st.session_state[jornada_key_state]:
        st.session_state[jornada_key_state] = jornada_elegida
        st.rerun()

    st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

    partidos_jornada = CALENDARIO_JORNADAS.get(jornada_elegida, [])

    if partidos_jornada:
        round_obj = next((r for r in rounds_info if r.get("number") == jornada_elegida), None)
        is_closed = round_obj and round_obj.get("status") == "closed"
        round_id = round_obj.get("id") if round_obj else None

        puntos_jornada_sel = {}
        if is_closed and round_id and token and userid:
            ranking_data = obtener_ranking_jornada(token, userid, championship_id, userteam_id, round_id)
            for item in ranking_data:
                nombre_api = item.get("name")
                pts = item.get("points", 0)
                info_eq = buscar_equipo_info(nombre_api, equipos)
                if info_eq and "nombre_equipo" in info_eq:
                    puntos_jornada_sel[info_eq["nombre_equipo"]] = pts

        equipos_jugando = set()
        for n1_cal, n2_cal in partidos_jornada:
            equipos_jugando.add(normalizar_nombre_equipo(n1_cal))
            equipos_jugando.add(normalizar_nombre_equipo(n2_cal))
        
        todos_los_equipos = set(equipos.keys()) if equipos else set(ABREVIATURAS.keys())
        descansa_set = todos_los_equipos - equipos_jugando
        equipo_descansa = list(descansa_set)[0] if descansa_set else None

        for nombre1_cal, nombre2_cal in partidos_jornada:
            nombre1 = normalizar_nombre_equipo(nombre1_cal)
            nombre2 = normalizar_nombre_equipo(nombre2_cal)

            abrev1 = ABREVIATURAS.get(nombre1_cal, ABREVIATURAS.get(nombre1, nombre1[:3].upper()))
            abrev2 = ABREVIATURAS.get(nombre2_cal, ABREVIATURAS.get(nombre2, nombre2[:3].upper()))

            eq1_info = buscar_equipo_info(nombre1_cal, equipos)
            eq2_info = buscar_equipo_info(nombre2_cal, equipos)

            escudo1 = obtener_ruta_escudo(eq1_info.get("id"), eq1_info.get("escudo_url"))
            escudo2 = obtener_ruta_escudo(eq2_info.get("id"), eq2_info.get("escudo_url"))

            def get_img_src(escudo_val):
                if not escudo_val:
                    return ""
                if str(escudo_val).startswith("http"):
                    return escudo_val
                else:
                    b64 = get_image_base64(escudo_val)
                    return f"data:image/png;base64,{b64}" if b64 else ""

            src1 = get_img_src(escudo1)
            src2 = get_img_src(escudo2)

            img_tag1 = f'<img src="{src1}" width="50" style="object-fit: contain;"/>' if src1 else '⚽'
            img_tag2 = f'<img src="{src2}" width="50" style="object-fit: contain;"/>' if src2 else '⚽'

            if is_closed:
                pts1 = puntos_jornada_sel.get(nombre1, 0)
                pts2 = puntos_jornada_sel.get(nombre2, 0)

                gf1, gf2 = calcular_goles_partido(pts1, pts2)

                centro_html = f"""<div style="text-align: center;"><div style="font-size: 1.15rem; font-weight: 800; color: #ffffff;">{gf1} - {gf2}</div><div style="font-size: 0.68rem; color: #8aa4ae; margin-top: 2px;">({pts1}p) &nbsp; ({pts2}p)</div></div>"""
            else:
                centro_html = '<div style="font-size: 1.1rem; font-weight: bold; color: #8aa4ae; padding: 0 8px;">VS</div>'

            html_partido = (
                f"<div class='match-box'>"
                f"<div style=\"display: flex; align-items: center; justify-content: space-between; width: 100%;\">"
                f"<div style=\"display: flex; align-items: center; gap: 8px;\">"
                f"{img_tag1}"
                f"<span style=\"font-size: 1.0rem; font-weight: bold; color: #ffffff;\">{abrev1}</span>"
                f"</div>"
                f"{centro_html}"
                f"<div style=\"display: flex; align-items: center; gap: 8px; flex-direction: row-reverse;\">"
                f"{img_tag2}"
                f"<span style=\"font-size: 1.0rem; font-weight: bold; color: #ffffff;\">{abrev2}</span>"
                f"</div>"
                f"</div>"
                f"</div>"
            )

            st.markdown(html_partido, unsafe_allow_html=True)

        if equipo_descansa:
            abrev_desc = ABREVIATURAS.get(equipo_descansa, equipo_descansa[:3].upper())
            eq_desc_info = buscar_equipo_info(equipo_descansa, equipos)
            escudo_desc = obtener_ruta_escudo(eq_desc_info.get("id"), eq_desc_info.get("escudo_url"))
            src_desc = get_img_src(escudo_desc)
            img_desc_tag = f'<img src="{src_desc}" width="35" style="object-fit: contain; vertical-align: middle; margin-left: 10px;"/>' if src_desc else '⚽'

            html_descanso = (
                f"<div style='background: #23322e; border: 1px dashed #8aa4ae; border-radius: 8px; padding: 8px 12px; margin-top: 10px; display: flex; align-items: center; justify-content: center; color: #ffffff; font-size: 0.9rem;'>"
                f"<span style=\"color: #8aa4ae; font-weight: bold; margin-right: 6px;\">DESCANSA:</span>"
                f"<span style=\"font-weight: bold; color: #ffffff;\">{equipo_descansa.upper()} ({abrev_desc})</span>"
                f"{img_desc_tag}"
                f"</div>"
            )

            st.markdown(html_descanso, unsafe_allow_html=True)
    else:
        st.warning("No hay enfrentamientos programados para esta jornada.")
