import streamlit as st
import pandas as pd
import yaml
import os
import streamlit_authenticator as stauth

# ---------------------------------------------------------------------------
# Configuración de página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="GDD ACHS",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS personalizado ACHS
st.markdown("""
<style>
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #004C14, #0a7a2a);
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .main-header h2 { margin: 0; font-size: 18px; }
    .main-header .sub { opacity: 0.7; font-size: 13px; }
    
    /* Metric cards */
    div[data-testid="stMetric"] {
        background: white;
        border-left: 4px solid #13C045;
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,.08);
    }
    div[data-testid="stMetric"][data-testid-negative] {
        border-left-color: #dc2626;
    }
    
    /* Semáforo dots */
    .dot-verde { color: #13C045; font-size: 16px; }
    .dot-rojo { color: #dc2626; font-size: 16px; }
    .dot-naranja { color: #f59e0b; font-size: 16px; }
    
    /* Hide Streamlit menu */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #f8faf8;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------------
CONFIG_PATH = "config_usuarios.yaml"

@st.cache_data
def load_auth_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

config = load_auth_config()

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

# Login
authenticator.login(location='main', fields={
    'Form name': 'GDD ACHS — Iniciar sesión',
    'Username': 'Usuario',
    'Password': 'Contraseña',
    'Login': 'Entrar',
})

if st.session_state.get("authentication_status") is False:
    st.error("Usuario o contraseña incorrectos.")
    st.stop()
elif st.session_state.get("authentication_status") is None:
    st.stop()

# Usuario autenticado
username = st.session_state["username"]
user_info = config['credentials']['usernames'][username]
user_name = user_info['name']
user_rol = user_info.get('rol', 'experto')
user_territorio = user_info.get('territorio')
user_subgerencia = user_info.get('subgerencia')


# ---------------------------------------------------------------------------
# Funciones de datos
# ---------------------------------------------------------------------------
DATA_FILE = "datos_accidentabilidad.csv"

def cargar_datos():
    """Carga el CSV de datos si existe."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, dtype=str)
        # Normalizar nombres de columnas
        df.columns = [c.strip() for c in df.columns]
        return df
    return None

def detectar_columnas(df):
    """Detecta las columnas jerárquicas y numéricas."""
    cols = df.columns.tolist()
    jerarquia = {}
    
    for name, options in [
        ('territorio', ['TERRITORIO', 'GTE']),
        ('subgerencia', ['SUBGERENCIA', 'SUBG']),
        ('agencia', ['AGENCIA']),
        ('jgc', ['JGC']),
        ('experto', ['EXPERTO']),
    ]:
        for opt in options:
            if opt in cols:
                jerarquia[name] = opt
                break
    
    return jerarquia

def equipo_label():
    if user_rol == 'admin':
        return 'Nacional'
    parts = []
    if user_territorio:
        parts.append(user_territorio)
    if user_subgerencia:
        parts.append(user_subgerencia)
    return ' → '.join(parts) if parts else 'Sin asignación'

def filtrar_equipo(df, jerarquia):
    """Filtra datos del equipo del usuario para el resumen."""
    if user_rol == 'admin' or not user_territorio:
        return df
    
    col_ter = jerarquia.get('territorio')
    col_sub = jerarquia.get('subgerencia')
    
    mask = pd.Series([True] * len(df))
    if col_ter and user_territorio:
        mask = mask & (df[col_ter] == user_territorio)
    if col_sub and user_subgerencia:
        mask = mask & (df[col_sub] == user_subgerencia)
    
    return df[mask]

def semaforo(valor, meta):
    """Retorna emoji de semáforo."""
    try:
        v, m = float(valor), float(meta)
        if m == 0:
            return "⚪"
        ratio = v / m
        if ratio <= 0.9:
            return "🟢"
        elif ratio <= 1.0:
            return "🟡"
        else:
            return "🔴"
    except (ValueError, TypeError):
        return "⚪"

def safe_int(val):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0

def safe_float(val):
    try:
        return round(float(val), 1)
    except (ValueError, TypeError):
        return 0.0


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 🟢 GDD ACHS")
    st.markdown(f"**{user_name}**  \n`{user_rol.upper()}`")
    st.divider()
    
    seccion = st.radio(
        "Sección",
        ["📊 Accidentabilidad", "📋 Cobertura", "⚙️ Cargar datos"],
        label_visibility="collapsed",
    )
    
    st.divider()
    authenticator.logout("Cerrar sesión", "sidebar")


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="main-header">
    <div>
        <h2>Mi equipo: {equipo_label()}</h2>
        <div class="sub">{user_name} · {user_rol.capitalize()}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Cargar datos
df = cargar_datos()

# ---------------------------------------------------------------------------
# Sección: Accidentabilidad
# ---------------------------------------------------------------------------
if seccion == "📊 Accidentabilidad":
    
    if df is None:
        st.info("No hay datos cargados. Ve a **⚙️ Cargar datos** para subir el CSV.")
        st.stop()
    
    jerarquia = detectar_columnas(df)
    df_equipo = filtrar_equipo(df, jerarquia)
    
    # ---- Cuadros resumen personalizados ----
    st.subheader("Resumen de mi equipo")
    
    # Detectar columnas numéricas relevantes
    cols_acc = [c for c in df.columns if 'ACC' in c.upper() or 'ACCIDENTE' in c.upper()]
    cols_ctp = [c for c in df.columns if 'CTP' in c.upper()]
    cols_dp = [c for c in df.columns if 'DP' in c.upper() or 'DIAS_PERDIDOS' in c.upper()]
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Registros equipo", len(df_equipo))
    with c2:
        if cols_acc:
            total_acc = df_equipo[cols_acc[0]].apply(safe_int).sum()
            st.metric("Accidentes", total_acc)
    with c3:
        if cols_ctp:
            total_ctp = df_equipo[cols_ctp[0]].apply(safe_int).sum()
            st.metric("Acc. CTP", total_ctp)
    with c4:
        if cols_dp:
            total_dp = df_equipo[cols_dp[0]].apply(safe_int).sum()
            st.metric("Días perdidos", total_dp)
    
    st.divider()
    
    # ---- Navegación jerárquica ----
    st.subheader("Explorar por jerarquía")
    
    col_territorio = jerarquia.get('territorio')
    col_subgerencia = jerarquia.get('subgerencia')
    col_agencia = jerarquia.get('agencia')
    col_jgc = jerarquia.get('jgc')
    col_experto = jerarquia.get('experto')
    
    # Filtros en cascada
    f1, f2, f3, f4 = st.columns(4)
    
    df_filtered = df.copy()
    
    with f1:
        if col_territorio:
            territorios = ["Todos"] + sorted(df[col_territorio].dropna().unique().tolist())
            sel_territorio = st.selectbox("Territorio", territorios)
            if sel_territorio != "Todos":
                df_filtered = df_filtered[df_filtered[col_territorio] == sel_territorio]
    
    with f2:
        if col_subgerencia:
            subgerencias = ["Todas"] + sorted(df_filtered[col_subgerencia].dropna().unique().tolist())
            sel_subgerencia = st.selectbox("Subgerencia", subgerencias)
            if sel_subgerencia != "Todas":
                df_filtered = df_filtered[df_filtered[col_subgerencia] == sel_subgerencia]
    
    with f3:
        if col_agencia:
            agencias = ["Todas"] + sorted(df_filtered[col_agencia].dropna().unique().tolist())
            sel_agencia = st.selectbox("Agencia", agencias)
            if sel_agencia != "Todas":
                df_filtered = df_filtered[df_filtered[col_agencia] == sel_agencia]
    
    with f4:
        if col_jgc:
            jgcs = ["Todos"] + sorted(df_filtered[col_jgc].dropna().unique().tolist())
            sel_jgc = st.selectbox("JGC", jgcs)
            if sel_jgc != "Todos":
                df_filtered = df_filtered[df_filtered[col_jgc] == sel_jgc]
    
    # ---- Tabla de resultados ----
    st.markdown(f"**{len(df_filtered)} registros**")
    
    # Seleccionar columnas a mostrar
    cols_mostrar = []
    for nivel in [col_territorio, col_subgerencia, col_agencia, col_jgc, col_experto]:
        if nivel:
            cols_mostrar.append(nivel)
    
    # Agregar columnas numéricas principales
    cols_numericas = [c for c in df.columns if c not in cols_mostrar]
    cols_display = cols_mostrar + cols_numericas[:10]  # Limitar para no saturar
    
    # Convertir numéricas
    df_display = df_filtered[cols_display].copy()
    for c in cols_numericas[:10]:
        if c in df_display.columns:
            df_display[c] = df_display[c].apply(safe_float)
    
    st.dataframe(
        df_display,
        use_container_width=True,
        height=500,
        hide_index=True,
    )
    
    # ---- Expandables por nivel ----
    if col_territorio and sel_territorio == "Todos":
        st.subheader("Vista por Territorio")
        for ter in sorted(df[col_territorio].dropna().unique()):
            df_ter = df[df[col_territorio] == ter]
            n_rows = len(df_ter)
            
            # Calcular métricas del territorio
            acc_label = ""
            if cols_acc:
                acc_total = df_ter[cols_acc[0]].apply(safe_int).sum()
                acc_label = f" · Acc: {acc_total}"
            
            with st.expander(f"📍 {ter} ({n_rows} registros{acc_label})"):
                if col_subgerencia:
                    for sub in sorted(df_ter[col_subgerencia].dropna().unique()):
                        df_sub = df_ter[df_ter[col_subgerencia] == sub]
                        sub_acc = ""
                        if cols_acc:
                            sub_acc = f" · Acc: {df_sub[cols_acc[0]].apply(safe_int).sum()}"
                        st.markdown(f"**{sub}** ({len(df_sub)} registros{sub_acc})")
                else:
                    st.dataframe(df_ter[cols_display], hide_index=True, use_container_width=True)


# ---------------------------------------------------------------------------
# Sección: Cobertura
# ---------------------------------------------------------------------------
elif seccion == "📋 Cobertura":
    st.subheader("Cobertura")
    st.info("Próximamente — Dashboard de cobertura")


# ---------------------------------------------------------------------------
# Sección: Cargar datos
# ---------------------------------------------------------------------------
elif seccion == "⚙️ Cargar datos":
    
    if user_rol != 'admin':
        st.warning("Solo los administradores pueden cargar datos.")
        st.stop()
    
    st.subheader("Cargar CSV de Accidentabilidad")
    st.write("Sube el CSV exportado desde Databricks. Esto reemplaza todos los datos actuales.")
    
    uploaded = st.file_uploader(
        "Arrastra o selecciona tu CSV",
        type=["csv"],
        help="Formato esperado: ACC_BP_CARTERA__1_.csv"
    )
    
    if uploaded is not None:
        try:
            # Detectar separador
            raw = uploaded.read().decode('utf-8-sig')
            sep = ';' if raw.count(';') > raw.count(',') else ','
            uploaded.seek(0)
            
            df_new = pd.read_csv(uploaded, sep=sep, dtype=str)
            df_new.columns = [c.strip() for c in df_new.columns]
            
            st.success(f"✓ Archivo leído: {len(df_new)} filas, {len(df_new.columns)} columnas")
            
            # Preview
            st.markdown("**Vista previa (primeras 5 filas):**")
            st.dataframe(df_new.head(), use_container_width=True, hide_index=True)
            
            st.markdown(f"**Columnas detectadas:** {', '.join(df_new.columns.tolist())}")
            
            # Confirmar carga
            if st.button("✅ Confirmar y guardar datos", type="primary"):
                df_new.to_csv(DATA_FILE, index=False)
                st.success(f"✓ {len(df_new)} registros guardados correctamente.")
                st.balloons()
                # Limpiar cache para que se recarguen los datos
                st.cache_data.clear()
                st.rerun()
                
        except Exception as e:
            st.error(f"Error procesando archivo: {str(e)}")
    
    # Info del archivo actual
    st.divider()
    if df is not None:
        st.markdown(f"**Datos actuales:** {len(df)} registros cargados")
        st.markdown(f"**Columnas:** {', '.join(df.columns.tolist())}")
    else:
        st.markdown("**No hay datos cargados actualmente.**")
