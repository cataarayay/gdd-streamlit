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

# === COLUMNAS ===
COL_NIVEL='nivel'; COL_CARTERA='cartera_nivel'; COL_NOMBRE='nombre_nivel'
COL_BP='bp_sucursal'; COL_RUT='rut_empresa'; COL_RAZON='razon_social'
COL_GTE='cartera_gte'; COL_GTE_NOM='nombre_gte'
COL_SUBG='cartera_subg'; COL_SUBG_NOM='nombre_subg'
COL_AGENCIA='agencia'
COL_JGC='cartera_jgc'; COL_JGC_NOM='nombre_jgc'
COL_EXP='cartera_experto'; COL_EXP_NOM='nombre_experto'
COL_FECHA='fecha_actualizacion'

# Métricas que SE SUMAN (varían por bp_sucursal)
SUM_COLS = {
    'MTD': {'acc':'acc_total_mtd','ctp':'acc_ctp_mtd','dp':'dp_total_mtd','graves':'acc_grave_mtd','fatales':'acc_fatal_mtd','meta':'meta_mtd','acc_cob':'acc_total_mtd_cob','acc_fid':'acc_total_mtd_fid'},
    'MC':  {'acc':'acc_total_mc','ctp':'acc_ctp_mc','dp':'dp_total_mc','graves':'acc_grave_mc','fatales':'acc_fatal_mc','meta':'meta_mc','acc_cob':'acc_total_mc_cob','acc_fid':'acc_total_mc_fid'},
    'YTD': {'acc':'acc_total_ytd','ctp':'acc_ctp_ytd','dp':'dp_total_ytd','graves':'acc_grave_ytd','fatales':'acc_fatal_ytd','meta':'meta_ytd','acc_cob':'acc_total_ytd_cob','acc_fid':'acc_total_ytd_fid'},
}
# Métricas CTP que se toman PRIMER VALOR (constantes por grupo)
FIRST_COLS = {
    'MTD': {'meta_ctp':'meta_ctp_mtd','real_ctp':'real_ctp_mtd'},
    'MC':  {'meta_ctp':'meta_ctp_mc','real_ctp':'real_ctp_mc'},
    'YTD': {'meta_ctp':'meta_ctp_ytd','real_ctp':'real_ctp_ytd'},
}

# === AUTH ===
CONFIG_PATH = "config_usuarios.yaml"
DATA_FILE = "datos_accidentabilidad.csv"

@st.cache_data
def load_users():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f).get('usuarios', {})

def check_login(u, p):
    users = load_users()
    if u not in users: return False
    return bcrypt.checkpw(p.encode(), users[u]['password'].encode())

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

if not st.session_state.logged_in:
    _,cc,_ = st.columns([1,1,1])
    with cc:
        st.markdown("### 🟢 GDD ACHS\n**Iniciar sesión**")
        with st.form("login"):
            u = st.text_input("Usuario")
            pw = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                if check_login(u, pw):
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
    st.stop()

ui = load_users().get(st.session_state.username, {})
user_name = ui.get('name', st.session_state.username)
user_rol = ui.get('rol', 'experto')
user_territorio = ui.get('territorio')
user_subgerencia = ui.get('subgerencia')

# === FUNCIONES ===
@st.cache_data
def cargar_datos():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, dtype=str)
        df.columns = [c.strip() for c in df.columns]
        return df
    return None

def to_float(df, col):
    if col in df.columns:
        return pd.to_numeric(df[col], errors='coerce').fillna(0)
    return pd.Series(0, index=df.index)

def safe_sum(df, col):
    return to_float(df, col).sum()

def safe_first(df, col):
    """Primer valor no-nulo de una columna."""
    if col in df.columns:
        vals = pd.to_numeric(df[col], errors='coerce').dropna()
        return vals.iloc[0] if len(vals) > 0 else 0
    return 0

def semaforo(real, meta):
    r, m = float(real), float(meta)
    if m == 0: return "⚪"
    ratio = r / m
    if ratio <= 0.9: return "🟢"
    elif ratio <= 1.0: return "🟡"
    return "🔴"

def fmt(val): return f"{int(val):,}"

