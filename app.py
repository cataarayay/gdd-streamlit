import streamlit as st
import pandas as pd
import yaml
import os
import bcrypt

st.set_page_config(page_title="GDD ACHS", page_icon="🟢", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-header {background:linear-gradient(135deg,#004C14,#0a7a2a);color:white;padding:16px 24px;border-radius:8px;margin-bottom:16px}
    .main-header h2 {margin:0;font-size:18px}
    .main-header .sub {opacity:.7;font-size:13px}
    div[data-testid="stMetric"] {background:white;border-left:4px solid #13C045;padding:12px 16px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
    #MainMenu {visibility:hidden}
    footer {visibility:hidden}
    [data-testid="stSidebar"] {background:#f8faf8}
    .mipe-banner {background:linear-gradient(135deg,#b45309,#d97706);color:white;padding:8px 16px;border-radius:6px;margin-bottom:8px;font-size:14px}
</style>
""", unsafe_allow_html=True)

# === COLUMNAS CSV ===
COL_NIVEL = 'nivel'
COL_CARTERA_NIVEL = 'cartera_nivel'
COL_NOMBRE_NIVEL = 'nombre_nivel'
COL_BP = 'bp_sucursal'
COL_RUT = 'rut_empresa'
COL_RAZON = 'razon_social'
COL_GTE = 'cartera_gte'
COL_GTE_NOM = 'nombre_gte'
COL_SUBG = 'cartera_subg'
COL_SUBG_NOM = 'nombre_subg'
COL_AGENCIA = 'agencia'
COL_JGC = 'cartera_jgc'
COL_JGC_NOM = 'nombre_jgc'
COL_EXP = 'cartera_experto'
COL_EXP_NOM = 'nombre_experto'
COL_FECHA = 'fecha_actualizacion'

METRIC_COLS = {
    'MTD': {'acc':'acc_total_mtd','ctp':'acc_ctp_mtd','dp':'dp_total_mtd','graves':'acc_grave_mtd','fatales':'acc_fatal_mtd','meta':'meta_mtd','meta_ctp':'meta_ctp_mtd','real_ctp':'real_ctp_mtd','acc_cob':'acc_total_mtd_cob','ctp_cob':'acc_ctp_mtd_cob','dp_cob':'dp_total_mtd_cob','acc_fid':'acc_total_mtd_fid','ctp_fid':'acc_ctp_mtd_fid','dp_fid':'dp_total_mtd_fid'},
    'MC':  {'acc':'acc_total_mc','ctp':'acc_ctp_mc','dp':'dp_total_mc','graves':'acc_grave_mc','fatales':'acc_fatal_mc','meta':'meta_mc','meta_ctp':'meta_ctp_mc','real_ctp':'real_ctp_mc','acc_cob':'acc_total_mc_cob','ctp_cob':'acc_ctp_mc_cob','dp_cob':'dp_total_mc_cob','acc_fid':'acc_total_mc_fid','ctp_fid':'acc_ctp_mc_fid','dp_fid':'dp_total_mc_fid'},
    'YTD': {'acc':'acc_total_ytd','ctp':'acc_ctp_ytd','dp':'dp_total_ytd','graves':'acc_grave_ytd','fatales':'acc_fatal_ytd','meta':'meta_ytd','meta_ctp':'meta_ctp_ytd','real_ctp':'real_ctp_ytd','acc_cob':'acc_total_ytd_cob','ctp_cob':'acc_ctp_ytd_cob','dp_cob':'dp_total_ytd_cob','acc_fid':'acc_total_ytd_fid','ctp_fid':'acc_ctp_ytd_fid','dp_fid':'dp_total_ytd_fid'},
}

# === AUTH ===
CONFIG_PATH = "config_usuarios.yaml"
DATA_FILE = "datos_accidentabilidad.csv"

@st.cache_data
def load_users():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f).get('usuarios', {})

def check_login(username, password):
    users = load_users()
    if username not in users: return False
    return bcrypt.checkpw(password.encode(), users[username]['password'].encode())

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

if not st.session_state.logged_in:
    _,col_c,_ = st.columns([1,1,1])
    with col_c:
        st.markdown("### 🟢 GDD ACHS")
        st.markdown("**Iniciar sesión**")
        with st.form("login_form"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                if check_login(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
    st.stop()

user_info = load_users().get(st.session_state.username, {})
user_name = user_info.get('name', st.session_state.username)
user_rol = user_info.get('rol', 'experto')
user_territorio = user_info.get('territorio')
user_subgerencia = user_info.get('subgerencia')

# === FUNCIONES ===
@st.cache_data
def cargar_datos():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, dtype=str)
        df.columns = [c.strip() for c in df.columns]
        return df
    return None

def to_num(df, cols):
    """Convierte columnas a numérico."""
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    return df

def safe_sum(df, col):
    if col in df.columns:
        return pd.to_numeric(df[col], errors='coerce').fillna(0).sum()
    return 0

def semaforo(real, meta):
    r, m = float(real), float(meta)
    if m == 0: return "⚪"
    ratio = r / m
    if ratio <= 0.9: return "🟢"
    elif ratio <= 1.0: return "🟡"
    return "🔴"

def fmt(val):
    """Formato con separador de miles."""
    return f"{int(val):,}"

def obtener_fecha(df):
    if COL_FECHA in df.columns:
        f = df[COL_FECHA].dropna().unique()
        if len(f) > 0: return f[0]
    return "—"

def equipo_label():
    if user_rol == 'admin' or not user_territorio: return 'Nacional'
    parts = [user_territorio]
    if user_subgerencia: parts.append(user_subgerencia)
    return ' → '.join(parts)

def get_nivel(df, nivel):
    """Filtra filas de un nivel jerárquico."""
    return df[df[COL_NIVEL] == nivel]

def agrupar_metricas(df, group_col, name_col, p):
    """Agrupa por group_col y suma métricas del periodo p."""
    mcols = [p['acc'],p['ctp'],p['dp'],p['graves'],p['fatales'],p['meta'],p['meta_ctp'],p['real_ctp'],p['acc_cob'],p['ctp_cob'],p['dp_cob'],p['acc_fid'],p['ctp_fid'],p['dp_fid']]
    mcols_present = [c for c in mcols if c in df.columns]
    df = to_num(df, mcols_present)
    
    agg = {c: 'sum' for c in mcols_present}
    if name_col and name_col in df.columns and name_col != group_col:
        agg[name_col] = 'first'
    
    grouped = df.groupby(group_col, dropna=False).agg(agg).reset_index()
    return grouped, mcols_present

def render_tabla(df_agrupado, group_col, name_col, label, p):
    """Renderiza tabla con semáforo y métricas."""
    display = pd.DataFrame()
    
    if name_col and name_col in df_agrupado.columns:
        display[label] = df_agrupado[name_col].astype(str) + ' (' + df_agrupado[group_col].astype(str) + ')'
    else:
        display[label] = df_agrupado[group_col].astype(str)
    
    # Semáforo
    if p['acc'] in df_agrupado.columns and p['meta'] in df_agrupado.columns:
        display['🚦'] = df_agrupado.apply(lambda r: semaforo(r[p['acc']], r[p['meta']]), axis=1)
    
    col_map = {p['acc']:'Acc Total', p['meta']:'Meta', p['ctp']:'Acc CTP', p['meta_ctp']:'Meta CTP', p['real_ctp']:'Real CTP', p['dp']:'DP', p['graves']:'Graves', p['fatales']:'Fatales', p['acc_cob']:'Acc COB', p['acc_fid']:'Acc FID'}
    
    for src, dst in col_map.items():
        if src in df_agrupado.columns:
            display[dst] = df_agrupado[src].astype(int)
    
    if 'Acc Total' in display.columns:
        display = display.sort_values('Acc Total', ascending=False)
    
    return display

def render_resumen(df_nivel, p, label=""):
    """Renderiza las 6 tarjetas de resumen."""
    acc = safe_sum(df_nivel, p['acc'])
    meta = safe_sum(df_nivel, p['meta'])
    ctp = safe_sum(df_nivel, p['ctp'])
    meta_ctp = safe_sum(df_nivel, p['meta_ctp'])
    real_ctp = safe_sum(df_nivel, p['real_ctp'])
    dp = safe_sum(df_nivel, p['dp'])
    graves = safe_sum(df_nivel, p['graves'])
    fatales = safe_sum(df_nivel, p['fatales'])
    acc_cob = safe_sum(df_nivel, p['acc_cob'])
    acc_fid = safe_sum(df_nivel, p['acc_fid'])
    
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: st.metric(f"Acc. Totales {semaforo(acc,meta)}", fmt(acc), f"Meta: {fmt(meta)}")
    with c2: st.metric(f"Acc. CTP {semaforo(real_ctp,meta_ctp)}", fmt(ctp), f"Real CTP: {fmt(real_ctp)}")
    with c3: st.metric("Días Perdidos", fmt(dp))
    with c4: st.metric("Graves", fmt(graves))
    with c5: st.metric("Fatales", fmt(fatales))
    with c6: st.metric("Empresas", fmt(len(df_nivel)))
    
    # Desglose COB/FID
    cc1, cc2, cc3, cc4 = st.columns(4)
    with cc1: st.caption(f"Acc COB: {fmt(acc_cob)}")
    with cc2: st.caption(f"Acc FID: {fmt(acc_fid)}")

# === SIDEBAR ===
with st.sidebar:
    st.markdown("### 🟢 GDD ACHS")
    st.markdown(f"**{user_name}**  \n`{user_rol.upper()}`")
    st.divider()
    seccion = st.radio("Sección", ["📊 Accidentabilidad", "📋 Cobertura", "⚙️ Cargar datos"], label_visibility="collapsed")
    st.divider()
    if st.button("Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

# === HEADER ===
df = cargar_datos()
fecha = obtener_fecha(df) if df is not None else "—"
st.markdown(f'<div class="main-header"><div><h2>Mi equipo: {equipo_label()}</h2><div class="sub">{user_name} · {user_rol.capitalize()} · Actualización: {fecha}</div></div></div>', unsafe_allow_html=True)

# =====================================================================
# ACCIDENTABILIDAD
# =====================================================================
if seccion == "📊 Accidentabilidad":
    if df is None:
        st.info("No hay datos cargados. Ve a **⚙️ Cargar datos** para subir el CSV.")
        st.stop()

    periodo_sel = st.radio("Período", ["MC", "MTD", "YTD"], horizontal=True, index=0)
    p = METRIC_COLS[periodo_sel]

    # --- RESUMEN NACIONAL (usando nivel GTE para no duplicar) ---
    st.subheader("Resumen de mi equipo")
    
    df_gte = get_nivel(df, 'GTE')
    
    # Filtrar por equipo del usuario
    if user_territorio and user_territorio == 'SGMP0001':
        # MIPE: usar AGENCIA_MIPE
        df_equipo = get_nivel(df, 'AGENCIA_MIPE')
    elif user_territorio:
        df_equipo = df_gte[df_gte[COL_GTE] == user_territorio]
    else:
        df_equipo = df_gte
    
    render_resumen(df_equipo, p)
    st.divider()

    # --- NAVEGACIÓN JERÁRQUICA ---
    st.subheader("Explorar por jerarquía")

    # Filtro 1: Territorio
    territorios = df_gte[COL_GTE].dropna().unique()
    ter_nombres = {}
    for t in territorios:
        nombres = df_gte[df_gte[COL_GTE]==t][COL_GTE_NOM].dropna().unique()
        ter_nombres[t] = nombres[0] if len(nombres) > 0 else t
    
    ter_opciones = ["Nacional"] + [f"{ter_nombres[t]} ({t})" for t in sorted(territorios)] + ["MIPE (SGMP0001)"]
    
    f1, f2, f3, f4 = st.columns(4)
    
    with f1:
        sel_ter = st.selectbox("Territorio", ter_opciones)
    
    is_mipe = "MIPE" in sel_ter
    sel_ter_cod = None
    if sel_ter != "Nacional" and not is_mipe:
        sel_ter_cod = sel_ter.split("(")[-1].replace(")","").strip()
    
    # Filtro 2: Subgerencia
    with f2:
        if is_mipe:
            subg_opciones = ["SGMP0001 - Laura Sierra"]
            sel_subg = st.selectbox("Subgerencia", subg_opciones)
            sel_subg_cod = "SGMP0001"
        elif sel_ter_cod:
            df_subg = get_nivel(df, 'SUBG')
            subgs = df_subg[df_subg[COL_GTE]==sel_ter_cod][[COL_SUBG, COL_SUBG_NOM]].drop_duplicates().dropna()
            subg_opciones = ["Todas"] + [f"{row[COL_SUBG_NOM]} ({row[COL_SUBG]})" for _, row in subgs.iterrows()]
            sel_subg = st.selectbox("Subgerencia", subg_opciones)
            sel_subg_cod = sel_subg.split("(")[-1].replace(")","").strip() if sel_subg != "Todas" else None
        else:
            sel_subg = st.selectbox("Subgerencia", ["Seleccione territorio primero"], disabled=True)
            sel_subg_cod = None
    
    # Filtro 3: Agencia
    with f3:
        nivel_ag = 'AGENCIA_MIPE' if is_mipe else 'AGENCIA'
        df_agencias = get_nivel(df, nivel_ag)
        if is_mipe:
            df_agencias = df_agencias[df_agencias[COL_SUBG]=='SGMP0001']
        elif sel_subg_cod:
            df_agencias = df_agencias[df_agencias[COL_SUBG]==sel_subg_cod]
        elif sel_ter_cod:
            df_agencias = df_agencias[df_agencias[COL_GTE]==sel_ter_cod]
        
        if sel_ter_cod or is_mipe:
            ag_opciones = ["Todas"] + sorted(df_agencias[COL_AGENCIA].dropna().unique().tolist())
            sel_ag = st.selectbox("Agencia", ag_opciones)
        else:
            sel_ag = st.selectbox("Agencia", ["Seleccione territorio primero"], disabled=True)
            sel_ag = "Todas"
    
    # Filtro 4: JGC
    with f4:
        df_jgcs = get_nivel(df, 'JGC')
        if sel_ag != "Todas" and sel_ag != "Seleccione territorio primero":
            df_jgcs = df_jgcs[df_jgcs[COL_AGENCIA]==sel_ag]
        elif sel_subg_cod:
            df_jgcs = df_jgcs[df_jgcs[COL_SUBG]==sel_subg_cod]
        elif sel_ter_cod:
            df_jgcs = df_jgcs[df_jgcs[COL_GTE]==sel_ter_cod]
        elif is_mipe:
            df_jgcs = df_jgcs[df_jgcs[COL_SUBG]=='SGMP0001']
        
        if sel_ter_cod or is_mipe:
            jgc_names = df_jgcs[[COL_JGC, COL_JGC_NOM]].drop_duplicates().dropna()
            jgc_opciones = ["Todos"] + [f"{row[COL_JGC_NOM]} ({row[COL_JGC]})" for _, row in jgc_names.iterrows()]
            sel_jgc = st.selectbox("JGC", jgc_opciones)
        else:
            sel_jgc = st.selectbox("JGC", ["Seleccione territorio primero"], disabled=True)
            sel_jgc = "Todos"
    
    sel_jgc_cod = None
    if sel_jgc != "Todos" and "Seleccione" not in sel_jgc:
        sel_jgc_cod = sel_jgc.split("(")[-1].replace(")","").strip()

    # === DETERMINAR QUÉ MOSTRAR ===
    # Cada nivel usa su propia tabla para no duplicar
    
    if is_mipe:
        st.markdown('<div class="mipe-banner">📋 Vista MIPE — Subgerencia SGMP0001</div>', unsafe_allow_html=True)
    
    if sel_jgc_cod:
        # Mostrar EXPERTOS del JGC seleccionado
        df_show = get_nivel(df, 'EXPERTO')
        df_show = df_show[df_show[COL_JGC]==sel_jgc_cod]
        grouped, mcols = agrupar_metricas(df_show, COL_EXP, COL_EXP_NOM, p)
        display = render_tabla(grouped, COL_EXP, COL_EXP_NOM, "Experto", p)
        
    elif sel_ag != "Todas" and sel_ag != "Seleccione territorio primero":
        # Mostrar JGCs de la agencia seleccionada
        df_show = get_nivel(df, 'JGC')
        df_show = df_show[df_show[COL_AGENCIA]==sel_ag]
        if is_mipe:
            df_show = df_show[df_show[COL_SUBG]=='SGMP0001']
        grouped, mcols = agrupar_metricas(df_show, COL_JGC, COL_JGC_NOM, p)
        display = render_tabla(grouped, COL_JGC, COL_JGC_NOM, "JGC", p)
        
    elif sel_subg_cod:
        # Mostrar AGENCIAS de la subgerencia
        nivel_ag = 'AGENCIA_MIPE' if is_mipe else 'AGENCIA'
        df_show = get_nivel(df, nivel_ag)
        df_show = df_show[df_show[COL_SUBG]==sel_subg_cod]
        grouped, mcols = agrupar_metricas(df_show, COL_AGENCIA, COL_AGENCIA, p)
        display = render_tabla(grouped, COL_AGENCIA, None, "Agencia", p)
        
    elif sel_ter_cod:
        # Mostrar SUBGERENCIAS del territorio
        df_show = get_nivel(df, 'SUBG')
        df_show = df_show[df_show[COL_GTE]==sel_ter_cod]
        grouped, mcols = agrupar_metricas(df_show, COL_SUBG, COL_SUBG_NOM, p)
        display = render_tabla(grouped, COL_SUBG, COL_SUBG_NOM, "Subgerencia", p)
        
    elif is_mipe:
        # Mostrar agencias MIPE
        df_show = get_nivel(df, 'AGENCIA_MIPE')
        df_show = df_show[df_show[COL_SUBG]=='SGMP0001']
        grouped, mcols = agrupar_metricas(df_show, COL_AGENCIA, COL_AGENCIA, p)
        display = render_tabla(grouped, COL_AGENCIA, None, "Agencia MIPE", p)
    
    else:
        # Nacional: mostrar TERRITORIOS + MIPE
        # Territorios normales
        grouped_ter, mcols = agrupar_metricas(df_gte.dropna(subset=[COL_GTE]), COL_GTE, COL_GTE_NOM, p)
        display_ter = render_tabla(grouped_ter, COL_GTE, COL_GTE_NOM, "Territorio", p)
        
        # MIPE
        df_mipe = get_nivel(df, 'AGENCIA_MIPE')
        df_mipe = df_mipe[df_mipe[COL_SUBG]=='SGMP0001']
        mcols_m = [c for c in [p['acc'],p['ctp'],p['dp'],p['graves'],p['fatales'],p['meta'],p['meta_ctp'],p['real_ctp'],p['acc_cob'],p['ctp_cob'],p['dp_cob'],p['acc_fid'],p['ctp_fid'],p['dp_fid']] if c in df_mipe.columns]
        df_mipe = to_num(df_mipe, mcols_m)
        mipe_row = {c: df_mipe[c].sum() for c in mcols_m}
        mipe_row['Territorio'] = 'MIPE (SGMP0001)'
        mipe_row['🚦'] = semaforo(mipe_row.get(p['acc'],0), mipe_row.get(p['meta'],0))
        
        col_map = {p['acc']:'Acc Total', p['meta']:'Meta', p['ctp']:'Acc CTP', p['meta_ctp']:'Meta CTP', p['real_ctp']:'Real CTP', p['dp']:'DP', p['graves']:'Graves', p['fatales']:'Fatales', p['acc_cob']:'Acc COB', p['acc_fid']:'Acc FID'}
        mipe_display = {'Territorio': 'MIPE (SGMP0001)', '🚦': mipe_row['🚦']}
        for src, dst in col_map.items():
            if src in mipe_row:
                mipe_display[dst] = int(mipe_row[src])
        
        mipe_df = pd.DataFrame([mipe_display])
        # Asegurar mismas columnas
        for col in display_ter.columns:
            if col not in mipe_df.columns:
                mipe_df[col] = 0
        mipe_df = mipe_df[display_ter.columns]
        
        display = pd.concat([display_ter, mipe_df], ignore_index=True)
    
    # Mostrar tabla
    st.markdown(f"**{len(display)} filas · Período: {periodo_sel}**")
    st.dataframe(display, use_container_width=True, height=min(600, 40 + len(display) * 35), hide_index=True)
    
    # Totales
    st.markdown("---")
    num_cols = ['Acc Total','Acc CTP','DP','Graves','Fatales']
    t_cols = st.columns(len(num_cols))
    for i, col in enumerate(num_cols):
        with t_cols[i]:
            if col in display.columns:
                st.metric(f"Total {col}", fmt(display[col].sum()))
    
    # === BUSCADOR DE EMPRESAS ===
    st.divider()
    st.subheader("🔍 Buscar empresa")
    busqueda = st.text_input("RUT o razón social", placeholder="Ej: 76123456 o CONSTRUCTORA...")
    
    if busqueda:
        busq = busqueda.upper().strip()
        # Buscar en nivel GTE (tiene todas las empresas)
        df_busq = df_gte[
            df_gte[COL_RUT].astype(str).str.contains(busq, na=False) |
            df_gte[COL_RAZON].astype(str).str.upper().str.contains(busq, na=False)
        ]
        if len(df_busq) == 0:
            st.warning("No se encontraron empresas.")
        else:
            cols_show = [COL_RUT, COL_RAZON, COL_GTE_NOM, COL_BP, p['acc'], p['ctp'], p['dp']]
            cols_show = [c for c in cols_show if c in df_busq.columns]
            df_bd = df_busq[cols_show].copy()
            for c in [p['acc'], p['ctp'], p['dp']]:
                if c in df_bd.columns:
                    df_bd[c] = pd.to_numeric(df_bd[c], errors='coerce').fillna(0).astype(int)
            df_bd = df_bd.rename(columns={COL_RUT:'RUT', COL_RAZON:'Razón Social', COL_GTE_NOM:'Territorio', COL_BP:'BP Sucursal', p['acc']:'Acc Total', p['ctp']:'Acc CTP', p['dp']:'DP'})
            st.markdown(f"**{len(df_bd)} resultados**")
            st.dataframe(df_bd, use_container_width=True, hide_index=True, height=300)

# =====================================================================
# COBERTURA
# =====================================================================
elif seccion == "📋 Cobertura":
    st.subheader("Cobertura")
    st.info("Próximamente — Dashboard de cobertura")

# =====================================================================
# CARGAR DATOS
# =====================================================================
elif seccion == "⚙️ Cargar datos":
    if user_rol != 'admin':
        st.warning("Solo los administradores pueden cargar datos.")
        st.stop()
    st.subheader("Cargar CSV de Accidentabilidad")
    st.write("Sube el CSV exportado desde Databricks. Esto reemplaza todos los datos actuales.")
    uploaded = st.file_uploader("Arrastra o selecciona tu CSV", type=["csv"])
    if uploaded is not None:
        try:
            raw = uploaded.read().decode('utf-8-sig')
            sep = ';' if raw.count(';') > raw.count(',') else ','
            uploaded.seek(0)
            df_new = pd.read_csv(uploaded, sep=sep, dtype=str)
            df_new.columns = [c.strip() for c in df_new.columns]
            
            # Validar niveles
            if COL_NIVEL in df_new.columns:
                niveles = df_new[COL_NIVEL].unique()
                st.success(f"✓ **{len(df_new):,}** filas · Niveles: {', '.join(sorted(niveles))}")
            else:
                st.warning("⚠ No se encontró columna 'nivel'")
            
            st.dataframe(df_new.head(10), use_container_width=True, hide_index=True)
            
            if st.button("✅ Confirmar y guardar datos", type="primary"):
                df_new.to_csv(DATA_FILE, index=False)
                st.success(f"✓ {len(df_new):,} registros guardados.")
                st.balloons()
                st.cache_data.clear()
                st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    st.divider()
    if df is not None:
        niveles = df[COL_NIVEL].value_counts()
        st.markdown(f"**Datos actuales:** {len(df):,} registros · Fecha: {fecha}")
        st.markdown(f"**Niveles:** {', '.join([f'{n}: {c:,}' for n,c in niveles.items()])}")
    else:
        st.markdown("**No hay datos cargados.**")
