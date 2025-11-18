import streamlit as st
import pandas as pd
import plotly.express as px
import gdown
from fpdf import FPDF

# --- Configuración de página ---
st.set_page_config(page_title="SACC-CIVIL - Visor de Base de Datos", layout="wide")

st.title("📊 SACC-CIVIL / INFORMACIÓN UNIFICADA")

# ---------------------------------------------------------------------
# EJEMPLO DE BASE — sustituye esta parte por tu carga real
# ---------------------------------------------------------------------
df = pd.DataFrame({
    "ID": [1, 2, 3],
    "Nombre": ["Juan Pérez", "Ana López", "Luis Méndez"],
    "Programa": ["Civil", "Geotecnia", "Estructuras"],
    "Ingreso": [2020, 2021, 2022],
    "Estado": ["Regular", "Rezagado", "Egresado"]
})

st.subheader("📄 Resultados")

# ---------------------------------------------------------------------
# TABLA INTERACTIVA CON SELECCIÓN                                             
# ---------------------------------------------------------------------

selected = st.data_editor(
    df,
    hide_index=True,
    use_container_width=True,
    disabled=True,
    column_config={
        "ID": st.column_config.NumberColumn(label="ID", disabled=True),
        "Nombre": st.column_config.TextColumn(label="Nombre", disabled=True),
        "Programa": st.column_config.TextColumn(label="Programa", disabled=True),
        "Ingreso": st.column_config.NumberColumn(label="Ingreso", disabled=True),
        "Estado": st.column_config.TextColumn(label="Estado", disabled=True),
    }
)

# Crear variable en session_state si no existe
if "selected_rows" not in st.session_state:
    st.session_state.selected_rows = []

# Guardar selección
st.session_state.selected_rows = selected.get("selected_rows", [])

# ---------------------------------------------------------------------
# MOSTRAR DETALLE AUTOMÁTICO
# ---------------------------------------------------------------------
st.subheader("🔍 Ver detalle del registro seleccionado")

if st.session_state.selected_rows:
    idx = st.session_state.selected_rows[0]  # primer registro seleccionado
    registro = df.iloc[idx]

    # Muestra detalle
    st.write("### 🧾 Resumen del registro")
    st.json(registro.to_dict())

else:
    st.info("Selecciona un registro en la tabla de arriba para ver el detalle.")