def obtener_fecha(df):
    if COL_FECHA in df.columns:
        f = df[COL_FECHA].dropna().unique()
        return f[0] if len(f) > 0 else "—"
    return "—"

def equipo_label():
    if user_rol == 'admin' or not user_territorio: return 'Nacional'
    return ' → '.join(filter(None, [user_territorio, user_subgerencia]))

def get_nivel(df, nivel):
    return df[df[COL_NIVEL] == nivel]

def agrupar(df, group_col, name_col):
    """Agrupa: suma métricas normales, primer valor para CTP, todos los períodos."""
    agg_dict = {}
    # Sumar
    for per in ['MTD','MC','YTD']:
        for key, col in SUM_COLS[per].items():
            if col in df.columns:
                df[col] = to_float(df, col)
                agg_dict[col] = 'sum'
    # Primer valor CTP
    for per in ['MTD','MC','YTD']:
        for key, col in FIRST_COLS[per].items():
            if col in df.columns:
                df[col] = to_float(df, col)
                agg_dict[col] = 'first'
    
    if name_col and name_col in df.columns and name_col != group_col:
        agg_dict[name_col] = 'first'
    
    return df.groupby(group_col, dropna=False).agg(agg_dict).reset_index()

def build_display(grouped, group_col, name_col, label):
    """Construye tabla display con MTD/MC/YTD en columnas."""
    display = pd.DataFrame()
    
    # Nombre
    if name_col and name_col in grouped.columns and name_col != group_col:
        display[label] = grouped[name_col].astype(str)
    else:
        display[label] = grouped[group_col].astype(str)
    
    # Para cada período: semáforo, acc, meta, ctp, real_ctp, meta_ctp, dp, graves, fatales
    for per in ['MTD','MC','YTD']:
        s = SUM_COLS[per]
        f = FIRST_COLS[per]
        
        # Semáforo
        if s['acc'] in grouped.columns and s['meta'] in grouped.columns:
            display[f'🚦{per}'] = grouped.apply(lambda r: semaforo(r.get(s['acc'],0), r.get(s['meta'],0)), axis=1)
        
        col_map = [
            (s['acc'], f'Acc {per}'),
            (s['meta'], f'Meta {per}'),
            (s['ctp'], f'CTP {per}'),
            (f['real_ctp'], f'Real CTP {per}'),
            (f['meta_ctp'], f'Meta CTP {per}'),
            (s['dp'], f'DP {per}'),
            (s['graves'], f'Grav {per}'),
            (s['fatales'], f'Fat {per}'),
        ]
        for src, dst in col_map:
            if src in grouped.columns:
                display[dst] = grouped[src].astype(int)
    
    # Ordenar por Acc MC descendente
    sort_col = 'Acc MC' if 'Acc MC' in display.columns else ('Acc MTD' if 'Acc MTD' in display.columns else None)
    if sort_col:
        display = display.sort_values(sort_col, ascending=False)
    
    return display

