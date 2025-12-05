import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import unicodedata

# ==========================================================
# 🔧 FUNCIÓN PARA NORMALIZAR TEXTO (sin acentos)
# ==========================================================
def normalizar(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")

# ==========================================================
# 🔧 LECTOR DIRECTO DE GOOGLE SHEETS (CSV)
# ==========================================================
@st.cache_data(ttl=604800)
def cargar_gsheet(sheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    df = pd.read_csv(url)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    return df, fecha

# ==========================================================
# CONFIGURACIÓN STREAMLIT
# ==========================================================
st.set_page_config(page_title="SACC-CIVIL - Visor de Base de Datos", layout="wide")
st.title("📊 SACC-CIVIL / INFORMACIÓN UNIFICADA 📊")

st.subheader("🎓 Selecciona el programa")

programa = st.selectbox(
    "Elige la base de datos:",
    ["-- Seleccionar --", "Maestría", "Doctorado"]
)

# IDs REALES + GIDs REALES
sheet_ids = {
    "Maestría": {
        "id": "1ABwQL9xIio_HNo6fMKwbEsaz49DrksfvAzZ0SuJCFrw",
        "gid": 245806391
    },
    "Doctorado": {
        "id": "1JchfOLVMr9GXBNldagKPSrsChmy_zx9885eE5PZl6ic",
        "gid": 1721735316
    }
}

# Botón refrescar
if st.button("🔄 Refrescar datos"):
    st.cache_data.clear()
    st.success("Datos refrescados. Selecciona nuevamente el programa.")

# Cargar datos
if programa != "-- Seleccionar --":
    try:
        df, fecha_act = cargar_gsheet(
            sheet_ids[programa]["id"],
            sheet_ids[programa]["gid"]
        )
        st.success(f"✅ Base de datos cargada: {programa}")
        st.info(f"📅 Última actualización: {fecha_act}")
    except Exception as e:
        st.error(f"❌ Error al cargar el archivo: {e}")
        st.stop()
else:
    st.stop()

# ==========================================================
# 🔍 BÚSQUEDA
# ==========================================================
st.subheader("🔍 Buscar registros")
columnas = ["(Todas las columnas)"] + list(df.columns)
columna_sel = st.selectbox("Selecciona una columna:", columnas)
query = st.text_input("Introduce palabra o frase:")

if query:
    texto = normalizar(query)
    if columna_sel == "(Todas las columnas)":
        resultados = df[
            df.apply(lambda fila: any(texto in normalizar(str(v)) for v in fila.values), axis=1)
        ]
    else:
        resultados = df[
            df[columna_sel].astype(str).apply(lambda x: texto in normalizar(x))
        ]
else:
    resultados = df

st.write(f"🔹 Registros encontrados: {len(resultados)}")
st.dataframe(resultados, use_container_width=True)

# ==========================================================
# 📋 DETALLE DE REGISTRO
# ==========================================================
if not resultados.empty:
    st.subheader("📋 Ver detalle de un registro")

    columna_visible = "NOMBRE COMPLETO" if "NOMBRE COMPLETO" in resultados.columns else resultados.columns[0]

    opciones = resultados.index.astype(str) + " – " + resultados[columna_visible].astype(str)
    eleccion = st.selectbox("Selecciona un registro:", opciones)
    idx_real = int(eleccion.split(" – ")[0])
    registro = resultados.loc[idx_real]

    st.json(registro.to_dict())

    # ==========================================================
    # 🧾 EXPORTAR RESULTADOS
    # ==========================================================
    st.subheader("🧾 Exportar resultados (TXT o CSV)")

    columnas_export = st.multiselect("Selecciona columnas:", df.columns.tolist())
    tipo_export = st.radio("Formato:", ["TXT", "CSV"], horizontal=True)

    if st.button("💾 Exportar"):
        if not columnas_export:
            st.warning("⚠️ Selecciona al menos una columna.")
        else:
            df_export = resultados[columnas_export]

            if tipo_export == "TXT":
                contenido = df_export.to_csv(index=False, sep="\t")
                data = contenido.encode("utf-8")
                nombre_archivo = "export_resultados.txt"
                mime = "text/plain"
            else:
                contenido = df_export.to_csv(index=False)
                data = contenido.encode("utf-8")
                nombre_archivo = "export_resultados.csv"
                mime = "text/csv"

            st.download_button(
                f"⬇️ Descargar {nombre_archivo}",
                data,
                file_name=nombre_archivo,
                mime=mime
            )

    # ==========================================================
    # 📄 GENERAR PDF
    # ==========================================================
    st.subheader("📄 Generar PDF del registro seleccionado")

    if st.button("📄 Generar reporte PDF"):
        dict_registro = registro.to_dict()

        texto_limpio = ""
        for k, v in dict_registro.items():
            linea = f"{k}: {v}"
            linea = linea.encode("latin-1", "replace").decode("latin-1")
            texto_limpio += linea + "\n"

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Helvetica", size=14)
        pdf.cell(0, 10, "Detalle del registro seleccionado", ln=True)
        pdf.ln(5)
        pdf.set_font("Helvetica", size=11)

        for linea in texto_limpio.split("\n"):
            if linea.strip():
                try:
                    pdf.multi_cell(0, 8, linea)
                except:
                    pdf.multi_cell(0, 8, "[Texto no imprimible]")

        pdf.output("reporte.pdf")

        with open("reporte.pdf", "rb") as f:
            st.download_button(
                "⬇️ Descargar PDF",
                f,
                file_name=f"reporte_{idx_real}.pdf",
                mime="application/pdf"
            )

else:
    st.warning("⚠️ No se encontraron resultados.")
