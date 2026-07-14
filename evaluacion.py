import streamlit as st
import requests

# Configuración de la página
st.set_page_config(page_title="Evaluador de Automatizaciones", layout="centered")

st.title("🤖 Evaluador de Viabilidad de Automatizaciones")
st.write("Introduce los detalles de tu tarea manual para determinar si es viable pasar al flujo de desarrollo.")

st.markdown("---")

### 1. FORMULARIO PARA EL USUARIO
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

### 3. ENVÍO DE DATOS A LA API DE APPSHEET

# Recuperar credenciales de forma segura desde los secrets
APP_ID = st.secrets["APPSHEET_APP_ID"]
ACCESS_KEY = st.secrets["APPSHEET_ACCESS_KEY"]

def guardar_en_appsheet(estatus):
    # AppSheet requiere el nombre exacto de la tabla conectada (usualmente el nombre de la pestaña o archivo)
    # AJUSTA ESTE NOMBRE si en tu AppSheet la tabla se llama diferente
    NOMBRE_TABLA_APPSHEET = "Inventario Automatización" 
    
    url = f"https://api.appsheet.com/api/v1/apps/{APP_ID}/tables/{NOMBRE_TABLA_APPSHEET}/Action"
    
    headers = {
        "ApplicationAccessKey": ACCESS_KEY,
        "Content-Type": "application/json"
    }
    
    # El cuerpo (Payload) estructurado bajo el estricto formato de la API de AppSheet
    payload = {
        "Action": "Add",
        "Properties": {
            "Locale": "es-MX",
            "Timezone": "Central Standard Time"
        },
        "Rows": [
            {
                # Asegúrate de usar los nombres de columnas EXACTOS de tu base de datos
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
        ]
    }
    
    with st.spinner("Conectando con AppSheet..."):
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                st.success(f"✅ ¡Datos procesados por AppSheet exitosamente bajo el estatus: **{estatus}**!")
            else:
                st.error(f"❌ Error al guardar en AppSheet: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"❌ Error de conexión con AppSheet: {e}")

# Diálogo de rechazo por ROI
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
        guardar_en_appsheet("Para Revisión (Forzado por usuario)")
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
            guardar_en_appsheet("Aprobado Automático (Viable)")
        else:
            mostrar_popup_rechazo(veces_al_ano, horas_al_ano)