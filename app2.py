import streamlit as st
import pandas as pd
from datetime import datetime
import re

# 📌 NUEVOS imports para ReportLab (PDF estable)
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
import io

# ==========================================================
#  🔧 FUNCIONES PARA LIMPIAR TEXTO
# ==========================================================

def limpiar_texto(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    return s.encode("ascii", "ignore").decode()

def texto_seguro(s: str) -> str:
    s = limpiar_texto(s)
    s = s.replace("\xa0", " ")
    s = s.replace("\u200b", "")
    s = s.replace("\u2013", "-")
    s = s.replace("\u2014", "-")
    s = s.strip()
    return s if s else "[Texto eliminado]"

# ==========================================================
#  🖥️ CONFIGURACIÓN DE PÁGINA
# ==========================================================

st.set_page_config(page_title="SACC-CIVIL - Visor de Base de Datos", layout="wide")
st.title("📊 SACC-CIVIL / INFORMACIÓN UNIFICADA")

@st.cache_data(ttl=604800)
def cargar_excel(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    df = pd.read_excel(url, sheet_name=0)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    return df, fecha

st.subheader("🎓 Selecciona el programa que deseas consultar")

programa = st.selectbox(
    "Elige la base de datos:",
    ["-- Seleccionar --", "Maestría", "Doctorado"]
)

sheet_ids = {
    "Doctorado": "12JOAshO8u1nX-DDNPxxsLmEHKpA4SCGh",
    "Maestría": "1t4sMTc-ODsNb0OG2T8Zo3WFx6TIKIR41"
}

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

# ==========================================================
#  🔎 BÚSQUEDA Y RESULTADOS
# ==========================================================

if "df" in locals() or "df" in globals():
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
    st.dataframe(resultados, use_container_width=True)

    if not resultados.empty:

        # ======================================================
        #  📄 DETALLE DEL REGISTRO
        # ======================================================
        st.subheader("📋 Ver detalle de un registro")

        columna_visible = "NOMBRE COMPLETO"

        if columna_visible not in resultados.columns:
            st.error(f"⚠️ La columna '{columna_visible}' no existe en la base de datos.")
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

        # ======================================================
        #  🧾 EXPORTACIONES
        # ======================================================
        st.subheader("🧾 Exportar resultados (múltiples columnas)")
        
        columnas_export = st.multiselect(
            "Selecciona las columnas que deseas exportar:",
            df.columns.tolist(),
            help="Puedes elegir una o varias columnas."
        )

        tipo_export = st.radio(
            "Formato de exportación:",
            ["TXT", "CSV"],
            horizontal=True
        )

        if st.button("💾 Exportar"):
            if not columnas_export:
                st.warning("⚠️ Selecciona al menos una columna para exportar.")
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

        # ======================================================
        #  📄 GENERACIÓN DEL PDF (NUEVO - REPORTLAB 100% ESTABLE)
        # ======================================================
        st.subheader("📄 Generar reporte PDF del registro seleccionado")

        if st.button("📄 Generar reporte PDF"):
            
            dict_registro = registro.to_dict()

            # Crear buffer en memoria
            buffer = io.BytesIO()

            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                title="Detalle del Registro"
            )

            styles = getSampleStyleSheet()
            elementos = []

            titulo = Paragraph("<b>Detalle del Registro</b>", styles["Title"])
            elementos.append(titulo)
            elementos.append(Spacer(1, 12))

            # Construir tabla
            tabla_data = [["Campo", "Valor"]]
            for k, v in dict_registro.items():
                tabla_data.append([texto_seguro(str(k)), texto_seguro(str(v))])

            tabla = Table(tabla_data, colWidths=[150, 350])

            tabla.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E86C1")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
            ]))

            elementos.append(tabla)

            doc.build(elementos)
            buffer.seek(0)

            st.download_button(
                "⬇️ Descargar PDF del registro",
                buffer,
                file_name=f"registro_{idx_real}.pdf",
                mime="application/pdf"
            )

    else:
        st.warning("⚠️ No se encontraron resultados con ese criterio de búsqueda.")
