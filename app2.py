import streamlit as st
import pandas as pd

# --- Configuración de página ---
st.set_page_config(page_title="SACC-CIVIL - Visor de Base de Datos", layout="wide")
st.title("📊 SACC-CIVIL / INFORMACIÓN UNIFICADA")

# --- Cargar archivo desde el usuario ---
st.sidebar.header("Cargar base de datos")
uploaded_file = st.sidebar.file_uploader("Selecciona un archivo Excel o CSV", type=["xlsx", "csv"])

# Evitar errores cuando no hay archivo cargado
if uploaded_file is None:
    st.info("📂 Carga un archivo para comenzar.")
    st.stop()

# --- Lectura del archivo ---
if uploaded_file.name.endswith(".csv"):
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_excel(uploaded_file)

st.success("Archivo cargado con éxito.")

# --- Mostrar tabla de resultados ---
st.subheader("🔎 Resultados")

# Mostrar tabla y permitir seleccionar una fila
selected_index = st.dataframe(
    df,
    use_container_width=True,
    hide_index=False,  # Para que el usuario vea el índice real
)

# --- Selección de fila ---
st.write("### Selecciona una fila para ver el detalle")

row_to_show = st.number_input(
    "Introduce el número de fila (índice):",
    min_value=0,
    max_value=len(df) - 1,
    step=1
)

selected_row = df.iloc[row_to_show]

# --- VER DETALLE DE UN REGISTRO ---
st.subheader("📄 Ver detalle de un registro seleccionado")
st.json(selected_row.to_dict())

# --- Seleccionar columnas para exportar ---
st.subheader("📤 Exportación de datos (hasta 4 columnas)")

column_options = df.columns.tolist()

selected_columns = st.multiselect(
    "Selecciona las columnas a exportar:",
    options=column_options,
    max_selections=4
)

if selected_columns:
    export_df = df[selected_columns]

    st.write("### Vista previa de la exportación")
    st.dataframe(export_df, use_container_width=True)

    # Botón para descargar archivo CSV
    csv_export = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Descargar archivo CSV",
        data=csv_export,
        file_name="exportacion_sacc.csv",
        mime="text/csv"
    )

else:
    st.info("Selecciona hasta 4 columnas para habilitar la exportación.")
