# =========================================================
# ARCHIVO: web.py
# VERSIÓN: v.2.99.23 (Separación vertical en partidos y spinner personalizado)
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

EQUIVALENCIAS_NOMBRES = {
    "Cskalaropa": "CSKAlaropa"
}

def normalizar_nombre_equipo(nombre):
    """Traduce el nombre del calendario al nombre oficial de la API si existe equivalencia."""
    return EQUIVALENCIAS_NOMBRES.get(nombre, nombre)


def formatear_nombre_futmondo(nombre_completo):
    """Formatea el nombre al estilo Futmondo (ej. Mario Soriano -> M. Soriano, Kang-In Lee -> K. Lee)."""
    if not nombre_completo:
        return "Jugador"
    partes = nombre_completo.strip().split()
    if len(partes) > 1:
        return f"{partes[0][0].upper()}. {' '.join(partes[1:])}"
    return nombre_completo


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
    """Convierte una ruta local a cadena Base64 para HTML."""
    if not path_str_or_path:
        return None
    p = Path(path_str_or_path)
    if p.exists() and p.is_file():
        with open(p, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return None


def obtener_ruta_escudo(team_id, escudo_url_api=None):
    """Busca primero el escudo localmente y si no, usa la URL de la API."""
    if ESCUDOS_DIR.exists() and team_id:
        for ext in [".png", ".jpg", ".jpeg", ".webp", ".svg"]:
            escudo_local = ESCUDOS_DIR / f"{team_id}{ext}"
            if escudo_local.exists():
                return str(escudo_local)
    return escudo_url_api


def buscar_equipo_info(nombre_calendario, equipos_dict):
    """Busca de forma flexible la información de un equipo."""
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
    if pts <= 99: return 0
    elif 100 <= pts <= 119: return 1
    elif 120 <= pts <= 129: return 2
    elif 130 <= pts <= 139: return 3
    elif 140 <= pts <= 149: return 4
    elif 150 <= pts <= 159: return 5
    elif 160 <= pts <= 169: return 6
    elif 170 <= pts <= 179: return 7
    elif 180 <= pts <= 189: return 8
    else: return 8 + (pts - 180) // 10


def calcular_goles_partido(pts1, pts2, aplicar_regla_diferencia=True):
    g1 = puntos_a_goles_base(pts1)
    g2 = puntos_a_goles_base(pts2)

    if aplicar_regla_diferencia and g1 == g2:
        if pts1 > pts2 and (pts1 - pts2) >= 10:
            g1 += 1
        elif pts2 > pts1 and (pts2 - pts1) >= 10:
            g2 += 1

    return g1, g2


# ---------------------------------------------------------
# 2. FUNCIONES API FUTMONDO & CACHÉ
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


@st.cache_data(ttl=600)
def obtener_round_lineup(token, userid, championship_id, round_id, userteam_id):
    """Consulta la alineación detallada y puntos de un equipo en una jornada concreta."""
    url = "https://api.futmondo.com/1/userteam/roundlineup"
    payload = {
        "header": {"token": token, "userid": userid},
        "query": {
            "championshipId": championship_id,
            "round": round_id,
            "userteamId": userteam_id
        },
        "answer": {}
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json().get("answer", {})
    except Exception:
        return {}


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

                gf1, gf2 = calcular_goles_partido(pts1, pts2, aplicar_regla_diferencia=True)

                if gf1 > gf2: res1, res2, res_letra1, res_letra2 = "G", "P", "G", "P"
                elif gf1 < gf2: res1, res2, res_letra1, res_letra2 = "P", "G", "P", "G"
                else: res1, res2, res_letra1, res_letra2 = "E", "E", "E", "E"

                stats[eq1]["J"] += 1
                stats[eq1]["GF"] += gf1
                stats[eq1]["GC"] += gf2
                if res1 == "G": stats[eq1]["G"] += 1; stats[eq1]["Puntos"] += 3
                elif res1 == "E": stats[eq1]["E"] += 1; stats[eq1]["Puntos"] += 1
                else: stats[eq1]["P"] += 1
                stats[eq1]["forma"][num_jornada] = res_letra1

                stats[eq2]["J"] += 1
                stats[eq2]["GF"] += gf2
                stats[eq2]["GC"] += gf1
                if res2 == "G": stats[eq2]["G"] += 1; stats[eq2]["Puntos"] += 3
                elif res2 == "E": stats[eq2]["E"] += 1; stats[eq2]["Puntos"] += 1
                else: stats[eq2]["P"] += 1
                stats[eq2]["forma"][num_jornada] = res_letra2

    lista_clasif = []
    for eq, data in stats.items():
        data["DG"] = data["GF"] - data["GC"]
        lista_clasif.append(data)

    lista_clasif = sorted(lista_clasif, key=lambda x: (x["Puntos"], x["DG"], x["GF"], x["SUM"]), reverse=True)

    for idx, row in enumerate(lista_clasif):
        row["Pos"] = idx + 1

    return lista_clasif, jornadas_jugadas_count


# ---------------------------------------------------------
# 4. RENDERIZADOR DE CLASIFICACIÓN TIPO EXCEL
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
.excel-table-container { width: 100%; overflow-x: auto; margin-top: -3px; background: #354d47; border-radius: 8px; padding: 8px; border: none !important; box-sizing: border-box; }
.excel-table { width: 100%; border-collapse: collapse; font-family: 'Montserrat', 'Segoe UI', Roboto, sans-serif; color: #ffffff; font-size: 0.95rem; letter-spacing: 0.5px; border: none !important; }
.excel-table th, .excel-table td, .excel-table tr, .excel-table thead, .excel-table tbody { border: none !important; border-top: none !important; border-bottom: none !important; border-left: none !important; border-right: none !important; }
.excel-table th { color: #8aa4ae; font-weight: 800; text-align: center; padding: 5px 4px; font-size: 0.85rem; letter-spacing: 1px; text-transform: uppercase; }
.excel-table td { padding: 9px 6px; text-align: center; vertical-align: middle; }
.excel-table .td-pos { color: #8aa4ae; font-weight: 700; width: 35px; font-size: 0.95rem; letter-spacing: 1px; }
.excel-table .td-equipo { text-align: left; font-weight: 800; font-size: 1.02rem; letter-spacing: 0.8px; }
.excel-table .team-wrapper { display: flex; align-items: center; gap: 8px; min-width: 0; }
.excel-table .team-wrapper span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; }
.excel-table .team-logo { width: 26px; height: 26px; object-fit: contain; flex-shrink: 0; }
.excel-table .pts-green { background-color: #277e3c !important; color: #ffffff !important; font-weight: 900 !important; font-size: 1.1rem !important; border-radius: 4px; }
.excel-table .pts-gold { background-color: #b58100 !important; color: #ffffff !important; font-weight: 900 !important; font-size: 1.1rem !important; border-radius: 4px; }
.excel-table .pts-red { background-color: #c0392b !important; color: #ffffff !important; font-weight: 900 !important; font-size: 1.1rem !important; border-radius: 4px; }

/* Estilos refinados de los círculos de forma */
.form-badge {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 900;
    margin: 0 auto;
    box-sizing: border-box;
}
.form-win {
    background-color: #27ae60;
    color: #ffffff;
    border: 2px solid #27ae60;
    box-shadow: 0 0 0 2px rgba(46, 204, 113, 0.25);
}
.form-draw {
    background-color: #7f8c8d;
    color: #ffffff;
    border: 2px solid #7f8c8d;
    box-shadow: 0 0 0 2px rgba(127, 140, 141, 0.25);
}
.form-loss {
    background-color: #e74c3c;
    color: #ffffff;
    border: 2px solid #e74c3c;
    box-shadow: 0 0 0 2px rgba(231, 76, 60, 0.25);
}
.form-empty {
    background-color: transparent;
    border: 2px solid #7f8c8d;
    color: transparent;
    width: 22px;
    height: 22px;
}
</style>
"""

    html_body = f"""{css_style}
<div class="excel-table-container">
<table class="excel-table">
<thead>
<tr>
    <th rowspan="2">POS</th>
    <th rowspan="2" style="text-align: left; padding-left: 28px;">EQUIPO</th>
    <th rowspan="2">J</th><th rowspan="2">G</th><th rowspan="2">E</th><th rowspan="2">P</th>
    <th rowspan="2">GF</th><th rowspan="2">GC</th><th rowspan="2">DG</th><th rowspan="2">PTS</th>
    <th colspan="{len(jornadas_forma)}" class="th-forma">FORMA</th>
</tr>
<tr>
"""
    for j in jornadas_forma:
        html_body += f"<th>J{j}</th>" if j is not None else "<th>-</th>"
    html_body += "</tr></thead><tbody>"

    for idx, row in enumerate(datos_clasificacion):
        if row["Pos"] == total_equipos: pts_class = "pts-red"; border_color = "#c0392b"
        elif row["Pos"] <= 8: pts_class = "pts-green"; border_color = "#277e3c"
        else: pts_class = "pts-gold"; border_color = "#b58100"

        row_bg = "#151e19" if idx % 2 == 0 else "#354d47"

        forma_dots_html = ""
        for j in jornadas_forma:
            if j is None:
                forma_dots_html += '<td><span class="form-badge form-empty"></span></td>'
            else:
                resultado = row.get("forma", {}).get(j)
                if resultado == "G":
                    forma_dots_html += '<td><span class="form-badge form-win">✓</span></td>'
                elif resultado == "E":
                    forma_dots_html += '<td><span class="form-badge form-draw">-</span></td>'
                elif resultado == "P":
                    forma_dots_html += '<td><span class="form-badge form-loss">×</span></td>'
                else:
                    forma_dots_html += '<td><span class="form-badge form-empty"></span></td>'

        escudo_val = row.get("escudo")
        if escudo_val:
            img_src = escudo_val if str(escudo_val).startswith("http") else (f"data:image/png;base64,{get_image_base64(escudo_val)}" if get_image_base64(escudo_val) else "")
            img_html = f'<img src="{img_src}" class="team-logo"/>' if img_src else "⚽"
        else:
            img_html = "⚽"

        html_body += f"""<tr style="background-color: {row_bg};">
<td class="td-pos" style="border-right: 3px solid {border_color};">{row['Pos']}</td>
<td class="td-equipo"><div class="team-wrapper">{img_html}<span>{row['Equipo'].upper()}</span></div></td>
<td>{row['J']}</td><td>{row['G']}</td><td>{row['E']}</td><td>{row['P']}</td>
<td>{row['GF']}</td><td>{row['GC']}</td><td>{row['DG']}</td>
<td class="{pts_class}">{row['Puntos']}</td>
{forma_dots_html}
</tr>"""

    html_body += "</tbody></table></div>"
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
LOGO_COMP = ASSETS_DIR / "The-Super-Mandingo-League-Logo.png"

# Estilos CSS generales
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&display=swap');
    .stApp { background-color: #11191d; color: #ffffff; font-family: 'Segoe UI', Roboto, sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
    
    .match-container {
        background-color: #354d47; border: 1px solid #8aa4ae; border-radius: 8px;
        padding: 14px 18px; display: flex; align-items: center; justify-content: space-between;
        min-height: 95px; box-sizing: border-box; width: 100%;
        margin-bottom: 14px; /* <--- Espacio vertical entre partidos en web */
    }
    .match-team { display: flex; align-items: center; gap: 12px; width: 35%; font-weight: 800; font-size: 1.15rem; letter-spacing: 0.5px; }
    .match-team.right { justify-content: flex-end; text-align: right; }
    
    .match-center { text-align: center; width: 30%; display: flex; justify-content: center; align-items: center; }
    .score-box {
        background-color: #23322e;
        border: 1px solid #8aa4ae;
        border-radius: 8px;
        padding: 0 24px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 900;
        font-size: 2.3rem;
        letter-spacing: 3px;
        color: #ffffff;
        box-shadow: inset 0 1px 4px rgba(0,0,0,0.4);
    }
    
    /* Botón desplegable adaptado a columnas nativas */
    div[data-testid="stButton"] {
        width: 100% !important;
        margin-top: -18px !important;
        margin-bottom: 18px !important;
        z-index: 5 !important;
    }
    div[data-testid="stButton"] > button {
        width: 100% !important;
        height: 24px !important;
        min-height: 24px !important;
        background-color: #23322e !important;
        border: 1px solid #8aa4ae !important;
        border-top: none !important;
        border-radius: 0 0 6px 6px !important;
        padding: 0 !important;
        font-size: 1.1rem !important;
        color: #ffffff !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.4);
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #2e423d !important;
        border-color: #ffffff !important;
        color: #ffffff !important;
    }

    @media (max-width: 768px) {
        .match-container {
            min-height: auto !important;
            padding: 10px 12px !important;
            margin-bottom: 12px !important; /* <--- Espacio vertical entre partidos en móvil */
        }
        .score-box {
            font-size: 1.5rem !important;
            height: 46px !important;
            padding: 0 12px !important;
            letter-spacing: 1px !important;
        }
        
        /* Contenedor del botón centrado y con solapamiento en móvil */
        div.row-widget.stButton, div[data-testid="stButton"] {
            margin-top: -36px !important;
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
            z-index: 5 !important;
        }
        
        /* Botón pequeño, centrado y fundido con la tarjeta (sin borde superior) */
        div[data-testid="stButton"] button {
            min-height: 22px !important;
            height: 24px !important;
            width: 70px !important;
            margin: 0 auto !important;
            display: block !important;
            padding: 0px !important;
            font-size: 11px !important;
            border-top: none !important;
            border-radius: 0 0 6px 6px !important;
        }
    }

    .lineup-unified-card {
        background-color: #354d47; border: 1px solid #8aa4ae; border-radius: 8px;
        padding: 14px 18px; margin-bottom: 12px; box-sizing: border-box; width: 100%;
    }

    .fields-flex-container {
        display: flex;
        gap: 12px;
        width: 100%;
    }

    .soccer-field {
        background: linear-gradient(135deg, #236136 0%, #154222 100%);
        border: 2px solid rgba(255, 255, 255, 0.4);
        border-radius: 8px;
        padding: 38px 6px 12px 6px;
        position: relative;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 380px;
        box-sizing: border-box;
        box-shadow: inset 0 0 15px rgba(0,0,0,0.5);
    }
    .field-line-center {
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: rgba(255, 255, 255, 0.3);
        pointer-events: none;
    }
    .field-header-top-left {
        position: absolute;
        top: 8px;
        left: 10px;
        display: flex;
        align-items: center;
        gap: 6px;
        z-index: 5;
        background: rgba(0, 0, 0, 0.4);
        padding: 3px 8px;
        border-radius: 4px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .field-header-top-right {
        position: absolute;
        top: 8px;
        right: 10px;
        font-weight: 900;
        font-size: 0.85rem;
        color: #2ecc71;
        z-index: 5;
        background: rgba(0, 0, 0, 0.6);
        padding: 3px 8px;
        border-radius: 4px;
        border: 1px solid rgba(46, 204, 113, 0.3);
        text-shadow: 0 1px 2px rgba(0,0,0,0.8);
    }

    .field-row {
        display: flex;
        justify-content: center;
        gap: 6px;
        z-index: 2;
        margin: 4px 0;
        width: 100%;
    }
    .player-card {
        background: rgba(0, 0, 0, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 6px;
        padding: 4px 5px;
        text-align: center;
        max-width: 78px;
        min-width: 54px;
        box-sizing: border-box;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .player-name {
        font-size: 0.62rem;
        color: #ffffff;
        font-weight: 700;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .player-pts {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background-color: #2ecc71;
        color: #151e19;
        font-size: 0.68rem;
        font-weight: 900;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 3px auto 0 auto;
        box-shadow: 0 1px 3px rgba(0,0,0,0.4);
    }
    .player-pts-zero {
        background-color: #3b524b !important;
        color: #b0c4de !important;
    }
    .player-pts-captain {
        background-color: #f1c40f !important;
        color: #151e19 !important;
    }
    .player-pts-captain-zero {
        border: 2px solid #f1c40f !important;
        box-sizing: border-box;
    }

    @media (max-width: 768px) {
        .fields-flex-container {
            flex-direction: column !important;
            gap: 16px !important;
        }
        .soccer-field {
            min-height: 320px !important;
            padding: 34px 4px 8px 4px !important;
        }
        .player-card {
            min-width: 46px !important;
            max-width: 68px !important;
            padding: 3px 3px !important;
        }
        .player-name {
            font-size: 0.55rem !important;
        }
        .player-pts {
            width: 22px;
            height: 22px;
            font-size: 0.6rem;
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
        <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 8px;'>
            <img src='data:image/png;base64,{img_comp_b64}' width='220' alt='Logo SuperMandingo' />
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---------------------------------------------------------
# 7. AUTENTICACIÓN Y CARGA DE DATOS DE FUTMONDO
# ---------------------------------------------------------
email = st.secrets.get("FUTMONDO_USER") or st.secrets.get("futmondo", {}).get("email") or "scorderorando@gmail.com"
password = st.secrets.get("FUTMONDO_PASS") or st.secrets.get("futmondo", {}).get("password")
championship_id = st.secrets.get("FUTMONDO_CHAMPIONSHIP_ID") or st.secrets.get("futmondo", {}).get("championship_id") or "5b56e918529e47fd32faea09"

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
            if running_rounds: jornada_actual = running_rounds[0]
            elif closed_rounds: jornada_actual = min(FIN_SM, max(closed_rounds) + 1)

round_statuses = {r.get("number"): r.get("status") for r in rounds_info} if rounds_info else {}

# ---------------------------------------------------------
# 8. GESTIÓN DE ESTADO PARA LA JORNADA SELECCIONADA
# ---------------------------------------------------------
jornada_key_state = "jornada_supermandingo"
if jornada_key_state not in st.session_state:
    st.session_state[jornada_key_state] = max(INICIO_SM, min(jornada_actual, FIN_SM))

jornada_seleccionada = st.session_state[jornada_key_state]

# ---------------------------------------------------------
# 9. VISTA PRINCIPAL EN COLUMNAS (LADO A LADO)
# ---------------------------------------------------------
col_tabla, col_partidos = st.columns([1.35, 1], gap="medium")

# --- COLUMNA IZQUIERDA: CLASIFICACIÓN ---
with col_tabla:
    st.markdown(
        """
        <div style='margin-bottom: 5px;'>
            <h3 style='color: #ffffff; margin: 0; font-family: "Montserrat", sans-serif; letter-spacing: 1.5px; font-size: 1.2rem; font-weight: 800;'>📊 CLASIFICACIÓN</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if equipos and rounds_info and token and userid:
        datos_clasificacion, jornadas_jugadas_count = calcular_clasificacion_real(
            equipos, rounds_info, token, userid, championship_id, userteam_id
        )
        html_tabla = render_tabla_clasificacion(datos_clasificacion, max(1, jornadas_jugadas_count))
        st.markdown(html_tabla, unsafe_allow_html=True)
    else:
        st.warning("Cargando datos reales de la API de Futmondo...")

# --- COLUMNA DERECHA: ENFRENTAMIENTOS Y JORNADAS ---
with col_partidos:
    st.markdown(
        """
        <div style='margin-bottom: 10px;'>
            <h3 style='color: #ffffff; margin: 0; font-family: "Montserrat", sans-serif; letter-spacing: 1.5px; font-size: 1.2rem; font-weight: 800;'>⚽ ENFRENTAMIENTOS</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    def format_func_jornada(x):
        base_str = f"JORNADA {x} — J{MAPEO_LIGA_REAL.get(x, x)} de Liga"
        if round_statuses.get(x) == "running":
            return f"{base_str} 🔴 EN JUEGO"
        return base_str

    jornada_elegida = st.selectbox(
        "Selecciona la Jornada",
        options=list(range(INICIO_SM, FIN_SM + 1)),
        index=st.session_state[jornada_key_state] - INICIO_SM,
        format_func=format_func_jornada,
        key="combo_jornada_selector",
        label_visibility="collapsed"
    )

    if jornada_elegida != st.session_state[jornada_key_state]:
        st.session_state[jornada_key_state] = jornada_elegida
        st.rerun()

    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    partidos_jornada = CALENDARIO_JORNADAS.get(jornada_elegida, [])

    if partidos_jornada:
        round_obj = next((r for r in rounds_info if r.get("number") == jornada_elegida), None)
        is_closed = round_obj and round_obj.get("status") == "closed"
        is_running = round_obj and round_obj.get("status") == "running"
        round_id = round_obj.get("id") if round_obj else None

        puntos_jornada_sel = {}
        ranking_data = []
        if round_id and token and userid:
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

        def get_img_src(escudo_val):
            if not escudo_val: return ""
            if str(escudo_val).startswith("http"): return escudo_val
            b64 = get_image_base64(escudo_val)
            return f"data:image/png;base64,{b64}" if b64 else ""

        for idx, (nombre1_cal, nombre2_cal) in enumerate(partidos_jornada):
            nombre1 = normalizar_nombre_equipo(nombre1_cal)
            nombre2 = normalizar_nombre_equipo(nombre2_cal)

            abrev1 = ABREVIATURAS.get(nombre1_cal, ABREVIATURAS.get(nombre1, nombre1[:3].upper()))
            abrev2 = ABREVIATURAS.get(nombre2_cal, ABREVIATURAS.get(nombre2, nombre2[:3].upper()))

            eq1_info = buscar_equipo_info(nombre1_cal, equipos)
            eq2_info = buscar_equipo_info(nombre2_cal, equipos)

            escudo1 = obtener_ruta_escudo(eq1_info.get("id"), eq1_info.get("escudo_url"))
            escudo2 = obtener_ruta_escudo(eq2_info.get("id"), eq2_info.get("escudo_url"))

            if is_closed or is_running:
                pts1 = puntos_jornada_sel.get(nombre1, 0)
                pts2 = puntos_jornada_sel.get(nombre2, 0)
                
                aplicar_diferencia = is_closed
                gf1, gf2 = calcular_goles_partido(pts1, pts2, aplicar_regla_diferencia=aplicar_diferencia)
                
                centro_texto = f'<div class="score-box">{gf1} - {gf2}</div>'
            else:
                centro_texto = f'<div class="score-box" style="padding: 0 24px; font-size: 1.5rem;">VS</div>'

            match_key = f"match_open_{jornada_elegida}_{idx}"
            if match_key not in st.session_state:
                st.session_state[match_key] = False

            src1 = get_img_src(escudo1)
            src2 = get_img_src(escudo2)
            
            img1_tag = f"<img src='{src1}' width='60' height='60' style='object-fit:contain;'/>" if src1 else "⚽"
            img2_tag = f"<img src='{src2}' width='60' height='60' style='object-fit:contain;'/>" if src2 else "⚽"

            # Tarjeta principal del partido
            st.markdown(
                f"""
                <div class="match-container">
                    <div class="match-team">
                        {img1_tag}
                        <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{abrev1}</span>
                    </div>
                    <div class="match-center">
                        {centro_texto}
                    </div>
                    <div class="match-team right">
                        <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{abrev2}</span>
                        {img2_tag}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if is_closed or is_running:
                btn_label = "▲" if st.session_state[match_key] else "▼"
                
                _, col_btn_centro, _ = st.columns([3.5, 3.0, 3.5])
                with col_btn_centro:
                    if st.button(btn_label, key=f"btn_{match_key}", use_container_width=True):
                        st.session_state[match_key] = not st.session_state[match_key]
                        st.rerun()

            if (is_closed or is_running) and st.session_state[match_key]:
                eq1_team_id = eq1_info.get("id") if eq1_info else None
                eq2_team_id = eq2_info.get("id") if eq2_info else None

                def procesar_alineacion_por_strategy(lineup_answer):
                    strategy_str = lineup_answer.get("strategy") or "1-4-3-3"
                    match_nums = re.findall(r'\d+', str(strategy_str))
                    
                    if len(match_nums) >= 4 and match_nums[0] == '1':
                        lineas_def_med_del = [int(x) for x in match_nums[1:]]
                    elif len(match_nums) == 3:
                        lineas_def_med_del = [int(x) for x in match_nums]
                    else:
                        lineas_def_med_del = [4, 3, 3]

                    def_count = lineas_def_med_del[0] if len(lineas_def_med_del) > 0 else 4
                    med_count = lineas_def_med_del[1] if len(lineas_def_med_del) > 1 else 3
                    del_count = lineas_def_med_del[2] if len(lineas_def_med_del) > 2 else 3

                    raw_players = lineup_answer.get("players", [])
                    
                    sorted_players = sorted(
                        raw_players, 
                        key=lambda x: x.get("position", 99) if isinstance(x.get("position", 99), int) else 99
                    )

                    por = []
                    todos_campo = []
                    
                    for p in sorted_players:
                        raw_name = p.get("name") or p.get("playerName") or "Jugador"
                        nombre = formatear_nombre_futmondo(raw_name)
                        
                        pts = p.get("customPoints") if p.get("customPoints") is not None else p.get("points", 0)
                        es_capitan = bool(p.get("cpt") or p.get("captain") or p.get("isCaptain") or p.get("is_captain"))
                        pos_val = p.get("position")
                        
                        j_obj = {"nombre": nombre, "puntos": pts, "capitan": es_capitan, "position": pos_val}
                        
                        if pos_val == 10 or pos_val == "10":
                            por.append(j_obj)
                        else:
                            todos_campo.append(j_obj)

                    delanteros = todos_campo[:del_count]
                    centrocampistas = todos_campo[del_count : del_count + med_count]
                    defensas = todos_campo[del_count + med_count:]
                    
                    if len(todos_campo) > (del_count + med_count + def_count):
                        defensas.extend(todos_campo[del_count + med_count + def_count:])

                    delanteros = sorted(delanteros, key=lambda x: x.get("position", 99))
                    centrocampistas = sorted(centrocampistas, key=lambda x: x.get("position", 99))
                    defensas = sorted(defensas, key=lambda x: x.get("position", 99))

                    filas_campo = [defensas, centrocampistas, delanteros]

                    return por, filas_campo

                if token and userid and round_id:
                    # Creamos un contenedor vacío para mostrar un spinner personalizado sin rastro de Streamlit
                    load_placeholder = st.empty()
                    load_placeholder.markdown("""
                        <div style="display: flex; align-items: center; justify-content: center; gap: 10px; padding: 15px; color: #2ecc71; font-weight: 700; font-family: 'Montserrat', sans-serif;">
                            <div style="width: 18px; height: 18px; border: 3px solid #2ecc71; border-top-color: transparent; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                            Cargando alineaciones...
                        </div>
                        <style>
                        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                        </style>
                    """, unsafe_allow_html=True)

                    l1_ans = obtener_round_lineup(token, userid, championship_id, round_id, eq1_team_id) if eq1_team_id else {}
                    l2_ans = obtener_round_lineup(token, userid, championship_id, round_id, eq2_team_id) if eq2_team_id else {}
                    
                    # Limpiamos el mensaje de carga una vez finalizado
                    load_placeholder.empty()

                    por1, filas1 = procesar_alineacion_por_strategy(l1_ans)
                    por2, filas2 = procesar_alineacion_por_strategy(l2_ans)
                else:
                    por1, filas1 = [], []
                    por2, filas2 = [], []

                def construir_fila_html(jugadores):
                    if not jugadores:
                        return ""
                    html = '<div class="field-row">'
                    for j in jugadores:
                        nombre_mostrar = j['nombre']
                        pts = j.get('puntos', 0)
                        es_capitan = j.get('capitan', False)
                        
                        if es_capitan:
                            if pts > 0:
                                pts_class = " player-pts-captain"
                            else:
                                pts_class = " player-pts-zero player-pts-captain-zero"
                        else:
                            pts_class = " player-pts-zero" if pts == 0 else ""

                        html += f'<div class="player-card"><div class="player-name">{nombre_mostrar}</div><div class="player-pts{pts_class}">{pts}</div></div>'
                    html += '</div>'
                    return html

                def construir_campo_tactico(nombre_eq, escudo_url, por, filas_campo):
                    src_esc = get_img_src(escudo_url)
                    header_img = f"<img src='{src_esc}' width='18' height='18' style='object-fit:contain; vertical-align:middle;'/>" if src_esc else "⚽ "
                    
                    todos_jugadores = por + [j for fila in filas_campo for j in fila]
                    total_pts = sum(j.get('puntos', 0) for j in todos_jugadores)

                    filas_html_str = ""
                    for fila in reversed(filas_campo):
                        filas_html_str += construir_fila_html(fila)
                    
                    filas_html_str += construir_fila_html(por)

                    return (
                        f'<div style="flex: 1; min-width: 0;">'
                        f'<div class="soccer-field">'
                        f'<div class="field-header-top-left">'
                        f'{header_img}<span style="color: #ffffff; font-weight: 800; font-size: 0.8rem; text-shadow: 0 1px 2px rgba(0,0,0,0.8);">{nombre_eq.upper()}</span>'
                        f'</div>'
                        f'<div class="field-header-top-right">'
                        f'{total_pts} pts'
                        f'</div>'
                        f'<div class="field-line-center"></div>'
                        f'{filas_html_str}'
                        f'</div>'
                        f'</div>'
                    )

                campo1_html = construir_campo_tactico(nombre1, escudo1, por1, filas1)
                campo2_html = construir_campo_tactico(nombre2, escudo2, por2, filas2)

                tarjeta_unificada_html = (
                    f'<div class="lineup-unified-card">'
                    f'<div class="fields-flex-container">'
                    f'{campo1_html}'
                    f'{campo2_html}'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(tarjeta_unificada_html, unsafe_allow_html=True)

        if equipo_descansa:
            abrev_desc = ABREVIATURAS.get(equipo_descansa, equipo_descansa[:3].upper())
            eq_desc_info = buscar_equipo_info(equipo_descansa, equipos)
            escudo_desc = obtener_ruta_escudo(eq_desc_info.get("id"), eq_desc_info.get("escudo_url"))
            src_desc = get_img_src(escudo_desc)
            img_desc_tag = f'<img src="{src_desc}" width="26" style="object-fit: contain; vertical-align: middle; margin-left: 6px;"/>' if src_desc else '⚽'

            html_descanso = (
                f"<div style='background: #23322e; border: 1px dashed #8aa4ae; border-radius: 8px; padding: 0px 8px; margin-top: 8px; display: flex; align-items: center; justify-content: center; color: #ffffff; font-size: 0.8rem; height: 46px; box-sizing: border-box; width: 100%;'>"
                f"<span style=\"color: #8aa4ae; font-weight: bold; margin-right: 4px;\">DESCANSA:</span>"
                f"<span style=\"font-weight: bold; color: #ffffff;\">{equipo_descansa.upper()}</span>"
                f"{img_desc_tag}"
                f"</div>"
            )
            st.markdown(html_descanso, unsafe_allow_html=True)
    else:
        st.warning("No hay enfrentamientos programados para esta jornada.")
