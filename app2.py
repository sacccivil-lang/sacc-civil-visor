import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF

# --- Configuración de página ---
st.set_page_config(page_title="SACC-CIVIL - Visor de Base de Datos", layout="wide")

st.title("📊 SACC-CIVIL / INFORMACIÓN UNIFICADA")

# --- Cargar Google Sheets automáticamente ---
sheet_id = "12JOAshO8u1nX-DDNPxxsLmEHKpA4SCGh"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

try:
    df = pd.read_excel(sheet_url, sheet_name=0)
    st.success("✅ Archivo cargado automáticamente desde Google Sheets.")
except Exception as e:
    st.error(f"Error al cargar el archivo: {e}")

# --- Si hay datos ---
if 'df' in locals():
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
    st.dataframe(resultados, use_container_width=True)

    if not resultados.empty:
        # ---------------------------------------------------------------------
        # --- Exportar múltiples columnas ---
        # ---------------------------------------------------------------------
        st.subheader("🧾 Exportar resultados (múltiples columnas)")

        columnas_export = st.multiselect(
            "Selecciona las columnas que deseas exportar:",
            df.columns.tolist(),
            help="Puedes elegir una o varias columnas."
        )

        tipo_export = st.radio("Formato de exportación:", ["TXT", "CSV"], horizontal=True)

        if st.button("💾 Exportar"):
            if not columnas_export:
                st.warning("⚠️ Selecciona al menos una columna para exportar.")
            else:
                df_export = resultados[columnas_export]

                if tipo_export == "TXT":
                    texto = df_export.to_csv(index=False, sep="\t")
                    file_name = "export_resultados.txt"
                    mime_type = "text/plain"
                    data_to_download = texto.encode("utf-8")

                elif tipo_export == "CSV":
                    file_name = "export_resultados.csv"
                    mime_type = "text/csv"
                    data_to_download = df_export.to_csv(index=False).encode("utf-8")

                st.download_button(
                    f"⬇️ Descargar {file_name}",
                    data_to_download,
                    file_name=file_name,
                    mime=mime_type
                )

        # --- Detalle ---
        st.subheader("📋 Ver detalle de un registro")
        selected = st.selectbox("Selecciona un registro:", resultados.index)
        registro = resultados.loc[selected]
        st.json(registro.to_dict())

        # --- Gráfica ---
        st.subheader("📈 Distribución por columna seleccionada")
        col = st.selectbox("Selecciona una columna para graficar:", df.columns)
        if pd.api.types.is_numeric_dtype(df[col]):
            chart = px.histogram(df, x=col, nbins=20, title=f"Distribución de {col}")
        else:
            chart = px.bar(df[col].value_counts().reset_index(),
                           x="index", y=col,
                           title=f"Frecuencia de {col}")
        st.plotly_chart(chart, use_container_width=True)

        # --- PDF ---
        if st.button("📄 Generar reporte PDF"):
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
                    chunks = [text[i:i + 100] for i in range(0, len(text), 100)]
                    for chunk in chunks:
                        pdf.multi_cell(0, 8, chunk)
                else:
                    pdf.multi_cell(0, 8, text)

            pdf.output("reporte.pdf")
            with open("reporte.pdf", "rb") as f:
                st.download_button(
                    "⬇️ Descargar PDF",
                    f,
                    file_name=f"reporte_{selected}.pdf",
                    mime="application/pdf"
                )
    else:
        st.warning("⚠️ No se encontraron resultados con ese criterio de búsqueda.")
