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
    .section-title {font-size:14px;font-weight:700;color:#004C14;text-transform:uppercase;letter-spacing:.5px;margin:16px 0 8px}
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

# Métricas que SE SUMAN
S = {
    'MTD': {'acc':'acc_total_mtd','ctp':'acc_ctp_mtd','dp':'dp_total_mtd','graves':'acc_grave_mtd','fatales':'acc_fatal_mtd','meta':'meta_mtd',
            'acc_cob':'acc_total_mtd_cob','ctp_cob':'acc_ctp_mtd_cob','dp_cob':'dp_total_mtd_cob',
            'acc_fid':'acc_total_mtd_fid','ctp_fid':'acc_ctp_mtd_fid','dp_fid':'dp_total_mtd_fid'},
    'MC':  {'acc':'acc_total_mc','ctp':'acc_ctp_mc','dp':'dp_total_mc','graves':'acc_grave_mc','fatales':'acc_fatal_mc','meta':'meta_mc',
            'acc_cob':'acc_total_mc_cob','ctp_cob':'acc_ctp_mc_cob','dp_cob':'dp_total_mc_cob',
            'acc_fid':'acc_total_mc_fid','ctp_fid':'acc_ctp_mc_fid','dp_fid':'dp_total_mc_fid'},
    'YTD': {'acc':'acc_total_ytd','ctp':'acc_ctp_ytd','dp':'dp_total_ytd','graves':'acc_grave_ytd','fatales':'acc_fatal_ytd','meta':'meta_ytd',
            'acc_cob':'acc_total_ytd_cob','ctp_cob':'acc_ctp_ytd_cob','dp_cob':'dp_total_ytd_cob',
            'acc_fid':'acc_total_ytd_fid','ctp_fid':'acc_ctp_ytd_fid','dp_fid':'dp_total_ytd_fid'},
}
# Métricas PRIMER VALOR (CTP meta/real)
F = {
    'MTD': {'meta_ctp':'meta_ctp_mtd','real_ctp':'real_ctp_mtd'},
    'MC':  {'meta_ctp':'meta_ctp_mc','real_ctp':'real_ctp_mc'},
    'YTD': {'meta_ctp':'meta_ctp_ytd','real_ctp':'real_ctp_ytd'},
}

ALL_METRIC_COLS = []
for per in ['MTD','MC','YTD']:
    ALL_METRIC_COLS += list(S[per].values()) + list(F[per].values())
ALL_METRIC_COLS = list(set(ALL_METRIC_COLS))

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

def to_float(series):
    return pd.to_numeric(series, errors='coerce').fillna(0)

def safe_sum(df, col):
    return to_float(df[col]).sum() if col in df.columns else 0

def safe_first(df, col):
    if col in df.columns:
        v = to_float(df[col])
        vals = v[v != 0]
        return vals.iloc[0] if len(vals) > 0 else (v.iloc[0] if len(v) > 0 else 0)
    return 0

def semaforo(real, meta):
    try:
        r, m = float(real), float(meta)
    except (ValueError, TypeError):
        return "⚪"
    if m == 0: return "⚪"
    ratio = r / m
    if ratio <= 0.9: return "🟢"
    elif ratio <= 1.0: return "🟡"
    return "🔴"

def cumpl(real, meta):
    try:
        r, m = float(real), float(meta)
    except (ValueError, TypeError):
        return "—"
    if m == 0: return "—"
    return f"{(r/m)*100:.0f}%"

def fmt(val):
    try: return f"{int(float(val)):,}"
    except: return "0"

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
    """Agrupa: suma métricas normales, primer valor para CTP."""
    df = df.copy()
    agg_dict = {}
    for col in ALL_METRIC_COLS:
        if col in df.columns:
            df[col] = to_float(df[col])
    
    for per in ['MTD','MC','YTD']:
        for key, col in S[per].items():
            if col in df.columns: agg_dict[col] = 'sum'
        for key, col in F[per].items():
            if col in df.columns: agg_dict[col] = 'first'
    
    if name_col and name_col in df.columns and name_col != group_col:
        agg_dict[name_col] = 'first'
    
    return df.groupby(group_col, dropna=False).agg(agg_dict).reset_index()

def build_tabla_compacta(grouped, group_col, name_col, label):
    """Tabla compacta estilo HTML original: Nombre | MTD(🚦 Real Meta %) | MC(🚦 Real Meta %) | YTD(🚦 Real Meta %) | DP YTD | Fat YTD"""
    t = pd.DataFrame()
    
    # Nombre
    if name_col and name_col in grouped.columns and name_col != group_col:
        t[label] = grouped[name_col].astype(str)
    else:
        t[label] = grouped[group_col].astype(str)
    
    # ACCIDENTES TOTALES por período
    for per in ['MTD','MC','YTD']:
        s = S[per]
        if s['acc'] in grouped.columns and s['meta'] in grouped.columns:
            t[f'{per}'] = grouped.apply(lambda r: semaforo(r.get(s['acc'],0), r.get(s['meta'],0)), axis=1)
            t[f'Acc {per}'] = grouped[s['acc']].astype(int)
            t[f'Meta {per}'] = grouped[s['meta']].astype(int)
            t[f'% {per}'] = grouped.apply(lambda r: cumpl(r.get(s['acc'],0), r.get(s['meta'],0)), axis=1)
    
    # CTP MC (el más relevante para gestión)
    mc = S['MC']
    f_mc = F['MC']
    if mc['ctp'] in grouped.columns:
        t['CTP MC'] = grouped[mc['ctp']].astype(int)
    if f_mc['real_ctp'] in grouped.columns:
        t['Real CTP'] = grouped[f_mc['real_ctp']].astype(int)
    if f_mc['meta_ctp'] in grouped.columns:
        t['Meta CTP'] = grouped[f_mc['meta_ctp']].astype(int)
    
    # DP YTD y Fatales YTD (acumulados anuales)
    ytd = S['YTD']
    if ytd['dp'] in grouped.columns:
        t['DP YTD'] = grouped[ytd['dp']].astype(int)
    if ytd['fatales'] in grouped.columns:
        t['Fat YTD'] = grouped[ytd['fatales']].astype(int)
    if ytd['graves'] in grouped.columns:
        t['Grav YTD'] = grouped[ytd['graves']].astype(int)
    
    # Ordenar por Acc MC desc
    if 'Acc MC' in t.columns:
        t = t.sort_values('Acc MC', ascending=False)
    
    return t

def build_top_empresas(df_nivel, p_key, tipo_cartera, n=10):
    """Top N empresas por accidentes. tipo_cartera: Total, COB, FID."""
    s = S[p_key]
    
    if tipo_cartera == 'COB':
        col_acc = s['acc_cob']
        col_ctp = s.get('ctp_cob')
        col_dp = s.get('dp_cob')
    elif tipo_cartera == 'FID':
        col_acc = s['acc_fid']
        col_ctp = s.get('ctp_fid')
        col_dp = s.get('dp_fid')
    else:
        col_acc = s['acc']
        col_ctp = s['ctp']
        col_dp = s['dp']
    
    if col_acc not in df_nivel.columns:
        return pd.DataFrame()
    
    df = df_nivel.copy()
    df[col_acc] = to_float(df[col_acc])
    
    # Filtrar solo filas con accidentes > 0
    df = df[df[col_acc] > 0]
    
    # Ordenar y tomar top N
    df = df.sort_values(col_acc, ascending=False).head(n)
    
    # Armar display
    display = pd.DataFrame()
    if COL_RAZON in df.columns: display['Empresa'] = df[COL_RAZON].astype(str)
    if COL_RUT in df.columns: display['RUT'] = df[COL_RUT].astype(str)
    if COL_BP in df.columns: display['BP Suc'] = df[COL_BP].astype(str)
    
    display['Acc'] = df[col_acc].astype(int)
    if col_ctp and col_ctp in df.columns:
        display['CTP'] = to_float(df[col_ctp]).astype(int)
    if col_dp and col_dp in df.columns:
        display['DP'] = to_float(df[col_dp]).astype(int)
    
    # Agregar ubicación jerárquica
    if COL_GTE_NOM in df.columns: display['Territorio'] = df[COL_GTE_NOM].astype(str)
    if COL_SUBG_NOM in df.columns: display['Subgerencia'] = df[COL_SUBG_NOM].astype(str)
    if COL_AGENCIA in df.columns: display['Agencia'] = df[COL_AGENCIA].astype(str)
    if COL_JGC_NOM in df.columns: display['JGC'] = df[COL_JGC_NOM].astype(str)
    if COL_EXP_NOM in df.columns: display['Experto'] = df[COL_EXP_NOM].astype(str)
    
    return display

def render_resumen(df_nivel, group_col):
    """Tarjetas resumen: Acc Total y CTP grandes, resto compacto abajo."""
    resumen = {}
    for per in ['MTD','MC','YTD']:
        s_p, f_p = S[per], F[per]
        r = {
            'acc': safe_sum(df_nivel, s_p['acc']),
            'meta': safe_sum(df_nivel, s_p['meta']),
            'ctp': safe_sum(df_nivel, s_p['ctp']),
            'dp': safe_sum(df_nivel, s_p['dp']),
            'graves': safe_sum(df_nivel, s_p['graves']),
            'fatales': safe_sum(df_nivel, s_p['fatales']),
        }
        if f_p['meta_ctp'] in df_nivel.columns and group_col in df_nivel.columns:
            df_c = df_nivel.copy()
            df_c[f_p['meta_ctp']] = to_float(df_c[f_p['meta_ctp']])
            df_c[f_p['real_ctp']] = to_float(df_c[f_p['real_ctp']])
            ctp_grp = df_c.groupby(group_col).agg({f_p['meta_ctp']:'first', f_p['real_ctp']:'first'})
            r['meta_ctp'] = ctp_grp[f_p['meta_ctp']].sum()
            r['real_ctp'] = ctp_grp[f_p['real_ctp']].sum()
        else:
            r['meta_ctp'] = 0; r['real_ctp'] = 0
        resumen[per] = r

    cols = st.columns(3)
    for i, per in enumerate(['MTD','MC','YTD']):
        r = resumen[per]
        with cols[i]:
            st.markdown(f"**{per}**")
            sem_acc = semaforo(r['acc'], r['meta'])
            sem_ctp = semaforo(r['real_ctp'], r['meta_ctp'])
            st.metric(f"Acc Total {sem_acc}", fmt(r['acc']), f"Meta: {fmt(r['meta'])} ({cumpl(r['acc'], r['meta'])})")
            st.metric(f"CTP {sem_ctp}", fmt(r['ctp']), f"Real: {fmt(r['real_ctp'])} / Meta: {fmt(r['meta_ctp'])}")
            st.caption(f"DP: {fmt(r['dp'])} · Graves: {fmt(r['graves'])} · Fatales: {fmt(r['fatales'])}")

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

    df_gte = get_nivel(df, 'GTE')
    
    # --- RESUMEN EQUIPO ---
    st.subheader("Resumen de mi equipo")
    if user_territorio and user_territorio == 'SGMP0001':
        df_equipo = get_nivel(df, 'AGENCIA_MIPE')[lambda d: d[COL_SUBG]=='SGMP0001']
        equipo_group = COL_AGENCIA
    elif user_territorio:
        df_equipo = df_gte[df_gte[COL_GTE] == user_territorio]
        equipo_group = COL_GTE
    else:
        df_equipo = df_gte
        equipo_group = COL_GTE
    
    render_resumen(df_equipo, equipo_group)
    st.divider()

    # --- FILTROS JERÁRQUICOS ---
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
            st.selectbox("Subgerencia", ["SGMP0001"]); sel_subg_cod = "SGMP0001"
        elif sel_ter_cod:
            subgs = get_nivel(df,'SUBG')
            subgs = subgs[subgs[COL_GTE]==sel_ter_cod][[COL_SUBG,COL_SUBG_NOM]].drop_duplicates().dropna()
            ops = ["Todas"] + [f"{r[COL_SUBG_NOM]} ({r[COL_SUBG]})" for _,r in subgs.iterrows()]
            sel_subg = st.selectbox("Subgerencia", ops)
            sel_subg_cod = sel_subg.split("(")[-1].replace(")","").strip() if sel_subg != "Todas" else None
        else:
            st.selectbox("Subgerencia", ["—"], disabled=True); sel_subg_cod = None
    
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
            st.selectbox("Agencia", ["—"], disabled=True); sel_ag = "Todas"
    
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
            st.selectbox("JGC", ["—"], disabled=True); sel_jgc = "Todos"
    sel_jgc_cod = sel_jgc.split("(")[-1].replace(")","").strip() if sel_jgc not in ["Todos","—"] else None

    if is_mipe:
        st.markdown('<div class="mipe-banner">📋 Vista MIPE — Subgerencia SGMP0001</div>', unsafe_allow_html=True)

    # === DETERMINAR VISTA ===
    if sel_jgc_cod:
        df_show = get_nivel(df, 'EXPERTO')[lambda d: d[COL_JGC]==sel_jgc_cod]
        grouped = agrupar(df_show, COL_EXP, COL_EXP_NOM)
        display = build_tabla_compacta(grouped, COL_EXP, COL_EXP_NOM, "Experto")
        nivel_empresas = 'EXPERTO'
        filtro_empresas = {COL_JGC: sel_jgc_cod}
    elif sel_ag not in ["Todas","—"]:
        df_show = get_nivel(df, 'JGC')[lambda d: d[COL_AGENCIA]==sel_ag]
        if is_mipe: df_show = df_show[df_show[COL_SUBG]=='SGMP0001']
        grouped = agrupar(df_show, COL_JGC, COL_JGC_NOM)
        display = build_tabla_compacta(grouped, COL_JGC, COL_JGC_NOM, "JGC")
        nivel_empresas = 'JGC'
        filtro_empresas = {COL_AGENCIA: sel_ag}
    elif sel_subg_cod:
        niv = 'AGENCIA_MIPE' if is_mipe else 'AGENCIA'
        df_show = get_nivel(df, niv)[lambda d: d[COL_SUBG]==sel_subg_cod]
        grouped = agrupar(df_show, COL_AGENCIA, COL_AGENCIA)
        display = build_tabla_compacta(grouped, COL_AGENCIA, None, "Agencia")
        nivel_empresas = niv
        filtro_empresas = {COL_SUBG: sel_subg_cod}
    elif sel_ter_cod:
        df_show = get_nivel(df, 'SUBG')[lambda d: d[COL_GTE]==sel_ter_cod]
        grouped = agrupar(df_show, COL_SUBG, COL_SUBG_NOM)
        display = build_tabla_compacta(grouped, COL_SUBG, COL_SUBG_NOM, "Subgerencia")
        nivel_empresas = 'SUBG'
        filtro_empresas = {COL_GTE: sel_ter_cod}
    elif is_mipe:
        df_show = get_nivel(df, 'AGENCIA_MIPE')[lambda d: d[COL_SUBG]=='SGMP0001']
        grouped = agrupar(df_show, COL_AGENCIA, COL_AGENCIA)
        display = build_tabla_compacta(grouped, COL_AGENCIA, None, "Agencia MIPE")
        nivel_empresas = 'AGENCIA_MIPE'
        filtro_empresas = {COL_SUBG: 'SGMP0001'}
    else:
        # Nacional
        grouped_ter = agrupar(df_gte.dropna(subset=[COL_GTE]), COL_GTE, COL_GTE_NOM)
        display_ter = build_tabla_compacta(grouped_ter, COL_GTE, COL_GTE_NOM, "Territorio")
        
        df_mipe = get_nivel(df, 'AGENCIA_MIPE')[lambda d: d[COL_SUBG]=='SGMP0001']
        grouped_mipe = agrupar(df_mipe, COL_SUBG, COL_SUBG_NOM)
        display_mipe = build_tabla_compacta(grouped_mipe, COL_SUBG, COL_SUBG_NOM, "Territorio")
        if len(display_mipe) > 0:
            display_mipe.iloc[0, display_mipe.columns.get_loc("Territorio")] = "MIPE (SGMP0001)"
        for col in display_ter.columns:
            if col not in display_mipe.columns: display_mipe[col] = 0
        display_mipe = display_mipe[display_ter.columns]
        display = pd.concat([display_ter, display_mipe], ignore_index=True)
        nivel_empresas = 'GTE'
        filtro_empresas = {}

    # === TABLA PRINCIPAL ===
    st.markdown(f'<div class="section-title">Accidentes Totales — {len(display)} filas</div>', unsafe_allow_html=True)
    st.dataframe(display, use_container_width=True, height=min(500, 45 + len(display) * 35), hide_index=True)

    # === DETALLE POR FILA (expander) ===
    if len(display) > 0 and len(display) <= 20:
        first_col = display.columns[0]
        for _, row in display.iterrows():
            nombre = row[first_col]
            with st.expander(f"📋 Detalle: {nombre}"):
                dc1, dc2, dc3 = st.columns(3)
                for i, per in enumerate(['MTD','MC','YTD']):
                    with [dc1,dc2,dc3][i]:
                        st.markdown(f"**{per}**")
                        acc_col = f'Acc {per}'
                        meta_col = f'Meta {per}'
                        pct_col = f'% {per}'
                        acc_v = row.get(acc_col, 0)
                        meta_v = row.get(meta_col, 0)
                        pct_v = row.get(pct_col, '—')
                        st.write(f"Acc: **{acc_v}** / Meta: **{meta_v}** → **{pct_v}**")
                
                if 'CTP MC' in row: st.write(f"CTP MC: **{row.get('CTP MC',0)}** · Real CTP: **{row.get('Real CTP',0)}** · Meta CTP: **{row.get('Meta CTP',0)}**")
                if 'DP YTD' in row: st.write(f"DP YTD: **{row.get('DP YTD',0)}** · Graves YTD: **{row.get('Grav YTD',0)}** · Fatales YTD: **{row.get('Fat YTD',0)}**")

    # === TOP 10 EMPRESAS ===
    st.divider()
    st.subheader("🏢 Top 10 empresas con más accidentes")
    
    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        tipo_cartera = st.radio("Tipo cartera", ["Total", "COB", "FID"], horizontal=True)
    with tc2:
        periodo_top = st.radio("Período", ["MC", "MTD", "YTD"], horizontal=True, key="per_top")
    
    # Obtener datos del nivel actual para las empresas
    df_empresas = get_nivel(df, nivel_empresas)
    for col, val in filtro_empresas.items():
        df_empresas = df_empresas[df_empresas[col] == val]
    
    top = build_top_empresas(df_empresas, periodo_top, tipo_cartera, n=10)
    
    if len(top) == 0:
        st.info("No hay empresas con accidentes en este filtro.")
    else:
        st.dataframe(top, use_container_width=True, hide_index=True, height=min(420, 45 + len(top) * 35))

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
            mc = S['MC']
            ce = [COL_RUT, COL_RAZON, COL_GTE_NOM, COL_BP, mc['acc'], mc['ctp'], mc['dp']]
            ce = [c for c in ce if c in df_b.columns]
            dbd = df_b[ce].copy()
            for c in [mc['acc'],mc['ctp'],mc['dp']]:
                if c in dbd.columns: dbd[c] = to_float(dbd[c]).astype(int)
            dbd = dbd.rename(columns={COL_RUT:'RUT',COL_RAZON:'Razón Social',COL_GTE_NOM:'Territorio',COL_BP:'BP',mc['acc']:'Acc MC',mc['ctp']:'CTP MC',mc['dp']:'DP MC'})
            st.markdown(f"**{len(dbd)} resultados**")
            st.dataframe(dbd, use_container_width=True, hide_index=True, height=300)

elif seccion == "📋 Cobertura":
    st.subheader("Cobertura")
    st.info("Próximamente")

elif seccion == "⚙️ Cargar datos":
    if user_rol != 'admin':
        st.warning("Solo administradores."); st.stop()
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
                st.balloons(); st.cache_data.clear(); st.rerun()
        except Exception as e:
            st.error(str(e))
    st.divider()
    if df is not None:
        st.markdown(f"**Datos:** {len(df):,} registros · Fecha: {fecha}")
