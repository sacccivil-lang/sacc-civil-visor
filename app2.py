import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- Configuración de página ---
st.set_page_config(page_title="SACC-CIVIL - Visor de Base de Datos", layout="wide")
st.title("📊 SACC-CIVIL / INFORMACIÓN UNIFICADA")

# --- Cache de lectura ---
@st.cache_data(ttl=604800)
def cargar_excel(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    df = pd.read_excel(url, sheet_name=0)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    return df, fecha

# --- Selección del programa ---
st.subheader("🎓 Selecciona el programa que deseas consultar")

programa = st.selectbox(
    "Elige la base de datos:",
    ["-- Seleccionar --", "Maestría", "Doctorado"]
)

sheet_ids = {
    "Doctorado": "12JOAshO8u1nX-DDNPxxsLmEHKpA4SCGh",
    "Maestría": "1t4sMTc-ODsNb0OG2T8Zo3WFx6TIKIR41"
}

# --- Refrescar datos ---
if st.button("🔄 Refrescar datos (forzar actualización)"):
    st.cache_data.clear()
    st.success("Datos refrescados. Vuelve a seleccionar el programa para recargar.")

if programa != "-- Seleccionar --":
    try:
        df, fecha_act = cargar_excel(sheet_ids[programa])
        st.success(f"✅ Base de datos cargada: **{programa}**")
        st.info(f"📅 Última actualización: **{fecha_act}**")
    except Exception as e:
        st.error(f"❌ Error al cargar el archivo: {e}")
else:
    st.stop()

# =====================================================================
# --- CONSULTA Y BÚSQUEDA ---
# =====================================================================

st.subheader("🔍 Buscar registros")

columnas = ["(Todas las columnas)"] + list(df.columns)
columna_sel = st.selectbox("Selecciona una columna para buscar:", columnas)
query = st.text_input("Introduce palabra o frase para buscar:")

if query:
    if columna_sel == "(Todas las columnas)":
        resultados = df[df.apply(lambda r: r.astype(str).str.contains(query, case=False, na=False).any(), axis=1)]
    else:
        resultados = df[df[columna_sel].astype(str).str.contains(query, case=False, na=False)]
else:
    resultados = df

st.write(f"🔹 Registros encontrados: {len(resultados)}")

# =====================================================================
# --- TABLA CON SELECCIÓN DE FILA AUTOMÁTICA ---
# =====================================================================

st.subheader("📄 Resultados")

# Reset index para que la tabla no pierda filas
resultados_display = resultados.reset_index(drop=True)

selection = st.data_editor(
    resultados_display,
    use_container_width=True,
    hide_index=True,
    disabled=True,
    selection_mode="single-row",
    key="tabla_resultados"
)

# Determinar si hay selección
selected_rows = selection.get("selection", {}).get("rows", [])

# =====================================================================
# --- DESPLIEGUE AUTOMÁTICO DEL DETALLE ---
# =====================================================================

if selected_rows:
    fila = selected_rows[0]
    registro = resultados_display.loc[fila]

    st.subheader("📋 Detalle del registro seleccionado")
    st.json(registro.to_dict())

    # =================================================================
    # --- GENERAR PDF ---
    # =================================================================
    if st.button("📄 Generar reporte PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Resumen del registro seleccionado", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", size=11)

        for k, v in registro.items():
            texto = f"{k}: {str(v)}".replace("\n", " ")
            if len(texto) > 100:
                chunks = [texto[i:i+100] for i in range(0, len(texto), 100)]
                for chunk in chunks:
                    pdf.multi_cell(0, 8, chunk)
            else:
                pdf.multi_cell(0, 8, texto)

        pdf.output("reporte.pdf")

        with open("reporte.pdf", "rb") as f:
            st.download_button(
                "⬇️ Descargar PDF",
                f,
                file_name=f"reporte_seleccion.pdf",
                mime="application/pdf"
            )

# =====================================================================
# --- EXPORTAR RESULTADOS ---
# =====================================================================

st.subheader("🧾 Exportar resultados")

columnas_export = st.multiselect(
    "Selecciona las columnas que deseas exportar:",
    df.columns.tolist(),
    help="Puedes seleccionar varias columnas."
)

tipo_export = st.radio("Formato de exportación:", ["TXT", "CSV"], horizontal=True)

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
