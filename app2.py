import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import re  # ← necesario para limpiar caracteres

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
    st.dataframe(resultados, use_container_width=True)

    if not resultados.empty:

        # =====================================================================
        # --- DETALLE DEL REGISTRO (primero) ---
        # =====================================================================
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

        # =====================================================================
        # --- Exportar múltiples columnas ---
        # =====================================================================
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

        # =====================================================================
        # --- Generar PDF (DETALLE EXACTO + FIX DE ERRORES) ---
        # =====================================================================
        st.subheader("📄 Generar reporte PDF del registro seleccionado")

        if st.button("📄 Generar reporte PDF"):

            # Convertir registro a texto limpio
            texto_registro = ""
            for k, v in registro.items():
                texto_registro += f"{k}: {v}\n"

            # Crear PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
            pdf.set_font("DejaVu", "", 14)

            pdf.cell(0, 10, "Detalle del registro seleccionado", ln=True)
            pdf.ln(5)

            pdf.set_font("DejaVu", "", 11)

            # LINE-BY-LINE RENDERING SAFE MODE
            for linea in texto_registro.split("\n"):

                # 1. Eliminar caracteres invisibles / no imprimibles
                linea = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\xA0-\xFF]", "", str(linea))

                # 2. Tabulaciones → espacio
                linea = linea.replace("\t", " ")

                # 3. Evitar líneas sin espacios extremadamente largas
                if len(linea) > 120 and " " not in linea:
                    linea = linea[:120] + "..."

                linea = linea.strip()
                if linea:

                    try:
                        pdf.multi_cell(0, 8, linea)
                    except:
                        pdf.multi_cell(0, 8, "Texto no imprimible en este campo.")

            pdf.output("reporte.pdf")

            with open("reporte.pdf", "rb") as f:
                st.download_button(
                    "⬇️ Descargar PDF",
                    f,
                    file_name=f"reporte_{idx_real}.pdf",
                    mime="application/pdf"
                )

    else:
        st.warning("⚠️ No se encontraron resultados con ese criterio de búsqueda.")
