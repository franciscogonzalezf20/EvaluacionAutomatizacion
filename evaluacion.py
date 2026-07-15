import streamlit as st
import pandas as pd
import time
from streamlit_gsheets import GSheetsConnection # Conector oficial de Streamlit

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

### 3. FUNCIÓN PARA ESCRIBIR DIRECTO EN GOOGLE SHEETS
def guardar_en_google_sheets(estatus):
    with st.spinner("Conectando con Google Sheets e insertando registro..."):
        try:
            # 1. Establecer conexión usando las credenciales de los Secrets
            conn = st.connection("gsheets", type=GSheetsConnection)
            
            # 2. Leer los datos actuales especificando la pestaña (worksheet)
            # Cambia "Sheet1" si tu pestaña se llama diferente (ej: "Hoja 1")
            df_actual = conn.read(worksheet="Fuente", ttl=0)
            
            # Determinar el siguiente ID (numérico correlativo)
            if not df_actual.empty and "ID" in df_actual.columns:
                ultimo_id = pd.to_numeric(df_actual["ID"], errors='coerce').max()
                nuevo_id = int(ultimo_id + 1) if not pd.isna(ultimo_id) else 1
            else:
                nuevo_id = 1

            # 3. Estructurar la nueva fila respetando idénticamente las columnas
            nueva_fila = pd.DataFrame([{
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
            }])
            
            # 4. Concatenar la nueva fila al DataFrame original
            df_actualizado = pd.concat([df_actual, nueva_fila], ignore_index=True)
            
            # 5. Reescribir el documento de Google Sheets en la pestaña correcta
            conn.update(worksheet="Fuente", data=df_actualizado)
            
            st.success(f"✅ ¡Datos guardados exitosamente en el Excel bajo el estatus: **{estatus}**!")
            
        except Exception as e:
            st.error(f"❌ Error al interactuar con Google Sheets: {e}")
            # Esto nos mostrará el detalle técnico del error de Google
            st.warning("Detalles técnicos del error para depuración:")
            st.exception(e)


# Diálogo emergente para solicitudes que no cumplen con el ROI mínimo
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
        guardar_en_google_sheets("Para Revisión (Forzado por usuario)")

# Botón Principal de Evaluación
if st.button("🚀 Evaluar Automatización", type="primary"):
    if not tarea.strip() or not documentacion.strip():
        st.error("❌ Por favor, llena los campos obligatorios: **Nombre de la tarea** y **Documentación paso a paso**.")
    else:
        # Algoritmo de cálculo de viabilidad por horas
        equivalencia_anual = {"Diario": 240, "Semanal": 52, "Quincenal": 24, "Mensual": 12}
        veces_al_ano = equivalencia_anual[frecuencia]
        horas_al_ano = (duracion * veces_al_ano) / 60
        
        if horas_al_ano >= 24.0 or criticidad == "Alta":
            guardar_en_google_sheets("Aprobado Automático (Viable)")
        else:
            mostrar_popup_rechazo(veces_al_ano, horas_al_ano)