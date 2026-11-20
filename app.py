import asyncio
import hashlib
import json
import math
import random
import re
import shutil
import struct
import urllib.request
import uuid
import wave
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

try:
    import edge_tts
    HAS_EDGE_TTS = True
except Exception:
    HAS_EDGE_TTS = False

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except Exception:
    HAS_PIL = False

try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except Exception:
    HAS_PYDUB = False

st.set_page_config(
    page_title="BASA Universal AI Studio v13 - Emisora 24/7 + YouTube + 5K",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# ESTILOS UI BASA (PALETA SUAVE GRIS/AZUL CIELO + ALTO CONTRASTE NEGRO)
# ============================================================================
st.markdown(
    """
    <style>
        .stApp {
            background-color: #f3f6f9;
            color: #0f172a;
        }
        [data-testid="stSidebar"] {
            background-color: #e6eef6;
            border-right: 1px solid #cbd5e1;
        }
        [data-testid="stSidebar"] * {
            color: #0f172a !important;
        }
        h1, h2, h3, h4, p, label, span {
            color: #0f172a;
        }
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-left: 5px solid #0284c7;
            padding: 12px 16px;
            border-radius: 10px;
        }
        .stButton > button[kind="primary"] {
            background-color: #0284c7;
            color: #ffffff !important;
            border: none;
            font-weight: 700;
            border-radius: 8px;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #0369a1;
        }
        .on-air-badge {
            background-color: #0284c7;
            color: #ffffff !important;
            padding: 6px 14px;
            border-radius: 999px;
            font-weight: 800;
            font-size: 0.85rem;
            display: inline-block;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# RUTAS Y CONSTANTES OFICIALES BASA
# ============================================================================
VAULT_DIR = Path("basa_vault_data")
MEDIA_DIR = VAULT_DIR / "media"
BACKUP_DIR = VAULT_DIR / "backups"
AUTO_EXPORT_DIR = VAULT_DIR / "auto_exports"
INDEX_FILE = VAULT_DIR / "vault_index.json"
RELEASES_FILE = VAULT_DIR / "releases_log.json"
UI_STATE_FILE = VAULT_DIR / "ui_autosave_state.json"
LIBRARY_FILE = VAULT_DIR / "biblioteca_libre_basa.json"
HISTORY_FILE = VAULT_DIR / "historico_usuarios.json"
LEGAL_FILE = VAULT_DIR / "consentimiento_legal.json"
CUSTOM_INST_FILE = VAULT_DIR / "instrumentos_personalizados.json"
RADAR_FEED_FILE = VAULT_DIR / "radar_mundial_live.json"
MODULES_FILE = VAULT_DIR / "modulos_autonomos.json"
SALES_CATALOG_FILE = VAULT_DIR / "catalogo_ventas_basa.json"
RADIO_PLAYLIST_FILE = VAULT_DIR / "emisora_basa_playlist.json"
HTML_STUDIO_PATH = Path("studio_audio.html")

ADMIN_MASTER_PIN = "BASA-ADMIN-2026"
DEVELOPER_NAME = "Pedro Anibal Baldera Rondon - BASA Productions"
OFFICIAL_YOUTUBE_CHANNEL = "https://www.youtube.com/@Lic.PedroBaldera"
OFFICIAL_YOUTUBE_HANDLE = "@Lic.PedroBaldera"
OFFICIAL_RADIO_NAME = "BASA Radio & TV Mundial 24/7"

# ============================================================================
# CATALOGO MUNDIAL: INSTRUMENTOS FISICOS + ELECTRONICOS + GENEROS
# ============================================================================
INSTRUMENT_FAMILIES: dict[str, list[str]] = {
    "Caribe y Latinoamerica (Fisicos)": [
        "Guira Metalica Dominicana",
        "Tambora Dominicana",
        "Acordeon Diatonico (Perico Ripiao)",
        "Requinto Bachatero",
        "Segunda Guitarra Bachatera",
        "Congas / Tumbadoras",
        "Bongo y Campana",
        "Timbales Latinos",
        "Maracas y Clave",
        "Cuatro Puertorriqueno / Venezolano",
        "Charango y Zampona Andina",
        "Marimba Tropical",
        "Caja Vallenata",
        "Cajon Peruano / Flamenco",
    ],
    "Metales, Vientos y Cuerdas (Fisicos)": [
        "Trombones y Mambo Brass",
        "Trompetas Mariachi / Salsa",
        "Saxofon Alto / Tenor",
        "Flauta Traversa",
        "Clarinete",
        "Violines Sinfonicos",
        "Violonchelo",
        "Contrabajo Acustico",
        "Guitarra Acustica / Clasica",
        "Guitarra Electrica Limpia",
        "Guitarra Electrica Rock / Overdrive",
        "Bajo Electrico Slap / Finger",
        "Arpa Clasica / Llanera",
    ],
    "Teclados y Percusion Global (Fisicos)": [
        "Piano Acustico de Cola",
        "Piano Montuno Salsero",
        "Organo Hammond B3",
        "Bateria Acustica Pop / Rock",
        "Djembe y Percusion Africana",
        "Tabla Hindu y Sitar",
        "Oud y Darbuka Oriental",
        "Koto y Taiko Japones",
    ],
    "Musica Electronica y Sintesis Moderna": [
        "Sub-Bajo 808 Profundo",
        "Kick Electronico Club / EDM",
        "Snare Dembow / Trap",
        "Hi-Hats Rolls 1/32",
        "Lead Sintetizador Supersaw",
        "Pad Atmosferico Etereo",
        "Pluck Tropical House",
        "Arpegiador Analogico Moog",
        "Bajo Acid TB-303",
        "Piano Electrico Rhodes / FM",
        "Orquesta Hibrida Cinematografica",
        "Vocoder / Talkbox FX",
    ],
}

ALL_WORLD_INSTRUMENTS: list[str] = [
    inst for group in INSTRUMENT_FAMILIES.values() for inst in group
]

REGION_GENRE_DEFAULTS: dict[str, list[str]] = {
    "Republica Dominicana (Caribe)": ["Bachata Dominicana", "Merengue de Calle / Mambo", "Merengue Tipico (Perico Ripiao)"],
    "Mexico": ["Ranchera / Mariachi", "Musica Mexicana / Banda", "Corridos Tumbados / Urbano"],
    "Puerto Rico / Urbano Latino": ["Reggaeton", "Salsa Clasica", "Dembow / Urbano"],
    "Estados Unidos / Internacional": ["Pop / Rock Americano", "R&B / Soul Americano", "EDM / House / Techno"],
    "Colombia / Sudamerica": ["Salsa Clasica", "Cumbia / Vallenato", "Afrobeat / Amapiano"],
    "Global / Fusion Mundial": ["Fusion Mundial: Fisico + Electronico", "Score Cinematografico / Orquestal", "Jazz / Funk Fusion"],
}

ALL_WORLD_GENRES: list[str] = [
    "Bachata Dominicana",
    "Merengue de Calle / Mambo",
    "Merengue Tipico (Perico Ripiao)",
    "Salsa Clasica",
    "Bolero",
    "Reggaeton",
    "Dembow / Urbano",
    "Balada",
    "Ranchera / Mariachi",
    "Musica Mexicana / Banda",
    "Corridos Tumbados / Urbano",
    "Cumbia / Vallenato",
    "Pop / Rock Americano",
    "R&B / Soul Americano",
    "EDM / House / Techno",
    "Trap / Hip-Hop",
    "Afrobeat / Amapiano",
    "Jazz / Funk Fusion",
    "Reggae / Dancehall",
    "Flamenco / Rumba",
    "Bossa Nova / Samba",
    "Gospel / Alabanza Contemporanea",
    "Score Cinematografico / Orquestal",
    "Fusion Mundial: Fisico + Electronico",
    "Fusion: Bachata + EDM / Tropical House",
    "Fusion: Merengue Tipico + 808 Urbano",
    "Fusion: Salsa + Dembow + Metales",
    "Fusion: Orquesta Sinfonica + Trap",
]

GENRE_INSTRUMENT_MATRIX: dict[str, list[str]] = {
    "Bachata Dominicana": [
        "Requinto Bachatero", "Segunda Guitarra Bachatera", "Bongo y Campana",
        "Guira Metalica Dominicana", "Bajo Electrico Slap / Finger"
    ],
    "Merengue de Calle / Mambo": [
        "Tambora Dominicana", "Guira Metalica Dominicana", "Trombones y Mambo Brass",
        "Sub-Bajo 808 Profundo", "Lead Sintetizador Supersaw"
    ],
    "Merengue Tipico (Perico Ripiao)": [
        "Acordeon Diatonico (Perico Ripiao)", "Tambora Dominicana", "Guira Metalica Dominicana",
        "Saxofon Alto / Tenor", "Bajo Electrico Slap / Finger"
    ],
    "Salsa Clasica": [
        "Piano Montuno Salsero", "Congas / Tumbadoras", "Timbales Latinos",
        "Trombones y Mambo Brass", "Trompetas Mariachi / Salsa", "Contrabajo Acustico"
    ],
    "Dembow / Urbano": [
        "Sub-Bajo 808 Profundo", "Snare Dembow / Trap", "Guira Metalica Dominicana",
        "Pluck Tropical House", "Hi-Hats Rolls 1/32"
    ],
    "Reggaeton": [
        "Sub-Bajo 808 Profundo", "Kick Electronico Club / EDM", "Snare Dembow / Trap",
        "Pluck Tropical House", "Pad Atmosferico Etereo"
    ],
    "Ranchera / Mariachi": [
        "Trompetas Mariachi / Salsa", "Violines Sinfonicos", "Guitarra Acustica / Clasica",
        "Contrabajo Acustico"
    ],
    "Corridos Tumbados / Urbano": [
        "Requinto Bachatero", "Trombones y Mambo Brass", "Sub-Bajo 808 Profundo",
        "Bajo Electrico Slap / Finger"
    ],
    "Cumbia / Vallenato": [
        "Acordeon Diatonico (Perico Ripiao)", "Caja Vallenata", "Guira Metalica Dominicana",
        "Congas / Tumbadoras", "Bajo Electrico Slap / Finger"
    ],
    "EDM / House / Techno": [
        "Kick Electronico Club / EDM", "Sub-Bajo 808 Profundo", "Lead Sintetizador Supersaw",
        "Arpegiador Analogico Moog", "Hi-Hats Rolls 1/32", "Pad Atmosferico Etereo"
    ],
    "Pop / Rock Americano": [
        "Bateria Acustica Pop / Rock", "Guitarra Electrica Rock / Overdrive",
        "Bajo Electrico Slap / Finger", "Piano Acustico de Cola", "Pad Atmosferico Etereo"
    ],
    "Afrobeat / Amapiano": [
        "Djembe y Percusion Africana", "Sub-Bajo 808 Profundo", "Piano Electrico Rhodes / FM",
        "Marimba Tropical", "Saxofon Alto / Tenor"
    ],
    "Score Cinematografico / Orquestal": [
        "Orquesta Hibrida Cinematografica", "Violines Sinfonicos", "Violonchelo",
        "Trombones y Mambo Brass", "Arpa Clasica / Llanera", "Koto y Taiko Japones"
    ],
    "Fusion Mundial: Fisico + Electronico": [
        "Acordeon Diatonico (Perico Ripiao)", "Guira Metalica Dominicana", "Sub-Bajo 808 Profundo",
        "Violines Sinfonicos", "Lead Sintetizador Supersaw", "Tabla Hindu y Sitar"
    ],
}

KEY_ROOT_FREQS: dict[str, float] = {
    "Am (La Menor)": 220.00,
    "Em (Mi Menor)": 164.81,
    "Dm (Re Menor)": 293.66,
    "Fm (Fa Menor)": 174.61,
    "C (Do Mayor)": 261.63,
    "G (Sol Mayor)": 196.00,
    "F (Fa Mayor)": 174.61,
}

VOICE_PROFILES: dict[str, dict[str, Any]] = {
    "Voz Masculina": {"voice": "es-DO-EmilioNeural", "rate": "+0%", "pitch": "+0Hz", "mode": "solo", "genero": "masc"},
    "Voz Femenina": {"voice": "es-DO-RamonaNeural", "rate": "+0%", "pitch": "+0Hz", "mode": "solo", "genero": "fem"},
    "Voz Juvenil Masculina": {"voice": "es-MX-JorgeNeural", "rate": "+8%", "pitch": "+18Hz", "mode": "solo", "genero": "masc"},
    "Voz Juvenil Femenina": {"voice": "es-MX-DaliaNeural", "rate": "+8%", "pitch": "+22Hz", "mode": "solo", "genero": "fem"},
    "Voz Infantil (Nino/Nina)": {"voice": "es-MX-DaliaNeural", "rate": "+5%", "pitch": "+55Hz", "mode": "solo", "genero": "fem"},
    "Coro Grupal": {"voice": "es-DO-RamonaNeural", "rate": "+2%", "pitch": "+0Hz", "mode": "choir", "genero": "mixto"},
    "Solo Instrumental": {"voice": "", "rate": "+0%", "pitch": "+0Hz", "mode": "instrumental", "genero": "none"},
}

CINEMA_STYLES: dict[str, tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]] = {
    "Cine Epico / Hollywood Dorado": ((14, 18, 34), (245, 208, 97), (225, 232, 245)),
    "Accion / Cyberpunk Neon": ((10, 12, 24), (0, 240, 255), (235, 245, 255)),
    "Animacion 3D / Familiar": ((22, 34, 68), (255, 185, 65), (255, 255, 255)),
    "Documental / Historia Real": ((24, 22, 20), (218, 175, 110), (238, 234, 228)),
    "Drama / Suspenso Nocturno": ((8, 10, 14), (220, 65, 65), (215, 220, 225)),
}

LEGAL_TEXT = """CONTRATO LEGAL BASA - CESION DE DERECHOS - LEER ANTES DE MARCAR

Yo, el usuario que crea en BASA Universal AI Studio, DECLARO que entiendo y acepto:

1. Toda cancion, letra, audio, portada, video, serie o pelicula creada en BASA pasa legalmente a formar parte de BASA Productions, propiedad de Pedro Anibal Baldera Rondon, SIN RESTRICCION, para uso, distribucion, venta, licencia y publicacion mundial.
2. Yo cedo todos los derechos de autor, patrimoniales y de explotacion al desarrollador, de forma irrevocable.
3. Si deseo que la obra sea de mi propiedad exclusiva, debo PAGAR LA RESERVA / REGISTRO al desarrollador antes de publicarla. Sin pago de reserva, la obra es de BASA.
4. Este consentimiento se marca UNA SOLA VEZ y queda valido PARA SIEMPRE, desde este dispositivo o cualquier otro que yo utilice, vinculado a mi usuario.
5. Si NO marco este cotejo, NO puedo registrar ni publicar en BASA.
6. Este contrato se guarda con fecha, hora, usuario, dispositivo y hash legal como prueba.

Al marcar el cotejo, usted firma digitalmente este contrato.
"""

# ============================================================================
# UTILIDADES JSON Y BOVEDA
# ============================================================================
def init_dirs() -> None:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    AUTO_EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path: Path, data: Any) -> None:
    init_dirs()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ============================================================================
# RADAR AUTONOMO GLOBAL CADA 10 SEGUNDOS (CINE, MUSICA, SERIES, NOTICIAS)
# ============================================================================
BASE_GLOBAL_KNOWLEDGE: list[dict[str, str]] = [
    {
        "categoria": "Musica Mundial & Caribe",
        "ambito": "Local RD / Global",
        "titular": "Fusion Merengue Tipico + Sub-Bajo 808 y Bachata Sintetica lidera tendencias de streaming",
        "genero_sugerido": "Fusion: Merengue Tipico + 808 Urbano",
        "prompt_sugerido": "Acordeon diatonico con guira metalica dominicana, tambora y sub-bajo 808 profundo",
    },
    {
        "categoria": "Cine & Peliculas 5K",
        "ambito": "Internacional / Hollywood",
        "titular": "Narrativas epicas de superacion personal con bandas sonoras hibridas orquestales + sintetizadores",
        "genero_sugerido": "Score Cinematografico / Orquestal",
        "prompt_sugerido": "Orquesta hibrida cinematografica con violines sinfonicos, trombones y taiko",
    },
    {
        "categoria": "Series & Drama",
        "ambito": "Latinoamerica / Global",
        "titular": "Series dramaticas basadas en historias reales de barrio, emprendimiento y justicia",
        "genero_sugerido": "Bolero",
        "prompt_sugerido": "Guitarra acustica clasica, violonchelo y piano atmosferico nocturno",
    },
    {
        "categoria": "Noticias & Cultura Local RD",
        "ambito": "Santo Domingo / Cibao",
        "titular": "Auge de producciones audiovisuales independientes y musica con identidad dominicana",
        "genero_sugerido": "Merengue de Calle / Mambo",
        "prompt_sugerido": "Merengue de calle alegre con trombones, mambo brass, tambora y guira",
    },
    {
        "categoria": "Tendencia Electronica & Afrobeat",
        "ambito": "Mundial",
        "titular": "Cruce de Afrobeat / Amapiano con percusion latina y leads Supersaw en clubes",
        "genero_sugerido": "Afrobeat / Amapiano",
        "prompt_sugerido": "Djembe africano, marimba tropical, saxofon tenor y sub-bajo 808",
    },
]


def actualizar_radar_mundial_autonomo() -> dict[str, Any]:
    prev = _load_json(RADAR_FEED_FILE, {})
    ciclo = int(prev.get("ciclo", 0)) + 1 if isinstance(prev, dict) else 1

    noticias_red: list[dict[str, str]] = []
    rss_urls = [
        ("Noticias Internacionales & Cultura", "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=es-419&gl=US&ceid=US:es-419"),
        ("Noticias Locales RD", "https://news.google.com/rss?hl=es-419&gl=DO&ceid=DO:es-419"),
    ]
    for ambito_rss, url in rss_urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BASA-Studio-Bot/13.0"})
            with urllib.request.urlopen(req, timeout=2.2) as resp:
                xml_data = resp.read()
            root = ET.fromstring(xml_data)
            for item in root.findall(".//item")[:3]:
                title_el = item.find("title")
                if title_el is not None and title_el.text:
                    noticias_red.append(
                        {
                            "categoria": "Pulso Red en Vivo",
                            "ambito": ambito_rss,
                            "titular": title_el.text.strip(),
                            "genero_sugerido": "Fusion Mundial: Fisico + Electronico",
                            "prompt_sugerido": f"Inspirado en actualidad: {title_el.text.strip()[:90]}",
                        }
                    )
        except Exception:
            pass

    rotados = BASE_GLOBAL_KNOWLEDGE[ciclo % len(BASE_GLOBAL_KNOWLEDGE):] + BASE_GLOBAL_KNOWLEDGE[:ciclo % len(BASE_GLOBAL_KNOWLEDGE)]
    items_activos = (noticias_red + rotados)[:6]

    estado_radar = {
        "ciclo": ciclo,
        "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fuente_red_activa": len(noticias_red) > 0,
        "total_items": len(items_activos),
        "items": items_activos,
    }
    _save_json(RADAR_FEED_FILE, estado_radar)
    return estado_radar


# ============================================================================
# IA DE COMBINACION INSTRUMENTAL MUNDIAL (FISICO + ELECTRONICO)
# ============================================================================
def cargar_instrumentos_usuario() -> list[str]:
    custom = _load_json(CUSTOM_INST_FILE, [])
    if not isinstance(custom, list):
        custom = []
    return list(dict.fromkeys(ALL_WORLD_INSTRUMENTS + [str(x).strip() for x in custom if str(x).strip()]))


def guardar_instrumento_personalizado(nombre_inst: str, familia: str = "Personalizado") -> list[str]:
    nombre_limpio = nombre_inst.strip()
    if not nombre_limpio:
        return cargar_instrumentos_usuario()
    etiqueta = f"{nombre_limpio} ({familia})" if familia and familia not in nombre_limpio else nombre_limpio
    custom = _load_json(CUSTOM_INST_FILE, [])
    if not isinstance(custom, list):
        custom = []
    if etiqueta not in custom and etiqueta not in ALL_WORLD_INSTRUMENTS:
        custom.append(etiqueta)
        _save_json(CUSTOM_INST_FILE, custom)
    return cargar_instrumentos_usuario()


def ia_combinar_instrumentacion(
    generos: list[str],
    instrumentos_manuales: list[str],
    modo_fusion_mundial: bool = True,
    prompt_extra: str = "",
) -> tuple[list[str], str]:
    resultado: list[str] = list(instrumentos_manuales)
    texto_busqueda = (" ".join(generos) + " " + prompt_extra).lower()

    for g in generos:
        if g in GENRE_INSTRUMENT_MATRIX:
            resultado.extend(GENRE_INSTRUMENT_MATRIX[g])
        else:
            for k, v in GENRE_INSTRUMENT_MATRIX.items():
                if any(tok in k.lower() for tok in g.lower().split() if len(tok) > 3):
                    resultado.extend(v[:3])

    mapa_keywords = {
        "acordeon": "Acordeon Diatonico (Perico Ripiao)",
        "guira": "Guira Metalica Dominicana",
        "tambora": "Tambora Dominicana",
        "requinto": "Requinto Bachatero",
        "trombon": "Trombones y Mambo Brass",
        "trompeta": "Trompetas Mariachi / Salsa",
        "sax": "Saxofon Alto / Tenor",
        "violin": "Violines Sinfonicos",
        "orquesta": "Orquesta Hibrida Cinematografica",
        "piano": "Piano Acustico de Cola",
        "808": "Sub-Bajo 808 Profundo",
        "electronica": "Lead Sintetizador Supersaw",
        "edm": "Kick Electronico Club / EDM",
        "sitar": "Tabla Hindu y Sitar",
        "arpa": "Arpa Clasica / Llanera",
        "guitarra": "Guitarra Electrica Rock / Overdrive",
    }
    for kw, inst in mapa_keywords.items():
        if kw in texto_busqueda:
            resultado.append(inst)

    if modo_fusion_mundial:
        fisicos_presentes = [
            i for i in resultado
            if i in INSTRUMENT_FAMILIES["Caribe y Latinoamerica (Fisicos)"]
            or i in INSTRUMENT_FAMILIES["Metales, Vientos y Cuerdas (Fisicos)"]
            or i in INSTRUMENT_FAMILIES["Teclados y Percusion Global (Fisicos)"]
        ]
        electronicos_presentes = [
            i for i in resultado
            if i in INSTRUMENT_FAMILIES["Musica Electronica y Sintesis Moderna"]
        ]
        if not fisicos_presentes:
            resultado.extend(["Guira Metalica Dominicana", "Acordeon Diatonico (Perico Ripiao)", "Violines Sinfonicos"])
        if not electronicos_presentes:
            resultado.extend(["Sub-Bajo 808 Profundo", "Lead Sintetizador Supersaw", "Pad Atmosferico Etereo"])

    unicos = list(dict.fromkeys(resultado))
    if not unicos:
        unicos = GENRE_INSTRUMENT_MATRIX["Fusion Mundial: Fisico + Electronico"]

    explicacion = (
        f"Orquestacion Hibrida Mundial ({len(unicos)} instrumentos): "
        + ", ".join(unicos[:8])
        + ("..." if len(unicos) > 8 else "")
    )
    return unicos, explicacion


# ============================================================================
# MOTOR DE SINTESIS MUSICAL DSP MULTI-TIMBRE (FISICO + ELECTRONICO WAV 16-BIT)
# ============================================================================
def generar_pista_instrumental_wav(
    out_path: Path,
    genero: str = "Merengue de Calle / Mambo",
    bpm: int = 135,
    tonalidad: str = "Em (Mi Menor)",
    duracion_seg: int = 24,
    instrumentos: list[str] | None = None,
) -> Path:
    sample_rate = 44100
    bpm = max(65, min(195, int(bpm or 132)))
    duracion_seg = max(12, min(90, int(duracion_seg or 24)))
    total_samples = sample_rate * duracion_seg

    insts_low = " | ".join(instrumentos or []).lower()
    g_low = genero.lower()

    has_808 = "808" in insts_low or "dembow" in g_low or "reggaeton" in g_low or "trap" in g_low
    has_guira = "guira" in insts_low or "merengue" in g_low or "bachata" in g_low or "cumbia" in g_low
    has_brass_or_acc = any(k in insts_low for k in ["trombon", "trompeta", "acordeon", "sax", "orquesta"])
    has_strings_or_plucked = any(
        k in insts_low for k in ["requinto", "guitarra", "violin", "arpa", "charango", "sitar", "koto", "pluck"]
    )
    has_synth_lead = any(k in insts_low for k in ["supersaw", "moog", "acid", "arpegiador"])
    has_pad = any(k in insts_low for k in ["pad", "rhodes", "piano", "organo", "violonchelo"])
    has_hihats = "hi-hat" in insts_low or "edm" in g_low or "trap" in g_low

    root = KEY_ROOT_FREQS.get(tonalidad, 164.81)
    es_menor = "Menor" in tonalidad or "m (" in tonalidad
    intervalos = [0, 2, 3, 5, 7, 8, 10, 12] if es_menor else [0, 2, 4, 5, 7, 9, 11, 12]
    escala = [root * (2 ** (semi / 12.0)) for semi in intervalos]
    prog_grados = [0, 5, 2, 6] if es_menor else [0, 4, 5, 3]

    step_dur = 60.0 / bpm / 4.0
    step_samples = max(1, int(sample_rate * step_dur))
    total_steps = max(16, total_samples // step_samples)

    mix = [0.0] * total_samples
    rng = random.Random(2026)

    pat_verso = [0, -1, 2, -1, 4, -1, 2, -1, 3, -1, 2, -1, 1, -1, 0, -1]
    pat_mambo = [4, 4, 5, 4, 7, -1, 5, 4, 2, 2, 4, 2, 5, 4, 2, 0]

    for s in range(total_steps):
        step = s % 16
        bar = s // 16
        ratio = s / float(total_steps)
        start_idx = s * step_samples
        if start_idx >= total_samples:
            break

        deg = prog_grados[bar % 4]
        chord_root = escala[deg % len(escala)]
        chord_third = escala[(deg + 2) % len(escala)]
        chord_fifth = escala[(deg + 4) % len(escala)]

        if ratio < 0.12:
            seccion, energia = "intro", 0.76
        elif ratio < 0.38:
            seccion, energia = "verso", 0.92
        elif ratio < 0.65:
            seccion, energia = "coro", 1.06
        elif ratio < 0.88:
            seccion, energia = "mambo", 1.15
        else:
            seccion, energia = "outro", 0.74

        if step % 4 == 0 or (seccion == "mambo" and step == 14):
            k_len = min(int(sample_rate * 0.18), total_samples - start_idx)
            f_ini = 112.0 if "kick" in insts_low else 132.0
            for i in range(k_len):
                t = i / sample_rate
                freq = 36.0 + (f_ini - 36.0) * math.exp(-t * 26.0)
                env = math.exp(-t * 17.0) * 0.35 * energia
                mix[start_idx + i] += math.sin(2.0 * math.pi * freq * t) * env

        if step in (2, 6, 10, 14) or (seccion in ("coro", "mambo") and step in (3, 11, 15)):
            s_len = min(int(sample_rate * 0.085), total_samples - start_idx)
            for i in range(s_len):
                t = i / sample_rate
                freq = 120.0 + 225.0 * math.exp(-t * 36.0)
                env = math.exp(-t * 30.0) * 0.24 * energia
                tone = math.sin(2.0 * math.pi * freq * t)
                snap = (rng.random() * 2.0 - 1.0) * 0.38
                mix[start_idx + i] += (tone + snap) * env

        if has_guira or has_hihats or step % 2 == 0:
            is_strong = step % 4 == 0
            g_dur = 0.065 if is_strong else 0.030
            g_amp = (0.14 if is_strong else (0.08 if step % 2 == 0 else 0.05)) * energia
            g_len = min(int(sample_rate * g_dur), total_samples - start_idx)
            prev_n = 0.0
            for i in range(g_len):
                t = i / sample_rate
                raw_n = rng.random() * 2.0 - 1.0
                hp = raw_n - 0.88 * prev_n
                prev_n = raw_n
                env = math.exp(-t * (26.0 if is_strong else 55.0)) * g_amp
                mix[start_idx + i] += hp * env

        if seccion != "intro" and step in (0, 6, 8, 14):
            b_freq = (chord_fifth / 2.0) if step in (6, 14) else (chord_root / 2.0)
            b_dur = 0.36 if has_808 else 0.22
            b_len = min(int(sample_rate * b_dur), total_samples - start_idx)
            for i in range(b_len):
                t = i / sample_rate
                env = min(1.0, t / 0.012) * math.exp(-t * (5.2 if has_808 else 7.5)) * 0.32
                val = math.sin(2.0 * math.pi * b_freq * t) + 0.26 * math.sin(4.0 * math.pi * b_freq * t)
                mix[start_idx + i] += val * env

        if step in (0, 4, 8, 12) or (not has_pad and step in (2, 6, 10, 14)):
            c_dur = 0.34 if has_pad else 0.16
            c_len = min(int(sample_rate * c_dur), total_samples - start_idx)
            for i in range(c_len):
                t = i / sample_rate
                env = min(1.0, t / 0.025) * math.exp(-t * (6.0 if has_pad else 13.0)) * 0.11
                chord_sig = (
                    math.sin(2.0 * math.pi * chord_root * t)
                    + 0.78 * math.sin(2.0 * math.pi * chord_third * t)
                    + 0.68 * math.sin(2.0 * math.pi * chord_fifth * t)
                )
                mix[start_idx + i] += chord_sig * env

        if seccion != "outro":
            patron = pat_mambo if seccion in ("coro", "mambo") else pat_verso
            nota_idx = patron[step]
            if nota_idx >= 0:
                octava = 2.0 if ("bachata" in g_low or has_strings_or_plucked) else 1.0
                m_freq = escala[(deg + nota_idx) % len(escala)] * octava
                m_len = min(int(sample_rate * 0.17), total_samples - start_idx)
                for i in range(m_len):
                    t = i / sample_rate
                    env = min(1.0, t / 0.012) * math.exp(-t * 10.5) * 0.15 * energia
                    sig = 0.0
                    if has_brass_or_acc:
                        sig += (
                            math.sin(2.0 * math.pi * m_freq * t)
                            + 0.48 * math.sin(4.0 * math.pi * m_freq * t)
                            + 0.24 * math.sin(6.0 * math.pi * m_freq * t)
                        )
                    if has_strings_or_plucked or not (has_brass_or_acc or has_synth_lead):
                        sig += 0.85 * math.sin(2.0 * math.pi * m_freq * t) + 0.22 * math.sin(4.0 * math.pi * m_freq * t)
                    if has_synth_lead:
                        sig += 0.55 * (
                            math.sin(2.0 * math.pi * (m_freq * 0.996) * t)
                            + math.sin(2.0 * math.pi * (m_freq * 1.004) * t)
                        )
                    mix[start_idx + i] += sig * env

    peak = max((abs(x) for x in mix), default=1.0)
    norm_factor = 0.88 / peak if peak > 0.001 else 1.0

    pcm_bytes = bytearray()
    for sample_val in mix:
        clamped = max(-1.0, min(1.0, sample_val * norm_factor))
        pcm_bytes.extend(struct.pack("<h", int(clamped * 32767)))

    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(bytes(pcm_bytes))

    return out_path


def mezclar_voz_y_pista(voz_mp3: Path, pista_wav: Path, mezcla_out: Path) -> bool:
    if not HAS_PYDUB or not voz_mp3.exists() or not pista_wav.exists():
        return False
    try:
        voz = AudioSegment.from_file(str(voz_mp3)) + 2
        base = AudioSegment.from_wav(str(pista_wav)) - 4
        while len(base) < len(voz) + 2000:
            base = base + base
        base = base[: len(voz) + 2000].fade_out(1500)
        final_mix = base.overlay(voz, position=600)
        final_mix.export(str(mezcla_out), format="mp3", bitrate="192k")
        return mezcla_out.exists() and mezcla_out.stat().st_size > 0
    except Exception:
        return False


# ============================================================================
# MOTOR VISUAL 5K ULTRA HD (5120 x 2880) & PORTADAS MASTER
# ============================================================================
def generate_cover_5k(
    title: str,
    artist: str,
    genre: str,
    style_name: str,
    out_path: Path,
    resolucion: str = "5K Cinema Ultra HD (5120x2880)",
) -> Path:
    if not HAS_PIL:
        out_path.write_text(f"{title} - {artist} - {genre} [{resolucion}]", encoding="utf-8")
        return out_path

    bg, accent, txt = CINEMA_STYLES.get(style_name, CINEMA_STYLES["Cine Epico / Hollywood Dorado"])
    if "5K" in resolucion:
        W, H = 5120, 2880
    elif "4K" in resolucion:
        W, H = 3840, 2160
    else:
        W, H = 2048, 2048

    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)

    for i in range(0, H, 2):
        ratio = i / float(H)
        r = int(bg[0] + (32 - bg[0]) * ratio)
        g = int(bg[1] + (48 - bg[1]) * ratio)
        b = int(bg[2] + (88 - bg[2]) * ratio)
        draw.rectangle([(0, i), (W, i + 2)], fill=(r, g, b))

    cx, cy = W // 2, int(H * 0.42)
    rad1 = int(min(W, H) * 0.30)
    rad2 = int(min(W, H) * 0.21)
    stroke = max(6, W // 360)
    draw.ellipse([cx - rad1, cy - rad1, cx + rad1, cy + rad1], outline=accent, width=stroke)
    draw.ellipse([cx - rad2, cy - rad2, cx + rad2, cy + rad2], outline=txt, width=max(3, stroke // 2))

    margin = int(W * 0.035)
    draw.rectangle([margin, margin, W - margin, H - margin], outline=accent, width=max(4, stroke // 2))

    scale_f = W / 1920.0
    try:
        f_title = ImageFont.truetype("arial.ttf", int(96 * scale_f))
        f_sub = ImageFont.truetype("arial.ttf", int(48 * scale_f))
        f_small = ImageFont.truetype("arial.ttf", int(34 * scale_f))
    except Exception:
        f_title = ImageFont.load_default()
        f_sub = ImageFont.load_default()
        f_small = ImageFont.load_default()

    def center_text(y_pos: int, text_str: str, font_obj: Any, color_rgb: tuple[int, int, int]) -> None:
        bbox = draw.textbbox((0, 0), text_str, font=font_obj)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, y_pos), text_str, font=font_obj, fill=color_rgb)

    center_text(int(H * 0.68), title[:42], f_title, txt)
    center_text(int(H * 0.77), artist[:52], f_sub, accent)
    center_text(int(H * 0.84), f"{genre[:55]} | {resolucion}", f_small, txt)
    center_text(int(H * 0.90), "BASA RADIO & TV 24/7 | YOUTUBE: @Lic.PedroBaldera", f_small, accent)

    img.save(out_path, "JPEG", quality=94)
    return out_path


# ============================================================================
# IA - DETECCION AUTOMATICA DE GENERO, VOZ Y LETRA
# ============================================================================
def ia_detectar_genero_desde_letra(letra: str, ultima_seleccion: list[str]) -> tuple[str, str, int]:
    t = letra.lower()
    score: dict[str, int] = {g: 0 for g in ALL_WORLD_GENRES}
    reglas = {
        "Bachata Dominicana": ["amor", "corazon", "te extrano", "llorando", "perdon", "bachata", "amargue", "traicion"],
        "Merengue de Calle / Mambo": ["baila", "fiesta", "merengue", "mambo", "goza", "barrio", "jocoso", "risa", "cafe", "guanabana", "mandinga"],
        "Merengue Tipico (Perico Ripiao)": ["perico", "tipico", "acordeon", "guira", "campo", "cibao"],
        "Salsa Clasica": ["salsa", "clave", "tumbao", "sonero", "bailador"],
        "Dembow / Urbano": ["dembow", "perreo", "teteo", "calle", "bloke", "prra", "wey"],
        "Reggaeton": ["reggaeton", "perreo", "bellaqueo", "dem bow"],
        "Ranchera / Mariachi": ["mariachi", "ranchera", "charro", "tequila", "mexico", "caballo"],
        "Balada": ["balada", "triste", "melancolia", "recuerdo", "lluvia"],
        "Bolero": ["bolero", "beso", "eterno", "romantico"],
        "Cumbia / Vallenato": ["cumbia", "vallenato", "acordeon", "parrandero"],
        "Pop / Rock Americano": ["pop", "rock", "baby", "party", "dance"],
        "EDM / House / Techno": ["electronica", "club", "dj", "remix", "techno", "house"],
        "Score Cinematografico / Orquestal": ["pelicula", "cine", "epico", "orquesta", "heroe"],
    }
    for genero, palabras in reglas.items():
        for p in palabras:
            if p in t:
                score[genero] += 2
    if "cafe" in t and "ondina" in t:
        score["Merengue de Calle / Mambo"] += 5
    if "miniel" in t and "lethy" in t:
        score["Merengue de Calle / Mambo"] += 5
    mejor = max(score, key=lambda k: score[k])
    if score[mejor] == 0:
        if ultima_seleccion:
            return ultima_seleccion[0], "Se uso ultima seleccion del usuario.", 126
        return "Fusion Mundial: Fisico + Electronico", "IA activo Fusion Mundial (Fisico + Electronico) por defecto.", 128
    bpm_map = {
        "Bachata Dominicana": 126,
        "Merengue de Calle / Mambo": 134,
        "Merengue Tipico (Perico Ripiao)": 142,
        "Salsa Clasica": 106,
        "Dembow / Urbano": 122,
        "Reggaeton": 95,
        "Ranchera / Mariachi": 104,
        "Balada": 80,
        "Bolero": 86,
        "Cumbia / Vallenato": 98,
        "Pop / Rock Americano": 120,
        "EDM / House / Techno": 128,
        "Score Cinematografico / Orquestal": 100,
    }
    return mejor, f"IA detecto '{mejor}' por palabras clave en la letra.", bpm_map.get(mejor, 128)


def ia_elegir_mejor_voz(genero: str, letra: str, formato: str) -> tuple[str, dict[str, Any], str]:
    t = letra.lower()
    if "nino" in t or "nina" in t or "infantil" in t:
        return "Voz Infantil (Nino/Nina)", VOICE_PROFILES["Voz Infantil (Nino/Nina)"], "IA eligio Voz Infantil."
    if formato == "Coro Grupal (Voces en Bloque)":
        return "Coro Grupal", VOICE_PROFILES["Coro Grupal"], "Formato Coro: voces en bloque afinadas."
    if ("ella" in t and "mujer" in t) or "ella canta" in t:
        return "Voz Femenina", VOICE_PROFILES["Voz Femenina"], "IA eligio Voz Femenina."
    if genero in ["Balada", "Bolero", "Pop / Rock Americano"]:
        return "Voz Femenina", VOICE_PROFILES["Voz Femenina"], f"IA eligio Voz Femenina para {genero}."
    return "Voz Masculina", VOICE_PROFILES["Voz Masculina"], f"IA eligio Voz Masculina afinada para {genero}."


def ia_decidir_formato(letra: str) -> str:
    t = letra.lower()
    if "coro" in t or "todos" in t or "barrio" in t or "fiesta" in t:
        return "Coro Grupal (Voces en Bloque)"
    if "duo" in t or "los dos" in t or "tu y yo" in t or "nosotros" in t:
        return "Duo (2 Voces)"
    return "Solista"


def ia_expandir_desde_palabra(entrada: str, genero: str, modo: str) -> str:
    entrada = entrada.strip()
    if not entrada:
        return "Rumbo a celebrar, larga vida y salud, bajo el amparo del Senor."
    if modo == "Tal como lo escribo":
        return entrada
    palabras = entrada.split()
    if len(palabras) <= 5:
        return (
            f"[Verso]\n{entrada}. Que se escuche en la calle, que se baile en la fiesta.\n"
            f"[Coro]\nRumbo a celebrar, larga vida y salud, bajo el amparo del Senor. "
            f"Con {genero}, fusionando instrumentos fisicos y electronicos de BASA Productions."
        )
    return f"{entrada}\n\n[Coro IA - BASA]\nRumbo a celebrar, larga vida y salud, bajo el amparo del Senor, con {genero}, para el mundo entero."


def ia_combinar_generos(generos: list[str]) -> str:
    if len(generos) <= 1:
        return generos[0] if generos else "Fusion Mundial: Fisico + Electronico"
    return " + ".join(generos[:4]) + " - Fusion Mundial BASA"


# ============================================================================
# BOVEDA / HISTORICO / BIBLIOTECA / VENTAS / EMISORA / LEGAL
# ============================================================================
def load_autosave_state() -> dict[str, Any]:
    init_dirs()
    default_ui = {
        "project_title": "Fusion Mundial: Acordeon Tipico + 808",
        "selected_region": "Republica Dominicana (Caribe)",
        "selected_genres": ["Merengue de Calle / Mambo", "Bachata Dominicana", "EDM / House / Techno"],
        "selected_instruments": [
            "Acordeon Diatonico (Perico Ripiao)",
            "Guira Metalica Dominicana",
            "Tambora Dominicana",
            "Sub-Bajo 808 Profundo",
            "Lead Sintetizador Supersaw",
        ],
        "voice_type": "Automatico - IA elige mejor voz afinada",
        "tonalidad": "Em (Mi Menor)",
        "bpm": 134,
        "duracion_pista": 24,
        "resolucion_visual": "5K Cinema Ultra HD (5120x2880)",
        "master_prompt": "",
        "cine_title": "El Lapiz Pesa Mas que el Pico",
        "cine_ep": "Pelicula Completa 5K - T01",
        "cine_style": "Cine Epico / Hollywood Dorado",
        "cine_voice": "Voz Masculina",
        "cine_music_genre": "Score Cinematografico / Orquestal",
        "cine_idea": "Historia de superacion desde cero hasta alcanzar el exito en Republica Dominicana.",
        "cine_storyboard_text": "Escena 01 | El Inicio | Amanecer 5K en Santo Domingo.\nEscena 02 | El Desafio | Esfuerzo, fe y disciplina.\nEscena 03 | La Victoria | Celebracion en familia y legado.",
        "pub_title": "Rumbo a Celebrar (Master 5K)",
        "pub_artist": "Lic. Pedro Baldera - BASA Productions",
        "pub_lyrics": "Producido en BASA Universal AI Studio v13 | Canal Oficial: https://www.youtube.com/@Lic.PedroBaldera",
        "modo_proceso": "IA Automatica (Default) - La IA crea y afina",
        "formato_vocal": "Automatico - IA decide Solista / Duo / Coro",
        "ritmo_modo": "Automatico - IA decide segun letra",
        "usuario_actual": "pedro.baldera",
    }
    loaded = _load_json(UI_STATE_FILE, {})
    if isinstance(loaded, dict):
        default_ui.update(loaded)
    return default_ui


def autosave_callback() -> None:
    init_dirs()
    current = load_autosave_state()
    map_keys = {
        "ui_project_title": "project_title",
        "ui_region": "selected_region",
        "ui_genres": "selected_genres",
        "ui_instrumentos_sel": "selected_instruments",
        "ui_voice_type": "voice_type",
        "ui_tonalidad": "tonalidad",
        "ui_bpm": "bpm",
        "ui_duracion_pista": "duracion_pista",
        "ui_resolucion_visual": "resolucion_visual",
        "ui_master_prompt": "master_prompt",
        "ui_cine_title": "cine_title",
        "ui_cine_ep": "cine_ep",
        "ui_cine_style": "cine_style",
        "ui_cine_voice": "cine_voice",
        "ui_cine_music_genre": "cine_music_genre",
        "ui_cine_idea": "cine_idea",
        "ui_cine_storyboard_text": "cine_storyboard_text",
        "ui_pub_title": "pub_title",
        "ui_pub_artist": "pub_artist",
        "ui_pub_lyrics": "pub_lyrics",
        "ui_modo_proceso": "modo_proceso",
        "ui_formato_vocal": "formato_vocal",
        "ui_ritmo_modo": "ritmo_modo",
    }
    snapshot = dict(current)
    for k, target in map_keys.items():
        if k in st.session_state:
            snapshot[target] = st.session_state[k]
    snapshot["saved_at"] = datetime.now().isoformat()
    _save_json(UI_STATE_FILE, snapshot)


def on_region_change() -> None:
    reg = st.session_state.get("ui_region", "Republica Dominicana (Caribe)")
    st.session_state["ui_genres"] = REGION_GENRE_DEFAULTS.get(
        reg, ["Bachata Dominicana", "Merengue de Calle / Mambo", "Salsa Clasica"]
    )[:3]
    autosave_callback()


def init_vault() -> dict[str, Any]:
    init_dirs()
    default_station = {
        "station_name": OFFICIAL_RADIO_NAME,
        "youtube_channel": OFFICIAL_YOUTUBE_CHANNEL,
        "autonomous_permission": True,
        "auto_advance": True,
        "on_air": True,
        "active_track_id": None,
    }
    data = _load_json(INDEX_FILE, None)
    if data is None or not isinstance(data, dict):
        data = {
            "created_at": datetime.now().isoformat(),
            "assets": [],
            "autonomous_modules": [],
            "station_config": default_station,
        }
        _save_json(INDEX_FILE, data)
        return data
    data.setdefault("assets", [])
    data.setdefault("autonomous_modules", [])
    data.setdefault("station_config", default_station)
    return data


def repair_vault_assets(vault: dict[str, Any]) -> dict[str, Any]:
    cleaned = []
    for a in vault.get("assets", []):
        if not isinstance(a, dict):
            continue
        a.setdefault("id", str(uuid.uuid4())[:8])
        a.setdefault("title", "Sin titulo")
        a.setdefault("kind", "asset")
        a.setdefault("file", "")
        a.setdefault("created_at", datetime.now().isoformat())
        a.setdefault("meta", {})
        cleaned.append(a)
    vault["assets"] = cleaned
    return vault


def save_vault(data: dict[str, Any]) -> None:
    init_dirs()
    try:
        if INDEX_FILE.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy(INDEX_FILE, BACKUP_DIR / f"vault_index_{ts}.json")
    except Exception:
        pass
    _save_json(INDEX_FILE, data)


def add_asset(vault: dict[str, Any], title: str, kind: str, file_path: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    asset = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "kind": kind,
        "file": file_path,
        "created_at": datetime.now().isoformat(),
        "meta": meta or {},
    }
    vault.setdefault("assets", []).append(asset)
    save_vault(vault)
    return asset


def verificar_consentimiento(usuario: str) -> dict[str, Any] | None:
    data = _load_json(LEGAL_FILE, {})
    if not isinstance(data, dict):
        return None
    return data.get(usuario)


def guardar_consentimiento(usuario: str, acepta: bool, es_reserva_pagada: bool) -> dict[str, Any]:
    data = _load_json(LEGAL_FILE, {})
    if not isinstance(data, dict):
        data = {}
    texto_hash = hashlib.sha256((LEGAL_TEXT + usuario + datetime.now().isoformat()).encode("utf-8")).hexdigest()[:16]
    entry = {
        "usuario": usuario,
        "acepta_cesion": acepta,
        "reserva_pagada": es_reserva_pagada,
        "propiedad": "Usuario - Reserva Pagada" if es_reserva_pagada else "BASA Productions - Desarrollador",
        "fecha": datetime.now().isoformat(),
        "hash_legal": texto_hash,
        "valido_para_siempre": True,
        "dispositivos": "Todos - Este y cualquier otro",
        "desarrollador": DEVELOPER_NAME,
    }
    data[usuario] = entry
    _save_json(LEGAL_FILE, data)
    return entry


def guardar_historico(
    usuario: str,
    titulo: str,
    letra: str,
    genero: str,
    formato: str,
    voz: str,
    modo: str,
    archivos: list[str],
    propiedad: str,
    instrumentos: list[str] | None = None,
    en_radio: bool = True,
) -> dict[str, Any]:
    hist = _load_json(HISTORY_FILE, {})
    if not isinstance(hist, dict):
        hist = {}
    entry = {
        "id": str(uuid.uuid4())[:8],
        "usuario": usuario,
        "titulo": titulo,
        "letra": letra[:2500],
        "genero": genero,
        "instrumentos": instrumentos or [],
        "formato": formato,
        "voz": voz,
        "modo": modo,
        "archivos": archivos,
        "propiedad": propiedad,
        "en_emisora_radio": en_radio,
        "canal_youtube": OFFICIAL_YOUTUBE_CHANNEL,
        "created_at": datetime.now().isoformat(),
    }
    hist.setdefault(usuario, []).append(entry)
    _save_json(HISTORY_FILE, hist)

    lib = _load_json(LIBRARY_FILE, [])
    if not isinstance(lib, list):
        lib = []
    lib.append(
        {
            **entry,
            "biblioteca": "Biblioteca Libre BASA",
            "licencia": (
                "BASA Libre - Uso de BASA Productions sin restriccion"
                if propiedad.startswith("BASA")
                else "Reservada - Propiedad del Usuario"
            ),
        }
    )
    _save_json(LIBRARY_FILE, lib)

    # Agregar automaticamente a la parrilla de la Emisora de Radio BASA 24/7
    if en_radio and archivos:
        playlist = _load_json(RADIO_PLAYLIST_FILE, [])
        if not isinstance(playlist, list):
            playlist = []
        playlist.append(
            {
                "id": entry["id"],
                "titulo": titulo,
                "artista": "Lic. Pedro Baldera - BASA Productions",
                "genero": genero,
                "archivos": archivos,
                "youtube": OFFICIAL_YOUTUBE_CHANNEL,
                "agregado_en": datetime.now().isoformat(),
            }
        )
        _save_json(RADIO_PLAYLIST_FILE, playlist)

    return entry


def crear_paquete_obra_zip(obra: dict[str, Any]) -> Path:
    init_dirs()
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", str(obra.get("titulo", "Obra_BASA")))[:35] or "Obra_BASA"
    zip_path = AUTO_EXPORT_DIR / f"PACK_{safe}_{obra.get('id', '000')}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        meta_txt = (
            f"BASA UNIVERSAL AI STUDIO v13 - PAQUETE OFICIAL DE OBRA\n"
            f"Titulo: {obra.get('titulo')}\n"
            f"Genero: {obra.get('genero')}\n"
            f"Propiedad / Derechos: {obra.get('propiedad')}\n"
            f"Canal Oficial YouTube: {OFFICIAL_YOUTUBE_CHANNEL}\n"
            f"Emisora Oficial: {OFFICIAL_RADIO_NAME}\n"
            f"Fecha Produccion: {obra.get('created_at')}\n\n"
            f"LETRA / GUION:\n{obra.get('letra', '')}\n"
        )
        z.writestr("FICHA_Y_LETRA.txt", meta_txt)
        z.writestr("metadata.json", json.dumps(obra, indent=2, ensure_ascii=False))
        for fpath in obra.get("archivos", []):
            p = Path(fpath)
            if p.exists() and p.is_file():
                try:
                    z.write(p, arcname=p.name)
                except Exception:
                    pass
    return zip_path


# ============================================================================
# AUDIO TTS / STORYBOARD / ZIP GLOBAL
# ============================================================================
def clean_text_for_tts(text: str) -> str:
    text = re.sub(r"\[[^\]]+\]", " ", text)
    text = re.sub(r"[*#_>~`]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:1800] if len(text) > 1800 else text


async def _tts_async(text: str, voice: str, rate: str, pitch: str, out_path: Path) -> bool:
    if not HAS_EDGE_TTS:
        return False
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(str(out_path))
        return out_path.exists() and out_path.stat().st_size > 0
    except Exception:
        return False


def generate_voice_audio(text: str, profile: dict[str, Any], out_path: Path) -> tuple[bool, str]:
    if profile.get("mode") == "instrumental":
        return False, "Modo solo instrumental seleccionado."
    cleaned = clean_text_for_tts(text)
    if not cleaned:
        return False, "Escriba letra o guion para sintetizar voz."
    if not HAS_EDGE_TTS:
        return False, "edge-tts no instalado (se genero la pista instrumental WAV)."
    try:
        ok = asyncio.run(_tts_async(cleaned, profile["voice"], profile["rate"], profile["pitch"], out_path))
        if ok:
            return True, f"Voz generada: {out_path.name}"
        return False, "Sin conexion a edge-tts (se genero la pista instrumental WAV)."
    except Exception as e:
        return False, f"Error TTS: {e}"


def parse_storyboard(text: str) -> list[dict[str, str]]:
    scenes = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3:
            scenes.append({"id": parts[0], "title": parts[1], "desc": parts[2]})
        elif len(parts) == 2:
            scenes.append({"id": parts[0], "title": parts[1], "desc": parts[1]})
        else:
            scenes.append({"id": f"Escena {len(scenes) + 1:02d}", "title": "Escena", "desc": line})
    if not scenes:
        scenes = [{"id": "Escena 01", "title": "Inicio", "desc": text or "Historia BASA"}]
    return scenes


def export_project_zip(vault: dict[str, Any], title: str) -> Path:
    init_dirs()
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", title)[:40] or "BASA"
    zip_path = AUTO_EXPORT_DIR / f"{safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "README_BASA.txt",
            f"BASA v13\nProyecto: {title}\nCanal YouTube: {OFFICIAL_YOUTUBE_CHANNEL}\nFecha: {datetime.now().isoformat()}\nAutor: {DEVELOPER_NAME}\n",
        )
        z.writestr("vault_index.json", json.dumps(vault, indent=2, ensure_ascii=False))
        for a in vault.get("assets", []):
            p = Path(a.get("file", ""))
            if p.exists() and p.is_file():
                try:
                    z.write(p, arcname=f"media/{p.name}")
                except Exception:
                    pass
    return zip_path


# ============================================================================
# FRAGMENTO AUTONOMO EN VIVO (SE AUTO-ACTUALIZA CADA 10 SEGUNDOS SIN BLOQUEAR)
# ============================================================================
@st.fragment(run_every=10)
def panel_radar_autonomo_10s() -> None:
    radar = actualizar_radar_mundial_autonomo()
    items = radar.get("items", [])
    estado_conexion = "🌐 Red Global + Motor Local" if radar.get("fuente_red_activa") else "⚡ Nucleo Autonomo Local Activo"

    with st.container(border=True):
        c_top1, c_top2, c_top3 = st.columns([2.2, 1.3, 1])
        with c_top1:
            st.markdown(
                f"**📡 Radar Mundial & Emisora 24/7 (Auto-sync cada 10s)** — `{estado_conexion}`"
            )
        with c_top2:
            st.caption(f"Ciclo #{radar.get('ciclo', 1)} | Sync: {radar.get('ultima_actualizacion', '')}")
        with c_top3:
            if items and st.button("⚡ Aplicar Tendencia Actual", key=f"apply_radar_{radar.get('ciclo', 0)}", use_container_width=True):
                top = items[0]
                st.session_state["ui_master_prompt"] = top.get("prompt_sugerido", "")
                st.session_state["ui_project_title"] = top.get("titular", "Produccion BASA")[:48]
                autosave_callback()
                st.toast(f"Tendencia cargada: {top.get('categoria')}")

        if items:
            cols_r = st.columns(3)
            for idx, it in enumerate(items[:3]):
                with cols_r[idx]:
                    st.markdown(f"**{it.get('categoria', '')}** · *{it.get('ambito', '')}*")
                    st.caption(it.get("titular", ""))


# ============================================================================
# MAIN - BASA v13 EMISORA 24/7 + YOUTUBE + 5K + HISTORICO COMERCIAL
# ============================================================================
def main() -> None:
    init_dirs()
    vault = init_vault()
    vault = repair_vault_assets(vault)
    ui = load_autosave_state()
    catalogo_instrumentos = cargar_instrumentos_usuario()

    st.title("⚡ BASA Universal AI Studio v13 — Emisora 24/7 + YouTube + 5K")
    st.markdown(
        f"Desarrollado por **Pedro Baldera — BASA Productions** | "
        f"Canal Oficial: **[@Lic.PedroBaldera]({OFFICIAL_YOUTUBE_CHANNEL})** | "
        f"Emisora Online: **{OFFICIAL_RADIO_NAME}**"
    )

    panel_radar_autonomo_10s()

    with st.sidebar:
        st.header("👤 Usuario & Canal Oficial")
        usuario = st.text_input("Usuario", value=ui.get("usuario_actual", "pedro.baldera"), key="usuario_actual")
        st.markdown(f"📺 **YouTube:** [@Lic.PedroBaldera]({OFFICIAL_YOUTUBE_CHANNEL})")
        st.markdown(f"📻 **Emisora:** {OFFICIAL_RADIO_NAME}")

        st.header("🔐 Acceso")
        pin = st.text_input("PIN Admin", type="password", key="admin_pin")
        is_admin = (pin == ADMIN_MASTER_PIN) or (pin == "")
        if pin and not is_admin:
            st.error("PIN incorrecto. Solo lectura.")
        st.divider()

        st.header("⚖️ Contrato Legal - 1 sola vez")
        consent = verificar_consentimiento(usuario)
        if consent:
            st.success(f"✅ Contrato firmado: {consent.get('fecha', '')[:16]}")
            st.write(f"Propiedad: {consent.get('propiedad')}")
            st.caption(f"Hash: {consent.get('hash_legal')} | Valido para siempre.")
        else:
            st.warning("⚠️ Debe marcar el cotejo para registrar temas.")
            with st.expander("📜 Leer Contrato Legal Completo"):
                st.text_area("Contrato", LEGAL_TEXT, height=240, disabled=True)
            acepta = st.checkbox(
                "✅ Acepto y cedo derechos a BASA Productions (Pedro Baldera). Entiendo que toda cancion pasa a BASA sin restriccion, salvo que pague reserva.",
                key="legal_check",
            )
            reserva = st.checkbox(
                "💰 Pague Reserva - Quiero que sea de MI propiedad exclusiva (pagar al desarrollador)",
                key="legal_reserva",
            )
            if st.button("✍️ Firmar Contrato - Valido Para Siempre"):
                if not acepta:
                    st.error("Debe marcar el cotejo de aceptacion para firmar.")
                else:
                    e = guardar_consentimiento(usuario, True, reserva)
                    st.success(f"Contrato firmado. Propiedad: {e['propiedad']}.")
                    st.rerun()
            consent = None

        st.divider()
        st.header("📊 Estadisticas Globales")
        st.metric("Instrumentos Mundiales", len(catalogo_instrumentos))
        st.metric("Assets en Boveda", len(vault.get("assets", [])))
        playlist_radio = _load_json(RADIO_PLAYLIST_FILE, [])
        st.metric("En Emisora Radio 24/7", len(playlist_radio) if isinstance(playlist_radio, list) else 0)
        ventas_cat = _load_json(SALES_CATALOG_FILE, [])
        st.metric("Obras en Tienda / Venta", len(ventas_cat) if isinstance(ventas_cat, list) else 0)

        if st.button("💾 Guardar / Autosave"):
            autosave_callback()
            st.success("Guardado.")
        if st.button("📦 Exportar Boveda Completa ZIP"):
            zp = export_project_zip(vault, ui["project_title"])
            st.success(f"ZIP: {zp.name}")
            with open(zp, "rb") as f:
                st.download_button("⬇ Descargar ZIP", f.read(), file_name=zp.name, mime="application/zip")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "🎵 1. Estudio Musica Mundial IA",
            "🎬 2. Cine / Series / Drama 5K",
            "📻 3. Mi Emisora Radio & TV 24/7",
            "🚀 4. Publicar YouTube @Lic.PedroBaldera",
            "📚 5. Historico: Descargar / Vender",
            "🎛️ 6. Consola WebAudio en Vivo",
            "🧩 7. Auto-Desarrollo & Modulos",
        ]
    )

    # ========================================================================
    # TAB 1: ESTUDIO MUSICA MUNDIAL IA
    # ========================================================================
    with tab1:
        st.subheader("🎵 Orquestador Mundial: Instrumentos Fisicos + Electronica + Visual 5K")
        col1, col2 = st.columns([1.15, 1])

        with col1:
            project_title = st.text_input("Titulo del proyecto", value=ui["project_title"], key="ui_project_title")
            region = st.selectbox(
                "Region / Mercado",
                list(REGION_GENRE_DEFAULTS.keys()),
                index=list(REGION_GENRE_DEFAULTS.keys()).index(ui["selected_region"])
                if ui["selected_region"] in REGION_GENRE_DEFAULTS
                else 0,
                key="ui_region",
                on_change=on_region_change,
            )
            modo_proceso = st.selectbox(
                "¿Como procesar la cancion?",
                [
                    "IA Automatica (Default) - La IA crea y afina",
                    "Con ayuda IA - Yo escribo, IA mejora",
                    "Tal como lo escribo - Sin tocar mi letra",
                ],
                index=0,
                key="ui_modo_proceso",
            )
            ritmo_modo = st.selectbox(
                "Genero Principal (o Automatico IA)",
                ["Automatico - IA decide segun letra"]
                + ALL_WORLD_GENRES
                + ["Combinar Generos - Fusion Mundial Total"],
                key="ui_ritmo_modo",
            )
            genres = st.multiselect(
                "Generos adicionales para fusionar",
                ALL_WORLD_GENRES,
                default=[],
                key="ui_genres_manual",
            )

            st.markdown("---")
            st.markdown("**🎻🎛️ Lista de Instrumentacion Mundial (Fisicos + Electronicos)**")
            modo_auto_inst = st.checkbox(
                "🤖 Combinar automaticamente instrumentacion fisica + electronica con IA",
                value=True,
                key="ui_auto_combine_inst",
            )

            defaults_validos = [i for i in ui.get("selected_instruments", []) if i in catalogo_instrumentos]
            instrumentos_sel = st.multiselect(
                "Tu Lista de Instrumentos Activos",
                options=catalogo_instrumentos,
                default=defaults_validos,
                key="ui_instrumentos_sel",
            )

            with st.expander("➕ Agregar Nuevo Instrumento Fisico o Electronico a Mi Lista"):
                c_add1, c_add2, c_add3 = st.columns([2, 1.5, 1])
                with c_add1:
                    nuevo_inst_nombre = st.text_input(
                        "Nombre del instrumento",
                        placeholder="Ej: Saxofon Soprano, Sintetizador Juno-106, Pandero...",
                        key="new_inst_input",
                    )
                with c_add2:
                    nueva_familia = st.selectbox("Tipo", ["Fisico", "Electronico", "Hibrido"], key="new_inst_family")
                with c_add3:
                    st.write("")
                    st.write("")
                    if st.button("Agregar", use_container_width=True):
                        if nuevo_inst_nombre.strip():
                            guardar_instrumento_personalizado(nuevo_inst_nombre, nueva_familia)
                            st.success(f"Agregado: {nuevo_inst_nombre}")
                            st.rerun()

            st.markdown("---")
            c_ton, c_dur, c_res = st.columns(3)
            with c_ton:
                tonalidad_sel = st.selectbox(
                    "Tonalidad",
                    list(KEY_ROOT_FREQS.keys()),
                    index=list(KEY_ROOT_FREQS.keys()).index(ui.get("tonalidad", "Em (Mi Menor)"))
                    if ui.get("tonalidad", "Em (Mi Menor)") in KEY_ROOT_FREQS
                    else 1,
                    key="ui_tonalidad",
                )
            with c_dur:
                duracion_sel = st.slider(
                    "Duracion WAV (seg)",
                    12,
                    60,
                    int(ui.get("duracion_pista", 24)),
                    step=4,
                    key="ui_duracion_pista",
                )
            with c_res:
                resolucion_sel = st.selectbox(
                    "Calidad Imagen",
                    [
                        "5K Cinema Ultra HD (5120x2880)",
                        "4K Ultra HD (3840x2160)",
                        "Master Cuadrado (2048x2048)",
                    ],
                    key="ui_resolucion_visual",
                )

            formato_vocal = st.selectbox(
                "Formato Vocal",
                [
                    "Automatico - IA decide Solista / Duo / Coro",
                    "Solista",
                    "Duo (2 Voces)",
                    "Coro Grupal (Voces en Bloque)",
                    "Solo Instrumental (Sin Voz)",
                ],
                key="ui_formato_vocal",
            )
            voz_manual = st.selectbox(
                "Voz Manual (opcional)",
                ["Automatico - IA elige mejor voz afinada"] + list(VOICE_PROFILES.keys()),
                key="ui_voice_type",
            )
            bpm_manual = st.slider("BPM Manual (0 = Automatico segun genero)", 0, 190, 0, key="ui_bpm")
            publicar_emisora_auto = st.checkbox(
                "📻 Transmitir automaticamente en Mi Emisora Radio & TV 24/7 al terminar",
                value=True,
                key="ui_auto_radio",
            )
            master_prompt = st.text_area(
                "Prompt Maestro / Direccion Musical y Visual",
                value=ui["master_prompt"],
                height=68,
                key="ui_master_prompt",
                placeholder="Ej: Fusionar acordeon tipico y trombones con sub-bajo 808 y visual 5K epico...",
            )

        with col2:
            st.subheader("✍️ Letra / Historia / Idea Musical")
            entrada_usuario = st.text_area(
                "Su palabra / frase / oracion / historia completa",
                value="Miniel comio donde Lethy, luego cafe donde Ondina debajo de la mata de guanabana de Paca Alberto",
                height=190,
                key="entrada_usuario",
            )

            if st.button("✨ Vista Previa IA - Orquestacion, Genero y Voz", use_container_width=True):
                genero_prev, expl_prev, bpm_prev = ia_detectar_genero_desde_letra(
                    entrada_usuario, ui.get("selected_genres", [])
                )
                if (
                    ritmo_modo != "Automatico - IA decide segun letra"
                    and ritmo_modo != "Combinar Generos - Fusion Mundial Total"
                ):
                    genero_prev = ritmo_modo

                generos_para_ia = list(dict.fromkeys([genero_prev] + genres))
                insts_prev, expl_inst = ia_combinar_instrumentacion(
                    generos_para_ia,
                    instrumentos_sel,
                    modo_fusion_mundial=modo_auto_inst,
                    prompt_extra=master_prompt + " " + entrada_usuario,
                )
                formato_prev = (
                    ia_decidir_formato(entrada_usuario)
                    if formato_vocal.startswith("Automatico")
                    else formato_vocal
                )
                voz_prev, _, expl_voz = ia_elegir_mejor_voz(genero_prev, entrada_usuario, formato_prev)

                st.info(
                    f"**Genero:** {ia_combinar_generos(generos_para_ia)} | **BPM:** {bpm_prev if bpm_manual == 0 else bpm_manual} | "
                    f"**Tonalidad:** {tonalidad_sel} | **Voz:** {voz_prev}"
                )
                st.success(f"🎻🎛️ {expl_inst}")
                st.write(f"{expl_prev} {expl_voz}")
                letra_prev = ia_expandir_desde_palabra(entrada_usuario, genero_prev, modo_proceso)
                st.text_area("Letra que usaria la IA (preview)", letra_prev, height=130)

            c1, c2 = st.columns(2)
            with c1:
                generar = st.button("🎤 Generar Cancion + Orquesta WAV", type="primary", use_container_width=True)
            with c2:
                if st.button("🖼 Generar Portada 5K UHD", use_container_width=True):
                    if not consent:
                        st.error("⚖️ Debe firmar el contrato legal en la barra lateral antes de registrar.")
                    else:
                        with st.spinner(f"Renderizando imagen {resolucion_sel}..."):
                            gen_tmp, _, _ = ia_detectar_genero_desde_letra(
                                entrada_usuario, ui.get("selected_genres", [])
                            )
                            out_img = (
                                MEDIA_DIR
                                / f"portada5K_{re.sub(r'[^A-Za-z0-9_-]+', '_', project_title)[:28]}_{datetime.now().strftime('%H%M%S')}.jpg"
                            )
                            generate_cover_5k(
                                project_title,
                                "Lic. Pedro Baldera - BASA",
                                gen_tmp,
                                "Cine Epico / Hollywood Dorado",
                                out_img,
                                resolucion=resolucion_sel,
                            )
                            add_asset(vault, project_title, "portada_5k", str(out_img), {"genre": gen_tmp, "res": resolucion_sel})
                            st.success(f"Imagen 5K creada: {out_img.name}")
                            st.image(str(out_img), width=360)

            if generar:
                if not consent:
                    st.error("⚖️ Debe marcar y firmar el contrato legal en la barra lateral ANTES de registrar.")
                elif pin and not is_admin:
                    st.error("PIN incorrecto.")
                else:
                    with st.spinner("BASA IA produciendo obra completa (Audio + Portada 5K + Emisora + Historico)..."):
                        if ritmo_modo == "Automatico - IA decide segun letra":
                            genero_base, expl_g, bpm_ia = ia_detectar_genero_desde_letra(
                                entrada_usuario, ui.get("selected_genres", [])
                            )
                        elif ritmo_modo == "Combinar Generos - Fusion Mundial Total":
                            genero_base = genres[0] if genres else "Fusion Mundial: Fisico + Electronico"
                            bpm_ia = 132
                            expl_g = "Fusion Mundial Total activada por el usuario."
                        else:
                            genero_base = ritmo_modo
                            bpm_ia = 128
                            expl_g = "Genero principal seleccionado por el usuario."

                        generos_combinados = list(dict.fromkeys([genero_base] + genres))
                        genero_final = ia_combinar_generos(generos_combinados)
                        bpm_final = bpm_manual if bpm_manual != 0 else bpm_ia

                        instrumentos_finales, expl_inst_final = ia_combinar_instrumentacion(
                            generos_combinados,
                            instrumentos_sel,
                            modo_fusion_mundial=modo_auto_inst,
                            prompt_extra=master_prompt + " " + entrada_usuario,
                        )

                        if modo_proceso.startswith("Tal como"):
                            letra_final = entrada_usuario
                        elif modo_proceso.startswith("Con ayuda"):
                            letra_final = ia_expandir_desde_palabra(entrada_usuario, genero_final, "Con ayuda IA")
                        else:
                            letra_final = ia_expandir_desde_palabra(entrada_usuario, genero_final, "IA Automatica")

                        if formato_vocal.startswith("Automatico"):
                            formato_final = ia_decidir_formato(letra_final)
                        else:
                            formato_final = formato_vocal

                        if voz_manual.startswith("Automatico"):
                            voz_nombre, voz_perfil, expl_v = ia_elegir_mejor_voz(
                                genero_base, letra_final, formato_final
                            )
                        else:
                            voz_nombre = voz_manual
                            voz_perfil = VOICE_PROFILES[voz_manual]
                            expl_v = "Voz manual elegida por el usuario."

                        if formato_final == "Solo Instrumental (Sin Voz)":
                            voz_perfil = VOICE_PROFILES["Solo Instrumental"]

                        ts_tag = datetime.now().strftime("%H%M%S")
                        safe_slug = re.sub(r"[^A-Za-z0-9_-]+", "_", project_title)[:30] or "tema_basa"
                        propiedad = consent.get("propiedad", "BASA Productions - Desarrollador")

                        # 1. Pista Instrumental WAV 16-bit
                        out_wav = MEDIA_DIR / f"orquesta_{safe_slug}_{ts_tag}.wav"
                        generar_pista_instrumental_wav(
                            out_path=out_wav,
                            genero=genero_final,
                            bpm=bpm_final,
                            tonalidad=tonalidad_sel,
                            duracion_seg=duracion_sel,
                            instrumentos=instrumentos_finales,
                        )
                        archivos_generados = [str(out_wav)]
                        add_asset(
                            vault,
                            f"{project_title} (Orquesta WAV)",
                            "audio_instrumental",
                            str(out_wav),
                            {"genre": genero_final, "bpm": bpm_final, "propiedad": propiedad},
                        )

                        # 2. Portada oficial 5K automatica para YouTube y Emisora
                        out_cover = MEDIA_DIR / f"cover5K_{safe_slug}_{ts_tag}.jpg"
                        generate_cover_5k(
                            project_title,
                            "Lic. Pedro Baldera - BASA Productions",
                            genero_final,
                            "Cine Epico / Hollywood Dorado",
                            out_cover,
                            resolucion=resolucion_sel,
                        )
                        archivos_generados.append(str(out_cover))
                        add_asset(vault, f"{project_title} (Portada 5K)", "portada_5k", str(out_cover), {"genre": genero_final})

                        # 3. Voz TTS y mezcla master
                        out_voz = MEDIA_DIR / f"voz_{safe_slug}_{ts_tag}.mp3"
                        ok_voz, msg_voz = generate_voice_audio(letra_final, voz_perfil, out_voz)
                        out_mix = MEDIA_DIR / f"master_{safe_slug}_{ts_tag}.mp3"
                        ok_mix = False

                        if ok_voz:
                            archivos_generados.append(str(out_voz))
                            add_asset(
                                vault,
                                f"{project_title} (Voz)",
                                "audio_tema",
                                str(out_voz),
                                {"genre": genero_final, "voice": voz_nombre, "bpm": bpm_final, "propiedad": propiedad},
                            )
                            ok_mix = mezclar_voz_y_pista(out_voz, out_wav, out_mix)
                            if ok_mix:
                                archivos_generados.append(str(out_mix))
                                add_asset(
                                    vault,
                                    f"{project_title} (Master Final)",
                                    "audio_master",
                                    str(out_mix),
                                    {"genre": genero_final, "bpm": bpm_final, "propiedad": propiedad},
                                )

                        obra_reg = guardar_historico(
                            usuario,
                            project_title,
                            letra_final,
                            genero_final,
                            formato_final,
                            voz_nombre,
                            modo_proceso,
                            archivos_generados,
                            propiedad,
                            instrumentos=instrumentos_finales,
                            en_radio=publicar_emisora_auto,
                        )

                        st.success(f"✅ Obra Completa Producida y Guardada en Historico + Emisora 24/7: {project_title}")
                        st.info(f"🎻🎛️ {expl_inst_final}")
                        st.image(str(out_cover), width=320)

                        if ok_mix:
                            st.markdown("**🎧 Master Final (Voz + Orquestacion Hibrida):**")
                            st.audio(str(out_mix))

                        st.markdown("**🥁 Pista Instrumental Hibrida (WAV 16-bit):**")
                        st.audio(str(out_wav))
                        with open(out_wav, "rb") as fw:
                            st.download_button(
                                "⬇ Descargar Instrumental WAV",
                                fw.read(),
                                file_name=out_wav.name,
                                mime="audio/wav",
                            )

                        if ok_voz:
                            st.markdown("**🎤 Pista Vocal:**")
                            st.audio(str(out_voz))
                        else:
                            st.caption(f"Nota vocal: {msg_voz}")

                        pack_zip = crear_paquete_obra_zip(obra_reg, project_title)
                        with open(pack_zip, "rb") as fz:
                            st.download_button(
                                "📦 Descargar Paquete Completo (Audio + Portada 5K + Letra + JSON)",
                                fz.read(),
                                file_name=pack_zip.name,
                                mime="application/zip",
                            )

                        st.session_state["ui_genres"] = generos_combinados
                        autosave_callback()

    # ========================================================================
    # TAB 2: CINE / SERIES / DRAMA / PELICULAS 5K
    # ========================================================================
    with tab2:
        st.subheader("🎬 Cine / Video / Serie / Drama / Pelicula en 5K Ultra HD")
        cc1, cc2 = st.columns(2)
        with cc1:
            cine_title = st.text_input("Titulo de la Obra Audiovisual", value=ui["cine_title"], key="ui_cine_title")
            cine_ep = st.text_input("Episodio / Temporada / Capitulo", value=ui["cine_ep"], key="ui_cine_ep")
            cine_style = st.selectbox("Estilo visual 5K", list(CINEMA_STYLES.keys()), key="ui_cine_style")
            cine_voice = st.selectbox("Voz narrador / personajes", list(VOICE_PROFILES.keys()), key="ui_cine_voice")
            cine_genre = st.selectbox(
                "Banda Sonora / Musica de Fondo",
                ALL_WORLD_GENRES,
                index=ALL_WORLD_GENRES.index(ui["cine_music_genre"])
                if ui["cine_music_genre"] in ALL_WORLD_GENRES
                else 0,
                key="ui_cine_music_genre",
            )
            cine_idea = st.text_area("Sinopsis / Drama / Historia", value=ui["cine_idea"], key="ui_cine_idea")
            tipo_video = st.selectbox(
                "Formato Audiovisual",
                [
                    "Pelicula Completa 5K",
                    "Serie - Capitulo Dramatico",
                    "Video Musical 5K",
                    "Noticiero / Documental Internacional",
                    "Corto / Reels / TikTok",
                ],
                key="tipo_video",
            )
        with cc2:
            cine_story = st.text_area(
                "Storyboard 5K - Escena | Titulo | Descripcion",
                value=ui["cine_storyboard_text"],
                height=220,
                key="ui_cine_storyboard_text",
            )
            scenes = parse_storyboard(cine_story)
            st.info(f"Escenas: {len(scenes)} | Formato: {tipo_video} | Render 5K (5120x2880)")
            for s in scenes:
                st.markdown(f"**{s['id']} - {s['title']}**: {s['desc']}")

        if st.button("🎬 Generar Produccion Audiovisual 5K + Banda Sonora", type="primary"):
            if not consent:
                st.error("Debe firmar contrato legal primero.")
            else:
                with st.spinner("Renderizando poster 5K (5120x2880), banda sonora hibrida y narracion..."):
                    ts_c = datetime.now().strftime("%H%M%S")
                    poster = MEDIA_DIR / f"cine5K_poster_{ts_c}.jpg"
                    generate_cover_5k(
                        cine_title,
                        "Lic. Pedro Baldera - BASA Cinema 5K",
                        cine_genre,
                        cine_style,
                        poster,
                        resolucion="5K Cinema Ultra HD (5120x2880)",
                    )
                    add_asset(vault, cine_title, "poster_cine_5k", str(poster), {"style": cine_style, "tipo": tipo_video})

                    insts_cine, _ = ia_combinar_instrumentacion([cine_genre], [], modo_fusion_mundial=True)
                    banda_wav = MEDIA_DIR / f"cine_score_{ts_c}.wav"
                    generar_pista_instrumental_wav(banda_wav, cine_genre, 102, "Dm (Re Menor)", 20, insts_cine)
                    add_asset(vault, f"{cine_title} (Score 5K)", "audio_instrumental", str(banda_wav), {"tipo": tipo_video})

                    full_script = f"{cine_title}. {cine_idea}. " + " ".join(
                        [f"{s['title']}. {s['desc']}" for s in scenes]
                    )
                    out_audio = MEDIA_DIR / f"cine_narracion_{ts_c}.mp3"
                    ok, msg = generate_voice_audio(full_script, VOICE_PROFILES[cine_voice], out_audio)
                    archivos_cine = [str(poster), str(banda_wav)]
                    if ok:
                        archivos_cine.append(str(out_audio))
                        add_asset(vault, cine_title, "audio_cine", str(out_audio), {"scenes": len(scenes), "tipo": tipo_video})

                    guardar_historico(
                        usuario,
                        cine_title,
                        full_script,
                        cine_genre,
                        tipo_video,
                        cine_voice,
                        "IA Automatica",
                        archivos_cine,
                        consent.get("propiedad", "BASA Productions - Desarrollador"),
                        instrumentos=insts_cine,
                        en_radio=True,
                    )
                    st.success("Produccion 5K UHD + Banda Sonora generadas, guardadas y enviadas a Emisora 24/7.")
                    st.image(str(poster), width=420)
                    st.audio(str(banda_wav))
                    if ok:
                        st.audio(str(out_audio))

    # ========================================================================
    # TAB 3: MI EMISORA DE RADIO & TV ONLINE 24/7 (SUPERANDO STREAMING)
    # ========================================================================
    with tab3:
        st.subheader(f"📻 {OFFICIAL_RADIO_NAME} — Transmision Online Continua")
        st.markdown(
            f'<span class="on-air-badge">● EN VIVO / ON AIR 24/7</span> &nbsp; '
            f'Canal Oficial Vinculado: **[@Lic.PedroBaldera]({OFFICIAL_YOUTUBE_CHANNEL})**',
            unsafe_allow_html=True,
        )
        st.write("")

        playlist = _load_json(RADIO_PLAYLIST_FILE, [])
        if not isinstance(playlist, list):
            playlist = []

        if not playlist:
            st.info("Tu emisora esta lista para transmitir. Genera un tema en la Pestana 1 o 2 y aparecera aqui automaticamente al aire.")
        else:
            c_rad1, c_rad2 = st.columns([1.3, 1])
            with c_rad1:
                titulos_radio = [f"#{idx + 1} - {p.get('titulo', 'Sin titulo')} ({p.get('genero', '')})" for idx, p in enumerate(reversed(playlist))]
                seleccion_radio = st.selectbox("Parrilla de Programacion en Vivo", titulos_radio, key="radio_now_playing_sel")
                idx_real = len(playlist) - 1 - titulos_radio.index(seleccion_radio)
                pista_actual = playlist[idx_real]

                st.markdown(f"### 🎙️ Sonando Ahora: {pista_actual.get('titulo')}")
                st.caption(f"Artista / Productor: {pista_actual.get('artista')} | Genero: {pista_actual.get('genero')}")

                for fpath in pista_actual.get("archivos", []):
                    p = Path(fpath)
                    if p.exists() and p.is_file():
                        if p.suffix.lower() in [".mp3", ".wav"]:
                            st.caption(f"Canal Audio: {p.name}")
                            st.audio(str(p))
                        elif p.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                            st.image(str(p), width=360)

            with c_rad2:
                st.markdown("**📡 Panel de Control de Emisora & Redes**")
                st.info(
                    f"**Estacion:** {OFFICIAL_RADIO_NAME}\n\n"
                    f"**Total de Obras en Rotacion:** {len(playlist)}\n\n"
                    f"**Destino YouTube:** {OFFICIAL_YOUTUBE_CHANNEL}"
                )
                if st.button("🔀 Siguiente Tema Aleatorio en Emisora", use_container_width=True):
                    st.rerun()

                st.markdown("**Cola de Transmision (Ultimos 15):**")
                for item_r in reversed(playlist[-15:]):
                    st.markdown(f"- 🎵 **{item_r.get('titulo')}** — *{item_r.get('genero')}*")

    # ========================================================================
    # TAB 4: PUBLICAR EN YOUTUBE (@Lic.PedroBaldera) + SPOTIFY + REDES
    # ========================================================================
    with tab4:
        st.subheader(f"🚀 Publicar Directo en YouTube ({OFFICIAL_YOUTUBE_HANDLE}) + Spotify + Redes")
        st.markdown(
            f"Destino Oficial Configurado: **[Abrir Canal YouTube @Lic.PedroBaldera]({OFFICIAL_YOUTUBE_CHANNEL})**"
        )

        hist_pub = _load_json(HISTORY_FILE, {})
        obras_usuario = hist_pub.get(usuario, []) if isinstance(hist_pub, dict) else []
        opciones_obras = ["(Usar datos manuales abajo)"] + [
            f"{o.get('id')} | {o.get('titulo')} [{o.get('genero')}]" for o in reversed(obras_usuario)
        ]
        obra_elegida_pub = st.selectbox("Seleccionar obra producida del Historico para publicar", opciones_obras)

        default_pub_t = ui["pub_title"]
        default_pub_l = ui["pub_lyrics"]
        obra_obj_sel = None
        if obra_elegida_pub != "(Usar datos manuales abajo)":
            oid = obra_elegida_pub.split("|")[0].strip()
            for o in obras_usuario:
                if o.get("id") == oid:
                    obra_obj_sel = o
                    default_pub_t = o.get("titulo", default_pub_t)
                    default_pub_l = (
                        f"{o.get('letra', '')}\n\n"
                        f"---\nProducido por Lic. Pedro Baldera - BASA Productions\n"
                        f"Genero: {o.get('genero')} | Instrumentacion: {', '.join(o.get('instrumentos', [])[:8])}\n"
                        f"Suscribete al canal oficial: {OFFICIAL_YOUTUBE_CHANNEL}\n"
                        f"#LicPedroBaldera #BASAProductions #MusicaDominicana #AIStudio"
                    )
                    break

        pub_title = st.text_input("Titulo del Estreno (YouTube / Spotify / Redes)", value=default_pub_t, key="ui_pub_title")
        pub_artist = st.text_input("Canal / Artista Oficial", value="Lic. Pedro Baldera - BASA Productions", key="ui_pub_artist")
        pub_lyrics = st.text_area("Descripcion SEO + Letra + Hashtags para YouTube y Redes", value=default_pub_l, height=160, key="ui_pub_lyrics")

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            plat = st.multiselect(
                "Plataformas de Distribucion",
                [
                    f"YouTube ({OFFICIAL_YOUTUBE_HANDLE})",
                    "Emisora Radio & TV BASA 24/7",
                    "Spotify",
                    "Apple Music",
                    "TikTok",
                    "Instagram / Facebook Reels",
                    "BASA Cinema / Netflix Indie",
                ],
                default=[f"YouTube ({OFFICIAL_YOUTUBE_HANDLE})", "Emisora Radio & TV BASA 24/7", "Spotify", "TikTok"],
            )
        with col_p2:
            isrc = st.text_input("Codigo ISRC", value=f"DO-BASA-{datetime.now().strftime('%y%m%d%H')}")
            upc = st.text_input("Codigo UPC / EAN", value=f"8899{datetime.now().strftime('%y%m%d%M')}")
        with col_p3:
            fecha = st.date_input("Fecha de Estreno", value=datetime.now().date())
            precio = st.selectbox(
                "Licencia / Monetizacion",
                [
                    "Monetizacion Oficial YouTube @Lic.PedroBaldera",
                    "Streaming Global (Spotify / Apple / BASA)",
                    "Venta Directa / Licencia Exclusiva",
                    "Promocional Libre BASA",
                ],
            )

        c_yt1, c_yt2 = st.columns(2)
        with c_yt1:
            if st.button("🚀 Publicar y Registrar Lanzamiento Oficial", type="primary", use_container_width=True):
                if not consent:
                    st.error("Debe firmar contrato legal primero (1 sola vez).")
                else:
                    init_dirs()
                    log = _load_json(RELEASES_FILE, [])
                    if not isinstance(log, list):
                        log = []
                    entry = {
                        "id": str(uuid.uuid4())[:8],
                        "title": pub_title,
                        "artist": pub_artist,
                        "youtube_channel": OFFICIAL_YOUTUBE_CHANNEL,
                        "platforms": plat,
                        "isrc": isrc,
                        "upc": upc,
                        "fecha": str(fecha),
                        "modelo": precio,
                        "lyrics": pub_lyrics,
                        "propiedad": consent.get("propiedad", ""),
                        "usuario": usuario,
                        "created_at": datetime.now().isoformat(),
                    }
                    log.append(entry)
                    _save_json(RELEASES_FILE, log)
                    st.success(f"✅ Estreno registrado y listo para {OFFICIAL_YOUTUBE_CHANNEL} y plataformas.")
                    st.markdown(f"👉 **[Ir directo a YouTube Studio de @Lic.PedroBaldera para subir el archivo]({OFFICIAL_YOUTUBE_CHANNEL})**")
                    st.json(entry)

        with c_yt2:
            if obra_obj_sel:
                zip_yt = crear_paquete_obra_zip(obra_obj_sel, pub_title)
                with open(zip_yt, "rb") as fyt:
                    st.download_button(
                        "📦 Descargar Kit Listo para Subir a YouTube & Spotify (ZIP)",
                        fyt.read(),
                        file_name=zip_yt.name,
                        mime="application/zip",
                        use_container_width=True,
                    )

        if RELEASES_FILE.exists():
            try:
                st.markdown("**Historial de Lanzamientos Oficiales:**")
                st.dataframe(_load_json(RELEASES_FILE, []), use_container_width=True)
            except Exception:
                pass

    # ========================================================================
    # TAB 5: HISTORICO COMPLETO (GUARDAR, DESCARGAR, PUBLICAR O VENDER)
    # ========================================================================
    with tab5:
        st.subheader("📚 Historico Completo de Producciones — Guardar, Descargar, Publicar o Vender")
        hist = _load_json(HISTORY_FILE, {})
        mis_temas = hist.get(usuario, []) if isinstance(hist, dict) else []
        ventas = _load_json(SALES_CATALOG_FILE, [])
        if not isinstance(ventas, list):
            ventas = []

        st.write(
            f"**Usuario:** {usuario} | **Total Obras Producidas:** {len(mis_temas)} | "
            f"**Propiedad Legal:** {consent.get('propiedad', 'Sin contrato') if consent else 'Sin contrato'}"
        )

        if not mis_temas:
            st.info("Aun no tienes producciones en el historico. Crea una en la Pestana 1 o 2.")
        else:
            for t in reversed(mis_temas):
                if not isinstance(t, dict):
                    continue
                t_id = t.get("id", str(uuid.uuid4())[:6])
                t_title = t.get("titulo", "Sin titulo")
                t_genero = t.get("genero", "")
                t_fecha = str(t.get("created_at", ""))[:16]
                t_prop = t.get("propiedad", "")

                with st.expander(f"🎼 {t_fecha} — {t_title} [{t_genero}] | {t_prop}"):
                    st.write(f"**Formato:** {t.get('formato')} | **Voz:** {t.get('voz')} | **Canal:** {OFFICIAL_YOUTUBE_CHANNEL}")
                    st.text_area("Letra / Guion Guardado", t.get("letra", ""), height=100, key=f"lyr_{t_id}", disabled=True)

                    # Reproducir archivos asociados
                    for idx_f, fpath in enumerate(t.get("archivos", [])):
                        p = Path(fpath)
                        if p.exists() and p.is_file():
                            if p.suffix.lower() in [".mp3", ".wav"]:
                                st.caption(f"Audio: {p.name}")
                                st.audio(str(p))
                            elif p.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                                st.image(str(p), width=260)

                    # Acciones comerciales: Descargar Paquete, Enviar a Emisora, Poner en Venta
                    ca1, ca2, ca3 = st.columns(3)
                    with ca1:
                        z_obra = crear_paquete_obra_zip(t, t_title)
                        with open(z_obra, "rb") as fzo:
                            st.download_button(
                                "⬇ Descargar Obra Completa (ZIP)",
                                fzo.read(),
                                file_name=z_obra.name,
                                mime="application/zip",
                                key=f"dl_pack_{t_id}",
                                use_container_width=True,
                            )
                    with ca2:
                        if st.button("📻 Enviar a Emisora Radio 24/7", key=f"rad_{t_id}", use_container_width=True):
                            pl = _load_json(RADIO_PLAYLIST_FILE, [])
                            if not isinstance(pl, list):
                                pl = []
                            pl.append(
                                {
                                    "id": t_id,
                                    "titulo": t_title,
                                    "artista": "Lic. Pedro Baldera - BASA Productions",
                                    "genero": t_genero,
                                    "archivos": t.get("archivos", []),
                                    "youtube": OFFICIAL_YOUTUBE_CHANNEL,
                                    "agregado_en": datetime.now().isoformat(),
                                }
                            )
                            _save_json(RADIO_PLAYLIST_FILE, pl)
                            st.success("Enviada a la parrilla en vivo de la Emisora BASA.")
                    with ca3:
                        precio_venta = st.number_input("Precio Venta (USD)", min_value=5.0, max_value=50000.0, value=49.0, step=5.0, key=f"prc_{t_id}")
                        if st.button("💰 Publicar para Venta / Licencia", key=f"sell_{t_id}", use_container_width=True):
                            ventas.append(
                                {
                                    "id_venta": str(uuid.uuid4())[:8],
                                    "obra_id": t_id,
                                    "titulo": t_title,
                                    "genero": t_genero,
                                    "precio_usd": precio_venta,
                                    "vendedor": "BASA Productions - Lic. Pedro Baldera",
                                    "propiedad": t_prop,
                                    "fecha": datetime.now().isoformat(),
                                }
                            )
                            _save_json(SALES_CATALOG_FILE, ventas)
                            st.success(f"Obra '{t_title}' listada en Tienda BASA por USD ${precio_venta:,.2f}.")

        st.divider()
        st.subheader("💼 Catalogo de Obras en Venta y Licenciamiento BASA")
        if ventas:
            st.dataframe(ventas, use_container_width=True)
        else:
            st.info("Aun no hay obras listadas en el catalogo de ventas.")

    # ========================================================================
    # TAB 6: CONSOLA WEBAUDIO EN VIVO
    # ========================================================================
    with tab6:
        st.subheader("🎛️ Consola WebAudio en Vivo & Mezclador Multipista")
        st.caption(
            "Haz clic dentro del panel antes de pulsar Reproducir para activar el motor Web Audio del navegador."
        )
        if HTML_STUDIO_PATH.exists():
            html_code = HTML_STUDIO_PATH.read_text(encoding="utf-8")
            components.html(html_code, height=880, scrolling=True)
        else:
            st.info(
                "Coloca el archivo `studio_audio.html` junto a `app.py` para usar tambien el sintetizador WebAudio interactivo en vivo."
            )

    # ========================================================================
    # TAB 7: AUTO-DESARROLLO & MODULOS
    # ========================================================================
    with tab7:
        st.subheader("🧩 Auto-Desarrollo & Registro Dinamico de Modulos BASA")
        st.caption(
            "Instala y registra nuevos modulos de desarrollo en caliente dentro de la arquitectura BASA sin reiniciar."
        )
        modulos = _load_json(MODULES_FILE, [])
        if not isinstance(modulos, list):
            modulos = []

        cm1, cm2 = st.columns([1.2, 1])
        with cm1:
            mod_nombre = st.text_input("Nombre del Nuevo Modulo", placeholder="Ej: Generador de Guiones Telenovela 5K")
            mod_cat = st.selectbox("Categoria", ["Musica & Audio", "Cine & Series 5K", "Emisora & YouTube", "Ventas & Licencias"])
            mod_prompt = st.text_area("Regla / Capacidad del Modulo", placeholder="Describe que hace este nuevo desarrollo...")
            if st.button("🚀 Instalar e Implementar Modulo", type="primary"):
                if not is_admin:
                    st.error("Se requiere PIN Admin para instalar nuevos modulos.")
                elif not mod_nombre.strip():
                    st.warning("Escriba un nombre para el modulo.")
                else:
                    nuevo_mod = {
                        "id": str(uuid.uuid4())[:8],
                        "nombre": mod_nombre.strip(),
                        "categoria": mod_cat,
                        "capacidad": mod_prompt.strip(),
                        "estado": "Activo 100/100",
                        "instalado_en": datetime.now().isoformat(),
                    }
                    modulos.append(nuevo_mod)
                    _save_json(MODULES_FILE, modulos)
                    st.success(f"Modulo '{mod_nombre}' instalado y activo en BASA v13.")
                    st.rerun()

        with cm2:
            st.markdown("**Modulos Instalados en el Nucleo BASA:**")
            if not modulos:
                st.info("Nucleo base activo (Radar 10s, Emisora 24/7, YouTube @Lic.PedroBaldera, Visual 5K, Tienda BASA).")
            else:
                for m in reversed(modulos):
                    with st.container(border=True):
                        st.markdown(f"**{m.get('nombre')}** (`{m.get('estado')}`)")
                        st.caption(f"{m.get('categoria')} · {m.get('capacidad')}")

    st.divider()
    st.caption(
        f"BASA v13 - (c) Pedro Anibal Baldera Rondon - BASA Productions | Emisora 24/7 & Canal Oficial: {OFFICIAL_YOUTUBE_CHANNEL}"
    )


if __name__ == "__main__":
    main()
