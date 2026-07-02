
import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Buscador de Establecimientos por RBD", layout="wide")

st.title("🔍 Buscador Consolidado de Establecimientos (RBD)")
st.write("Bienvenido. Ingresa el RBD para obtener toda la información asociada de las bases de datos cargadas.")

# Directorio para guardar las bases de datos subidas
DATA_DIR = "data_sources"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Sidebar para administración y carga de archivos
st.sidebar.header("📁 Gestión de Bases de Datos")
uploaded_file = st.sidebar.file_uploader("Subir nueva base de datos (Excel o CSV)", type=["xlsx", "csv"])

if uploaded_file is not None:
    file_path = os.path.join(DATA_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success(f"Archivo '{uploaded_file.name}' guardado correctamente.")

# Listar archivos cargados
files = [f for f in os.listdir(DATA_DIR) if f.endswith(('.csv', '.xlsx'))]
if files:
    st.sidebar.write("**Archivos activos actualmente:**")
    for f in files:
        st.sidebar.text(f"• {f}")
    if st.sidebar.button("🗑️ Limpiar todas las bases de datos"):
        for f in files:
            os.remove(os.path.join(DATA_DIR, f))
        st.sidebar.warning("Todas las bases de datos han sido eliminadas.")
        st.rerun()
else:
    st.sidebar.info("No hay archivos cargados aún. Sube un CSV o Excel para comenzar.")

# Función para cargar y consolidar datos basados en el RBD
@st.cache_data(ttl=60) # Cache para mejorar rendimiento, expira en 1 minuto si cambian archivos
def cargar_datos_consolidados():
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(('.csv', '.xlsx'))]
    if not files:
        return None
    
    # Diccionario para acumular datos por RBD
    # Clave: RBD (string o int), Valor: diccionario con todos los campos combinados
    consolidado = {}
    
    for file in files:
        path = os.path.join(DATA_DIR, file)
        try:
            if file.endswith('.csv'):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
            
            # Normalizar nombres de columnas para encontrar el RBD (puede venir como rbd, RBD, Rbd, etc)
            df.columns = [c.strip() for c in df.columns]
            col_rbd = None
            for c in df.columns:
                if c.upper() == 'RBD':
                    col_rbd = c
                    break
            
            if col_rbd is None:
                continue # Si el archivo no tiene columna RBD, se ignora
                
            # Asegurar que RBD sea tratado como string limpio sin decimales
            df[col_rbd] = df[col_rbd].astype(str).str.split('.').str[0].str.strip()
            
            # Iterar por cada fila del archivo e ir sumando la información al mapa consolidado
            for _, row in df.iterrows():
                rbd_val = row[col_rbd]
                if rbd_val == 'nan' or not rbd_val:
                    continue
                    
                if rbd_val not in consolidado:
                    consolidado[rbd_val] = {}
                
                # Agregar los datos de las columnas (evitando pisar el RBD)
                for col in df.columns:
                    if col.upper() != 'RBD':
                        # Guardar el nombre de la columna con el nombre del archivo para saber de dónde viene
                        origen_col = f"{col} ({file.split('.')[0]})"
                        consolidado[rbd_val][origen_col] = row[col]
                        
        except Exception as e:
            st.error(f"Error procesando el archivo {file}: {e}")
            
    if not consolidado:
        return None
        
    return consolidado

# Cargar la estructura de datos
datos_completos = cargar_datos_consolidados()

# --- Interfaz de Búsqueda Principal ---
rbd_buscado = st.text_input("🎯 Ingrese el RBD del establecimiento a consultar:", "").strip()

if rbd_buscado:
    if datos_completos is None:
        st.warning("⚠️ No hay bases de datos cargadas en el sistema. Por favor, sube un archivo en la barra lateral.")
    elif rbd_buscado in datos_completos:
        st.success(f"✨ ¡Datos encontrados para el RBD: {rbd_buscado}!")
        
        # Convertir el diccionario del RBD específico a un DataFrame limpio para mostrarlo
        info_rbd = datos_completos[rbd_buscado]
        
        # Formatear la salida como una tabla estilizada de Atributo | Valor
        df_mostrar = pd.DataFrame(list(info_rbd.items()), columns=["Indicador / Variable (Origen)", "Valor Registrado"])
        
        # Mostrar tabla principal
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
        
        # Opción para ver los datos en formato horizontal o tipo ficha
        with st.expander("Ver en formato Ficha de Resumen"):
            for k, v in info_rbd.items():
                st.markdown(f"**{k}:** {v}")
    else:
        st.error(f"❌ El RBD '{rbd_buscado}' no se encuentra en ninguna de las bases de datos cargadas.")
        
st.markdown("---")
st.caption("Desarrollado en Python con Streamlit. Diseñado para un cruce de datos ágil y sin código para el usuario final.")
