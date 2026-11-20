import json
import sqlite3
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# -------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y ESTILOS BASA (ALTO CONTRASTE / TONOS SUAVES)
# -------------------------------------------------------------------
st.set_page_config(
    page_title="BASA Universal AI Studio | Producción Musical",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        /* Fondo general gris suave y texto negro de alto contraste */
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
        /* Tarjetas métricas */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-left: 5px solid #0284c7;
            padding: 14px 18px;
            border-radius: 10px;
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
        }
        /* Botones primarios azul cielo / contraste */
        .stButton > button[kind="primary"] {
            background-color: #0284c7;
            color: #ffffff !important;
            border: none;
            font-weight: 600;
            border-radius: 8px;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #0369a1;
        }
        .stButton > button[kind="secondary"] {
            background-color: #ffffff;
            color: #0f172a !important;
            border: 1px solid #94a3b8;
            font-weight: 600;
            border-radius: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

DB_PATH = Path("basa_music_projects.db")
HTML_MODULE_PATH = Path("studio_audio.html")


# -------------------------------------------------------------------
# CAPA DE PERSISTENCIA EN BASE DE DATOS (SQLITE)
# -------------------------------------------------------------------
def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS proyectos_musicales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                persona_artistica TEXT NOT NULL,
                genero TEXT NOT NULL,
                bpm INTEGER NOT NULL,
                duracion_seg INTEGER NOT NULL,
                modelo_ia TEXT NOT NULL,
                instrumentacion TEXT,
                letra TEXT,
                estado TEXT DEFAULT 'Maqueta',
                fecha_creacion TEXT NOT NULL
            )
            """
        )
        # Sembrar registros iniciales si la tabla está vacía
        cursor = conn.execute("SELECT COUNT(*) FROM proyectos_musicales")
        if cursor.fetchone()[0] == 0:
            proyectos_iniciales = [
                (
                    "El Lápiz Pesa Más que el Pico",
                    "El Forense de la Música",
                    "Merengue Típico (Perico Ripiao)",
                    138,
                    45,
                    "BASA-Típico-Engine",
                    "Acordeón, Güira Metálica, Tambora, Bajo",
                    "[Intro]\n¡Ay ombe! De Pimentel para el mundo entero...\n[Coro]\nEl lápiz pesa más que el pico y la pala,\ncuando la mente estudia y el alma no resbala.",
                    "Masterizado",
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                ),
                (
                    "Tardes de Aroma y Café",
                    "Aroma de Café",
                    "Bolero Clásico",
                    88,
                    60,
                    "BASA-Acústico-Bolero",
                    "Requinto, Guitarra Española, Bongó, Contrabajo",
                    "[Verso 1]\nEn el silencio tibio de la mañana,\nun sorbo de recuerdos abre la ventana.",
                    "En Producción",
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                ),
            ]
            conn.executemany(
                """
                INSERT INTO proyectos_musicales
                (titulo, persona_artistica, genero, bpm, duracion_seg, modelo_ia, instrumentacion, letra, estado, fecha_creacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                proyectos_iniciales,
            )
        conn.commit()


def cargar_proyectos() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT * FROM proyectos_musicales ORDER BY id DESC", conn
        )


def guardar_proyecto(
    titulo: str,
    persona: str,
    genero: str,
    bpm: int,
    duracion: int,
    modelo: str,
    instrumentos: str,
    letra: str,
    estado: str,
) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO proyectos_musicales
            (titulo, persona_artistica, genero, bpm, duracion_seg, modelo_ia, instrumentacion, letra, estado, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                titulo.strip(),
                persona,
                genero,
                int(bpm),
                int(duracion),
                modelo,
                instrumentos.strip(),
                letra.strip(),
                estado,
                datetime.now().strftime("%Y-%m-%d %H:%M"),
            ),
        )
        conn.commit()


def actualizar_estado_proyecto(proyecto_id: int, nuevo_estado: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE proyectos_musicales SET estado = ? WHERE id = ?",
            (nuevo_estado, proyecto_id),
        )
        conn.commit()


