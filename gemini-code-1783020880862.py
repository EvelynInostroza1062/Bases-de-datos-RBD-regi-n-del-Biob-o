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
@st.cache_data(ttl=10) # Cache corto para facilitar pruebas rápidos
def cargar_datos_consolidados():
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(('.csv', '.xlsx'))]
    if not files:
        return None
    
    consolidado = {}
    
    for file in files:
        path = os.path.join(DATA_DIR, file)
        try:
            if file.endswith('.csv'):
                df = pd.read_csv(path, dtype=str) # Forzar lectura inicial como texto
            else:
                df = pd.read_excel(path, dtype=str) # Forzar lectura inicial como texto
            
            # Limpiar nombres de columnas (quitar espacios en blanco fantasmas)
            df.columns = [str(c).strip() for c in df.columns]
            
            # Buscar la columna RBD sin importar mayúsculas/minúsculas
            col_rbd = None
            for c in df.columns:
                if c.upper() == 'RBD':
                    col_rbd = c
                    break
            
            if col_rbd is None:
                st.sidebar.warning(f"⚠️ El archivo '{file}' no tiene una columna llamada 'RBD'.")
                continue
                
            # Super limpieza del valor RBD fila por fila
            for _, row in df.iterrows():
                val_original = str(row[col_rbd]).strip()
                
                # Ignorar filas vacías
                if val_original == 'nan' or val_original == '' or pd.isna(row[col_rbd]):
                    continue
                
                # Quitar decimales si el Excel los agregó (ej: 1234.0 -> 1234)
                rbd_limpio = val_original.split('.')[0]
                
                if rbd_limpio not in consolidado:
                    consolidado[rbd_limpio] = {}
                
                # Agregar los datos de las demás columnas
                for col in df.columns:
                    if col.upper() != 'RBD':
                        origen_col = f"{col} ({file.split('.')[0]})"
                        consolidado[rbd_limpio][origen_col] = row[col]
                        
        except Exception as e:
            st.error(f"Error crítico procesando el archivo {file}: {e}")
            
    return consolidado if consolidado else None

# Cargar la estructura de datos
datos_completos = cargar_datos_consolidados()

# --- Interfaz de Búsqueda Principal ---
rbd_buscado = st.text_input("🎯 Ingrese el RBD del establecimiento a consultar:", "").strip()

if rbd_buscado:
    if datos_completos is None:
        st.warning("⚠️ No hay datos válidos cargados en el sistema. Por favor, revisa la barra lateral.")
    else:
        # Intentar buscar el RBD tal como lo escribió el usuario
        # Se limpia por si ingresó puntos o espacios
        rbd_buscado_limpio = rbd_buscado.replace('.', '').strip()
        
        if rbd_buscado_limpio in datos_completos:
            st.success(f"✨ ¡Datos encontrados para el RBD: {rbd_buscado_limpio}!")
            info_rbd = datos_completos[rbd_buscado_limpio]
            
            df_mostrar = pd.DataFrame(list(info_rbd.items()), columns=["Indicador / Variable (Origen)", "Valor Registrado"])
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
            
            with st.expander("Ver en formato Ficha de Resumen"):
                for k, v in info_rbd.items():
                    st.markdown(f"**{k}:** {v}")
        else:
            st.error(f"❌ El RBD '{rbd_buscado_limpio}' no se encuentra en ninguna de las bases de datos válidas.")
            
st.markdown("---")
st.caption("Buscador optimizado contra errores de formato.")