def render_resumen(df_nivel, group_col):
    """Tarjetas resumen con los 3 períodos."""
    # Para resumen nacional/equipo: sumar las métricas que se suman, y sumar los first values por grupo
    resumen = {}
    for per in ['MTD','MC','YTD']:
        s = SUM_COLS[per]
        f = FIRST_COLS[per]
        resumen[per] = {
            'acc': safe_sum(df_nivel, s['acc']),
            'meta': safe_sum(df_nivel, s['meta']),
            'ctp': safe_sum(df_nivel, s['ctp']),
            'dp': safe_sum(df_nivel, s['dp']),
            'graves': safe_sum(df_nivel, s['graves']),
            'fatales': safe_sum(df_nivel, s['fatales']),
        }
        # CTP: sumar los valores únicos por grupo jerárquico
        if f['meta_ctp'] in df_nivel.columns and group_col in df_nivel.columns:
            ctp_by_group = df_nivel.groupby(group_col).agg({f['meta_ctp']:'first', f['real_ctp']:'first'})
            resumen[per]['meta_ctp'] = ctp_by_group[f['meta_ctp']].sum() if f['meta_ctp'] in ctp_by_group.columns else 0
            resumen[per]['real_ctp'] = ctp_by_group[f['real_ctp']].sum() if f['real_ctp'] in ctp_by_group.columns else 0
        else:
            resumen[per]['meta_ctp'] = 0
            resumen[per]['real_ctp'] = 0
    
    # Mostrar en 3 columnas (MTD | MC | YTD)
    cols = st.columns(3)
    for i, per in enumerate(['MTD','MC','YTD']):
        r = resumen[per]
        with cols[i]:
            st.markdown(f"**{per}**")
            sem_acc = semaforo(r['acc'], r['meta'])
            sem_ctp = semaforo(r['real_ctp'], r['meta_ctp'])
            st.metric(f"Acc Total {sem_acc}", fmt(r['acc']), f"Meta: {fmt(r['meta'])}")
            st.metric(f"CTP {sem_ctp}", fmt(r['ctp']), f"Real: {fmt(r['real_ctp'])} / Meta: {fmt(r['meta_ctp'])}")
            st.metric("DP", fmt(r['dp']))
            mc1, mc2 = st.columns(2)
            with mc1: st.metric("Graves", fmt(r['graves']))
            with mc2: st.metric("Fatales", fmt(r['fatales']))

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
        st.info("No hay datos cargados. Ve a **⚙️ Cargar datos**.")
        st.stop()

    # --- RESUMEN ---
    st.subheader("Resumen de mi equipo")
    
    df_gte = get_nivel(df, 'GTE')
    if user_territorio and user_territorio == 'SGMP0001':
        df_equipo = get_nivel(df, 'AGENCIA_MIPE')
        df_equipo = df_equipo[df_equipo[COL_SUBG]=='SGMP0001']
        equipo_group = COL_AGENCIA
    elif user_territorio:
        df_equipo = df_gte[df_gte[COL_GTE] == user_territorio]
        equipo_group = COL_GTE
    else:
        df_equipo = df_gte
        equipo_group = COL_GTE
    
    render_resumen(df_equipo, equipo_group)
    st.divider()

    # --- FILTROS ---
    st.subheader("Explorar por jerarquía")
    
    f1, f2, f3, f4 = st.columns(4)
    
    with f1:
        ter_nombres = df_gte.groupby(COL_GTE)[COL_GTE_NOM].first().dropna().to_dict()
        ter_ops = ["Nacional"] + [f"{ter_nombres.get(t,t)} ({t})" for t in sorted(ter_nombres.keys())] + ["MIPE (SGMP0001)"]
        sel_ter = st.selectbox("Territorio", ter_ops)
    
    is_mipe = "MIPE" in sel_ter
    sel_ter_cod = sel_ter.split("(")[-1].replace(")","").strip() if sel_ter not in ["Nacional"] and not is_mipe else None
    
    with f2:
        if is_mipe:
            sel_subg = st.selectbox("Subgerencia", ["SGMP0001"])
            sel_subg_cod = "SGMP0001"
        elif sel_ter_cod:
            subgs = get_nivel(df,'SUBG')
            subgs = subgs[subgs[COL_GTE]==sel_ter_cod][[COL_SUBG,COL_SUBG_NOM]].drop_duplicates().dropna()
            ops = ["Todas"] + [f"{r[COL_SUBG_NOM]} ({r[COL_SUBG]})" for _,r in subgs.iterrows()]
            sel_subg = st.selectbox("Subgerencia", ops)
            sel_subg_cod = sel_subg.split("(")[-1].replace(")","").strip() if sel_subg != "Todas" else None
        else:
            st.selectbox("Subgerencia", ["—"], disabled=True)
            sel_subg_cod = None
    
    with f3:
        niv_ag = 'AGENCIA_MIPE' if is_mipe else 'AGENCIA'
        df_ag = get_nivel(df, niv_ag)
        if is_mipe: df_ag = df_ag[df_ag[COL_SUBG]=='SGMP0001']
        elif sel_subg_cod: df_ag = df_ag[df_ag[COL_SUBG]==sel_subg_cod]
        elif sel_ter_cod: df_ag = df_ag[df_ag[COL_GTE]==sel_ter_cod]
        
        if sel_ter_cod or is_mipe:
            ops = ["Todas"] + sorted(df_ag[COL_AGENCIA].dropna().unique().tolist())
            sel_ag = st.selectbox("Agencia", ops)
        else:
            st.selectbox("Agencia", ["—"], disabled=True)
            sel_ag = "Todas"
    
    with f4:
        df_jgc = get_nivel(df, 'JGC')
        if sel_ag not in ["Todas","—"]: df_jgc = df_jgc[df_jgc[COL_AGENCIA]==sel_ag]
        elif sel_subg_cod: df_jgc = df_jgc[df_jgc[COL_SUBG]==sel_subg_cod]
        elif sel_ter_cod: df_jgc = df_jgc[df_jgc[COL_GTE]==sel_ter_cod]
        elif is_mipe: df_jgc = df_jgc[df_jgc[COL_SUBG]=='SGMP0001']
        
        if sel_ter_cod or is_mipe:
            jnames = df_jgc[[COL_JGC,COL_JGC_NOM]].drop_duplicates().dropna()
            ops = ["Todos"] + [f"{r[COL_JGC_NOM]} ({r[COL_JGC]})" for _,r in jnames.iterrows()]
            sel_jgc = st.selectbox("JGC", ops)
        else:
            st.selectbox("JGC", ["—"], disabled=True)
            sel_jgc = "Todos"
    
    sel_jgc_cod = sel_jgc.split("(")[-1].replace(")","").strip() if sel_jgc not in ["Todos","—"] else None

    # === BANNER MIPE ===
    if is_mipe:
        st.markdown('<div class="mipe-banner">📋 Vista MIPE — Subgerencia SGMP0001</div>', unsafe_allow_html=True)

    # === DETERMINAR VISTA Y AGRUPAR ===
    if sel_jgc_cod:
        df_show = get_nivel(df, 'EXPERTO')
        df_show = df_show[df_show[COL_JGC]==sel_jgc_cod]
        grouped = agrupar(df_show, COL_EXP, COL_EXP_NOM)
        display = build_display(grouped, COL_EXP, COL_EXP_NOM, "Experto")
        
    elif sel_ag not in ["Todas","—"]:
        df_show = get_nivel(df, 'JGC')
        df_show = df_show[df_show[COL_AGENCIA]==sel_ag]
        if is_mipe: df_show = df_show[df_show[COL_SUBG]=='SGMP0001']
        grouped = agrupar(df_show, COL_JGC, COL_JGC_NOM)
        display = build_display(grouped, COL_JGC, COL_JGC_NOM, "JGC")
        
    elif sel_subg_cod:
        niv = 'AGENCIA_MIPE' if is_mipe else 'AGENCIA'
        df_show = get_nivel(df, niv)
        df_show = df_show[df_show[COL_SUBG]==sel_subg_cod]
        grouped = agrupar(df_show, COL_AGENCIA, COL_AGENCIA)
        display = build_display(grouped, COL_AGENCIA, None, "Agencia")
        
    elif sel_ter_cod:
        df_show = get_nivel(df, 'SUBG')
        df_show = df_show[df_show[COL_GTE]==sel_ter_cod]
        grouped = agrupar(df_show, COL_SUBG, COL_SUBG_NOM)
        display = build_display(grouped, COL_SUBG, COL_SUBG_NOM, "Subgerencia")
        
    elif is_mipe:
        df_show = get_nivel(df, 'AGENCIA_MIPE')
        df_show = df_show[df_show[COL_SUBG]=='SGMP0001']
        grouped = agrupar(df_show, COL_AGENCIA, COL_AGENCIA)
        display = build_display(grouped, COL_AGENCIA, None, "Agencia MIPE")
    
    else:
        # Nacional: territorios + MIPE
        grouped_ter = agrupar(df_gte.dropna(subset=[COL_GTE]), COL_GTE, COL_GTE_NOM)
        display_ter = build_display(grouped_ter, COL_GTE, COL_GTE_NOM, "Territorio")
        
        # MIPE como fila extra
        df_mipe = get_nivel(df, 'AGENCIA_MIPE')
        df_mipe = df_mipe[df_mipe[COL_SUBG]=='SGMP0001']
        grouped_mipe = agrupar(df_mipe, COL_SUBG, COL_SUBG_NOM)
        display_mipe = build_display(grouped_mipe, COL_SUBG, COL_SUBG_NOM, "Territorio")
        if len(display_mipe) > 0:
            display_mipe.iloc[0, display_mipe.columns.get_loc("Territorio")] = "MIPE (SGMP0001)"
        
        for col in display_ter.columns:
            if col not in display_mipe.columns:
                display_mipe[col] = 0
        display_mipe = display_mipe[display_ter.columns]
        display = pd.concat([display_ter, display_mipe], ignore_index=True)
    
    # === MOSTRAR TABLA ===
    st.markdown(f"**{len(display)} filas**")
    st.dataframe(display, use_container_width=True, height=min(600, 45 + len(display) * 35), hide_index=True)
    
    # === TOTALES ===
    st.markdown("---")
    tc = st.columns(6)
    for i, (per, idx) in enumerate([(p,i) for i,p in enumerate(['MTD','MC','YTD']) for _ in range(2)]):
        pass  # Skip complex total render, table has the data

    # === BUSCADOR ===
    st.divider()
    st.subheader("🔍 Buscar empresa")
    busqueda = st.text_input("RUT o razón social", placeholder="Ej: 76123456 o CONSTRUCTORA...")
    if busqueda:
        busq = busqueda.upper().strip()
        df_b = df_gte[
            df_gte[COL_RUT].astype(str).str.contains(busq, na=False) |
            df_gte[COL_RAZON].astype(str).str.upper().str.contains(busq, na=False)
        ]
        if len(df_b) == 0:
            st.warning("No se encontraron empresas.")
        else:
            mc = SUM_COLS['MC']
            ce = [COL_RUT, COL_RAZON, COL_GTE_NOM, COL_BP]
            ce += [mc['acc'], mc['ctp'], mc['dp']]
            ce = [c for c in ce if c in df_b.columns]
            dbd = df_b[ce].copy()
            for c in [mc['acc'],mc['ctp'],mc['dp']]:
                if c in dbd.columns: dbd[c] = to_float(dbd, c).astype(int)
            dbd = dbd.rename(columns={COL_RUT:'RUT',COL_RAZON:'Razón Social',COL_GTE_NOM:'Territorio',COL_BP:'BP',mc['acc']:'Acc MC',mc['ctp']:'CTP MC',mc['dp']:'DP MC'})
            st.markdown(f"**{len(dbd)} resultados**")
            st.dataframe(dbd, use_container_width=True, hide_index=True, height=300)

