import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection  # <--- Nueva librería para Google Sheets

# Configuración de la página
st.set_page_config(page_title="Evaluador de Automatizaciones", layout="centered")

st.title("🤖 Evaluador de Viabilidad de Automatizaciones")
st.write("Introduce los detalles de tu tarea manual para determinar si es viable pasar al flujo de desarrollo.")

st.markdown("---")

### 1. FORMULARIO PARA EL USUARIO COMPAÑERO (Campos Obligatorios)
st.subheader("📝 Datos Obligatorios de la Tarea")

tarea = st.text_input("Nombre de la Tarea (Máximo 20 caracteres):", max_chars=20)

col1, col2 = st.columns(2)
with col1:
    duracion = st.number_input("Duración aproximada de la actividad (en minutos):", min_value=1, value=15)
with col2:
    frecuencia = st.selectbox("¿Cada cuánto se hace de forma manual?", ["Diario", "Semanal", "Quincenal", "Mensual"])

criticidad = st.selectbox("Criticidad del proceso:", ["Baja", "Media", "Alta"])
documentacion = st.text_area("Documentación paso a paso de lo que haces manualmente:")

### 2. CAMPOS ADICIONALES
with st.expander("🛠️ Campos Técnicos Avanzados (Opcionales para el usuario)"):
    categoria = st.selectbox(
        "Categoría:", 
        ["No especificado", "batch basis middleware", "BDs", "Mainframe", "B24", "POS", "Planeacion"]
    )
    tipo_origen = st.selectbox(
        "Tipo / Origen:", 
        ["No especificado", "workaround", "deuda tecnica", "incidencia", "linea de comandos", "solicitud"]
    )
    servicio = st.text_input("Servicio afectado (Máximo 15 caracteres):", max_chars=15)
    adelanto = st.text_input("¿Existe algún adelanto de este proyecto? (Links, scripts previos, etc.):")

st.markdown("---")

### 3. LÓGICA DE CONEXIÓN Y GUARDADO EN GOOGLE SHEETS

# Inicializar la conexión con Google Sheets usando los secrets ocultos
conn = st.connection("gsheets", type=GSheetsConnection)

def guardar_en_sheets(estatus):
    try:
        # 1. Leer los datos actuales del Google Sheet
        df_actual = conn.read()
    except Exception:
        # Si la hoja está completamente vacía, estructuramos las columnas
        df_actual = pd.DataFrame(columns=[
            "ID", "Categoría", "Tarea", "Tipo/Origen", "Servicio", 
            "Duración Aprox (Minutos)", "Frecuencia", "Criticidad", 
            "Documentación / Paso a Paso", "Registro de Adelanto", "Estatus Revisión"
        ])
    
    nuevo_id = len(df_actual) + 1
    
    nuevo_registro = {
        "ID": nuevo_id,
        "Categoría": categoria,
        "Tarea": tarea[:20],
        "Tipo/Origen": tipo_origen,
        "Servicio": servicio[:15] if servicio else "N/A",
        "Duración Aprox (Minutos)": duracion,
        "Frecuencia": frecuencia,
        "Criticidad": criticidad,
        "Documentación / Paso a Paso": documentacion,
        "Registro de Adelanto": adelanto if adelanto else "Ninguno",
        "Estatus Revisión": estatus
    }
    
    # 2. Agregar el nuevo registro
    df_actual = pd.concat([df_actual, pd.DataFrame([nuevo_registro])], ignore_index=True)
    
    # 3. Reescribir el Google Sheet en la nube de forma segura
    conn.update(data=df_actual)
    st.success(f"✅ ¡Datos guardados exitosamente en Google Sheets bajo el estatus: **{estatus}**!")

# Diálogo/Popup para cuando NO cumple los requisitos
@st.dialog("⚠️ Solicitud retenida por Retorno de Inversión (ROI)")
def mostrar_popup_rechazo(veces_ano, horas_ano):
    st.write(f"### Hola. Analizamos la viabilidad de la tarea: **{tarea}**")
    st.write(
        "Para que el equipo pueda justificar las semanas de esfuerzo que toma programar, "
        "probar y desplegar una automatización, el proceso manual debe consumir un mínimo de **24 horas totales al año**."
    )
    st.info(
        f"**Desglose matemático de tu proceso:**\n"
        f"* Frecuencia: **{frecuencia}** ({veces_ano} veces al año)\n"
        f"* Tiempo por evento: **{duracion} minutos**\n"
        f"* Tiempo total actual consumido: **{horas_ano:.2f} horas al año**"
    )
    st.error(f"Tu proceso consume **{horas_ano:.2f} horas anuales** y su criticidad es **{criticidad}**.")
    st.markdown("---")
    if st.button("Sí, mandar a revisión manual de todos modos"):
        guardar_en_sheets("Para Revisión (Forzado por usuario)")
        st.rerun()

# Botón Principal de Evaluación
if st.button("🚀 Evaluar Automatización", type="primary"):
    if not tarea.strip() or not documentacion.strip():
        st.error("❌ Por favor, llena los campos obligatorios: **Nombre de la tarea** y **Documentación paso a paso**.")
    else:
        # Algoritmo de viabilidad
        equivalencia_anual = {"Diario": 240, "Semanal": 52, "Quincenal": 24, "Mensual": 12}
        veces_al_ano = equivalencia_anual[frecuencia]
        horas_al_ano = (duracion * veces_al_ano) / 60
        
        if horas_al_ano >= 24.0 or criticidad == "Alta":
            guardar_en_sheets("Aprobado Automático (Viable)")
        else:
            mostrar_popup_rechazo(veces_al_ano, horas_al_ano)