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
</style>
""", unsafe_allow_html=True)

# --- Columnas CSV ---
COL_NIVEL='nivel'; COL_GTE_COD='cartera_gte'; COL_GTE_NOM='nombre_gte'
COL_SUBG_COD='cartera_subg'; COL_SUBG_NOM='nombre_subg'; COL_AGENCIA='agencia'
COL_JGC_COD='cartera_jgc'; COL_JGC_NOM='nombre_jgc'
COL_EXP_COD='cartera_experto'; COL_EXP_NOM='nombre_experto'
COL_RUT='rut_empresa'; COL_RAZON='razon_social'; COL_FECHA='fecha_actualizacion'

PERIODOS = {
    'MTD': {'acc_total':'acc_total_mtd','acc_ctp':'acc_ctp_mtd','dp':'dp_total_mtd','graves':'acc_grave_mtd','fatales':'acc_fatal_mtd','meta':'meta_mtd','meta_ctp':'meta_ctp_mtd','real_ctp':'real_ctp_mtd'},
    'MC':  {'acc_total':'acc_total_mc','acc_ctp':'acc_ctp_mc','dp':'dp_total_mc','graves':'acc_grave_mc','fatales':'acc_fatal_mc','meta':'meta_mc','meta_ctp':'meta_ctp_mc','real_ctp':'real_ctp_mc'},
    'YTD': {'acc_total':'acc_total_ytd','acc_ctp':'acc_ctp_ytd','dp':'dp_total_ytd','graves':'acc_grave_ytd','fatales':'acc_fatal_ytd','meta':'meta_ytd','meta_ctp':'meta_ctp_ytd','real_ctp':'real_ctp_ytd'},
}

# --- Auth ---
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
    col_l, col_c, col_r = st.columns([1,1,1])
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

# --- Funciones ---
@st.cache_data
def cargar_datos():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, dtype=str)
        df.columns = [c.strip() for c in df.columns]
        if COL_NIVEL in df.columns:
            df[COL_NIVEL] = pd.to_numeric(df[COL_NIVEL], errors='coerce').fillna(0).astype(int)
        return df
    return None

def safe_int(val):
    try: return int(float(val))
    except: return 0

def sumar_col(df, col):
    return df[col].apply(safe_int).sum() if col in df.columns else 0

def semaforo(real, meta):
    r, m = safe_int(real), safe_int(meta)
    if m == 0: return "⚪"
    ratio = r / m
    if ratio <= 0.9: return "🟢"
    elif ratio <= 1.0: return "🟡"
    return "🔴"

def equipo_label():
    if user_rol == 'admin' or not user_territorio: return 'Nacional'
    parts = [user_territorio]
    if user_subgerencia: parts.append(user_subgerencia)
    return ' → '.join(parts)

def filtrar_equipo(df):
    if user_rol == 'admin' or not user_territorio: return df
    mask = pd.Series(True, index=df.index)
    if user_territorio == 'SGMP0001' and COL_SUBG_COD in df.columns:
        mask = mask & (df[COL_SUBG_COD] == 'SGMP0001')
    elif COL_GTE_COD in df.columns:
        mask = mask & (df[COL_GTE_COD] == user_territorio)
    if user_subgerencia and user_subgerencia != user_territorio and COL_SUBG_COD in df.columns:
        mask = mask & (df[COL_SUBG_COD] == user_subgerencia)
    return df[mask]

def obtener_fecha(df):
    if COL_FECHA in df.columns:
        f = df[COL_FECHA].dropna().unique()
        if len(f) > 0: return f[0]
    return "—"

# --- Sidebar ---
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

# --- Header ---
df = cargar_datos()
fecha = obtener_fecha(df) if df is not None else "—"
st.markdown(f'<div class="main-header"><div><h2>Mi equipo: {equipo_label()}</h2><div class="sub">{user_name} · {user_rol.capitalize()} · Actualización: {fecha}</div></div></div>', unsafe_allow_html=True)

# --- ACCIDENTABILIDAD ---
if seccion == "📊 Accidentabilidad":
    if df is None:
        st.info("No hay datos cargados. Ve a **⚙️ Cargar datos** para subir el CSV.")
        st.stop()

    periodo_sel = st.radio("Período", ["MC", "MTD", "YTD"], horizontal=True, index=0)
    p = PERIODOS[periodo_sel]

    st.subheader("Resumen de mi equipo")
    df_equipo = filtrar_equipo(df)
    df_emp = df_equipo[df_equipo[COL_NIVEL] == 0] if COL_NIVEL in df_equipo.columns else df_equipo

    acc_total = sumar_col(df_emp, p['acc_total'])
    meta = sumar_col(df_emp, p['meta'])
    acc_ctp = sumar_col(df_emp, p['acc_ctp'])
    meta_ctp = sumar_col(df_emp, p['meta_ctp'])
    dp_total = sumar_col(df_emp, p['dp'])
    graves = sumar_col(df_emp, p['graves'])
    fatales = sumar_col(df_emp, p['fatales'])

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: st.metric(f"Acc. Totales {semaforo(acc_total,meta)}", f"{acc_total:,}", f"Meta: {meta:,}")
    with c2: st.metric(f"Acc. CTP {semaforo(acc_ctp,meta_ctp)}", f"{acc_ctp:,}", f"Meta: {meta_ctp:,}")
    with c3: st.metric("Días Perdidos", f"{dp_total:,}")
    with c4: st.metric("Graves", f"{graves:,}")
    with c5: st.metric("Fatales", f"{fatales:,}")
    with c6: st.metric("Empresas", f"{len(df_emp):,}")

    st.divider()
    st.subheader("Explorar por jerarquía")

    f1,f2,f3,f4 = st.columns(4)
    with f1:
        territorios = df[df[COL_NIVEL]>=5][[COL_GTE_COD,COL_GTE_NOM]].drop_duplicates().dropna()
        ter_ops = ["Todos"] + [f"{r[COL_GTE_NOM]} ({r[COL_GTE_COD]})" for _,r in territorios.iterrows()]
        sel_ter = st.selectbox("Territorio", ter_ops)
    sel_ter_cod = sel_ter.split("(")[-1].replace(")","").strip() if sel_ter != "Todos" else None

    with f2:
        df_s = df[df[COL_NIVEL]>=4]
        if sel_ter_cod: df_s = df_s[df_s[COL_GTE_COD]==sel_ter_cod]
        subgs = df_s[[COL_SUBG_COD,COL_SUBG_NOM]].drop_duplicates().dropna()
        subg_ops = ["Todas"] + [f"{r[COL_SUBG_NOM]} ({r[COL_SUBG_COD]})" for _,r in subgs.iterrows()]
        sel_subg = st.selectbox("Subgerencia", subg_ops)
    sel_subg_cod = sel_subg.split("(")[-1].replace(")","").strip() if sel_subg != "Todas" else None

    with f3:
        df_a = df[df[COL_NIVEL]>=3]
        if sel_subg_cod: df_a = df_a[df_a[COL_SUBG_COD]==sel_subg_cod]
        elif sel_ter_cod: df_a = df_a[df_a[COL_GTE_COD]==sel_ter_cod]
        ag_ops = ["Todas"] + sorted(df_a[COL_AGENCIA].dropna().unique().tolist())
        sel_ag = st.selectbox("Agencia", ag_ops)

    with f4:
        df_j = df[df[COL_NIVEL]>=2]
        if sel_ag != "Todas": df_j = df_j[df_j[COL_AGENCIA]==sel_ag]
        elif sel_subg_cod: df_j = df_j[df_j[COL_SUBG_COD]==sel_subg_cod]
        elif sel_ter_cod: df_j = df_j[df_j[COL_GTE_COD]==sel_ter_cod]
        jgc_ops = ["Todos"] + sorted(df_j[COL_JGC_NOM].dropna().unique().tolist())
        sel_jgc = st.selectbox("JGC", jgc_ops)

    df_vista = df[df[COL_NIVEL]==0].copy()
    if sel_ter_cod: df_vista = df_vista[df_vista[COL_GTE_COD]==sel_ter_cod]
    if sel_subg_cod: df_vista = df_vista[df_vista[COL_SUBG_COD]==sel_subg_cod]
    if sel_ag != "Todas": df_vista = df_vista[df_vista[COL_AGENCIA]==sel_ag]
    if sel_jgc != "Todos": df_vista = df_vista[df_vista[COL_JGC_NOM]==sel_jgc]

    if sel_jgc != "Todos": group_col, group_label = COL_EXP_NOM, "Experto"
    elif sel_ag != "Todas": group_col, group_label = COL_JGC_NOM, "JGC"
    elif sel_subg_cod: group_col, group_label = COL_AGENCIA, "Agencia"
    elif sel_ter_cod: group_col, group_label = COL_SUBG_NOM, "Subgerencia"
    else: group_col, group_label = COL_GTE_NOM, "Territorio"

    mcols = [p['acc_total'],p['acc_ctp'],p['dp'],p['graves'],p['fatales'],p['meta'],p['meta_ctp'],p['real_ctp']]
    for col in mcols:
        if col in df_vista.columns:
            df_vista[col] = pd.to_numeric(df_vista[col], errors='coerce').fillna(0)

    if group_col in df_vista.columns:
        agg = {col:'sum' for col in mcols if col in df_vista.columns}
        df_res = df_vista.groupby(group_col, dropna=False).agg(agg).reset_index()
        ren = {group_col:group_label, p['acc_total']:'Acc Total', p['acc_ctp']:'Acc CTP', p['dp']:'Días Perdidos', p['graves']:'Graves', p['fatales']:'Fatales', p['meta']:'Meta', p['meta_ctp']:'Meta CTP', p['real_ctp']:'Real CTP'}
        df_res = df_res.rename(columns={k:v for k,v in ren.items() if k in df_res.columns})
        if 'Meta' in df_res.columns and 'Acc Total' in df_res.columns:
            df_res.insert(df_res.columns.get_loc('Acc Total'), '🚦', df_res.apply(lambda r: semaforo(r['Acc Total'], r['Meta']), axis=1))
        for c in ['Acc Total','Acc CTP','Días Perdidos','Graves','Fatales','Meta','Meta CTP','Real CTP']:
            if c in df_res.columns: df_res[c] = df_res[c].astype(int)
        if 'Acc Total' in df_res.columns:
            df_res = df_res.sort_values('Acc Total', ascending=False)
        st.markdown(f"**{group_label}** — {len(df_res)} filas · Período: **{periodo_sel}**")
        st.dataframe(df_res, use_container_width=True, height=min(500,40+len(df_res)*35), hide_index=True)

        st.markdown("---")
        t1,t2,t3,t4,t5 = st.columns(5)
        with t1: st.metric("Total Acc", f"{df_res['Acc Total'].sum():,}" if 'Acc Total' in df_res.columns else "—")
        with t2: st.metric("Total CTP", f"{df_res['Acc CTP'].sum():,}" if 'Acc CTP' in df_res.columns else "—")
        with t3: st.metric("Total DP", f"{df_res['Días Perdidos'].sum():,}" if 'Días Perdidos' in df_res.columns else "—")
        with t4: st.metric("Total Graves", f"{df_res['Graves'].sum():,}" if 'Graves' in df_res.columns else "—")
        with t5: st.metric("Total Fatales", f"{df_res['Fatales'].sum():,}" if 'Fatales' in df_res.columns else "—")

    st.divider()
    st.subheader("🔍 Buscar empresa")
    busqueda = st.text_input("RUT o razón social", placeholder="Ej: 76123456 o CONSTRUCTORA...")
    if busqueda:
        busq = busqueda.upper().strip()
        mask = df_vista[COL_RUT].astype(str).str.contains(busq, na=False) | df_vista[COL_RAZON].astype(str).str.upper().str.contains(busq, na=False)
        df_b = df_vista[mask]
        if len(df_b) == 0:
            st.warning("No se encontraron empresas.")
        else:
            ce = [COL_RUT,COL_RAZON,COL_GTE_NOM,COL_SUBG_NOM,COL_AGENCIA,COL_JGC_NOM,COL_EXP_NOM,p['acc_total'],p['acc_ctp'],p['dp']]
            ce = [c for c in ce if c in df_b.columns]
            df_bd = df_b[ce].rename(columns={COL_RUT:'RUT',COL_RAZON:'Razón Social',COL_GTE_NOM:'Territorio',COL_SUBG_NOM:'Subgerencia',COL_AGENCIA:'Agencia',COL_JGC_NOM:'JGC',COL_EXP_NOM:'Experto',p['acc_total']:'Acc Total',p['acc_ctp']:'Acc CTP',p['dp']:'DP'})
            st.markdown(f"**{len(df_bd)} empresas encontradas**")
            st.dataframe(df_bd, use_container_width=True, hide_index=True, height=300)

elif seccion == "📋 Cobertura":
    st.subheader("Cobertura")
    st.info("Próximamente — Dashboard de cobertura")

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
            st.success(f"✓ Archivo leído: **{len(df_new):,}** filas, **{len(df_new.columns)}** columnas")
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
        st.markdown(f"**Datos actuales:** {len(df):,} registros · Fecha: {fecha}")
    else:
        st.markdown("**No hay datos cargados.**")
