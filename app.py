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
    div[data-testid="stMetric"] {
        background: white;
        border-left: 4px solid #13C045;
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,.08);
    }
    .sem-verde { color: #13C045; }
    .sem-rojo { color: #dc2626; }
    .sem-naranja { color: #f59e0b; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="stSidebar"] { background: #f8faf8; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Columnas del CSV — mapeo central
# ---------------------------------------------------------------------------
# Jerarquía
COL_NIVEL = 'nivel'
COL_GTE_COD = 'cartera_gte'
COL_GTE_NOM = 'nombre_gte'
COL_SUBG_COD = 'cartera_subg'
COL_SUBG_NOM = 'nombre_subg'
COL_AGENCIA = 'agencia'
COL_JGC_COD = 'cartera_jgc'
COL_JGC_NOM = 'nombre_jgc'
COL_EXP_COD = 'cartera_experto'
COL_EXP_NOM = 'nombre_experto'
COL_BP = 'bp_sucursal'
COL_RUT = 'rut_empresa'
COL_RAZON = 'razon_social'
COL_FECHA = 'fecha_actualizacion'

# Métricas por período
PERIODOS = {
    'MTD': {
        'acc_total': 'acc_total_mtd', 'acc_ctp': 'acc_ctp_mtd', 'dp': 'dp_total_mtd',
        'graves': 'acc_grave_mtd', 'fatales': 'acc_fatal_mtd', 'meta': 'meta_mtd',
        'meta_ctp': 'meta_ctp_mtd', 'real_ctp': 'real_ctp_mtd',
        'acc_cob': 'acc_total_mtd_cob', 'acc_fid': 'acc_total_mtd_fid',
        'ctp_cob': 'acc_ctp_mtd_cob', 'ctp_fid': 'acc_ctp_mtd_fid',
        'dp_cob': 'dp_total_mtd_cob', 'dp_fid': 'dp_total_mtd_fid',
    },
    'MC': {
        'acc_total': 'acc_total_mc', 'acc_ctp': 'acc_ctp_mc', 'dp': 'dp_total_mc',
        'graves': 'acc_grave_mc', 'fatales': 'acc_fatal_mc', 'meta': 'meta_mc',
        'meta_ctp': 'meta_ctp_mc', 'real_ctp': 'real_ctp_mc',
        'acc_cob': 'acc_total_mc_cob', 'acc_fid': 'acc_total_mc_fid',
        'ctp_cob': 'acc_ctp_mc_cob', 'ctp_fid': 'acc_ctp_mc_fid',
        'dp_cob': 'dp_total_mc_cob', 'dp_fid': 'dp_total_mc_fid',
    },
    'YTD': {
        'acc_total': 'acc_total_ytd', 'acc_ctp': 'acc_ctp_ytd', 'dp': 'dp_total_ytd',
        'graves': 'acc_grave_ytd', 'fatales': 'acc_fatal_ytd', 'meta': 'meta_ytd',
        'meta_ctp': 'meta_ctp_ytd', 'real_ctp': 'real_ctp_ytd',
        'acc_cob': 'acc_total_ytd_cob', 'acc_fid': 'acc_total_ytd_fid',
        'ctp_cob': 'acc_ctp_ytd_cob', 'ctp_fid': 'acc_ctp_ytd_fid',
        'dp_cob': 'dp_total_ytd_cob', 'dp_fid': 'dp_total_ytd_fid',
    },
}

# Niveles jerárquicos en el CSV
NIVELES = {
    0: 'Empresa',
    1: 'Experto',
    2: 'JGC',
    3: 'Agencia',
    4: 'Subgerencia',
    5: 'Territorio',
    6: 'Nacional',
}

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

@st.cache_data
def cargar_datos():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, dtype=str)
        df.columns = [c.strip() for c in df.columns]
        # Convertir nivel a int
        if COL_NIVEL in df.columns:
            df[COL_NIVEL] = pd.to_numeric(df[COL_NIVEL], errors='coerce').fillna(0).astype(int)
        return df
    return None

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

def sumar_col(df, col):
    if col in df.columns:
        return df[col].apply(safe_int).sum()
    return 0

def semaforo(real, meta):
    r, m = safe_int(real), safe_int(meta)
    if m == 0:
        return "⚪"
    ratio = r / m
    if ratio <= 0.9:
        return "🟢"
    elif ratio <= 1.0:
        return "🟡"
    else:
        return "🔴"

def equipo_label():
    if user_rol == 'admin' or not user_territorio:
        return 'Nacional'
    parts = []
    if user_territorio:
        parts.append(user_territorio)
    if user_subgerencia:
        parts.append(user_subgerencia)
    return ' → '.join(parts)

def filtrar_equipo(df):
    """Filtra filas del equipo del usuario para el resumen."""
    if user_rol == 'admin' or not user_territorio:
        return df
    mask = pd.Series([True] * len(df), index=df.index)
    if user_territorio and COL_GTE_COD in df.columns:
        # MIPE usa SGMP0001 como territorio
        if user_territorio == 'SGMP0001' and COL_SUBG_COD in df.columns:
            mask = mask & (df[COL_SUBG_COD] == 'SGMP0001')
        else:
            mask = mask & (df[COL_GTE_COD] == user_territorio)
    if user_subgerencia and user_subgerencia != user_territorio and COL_SUBG_COD in df.columns:
        mask = mask & (df[COL_SUBG_COD] == user_subgerencia)
    return df[mask]

def obtener_fecha_actualizacion(df):
    if COL_FECHA in df.columns:
        fechas = df[COL_FECHA].dropna().unique()
        if len(fechas) > 0:
            return fechas[0]
    return "—"

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🟢 GDD ACHS")
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
df = cargar_datos()
fecha = obtener_fecha_actualizacion(df) if df is not None else "—"

st.markdown(f"""
<div class="main-header">
    <div>
        <h2>Mi equipo: {equipo_label()}</h2>
        <div class="sub">{user_name} · {user_rol.capitalize()} · Actualización: {fecha}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# ACCIDENTABILIDAD
# ---------------------------------------------------------------------------
if seccion == "📊 Accidentabilidad":

    if df is None:
        st.info("No hay datos cargados. Ve a **⚙️ Cargar datos** para subir el CSV.")
        st.stop()

    # Periodo selector
    periodo_sel = st.radio("Período", ["MC", "MTD", "YTD"], horizontal=True, index=0)
    p = PERIODOS[periodo_sel]

    # ---- RESUMEN MI EQUIPO ----
    st.subheader("Resumen de mi equipo")

    # Usar nivel empresa (0) para sumar sin duplicar
    df_equipo = filtrar_equipo(df)
    df_emp = df_equipo[df_equipo[COL_NIVEL] == 0] if COL_NIVEL in df_equipo.columns else df_equipo

    acc_total = sumar_col(df_emp, p['acc_total'])
    acc_ctp = sumar_col(df_emp, p['acc_ctp'])
    dp_total = sumar_col(df_emp, p['dp'])
    graves = sumar_col(df_emp, p['graves'])
    fatales = sumar_col(df_emp, p['fatales'])
    meta = sumar_col(df_emp, p['meta'])

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        sem = semaforo(acc_total, meta)
        st.metric(f"Acc. Totales {sem}", f"{acc_total:,}", f"Meta: {meta:,}")
    with c2:
        if p.get('real_ctp') and p.get('meta_ctp'):
            real_ctp = sumar_col(df_emp, p['real_ctp'])
            meta_ctp = sumar_col(df_emp, p['meta_ctp'])
            sem_ctp = semaforo(real_ctp, meta_ctp)
            st.metric(f"Acc. CTP {sem_ctp}", f"{acc_ctp:,}", f"Meta: {meta_ctp:,}")
        else:
            st.metric("Acc. CTP", f"{acc_ctp:,}")
    with c3:
        st.metric("Días Perdidos", f"{dp_total:,}")
    with c4:
        st.metric("Graves", f"{graves:,}")
    with c5:
        st.metric("Fatales", f"{fatales:,}")
    with c6:
        st.metric("Empresas", f"{len(df_emp):,}")

    st.divider()

    # ---- NAVEGACIÓN JERÁRQUICA ----
    st.subheader("Explorar por jerarquía")

    # Nivel a mostrar: usar filas del nivel correspondiente
    # Nivel 5=Territorio, 4=Subgerencia, 3=Agencia, 2=JGC, 1=Experto, 0=Empresa
    
    f1, f2, f3, f4 = st.columns(4)

    with f1:
        territorios = df[df[COL_NIVEL] >= 5][[COL_GTE_COD, COL_GTE_NOM]].drop_duplicates().dropna()
        ter_opciones = ["Todos"] + [f"{row[COL_GTE_NOM]} ({row[COL_GTE_COD]})" for _, row in territorios.iterrows()]
        sel_ter = st.selectbox("Territorio", ter_opciones)

    sel_ter_cod = None
    if sel_ter != "Todos":
        sel_ter_cod = sel_ter.split("(")[-1].replace(")", "").strip()

    with f2:
        if sel_ter_cod:
            subgs = df[(df[COL_NIVEL] >= 4) & (df[COL_GTE_COD] == sel_ter_cod)][[COL_SUBG_COD, COL_SUBG_NOM]].drop_duplicates().dropna()
        else:
            subgs = df[df[COL_NIVEL] >= 4][[COL_SUBG_COD, COL_SUBG_NOM]].drop_duplicates().dropna()
        subg_opciones = ["Todas"] + [f"{row[COL_SUBG_NOM]} ({row[COL_SUBG_COD]})" for _, row in subgs.iterrows()]
        sel_subg = st.selectbox("Subgerencia", subg_opciones)

    sel_subg_cod = None
    if sel_subg != "Todas":
        sel_subg_cod = sel_subg.split("(")[-1].replace(")", "").strip()

    with f3:
        if sel_subg_cod:
            ags = df[(df[COL_NIVEL] >= 3) & (df[COL_SUBG_COD] == sel_subg_cod)][[COL_AGENCIA]].drop_duplicates().dropna()
        elif sel_ter_cod:
            ags = df[(df[COL_NIVEL] >= 3) & (df[COL_GTE_COD] == sel_ter_cod)][[COL_AGENCIA]].drop_duplicates().dropna()
        else:
            ags = df[df[COL_NIVEL] >= 3][[COL_AGENCIA]].drop_duplicates().dropna()
        ag_opciones = ["Todas"] + sorted(ags[COL_AGENCIA].unique().tolist())
        sel_ag = st.selectbox("Agencia", ag_opciones)

    with f4:
        df_jgc_filter = df[df[COL_NIVEL] >= 2].copy()
        if sel_ag != "Todas":
            df_jgc_filter = df_jgc_filter[df_jgc_filter[COL_AGENCIA] == sel_ag]
        elif sel_subg_cod:
            df_jgc_filter = df_jgc_filter[df_jgc_filter[COL_SUBG_COD] == sel_subg_cod]
        elif sel_ter_cod:
            df_jgc_filter = df_jgc_filter[df_jgc_filter[COL_GTE_COD] == sel_ter_cod]
        jgcs = df_jgc_filter[[COL_JGC_NOM]].drop_duplicates().dropna()
        jgc_opciones = ["Todos"] + sorted(jgcs[COL_JGC_NOM].unique().tolist())
        sel_jgc = st.selectbox("JGC", jgc_opciones)

    # ---- Filtrar datos para la tabla ----
    # Mostrar filas de nivel empresa (0) filtradas
    df_vista = df[df[COL_NIVEL] == 0].copy()

    if sel_ter_cod:
        df_vista = df_vista[df_vista[COL_GTE_COD] == sel_ter_cod]
    if sel_subg_cod:
        df_vista = df_vista[df_vista[COL_SUBG_COD] == sel_subg_cod]
    if sel_ag != "Todas":
        df_vista = df_vista[df_vista[COL_AGENCIA] == sel_ag]
    if sel_jgc != "Todos":
        df_vista = df_vista[df_vista[COL_JGC_NOM] == sel_jgc]

    # ---- Tabla resumen por nivel seleccionado ----
    # Determinar el nivel de agrupación más bajo seleccionado
    if sel_jgc != "Todos":
        group_col = COL_EXP_NOM
        group_label = "Experto"
    elif sel_ag != "Todas":
        group_col = COL_JGC_NOM
        group_label = "JGC"
    elif sel_subg_cod:
        group_col = COL_AGENCIA
        group_label = "Agencia"
    elif sel_ter_cod:
        group_col = COL_SUBG_NOM
        group_label = "Subgerencia"
    else:
        group_col = COL_GTE_NOM
        group_label = "Territorio"

    # Agrupar y sumar
    metric_cols = [p['acc_total'], p['acc_ctp'], p['dp'], p['graves'], p['fatales'], p['meta']]
    if p.get('meta_ctp'):
        metric_cols += [p['meta_ctp'], p['real_ctp']]

    # Convertir a numérico
    for col in metric_cols:
        if col in df_vista.columns:
            df_vista[col] = pd.to_numeric(df_vista[col], errors='coerce').fillna(0)

    if group_col in df_vista.columns:
        agg_dict = {}
        col_labels = {}
        for col in metric_cols:
            if col in df_vista.columns:
                agg_dict[col] = 'sum'

        df_resumen = df_vista.groupby(group_col, dropna=False).agg(agg_dict).reset_index()

        # Renombrar columnas para display
        rename = {
            group_col: group_label,
            p['acc_total']: 'Acc Total',
            p['acc_ctp']: 'Acc CTP',
            p['dp']: 'Días Perdidos',
            p['graves']: 'Graves',
            p['fatales']: 'Fatales',
            p['meta']: 'Meta',
        }
        if p.get('meta_ctp') and p['meta_ctp'] in df_resumen.columns:
            rename[p['meta_ctp']] = 'Meta CTP'
        if p.get('real_ctp') and p['real_ctp'] in df_resumen.columns:
            rename[p['real_ctp']] = 'Real CTP'

        df_resumen = df_resumen.rename(columns={k: v for k, v in rename.items() if k in df_resumen.columns})

        # Agregar semáforo
        if 'Meta' in df_resumen.columns and 'Acc Total' in df_resumen.columns:
            df_resumen.insert(
                df_resumen.columns.get_loc('Acc Total'),
                '🚦',
                df_resumen.apply(lambda r: semaforo(r['Acc Total'], r['Meta']), axis=1)
            )

        # Formatear enteros
        for col in ['Acc Total', 'Acc CTP', 'Días Perdidos', 'Graves', 'Fatales', 'Meta', 'Meta CTP', 'Real CTP']:
            if col in df_resumen.columns:
                df_resumen[col] = df_resumen[col].astype(int)

        # Ordenar por accidentes totales descendente
        if 'Acc Total' in df_resumen.columns:
            df_resumen = df_resumen.sort_values('Acc Total', ascending=False)

        st.markdown(f"**{group_label}** — {len(df_resumen)} filas · Período: **{periodo_sel}**")
        st.dataframe(
            df_resumen,
            use_container_width=True,
            height=min(500, 40 + len(df_resumen) * 35),
            hide_index=True,
        )

        # ---- Totales ----
        st.markdown("---")
        t1, t2, t3, t4, t5 = st.columns(5)
        with t1:
            st.metric("Total Acc", f"{df_resumen['Acc Total'].sum():,}" if 'Acc Total' in df_resumen.columns else "—")
        with t2:
            st.metric("Total CTP", f"{df_resumen['Acc CTP'].sum():,}" if 'Acc CTP' in df_resumen.columns else "—")
        with t3:
            st.metric("Total DP", f"{df_resumen['Días Perdidos'].sum():,}" if 'Días Perdidos' in df_resumen.columns else "—")
        with t4:
            st.metric("Total Graves", f"{df_resumen['Graves'].sum():,}" if 'Graves' in df_resumen.columns else "—")
        with t5:
            st.metric("Total Fatales", f"{df_resumen['Fatales'].sum():,}" if 'Fatales' in df_resumen.columns else "—")

    else:
        st.warning(f"Columna {group_col} no encontrada en los datos.")

    # ---- Buscador de empresas ----
    st.divider()
    st.subheader("🔍 Buscar empresa")
    busqueda = st.text_input("RUT o razón social", placeholder="Ej: 76123456 o CONSTRUCTORA...")

    if busqueda:
        busq = busqueda.upper().strip()
        mask = (
            df_vista[COL_RUT].astype(str).str.contains(busq, na=False) |
            df_vista[COL_RAZON].astype(str).str.upper().str.contains(busq, na=False)
        )
        df_busq = df_vista[mask]

        if len(df_busq) == 0:
            st.warning("No se encontraron empresas.")
        else:
            cols_empresa = [COL_RUT, COL_RAZON, COL_GTE_NOM, COL_SUBG_NOM, COL_AGENCIA,
                           COL_JGC_NOM, COL_EXP_NOM, p['acc_total'], p['acc_ctp'], p['dp']]
            cols_empresa = [c for c in cols_empresa if c in df_busq.columns]

            df_busq_display = df_busq[cols_empresa].copy()
            df_busq_display = df_busq_display.rename(columns={
                COL_RUT: 'RUT', COL_RAZON: 'Razón Social',
                COL_GTE_NOM: 'Territorio', COL_SUBG_NOM: 'Subgerencia',
                COL_AGENCIA: 'Agencia', COL_JGC_NOM: 'JGC', COL_EXP_NOM: 'Experto',
                p['acc_total']: 'Acc Total', p['acc_ctp']: 'Acc CTP', p['dp']: 'DP',
            })
            st.markdown(f"**{len(df_busq_display)} empresas encontradas**")
            st.dataframe(df_busq_display, use_container_width=True, hide_index=True, height=300)


# ---------------------------------------------------------------------------
# COBERTURA
# ---------------------------------------------------------------------------
elif seccion == "📋 Cobertura":
    st.subheader("Cobertura")
    st.info("Próximamente — Dashboard de cobertura")


# ---------------------------------------------------------------------------
# CARGAR DATOS
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
        help="Formato: ACC_BP_CARTERA__1_.csv"
    )

    if uploaded is not None:
        try:
            raw = uploaded.read().decode('utf-8-sig')
            sep = ';' if raw.count(';') > raw.count(',') else ','
            uploaded.seek(0)

            df_new = pd.read_csv(uploaded, sep=sep, dtype=str)
            df_new.columns = [c.strip() for c in df_new.columns]

            st.success(f"✓ Archivo leído: **{len(df_new):,}** filas, **{len(df_new.columns)}** columnas")

            # Verificar columnas esperadas
            cols_esperadas = [COL_NIVEL, COL_GTE_COD, COL_SUBG_COD, COL_AGENCIA, COL_JGC_NOM]
            cols_faltantes = [c for c in cols_esperadas if c not in df_new.columns]
            if cols_faltantes:
                st.warning(f"Columnas faltantes: {', '.join(cols_faltantes)}")

            st.markdown("**Vista previa:**")
            st.dataframe(df_new.head(10), use_container_width=True, hide_index=True)

            if st.button("✅ Confirmar y guardar datos", type="primary"):
                df_new.to_csv(DATA_FILE, index=False)
                st.success(f"✓ {len(df_new):,} registros guardados correctamente.")
                st.balloons()
                st.cache_data.clear()
                st.rerun()

        except Exception as e:
            st.error(f"Error procesando archivo: {str(e)}")

    st.divider()
    if df is not None:
        st.markdown(f"**Datos actuales:** {len(df):,} registros · Fecha: {fecha}")
    else:
        st.markdown("**No hay datos cargados actualmente.**")
