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

    # ============================================================
    # TABLA INTERACTIVA CON SELECCIÓN DE FILA (st.data_editor)
    # ============================================================
    st.subheader("📋 Resultados (haz clic en una fila para ver detalle)")

    # muéstralo no-editable para evitar que la estructura cambie si el usuario edita
    editor_response = st.data_editor(
        resultados,
        use_container_width=True,
        hide_index=False,
        num_rows="dynamic",
        disabled=True  # deshabilitado para evitar ediciones que cambien la estructura devuelta
    )

    # ============================================================
    # EXTRAE de forma robusta la(s) fila(s) seleccionada(s)
    # ============================================================
    filas_seleccionadas = []  # posiciones (0-based) dentro de 'resultados'

    # 1) Si viene un dict con "selection" -> "rows"
    if isinstance(editor_response, dict):
        sel = editor_response.get("selection") or editor_response.get("selected_rows") or {}
        # sel puede ser dict o lista
        if isinstance(sel, dict):
            rows = sel.get("rows")  # caso esperado: lista de ints o lista de dicts
            if rows is None:
                # a veces la clave es 'rows' dentro de 'selection' pero con otro nesting
                rows = sel.get("row_ids") or sel.get("row")
            if isinstance(rows, list):
                # si cada elemento es dict, intentar extraer pos
                if rows and isinstance(rows[0], dict):
                    for r in rows:
                        # intentar diversas claves posibles
                        if "row" in r:
                            filas_seleccionadas.append(int(r["row"]))
                        elif "index" in r:
                            filas_seleccionadas.append(int(r["index"]))
                        elif "row_id" in r:
                            filas_seleccionadas.append(int(r["row_id"]))
                        elif "rowKey" in r:
                            filas_seleccionadas.append(int(r["rowKey"]))
                else:
                    # lista simple de enteros (posiciones)
                    try:
                        filas_seleccionadas = [int(x) for x in rows]
                    except:
                        filas_seleccionadas = []
        elif isinstance(sel, list):
            # si selection ya es lista de ints
            try:
                filas_seleccionadas = [int(x) for x in sel]
            except:
                filas_seleccionadas = []

    # 2) Si st.data_editor devolviera un DataFrame (versiones antiguas/extrañas)
    if not filas_seleccionadas:
        try:
            # si devuelve un DataFrame modificado, Streamlit suele poner atributos especiales
            # pero no siempre incluye selección; ignoramos este caso salvo que haya 'selected_rows'
            if hasattr(editor_response, "get") and isinstance(editor_response.get("selected_rows", None), list):
                filas_seleccionadas = [int(x) for x in editor_response.get("selected_rows", [])]
        except Exception:
            pass

    # 3) Como último recurso, si editor_response contiene directamente 'selected_rows'
    if not filas_seleccionadas and isinstance(editor_response, dict) and "selected_rows" in editor_response:
        try:
            filas_seleccionadas = [int(x) for x in editor_response["selected_rows"]]
        except:
            filas_seleccionadas = []

    # ============================================================
    # EXPORTAR VARIAS COLUMNAS A TXT o CSV (mantengo tu bloque)
    # ============================================================
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
                contenido = df_export.to_csv(index=False, sep="\t")
                data = contenido.encode("utf-8")
                nombre_archivo = "export_resultados.txt"
                mime = "text/plain"

            elif tipo_export == "CSV":
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

    # ============================================================
    # MOSTRAR DETALLE AUTOMÁTICAMENTE
    # ============================================================
    st.subheader("📘 Detalle del registro seleccionado")

    if filas_seleccionadas:
        # tomamos la primera selección (single-row)
        pos = filas_seleccionadas[0]
        # por seguridad, comprobar límites
        if 0 <= pos < len(resultados):
            indice_real = resultados.index[pos]
            registro = resultados.loc[indice_real]
            st.json(registro.to_dict())
        else:
            st.error("Índice de selección fuera de rango.")
    else:
        st.info("👈 Haz clic en una fila de la tabla para ver el detalle.")
        # Pista de depuración (te ayudará a entender qué estructura te devuelve st.data_editor)
        st.write("DEBUG: estructura devuelta por st.data_editor (solo lectura):")
        st.write(type(editor_response))
        # muestra solo las claves principales si es dict (evita volcar el DataFrame entero)
        if isinstance(editor_response, dict):
            st.write("Claves:", list(editor_response.keys()))
        else:
            st.write("Contenido (resumido):", str(editor_response)[:500])

    # ============================================================
    # GENERAR PDF DEL REGISTRO SELECCIONADO
    # ============================================================
    if filas_seleccionadas:
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
                    file_name=f"reporte_{indice_real}.pdf",
                    mime="application/pdf"
                )
else:
    st.warning("⚠️ No se encontraron resultados con ese criterio de búsqueda.")
