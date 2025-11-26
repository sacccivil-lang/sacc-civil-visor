import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- Configuración de página ---
st.set_page_config(page_title="SACC-CIVIL - Visor de Base de Datos", layout="wide")
st.title("📊 SACC-CIVIL / INFORMACIÓN UNIFICADA")

# --- Cache de lectura (se actualiza cada semana = 604800 s) ---
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

# --- Botón para refrescar datos ---
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

# --- Si hay datos ---
if "df" in locals() or "df" in globals():

    st.subheader("🔍 Buscar registros")

    columnas = ["(Todas las columnas)"] + list(df.columns)
    columna_sel = st.selectbox("Selecciona una columna para buscar:", columnas)
    query = st.text_input("Introduce palabra o frase para buscar:")

    # --- Filtro de búsqueda ---
    if query:
        if columna_sel == "(Todas las columnas)":
            resultados = df[df.apply(lambda r: r.astype(str).str.contains(query, case=False, na=False).any(), axis=1)]
        else:
            resultados = df[df[columna_sel].astype(str).str.contains(query, case=False, na=False)]
    else:
        resultados = df

    st.write(f"🔹 Registros encontrados: {len(resultados)}")

    # 🔥 TABLA CON SELECCIÓN ACTIVADA
    selection = st.data_table(
        resultados,
        use_container_width=True,
        selection_mode="single-row",
        on_select="rerun"
    )

    # Si se seleccionó una fila, mostrar detalles
    registro = None
    if selection and "selection" in selection:
        selected_rows = selection["selection"]["rows"]

        if selected_rows:
            fila = selected_rows[0]   # índice relativo dentro de resultados
            registro = resultados.iloc[fila]

            st.subheader("📋 Ver detalle del registro seleccionado")
            st.json(registro.to_dict())

    # --- Exportar TXT ---
    if not resultados.empty:
        st.subheader("🧾 Exportar resultados a TXT")
        col_txt = st.selectbox("Selecciona la columna que deseas exportar:", df.columns)

        if st.button("💾 Exportar a TXT"):
            texto = "\n".join(resultados[col_txt].dropna().astype(str).tolist())
            file_name = f"export_{col_txt}.txt"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(texto)
            with open(file_name, "rb") as f:
                st.download_button(
                    f"⬇️ Descargar {file_name}",
                    f,
                    file_name=file_name,
                    mime="text/plain"
                )

    # --- Generar PDF SOLO SI HAY REGISTRO SELECCIONADO ---
    if registro is not None:
        st.subheader("📄 Generar reporte PDF del registro seleccionado")

        if st.button("📄 Generar PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Resumen del registro seleccionado", ln=True)
            pdf.ln(5)
            pdf.set_font("Arial", size=11)

            for k, v in registro.items():
                text = f"{k}: {str(v)}".replace("\n", " ")
                if len(text) > 100:
                    chunks = [text[i:i+100] for i in range(0, len(text), 100)]
                    for chunk in chunks:
                        pdf.multi_cell(0, 8, chunk)
                else:
                    pdf.multi_cell(0, 8, text)

            pdf.output("reporte.pdf")
            with open("reporte.pdf", "rb") as f:
                st.download_button(
                    "⬇️ Descargar PDF",
                    f,
                    file_name=f"reporte_{fila}.pdf",
                    mime="application/pdf"
                )