def eliminar_proyecto(proyecto_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM proyectos_musicales WHERE id = ?", (proyecto_id,))
        conn.commit()


def exportar_excel(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Catalogo_BASA_Studio")
    return buffer.getvalue()


# -------------------------------------------------------------------
# INICIALIZACIÓN DE BASE DE DATOS Y BARRA LATERAL
# -------------------------------------------------------------------
init_db()
df_proyectos = cargar_proyectos()

with st.sidebar:
    st.markdown("## 🎛️ BASA Universal Studio")
    st.caption("Suite de Producción Musical, Letras y Síntesis Audio")
    st.divider()

    vista_activa = st.radio(
        "Navegación del Módulo",
        options=[
            "🎹 Estudio de Producción IA",
            "📂 Gestión de Proyectos y Catálogo",
            "📥 Importar / Exportar Respaldos",
        ],
        index=0,
    )

    st.divider()
    st.markdown("### 📊 Resumen del Catálogo")
    st.metric("Pistas Registradas", len(df_proyectos))
    bpm_promedio = int(df_proyectos["bpm"].mean()) if not df_proyectos.empty else 0
    st.metric("Tempo Promedio (BPM)", f"{bpm_promedio} BPM")

    st.divider()
    st.info(
        "**Consejo de Audio:** Haz clic dentro del panel del estudio antes de pulsar **Reproducir** para habilitar el motor Web Audio del navegador."
    )


# -------------------------------------------------------------------
# VISTA 1: ESTUDIO DE PRODUCCIÓN IA (MÓDULO HTML EMBEBIDO)
# -------------------------------------------------------------------
if vista_activa == "🎹 Estudio de Producción IA":
    st.title("🎹 BASA Universal AI Studio — Consola de Creación")
    st.markdown(
        "Compón letras, configura instrumentación dominicana y latina, mezcla canales en vivo y descarga pistas en **WAV PCM**."
    )

    if HTML_MODULE_PATH.exists():
        html_content = HTML_MODULE_PATH.read_text(encoding="utf-8")
        components.html(html_content, height=880, scrolling=True)
    else:
        st.warning(
            f"No se encontró el archivo `{HTML_MODULE_PATH}` en la carpeta raíz. "
            "Guarda el código HTML generado previamente con el nombre `studio_audio.html` junto a `app.py`."
        )

    with st.expander("➕ Registro Rápido de Nueva Producción en la Base de Datos BASA"):
        with st.form("form_registro_rapido", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                titulo_in = st.text_input("Título de la Obra *", placeholder="Ej. Caminos de Pimentel")
                persona_in = st.selectbox(
                    "Sello / Alias Creativo",
                    ["El Forense de la Música", "Aroma de Café", "BASA Audio Visual"],
                )
            with col2:
                genero_in = st.selectbox(
                    "Género Musical",
                    [
                        "Merengue Típico (Perico Ripiao)",
                        "Bachata",
                        "Bolero Clásico",
                        "Salsa Dura",
                        "Merengue de Calle",
                        "Dembow",
                        "Ranchera",
                    ],
                )
                modelo_in = st.selectbox(
                    "Motor IA Utilizado",
                    [
                        "BASA-Audio-V10 Pro",
                        "BASA-Típico-Engine",
                        "BASA-Vocal-Master",
                        "BASA-Acústico-Bolero",
                    ],
                )
            with col3:
                bpm_in = st.number_input("Tempo (BPM)", min_value=60, max_value=200, value=130)
                duracion_in = st.number_input("Duración (segundos)", min_value=15, max_value=300, value=45)

            instrumentos_in = st.text_input(
                "Instrumentación Principal",
                value="Acordeón, Güira Metálica, Tambora, Bajo",
            )
            letra_in = st.text_area(
                "Letra Estructurada ([Intro], [Verso], [Coro], [Mambo])",
                height=140,
            )
            estado_in = st.selectbox("Estado del Proyecto", ["Maqueta", "En Producción", "Masterizado", "Publicado"])

            if st.form_submit_button("💾 Guardar Proyecto en Base de Datos", type="primary"):
                if not titulo_in.strip():
                    st.error("El título de la obra es obligatorio.")
                else:
                    guardar_proyecto(
                        titulo_in,
                        persona_in,
                        genero_in,
                        bpm_in,
                        duracion_in,
                        modelo_in,
                        instrumentos_in,
                        letra_in,
                        estado_in,
                    )
                    st.success(f"Proyecto '{titulo_in}' guardado correctamente.")
                    st.rerun()


# -------------------------------------------------------------------
# VISTA 2: GESTIÓN DE PROYECTOS Y CATÁLOGO
# -------------------------------------------------------------------
elif vista_activa == "📂 Gestión de Proyectos y Catálogo":
    st.title("📂 Gestión de Proyectos Musicales — Catálogo BASA")

    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1:
        busqueda = st.text_input("🔍 Buscar por título, letra o instrumento", "")
    with col_f2:
        filtro_alias = st.selectbox(
            "Filtrar por Alias",
            ["Todos"] + sorted(df_proyectos["persona_artistica"].unique().tolist()),
        )
    with col_f3:
        filtro_estado = st.selectbox(
            "Filtrar por Estado",
            ["Todos", "Maqueta", "En Producción", "Masterizado", "Publicado"],
        )

    df_filtrado = df_proyectos.copy()
    if busqueda.strip():
        mask = (
            df_filtrado["titulo"].str.contains(busqueda, case=False, na=False)
            | df_filtrado["letra"].str.contains(busqueda, case=False, na=False)
            | df_filtrado["instrumentacion"].str.contains(busqueda, case=False, na=False)
        )
        df_filtrado = df_filtrado[mask]
    if filtro_alias != "Todos":
        df_filtrado = df_filtrado[df_filtrado["persona_artistica"] == filtro_alias]
    if filtro_estado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["estado"] == filtro_estado]

    st.dataframe(
        df_filtrado[
            [
                "id",
                "titulo",
                "persona_artistica",
                "genero",
                "bpm",
                "duracion_seg",
                "estado",
                "fecha_creacion",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    if not df_filtrado.empty:
        st.subheader("🛠️ Inspección y Control de Obra Seleccionada")
        opciones = {
            f"#{row['id']} — {row['titulo']} ({row['genero']})": row["id"]
            for _, row in df_filtrado.iterrows()
        }
        seleccion = st.selectbox("Selecciona una producción:", list(opciones.keys()))
        id_sel = opciones[seleccion]
        fila = df_filtrado[df_filtrado["id"] == id_sel].iloc[0]

        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"**Instrumentación:** {fila['instrumentacion']}")
            st.text_area("Letra y Estructura", value=fila["letra"], height=200, disabled=True)
        with c2:
            st.markdown(f"**Alias:** {fila['persona_artistica']}")
            st.markdown(f"**Motor IA:** {fila['modelo_ia']}")
            st.markdown(f"**Tempo / Duración:** {fila['bpm']} BPM | {fila['duracion_seg']}s")

            nuevo_estado = st.selectbox(
                "Actualizar Estado",
                ["Maqueta", "En Producción", "Masterizado", "Publicado"],
                index=["Maqueta", "En Producción", "Masterizado", "Publicado"].index(fila["estado"]),
            )
            if st.button("✅ Aplicar Cambio de Estado", type="primary", use_container_width=True):
                actualizar_estado_proyecto(int(id_sel), nuevo_estado)
                st.success("Estado actualizado.")
                st.rerun()

            if st.button("🗑️ Eliminar Proyecto", type="secondary", use_container_width=True):
                eliminar_proyecto(int(id_sel))
                st.warning("Proyecto eliminado de la base de datos.")
                st.rerun()


# -------------------------------------------------------------------
# VISTA 3: IMPORTAR / EXPORTAR RESPALDOS (JSON Y EXCEL)
# -------------------------------------------------------------------
elif vista_activa == "📥 Importar / Exportar Respaldos":
    st.title("📥 Importación desde Estudio HTML y Exportación de Catálogo")

    col_imp, col_exp = st.columns(2)

    with col_imp:
        st.subheader("⬆️ Importar Proyecto JSON desde el Estudio")
        st.markdown(
            "Sube el archivo `.json` descargado desde el botón **Exportar JSON** de la consola musical para registrarlo en SQLite."
        )
        archivo_json = st.file_uploader("Seleccionar archivo .json", type=["json"])
        if archivo_json is not None:
            try:
                datos = json.load(archivo_json)
                # Soporta tanto un objeto único como una lista de pistas
                registros = datos if isinstance(datos, list) else [datos]
                st.write(f"Se detectaron **{len(registros)}** pista(s) en el archivo.")
                if st.button("📥 Importar a Base de Datos BASA", type="primary"):
                    for item in registros:
                        guardar_proyecto(
                            titulo=item.get("title", item.get("titulo", "Pista Importada")),
                            persona=item.get("artist", "El Forense de la Música"),
                            genero=item.get("genre", item.get("genero", "Merengue Típico")),
                            bpm=int(item.get("bpm", 128)),
                            duracion=int(item.get("duration", 45)),
                            modelo=item.get("model", "BASA-Audio-V10 Pro"),
                            instrumentos=", ".join(item.get("instruments", []))
                            if isinstance(item.get("instruments"), list)
                            else str(item.get("instruments", "")),
                            letra=item.get("lyrics", item.get("letra", "")),
                            estado="Maqueta",
                        )
                    st.success("Importación completada con éxito.")
                    st.rerun()
            except Exception as e:
                st.error(f"Error al procesar el archivo JSON: {e}")

    with col_exp:
        st.subheader("⬇️ Descargar Catálogo Completo")
        st.markdown(
            "Exporta todo el inventario de canciones, letras, tiempos y metadatos para registro autoral o distribución."
        )
        if not df_proyectos.empty:
            excel_bytes = exportar_excel(df_proyectos)
            st.download_button(
                label="📊 Descargar Catálogo en Excel (.xlsx)",
                data=excel_bytes,
                file_name=f"Catalogo_BASA_Studio_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )

            json_bytes = df_proyectos.to_json(orient="records", indent=2, force_ascii=False).encode("utf-8")
            st.download_button(
                label="🧾 Descargar Respaldo Integral (.json)",
                data=json_bytes,
                file_name=f"Respaldo_BASA_Studio_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True,
            )
