import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import unicodedata
import re  # ← necesario para limpiar caracteres

# ==========================================================
# 🔧 FUNCIÓN PARA NORMALIZAR (búsqueda sin acentos)
# ==========================================================
def normalizar(texto):
    """Convierte texto a minúsculas y elimina acentos."""
    if not isinstance(texto, str):
        texto = str(texto)
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto

# ==========================================================
# 🔧 LECTOR DIRECTO DE GOOGLE SHEETS (CSV)
# ==========================================================
@st.cache_data(ttl=604800)
def cargar_gsheet(sheet_id, gid=0):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    df = pd.read_csv(url)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    return df, fecha

# ==========================================================
# CONFIGURACIÓN STREAMLIT
# ==========================================================
st.set_page_config(page_title="SACC-CIVIL - Visor de Base de Datos", layout="wide")
st.title("📊 SACC-CIVIL / INFORMACIÓN UNIFICADA 📊")

# Selección del programa
st.subheader("🎓 Selecciona el programa que deseas consultar")

programa = st.selectbox(
    "Elige la base de datos:",
    ["-- Seleccionar --", "Maestría", "Doctorado"]
)

# Nuevos archivos de Google Sheets
sheet_ids = {
    "Maestría": {"id": "1ABwQL9xIio_HNo6fMKwbEsaz49DrksfvAzZ0SuJCFrw", "gid": 0},
    "Doctorado": {"id": "1JchfOLVMr9GXBNldagKPSrsChmy_zx9885eE5PZl6ic", "gid": 0}
}

# Botón refrescar
if st.button("🔄 Refrescar datos (forzar actualización)"):
    st.cache_data.clear()
    st.success("Datos refrescados. Vuelve a seleccionar el programa para recargar.")

# Cargar datos
if programa != "-- Seleccionar --":
    try:
        df, fecha_act = cargar_gsheet(
            sheet_ids[programa]["id"],
            sheet_ids[programa]["gid"]
        )
        st.success(f"✅ Base de datos cargada: **{programa}**")
        st.info(f"📅 Última actualización: **{fecha_act}**")
    except Exception as e:
        st.error(f"❌ Error al cargar el archivo: {e}")
else:
    st.stop()

# ==========================================================
# BÚSQUEDA Y VISUALIZACIÓN
# ==========================================================
if "df" in locals() or "df" in globals():
    st.subheader("🔍 Buscar registros")

    columnas = ["(Todas las columnas)"] + list(df.columns)
    columna_sel = st.selectbox("Selecciona una columna para buscar:", columnas)
    query = st.text_input("Introduce palabra o frase para buscar:")

    # Búsqueda sin acentos
    if query:
        query_norm = normalizar(query)

        if columna_sel == "(Todas las columnas)":
            resultados = df[
                df.apply(
                    lambda fila: any(
                        query_norm in normalizar(str(valor))
                        for valor in fila.values
                    ),
                    axis=1
                )
            ]
        else:
            resultados = df[
                df[columna_sel].astype(str).apply(
                    lambda x: query_norm in normalizar(x)
                )
            ]
    else:
        resultados = df

    st.write(f"🔹 Registros encontrados: {len(resultados)}")
    st.dataframe(resultados, use_container_width=True)

    # Si hay resultados
    if not resultados.empty:

        # ============================================
        #     DETALLE DEL REGISTRO
        # ============================================
        st.subheader("📋 Ver detalle de un registro")

        columna_visible = "NOMBRE COMPLETO"

        if columna_visible not in resultados.columns:
            st.error(f"⚠️ La columna '{columna_visible}' no existe en la base.")
        else:
            opciones = (
                resultados.index.astype(str) +
                " – " +
                resultados[columna_visible].astype(str)
            )

            eleccion = st.selectbox("Selecciona un registro:", opciones)
            idx_real = int(eleccion.split(" – ")[0])
            registro = resultados.loc[idx_real]

            st.json(registro.to_dict())

        # ============================================
        #      EXPORTAR COLUMNAS
        # ============================================
        st.subheader("🧾 Exportar resultados")

        columnas_export = st.multiselect(
            "Selecciona las columnas:",
            df.columns.tolist()
        )

        tipo_export = st.radio(
            "Formato:",
            ["TXT", "CSV"],
            horizontal=True
        )

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

        # ============================================
        #      PDF
        # ============================================
        st.subheader("📄 Generar PDF del registro")

        if st.button("📄 Generar PDF"):

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
                linea = linea.strip()
                if linea:
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
