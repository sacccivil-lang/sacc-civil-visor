import streamlit as st
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
import io

# -------------------------
# CONFIGURACIÓN INICIAL
# -------------------------
st.set_page_config(page_title="SACC-CIVIL - Visor de Base de Datos", layout="wide")
st.title("📊 SACC-CIVIL / INFORMACIÓN UNIFICADA")

# -------------------------
# FUNCIÓN PARA GENERAR PDF
# -------------------------
def generar_pdf_registro(registro_dict):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        title="Detalle del Registro"
    )

    styles = getSampleStyleSheet()
    elementos = []

    # Título
    titulo = Paragraph("<b>Detalle del Registro</b>", styles['Title'])
    elementos.append(titulo)
    elementos.append(Spacer(1, 12))

    # Convertir registro a tabla
    tabla_data = [["Campo", "Valor"]]
    for k, v in registro_dict.items():
        tabla_data.append([str(k), str(v)])

    # Tabla
    tabla = Table(tabla_data, colWidths=[150, 350])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E86C1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elementos.append(tabla)
    doc.build(elementos)

    buffer.seek(0)
    return buffer


# -------------------------
# CARGA DE ARCHIVO
# -------------------------
uploaded_file = st.file_uploader("Subir base de datos (CSV o Excel)", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)

    st.success("Archivo cargado correctamente.")
    st.dataframe(df, use_container_width=True)

    # -------------------------
    # SELECCIÓN DE COLUMNAS A EXPORTAR
    # -------------------------
    st.subheader("📌 Selecciona hasta 4 columnas para exportación")
    columnas_seleccion = st.multiselect(
        "Elige columnas:",
        options=df.columns.tolist(),
        max_selections=4
    )

    # -------------------------
    # SELECCIÓN DE REGISTRO PARA VER DETALLE
    # -------------------------
    st.subheader("🔍 Ver detalle de un registro")

    indice = st.number_input(
        "Selecciona un índice de registro:",
        min_value=0,
        max_value=len(df)-1,
        step=1,
        format="%d"
    )

    registro = df.iloc[indice].to_dict()

    st.write("### 📝 Resumen del registro seleccionado")
    st.json(registro)

    # -------------------------
    # GENERAR PDF CON REPORTLAB
    # -------------------------
    st.subheader("📄 Exportar el registro a PDF (sin errores)")

    if st.button("Generar PDF del registro"):
        pdf_bytes = generar_pdf_registro(registro)
        st.download_button(
            label="📥 Descargar PDF",
            data=pdf_bytes,
            file_name="registro_sacc.pdf",
            mime="application/pdf"
        )

    # -------------------------
    # EXPORTACIÓN DE LAS COLUMNAS SELECCIONADAS
    # -------------------------
    st.subheader("📤 Exportar columnas seleccionadas")

    if columnas_seleccion:
        df_export = df[columnas_seleccion]

        st.dataframe(df_export, use_container_width=True)

        csv = df_export.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name="exportacion_columnas.csv",
            mime="text/csv"
        )
    else:
        st.info("Elige entre 1 y 4 columnas para activar la exportación.")