# =====================================================================
# COBERTURA
# =====================================================================
elif seccion == "📋 Cobertura":
    st.subheader("Cobertura")
    st.info("Próximamente")

# =====================================================================
# CARGAR DATOS
# =====================================================================
elif seccion == "⚙️ Cargar datos":
    if user_rol != 'admin':
        st.warning("Solo administradores.")
        st.stop()
    st.subheader("Cargar CSV de Accidentabilidad")
    st.write("Sube el CSV de Databricks. Reemplaza todos los datos.")
    uploaded = st.file_uploader("CSV", type=["csv"])
    if uploaded:
        try:
            raw = uploaded.read().decode('utf-8-sig')
            sep = ';' if raw.count(';') > raw.count(',') else ','
            uploaded.seek(0)
            df_new = pd.read_csv(uploaded, sep=sep, dtype=str)
            df_new.columns = [c.strip() for c in df_new.columns]
            niveles = df_new[COL_NIVEL].unique() if COL_NIVEL in df_new.columns else []
            st.success(f"✓ **{len(df_new):,}** filas · Niveles: {', '.join(sorted(niveles))}")
            st.dataframe(df_new.head(10), use_container_width=True, hide_index=True)
            if st.button("✅ Confirmar", type="primary"):
                df_new.to_csv(DATA_FILE, index=False)
                st.success(f"✓ {len(df_new):,} registros guardados.")
                st.balloons()
                st.cache_data.clear()
                st.rerun()
        except Exception as e:
            st.error(str(e))
    st.divider()
    if df is not None:
        st.markdown(f"**Datos:** {len(df):,} registros · Fecha: {fecha}")
        st.markdown(f"**Niveles:** {', '.join([f'{n}: {c:,}' for n,c in df[COL_NIVEL].value_counts().items()])}")
