import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

def get_groq_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except:
        return os.getenv('GROQ_API_KEY')

st.set_page_config(page_title="Bodega — Taller de Perico", layout="wide", initial_sidebar_state="expanded")

# --- ESTILOS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700&family=Barlow:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif;
    background-color: #0d1117;
    color: #c9d1d9;
}

/* Fondo general */
.stApp { background-color: #0d1117; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0a0f1a;
    border-right: 2px solid #1f6feb;
}
section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

/* Títulos */
h1, h2, h3 {
    font-family: 'Barlow Condensed', sans-serif;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #58a6ff !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: #161b22;
    border-bottom: 2px solid #1f6feb;
    gap: 0px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #8b949e !important;
    background-color: #161b22;
    border: 1px solid #30363d;
    border-bottom: none;
    padding: 8px 24px;
}
.stTabs [aria-selected="true"] {
    background-color: #1f6feb !important;
    color: #ffffff !important;
    border-color: #1f6feb !important;
}

/* Botones */
.stButton > button {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    background-color: #1f6feb;
    color: #ffffff;
    border: none;
    border-radius: 2px;
    padding: 8px 24px;
    transition: background 0.2s;
}
.stButton > button:hover { background-color: #388bfd; }

/* Inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div,
.stTextArea > div > div > textarea {
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 2px !important;
    color: #c9d1d9 !important;
}

/* Dataframe */
.stDataFrame { border: 1px solid #30363d; }

/* Métricas */
[data-testid="stMetricValue"] {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 2rem !important;
    color: #58a6ff !important;
}
[data-testid="stMetricLabel"] { color: #8b949e !important; }

/* Alertas */
.alerta-box {
    background-color: #1a0a0a;
    border-left: 4px solid #f85149;
    padding: 8px 12px;
    margin: 4px 0;
    font-size: 13px;
    font-family: 'Barlow Condensed', sans-serif;
    letter-spacing: 0.5px;
}

/* Header decorativo */
.header-strip {
    background: linear-gradient(90deg, #1f6feb 0%, #0d1117 100%);
    padding: 18px 24px;
    margin-bottom: 20px;
    border-left: 5px solid #58a6ff;
}
.header-strip h1 {
    margin: 0;
    font-size: 2rem;
    color: #ffffff !important;
}
.header-strip span {
    font-size: 13px;
    color: #8b949e;
    letter-spacing: 2px;
    text-transform: uppercase;
}

/* Divider */
hr { border-color: #21262d; }

/* Ocultar botón de chat flotante y menú hamburguesa */
#MainMenu, footer, [data-testid="stChatFloatingInputContainer"] { display: none !important; }

/* --- RESPONSIVE MÓVIL --- */
@media (max-width: 768px) {
    .header-strip { padding: 12px 14px; margin-bottom: 12px; }
    .header-strip h1 { font-size: 1.3rem !important; }
    .header-strip span { font-size: 10px; letter-spacing: 1px; }

    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    [data-testid="stMetricLabel"] { font-size: 11px !important; }

    /* Columnas apiladas en móvil */
    [data-testid="column"] { min-width: 100% !important; }

    /* Tabs más compactos */
    .stTabs [data-baseweb="tab"] {
        font-size: 12px;
        padding: 6px 10px;
        letter-spacing: 0.5px;
    }

    /* Botones full width */
    .stButton > button { width: 100%; font-size: 14px; padding: 10px 12px; }

    /* Sidebar más angosta */
    section[data-testid="stSidebar"] { min-width: 200px !important; }

    /* Dataframe scroll horizontal */
    .stDataFrame { overflow-x: auto; }

    /* Inputs más grandes para touch */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        font-size: 16px !important;
        padding: 10px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS ---
DB = 'bodega_perico.db'

def get_conn():
    return sqlite3.connect(DB)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS productos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  codigo TEXT UNIQUE, nombre TEXT,
                  marca TEXT, modelo TEXT,
                  stock INTEGER DEFAULT 0,
                  reorden INTEGER DEFAULT 5)''')
    c.execute('''CREATE TABLE IF NOT EXISTS movimientos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  fecha TEXT, tipo TEXT,
                  motivo TEXT, producto_id INTEGER,
                  cantidad INTEGER, notas TEXT,
                  FOREIGN KEY(producto_id) REFERENCES productos(id))''')

    c.execute("INSERT OR IGNORE INTO usuarios (username, password) VALUES (?,?)", ('admin', 'perico123'))

    refacciones = [
        ('K001', 'Kit Arrastre Reforzado',      'Choho',           'FT150 / DT150',     12, 5),
        ('A001', 'Aceite 4T 20W-50 Mineral',    'Motul 3000',      'Universal',          30, 10),
        ('L001', 'Llanta 3.00-18 Trasera',       'Timsun',          'FT150 / Cargo',      6,  4),
        ('B001', 'Bujía C7HSA',                  'NGK',             'Italika 125/150',    40, 15),
        ('F001', 'Balatas Delanteras',            'Alessia',         'DM200 / Pulsar',     10, 5),
        ('C001', 'Cámara de Llanta 18',           'Sayto',           'Universal',          20, 8),
        ('G001', 'Filtro de Gasolina Universal',  'Genérico',        'Universal',          25, 10),
        ('K002', 'Kit de Afinación',              'Varios',          'FT150',              15, 5),
    ]
    for r in refacciones:
        c.execute("INSERT OR IGNORE INTO productos (codigo, nombre, marca, modelo, stock, reorden) VALUES (?,?,?,?,?,?)", r)

    conn.commit()
    conn.close()

init_db()

# --- SESIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- LOGIN ---
if not st.session_state.logged_in:
    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        st.markdown("""
        <div style='text-align:center; padding: 40px 0 20px 0;'>
            <div style='font-family: Barlow Condensed, sans-serif; font-size: 3rem;
                        font-weight: 700; color: #58a6ff; letter-spacing: 3px;'>
                TALLER DE PERICO
            </div>
            <div style='color: #8b949e; letter-spacing: 4px; font-size: 12px; margin-top: 4px;'>
                CONTROL DE BODEGA
            </div>
            <div style='border-top: 2px solid #1f6feb; margin: 20px auto; width: 60%;'></div>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input("USUARIO", placeholder="usuario")
        password = st.text_input("CONTRASEÑA", type="password", placeholder="••••••••")

        if st.button("ENTRAR", use_container_width=True):
            conn = get_conn()
            df = pd.read_sql_query(
                "SELECT id FROM usuarios WHERE username=? AND password=?",
                conn, params=(username, password)
            )
            conn.close()
            if not df.empty:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
    st.stop()

# --- SIDEBAR ---
conn = get_conn()

st.sidebar.markdown("""
<div style='padding: 10px 0 6px 0;'>
    <div style='font-family: Barlow Condensed, sans-serif; font-size: 1.5rem;
                font-weight: 700; color: #58a6ff; letter-spacing: 2px;'>
       INVENTARIO DE TALLER
    </div>
    <div style='color: #8b949e; font-size: 11px; letter-spacing: 3px;'>BODEGA</div>
    <div style='border-bottom: 2px solid #1f6feb; margin-top: 10px;'></div>
</div>
""", unsafe_allow_html=True)

menu = st.sidebar.radio("", ["INVENTARIO", "ENTRADAS", "SALIDAS", "HISTORIAL", "PRODUCTOS", "ASISTENTE"])

st.sidebar.markdown("<hr>", unsafe_allow_html=True)

# Alertas de reorden en sidebar
df_alertas = pd.read_sql_query("SELECT nombre, stock, reorden FROM productos WHERE stock <= reorden", conn)
if not df_alertas.empty:
    st.sidebar.markdown("<div style='color:#f85149; font-family: Barlow Condensed; font-size:13px; letter-spacing:1px; font-weight:700;'>⚠ REORDEN REQUERIDO</div>", unsafe_allow_html=True)
    for _, r in df_alertas.iterrows():
        st.sidebar.markdown(f"<div class='alerta-box'>▸ {r['nombre']}<br><span style='color:#f85149;'>{r['stock']} pzas</span></div>", unsafe_allow_html=True)
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)

st.sidebar.markdown(f"<div style='color:#8b949e; font-size:12px; letter-spacing:1px;'>SESIÓN: {st.session_state.username.upper()}</div>", unsafe_allow_html=True)
if st.sidebar.button("CERRAR SESIÓN", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

# --- MÓDULO: INVENTARIO ---
if menu == "INVENTARIO":
    st.markdown("""
    <div class='header-strip'>
        <h1>INVENTARIO BODEGA</h1>
        <span>existencias actuales · taller de perico</span>
    </div>
    """, unsafe_allow_html=True)

    df_inv = pd.read_sql_query("""
        SELECT codigo AS 'CÓDIGO', nombre AS 'NOMBRE', marca AS 'MARCA',
               modelo AS 'MODELO', stock AS 'STOCK', reorden AS 'REORDEN'
        FROM productos ORDER BY nombre
    """, conn)

    total_piezas = df_inv['STOCK'].sum()
    bajo_reorden = len(df_inv[df_inv['STOCK'] <= df_inv['REORDEN']])
    total_productos = len(df_inv)

    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL PIEZAS EN BODEGA", f"{total_piezas:,}")
    c2.metric("PRODUCTOS REGISTRADOS", total_productos)
    c3.metric("BAJO PUNTO DE REORDEN", bajo_reorden)

    st.markdown("<hr>", unsafe_allow_html=True)

    def highlight_reorden(row):
        if row['STOCK'] <= row['REORDEN']:
            return ['background-color: #1a0a0a; color: #f85149'] * len(row)
        return [''] * len(row)

    st.dataframe(
        df_inv.style.apply(highlight_reorden, axis=1),
        use_container_width=True,
        hide_index=True
    )

# --- MÓDULO: ENTRADAS ---
elif menu == "ENTRADAS":
    st.markdown("""
    <div class='header-strip'>
        <h1>REGISTRAR ENTRADA</h1>
        <span>recepción de mercancía · bodega</span>
    </div>
    """, unsafe_allow_html=True)

    df_prod = pd.read_sql_query("SELECT id, codigo, nombre, stock FROM productos ORDER BY nombre", conn)
    opciones = [f"{r['codigo']} — {r['nombre']}  (stock: {r['stock']})" for _, r in df_prod.iterrows()]

    seleccion = st.selectbox("PRODUCTO", opciones)
    cantidad  = st.number_input("CANTIDAD QUE ENTRA", min_value=1, value=1)
    fecha     = st.date_input("FECHA", value=datetime.today())
    notas     = st.text_input("NOTAS (opcional)", placeholder="Ej: compra a proveedor, lote #...")

    if st.button("REGISTRAR ENTRADA", use_container_width=True):
        idx   = opciones.index(seleccion)
        pid   = int(df_prod.iloc[idx]['id'])
        cod   = df_prod.iloc[idx]['codigo']
        c = conn.cursor()
        c.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (cantidad, pid))
        c.execute("INSERT INTO movimientos (fecha, tipo, motivo, producto_id, cantidad, notas) VALUES (?,?,?,?,?,?)",
                  (str(fecha), 'ENTRADA', 'Recepción de mercancía', pid, cantidad, notas))
        conn.commit()
        st.success(f"Entrada registrada: +{cantidad} pzas de {df_prod.iloc[idx]['nombre']}")
        st.rerun()

# --- MÓDULO: SALIDAS ---
elif menu == "SALIDAS":
    st.markdown("""
    <div class='header-strip'>
        <h1>REGISTRAR SALIDA</h1>
        <span>despacho de piezas · bodega</span>
    </div>
    """, unsafe_allow_html=True)

    MOTIVOS = {
        "Surtir Mostrador":        "Se envía mercancía al área de mostrador",
        "Venta Directa Bodega":    "Venta directa al cliente desde bodega",
        "Pieza Dañada / Baja":     "Pieza dañada, defectuosa o dada de baja",
    }

    df_prod = pd.read_sql_query("SELECT id, codigo, nombre, stock FROM productos WHERE stock > 0 ORDER BY nombre", conn)

    if df_prod.empty:
        st.warning("No hay productos con stock disponible en bodega.")
    else:
        opciones = [f"{r['codigo']} — {r['nombre']}  (stock: {r['stock']})" for _, r in df_prod.iterrows()]

        seleccion = st.selectbox("PRODUCTO", opciones)
        motivo    = st.selectbox("MOTIVO DE SALIDA", list(MOTIVOS.keys()))
        idx       = opciones.index(seleccion)
        stock_act = int(df_prod.iloc[idx]['stock'])

        st.markdown(f"<div style='color:#8b949e; font-size:13px; margin-bottom:8px;'>▸ {MOTIVOS[motivo]}</div>", unsafe_allow_html=True)

        cantidad  = st.number_input("CANTIDAD QUE SALE", min_value=1, max_value=stock_act, value=1)
        fecha     = st.date_input("FECHA", value=datetime.today())
        notas     = st.text_input("NOTAS (opcional)", placeholder="Ej: folio, nombre cliente, descripción daño...")

        if st.button("REGISTRAR SALIDA", use_container_width=True):
            pid = int(df_prod.iloc[idx]['id'])
            c = conn.cursor()
            c.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (cantidad, pid))
            c.execute("INSERT INTO movimientos (fecha, tipo, motivo, producto_id, cantidad, notas) VALUES (?,?,?,?,?,?)",
                      (str(fecha), 'SALIDA', motivo, pid, cantidad, notas))
            conn.commit()
            st.success(f"Salida registrada: -{cantidad} pzas de {df_prod.iloc[idx]['nombre']} ({motivo})")
            st.rerun()

# --- MÓDULO: HISTORIAL ---
elif menu == "HISTORIAL":
    st.markdown("""
    <div class='header-strip'>
        <h1>HISTORIAL DE MOVIMIENTOS</h1>
        <span>entradas y salidas · bodega</span>
    </div>
    """, unsafe_allow_html=True)

    col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
    with col_f1:
        filtro_tipo = st.selectbox("TIPO", ["TODOS", "ENTRADA", "SALIDA"])
    with col_f2:
        filtro_motivo = st.selectbox("MOTIVO", ["TODOS", "Recepción de mercancía", "Surtir Mostrador", "Venta Directa Bodega", "Pieza Dañada / Baja"])
    with col_f3:
        filtro_fecha = st.date_input("DESDE", value=datetime(2024, 1, 1))

    query = """
        SELECT m.fecha AS 'FECHA', m.tipo AS 'TIPO', m.motivo AS 'MOTIVO',
               p.codigo AS 'CÓDIGO', p.nombre AS 'PRODUCTO',
               m.cantidad AS 'CANTIDAD', m.notas AS 'NOTAS'
        FROM movimientos m
        JOIN productos p ON m.producto_id = p.id
        WHERE m.fecha >= ?
    """
    params = [str(filtro_fecha)]

    if filtro_tipo != "TODOS":
        query += " AND m.tipo = ?"
        params.append(filtro_tipo)
    if filtro_motivo != "TODOS":
        query += " AND m.motivo = ?"
        params.append(filtro_motivo)

    query += " ORDER BY m.fecha DESC, m.id DESC"

    df_hist = pd.read_sql_query(query, conn, params=params)

    if df_hist.empty:
        st.info("No hay movimientos con los filtros seleccionados.")
    else:
        entradas = df_hist[df_hist['TIPO'] == 'ENTRADA']['CANTIDAD'].sum()
        salidas  = df_hist[df_hist['TIPO'] == 'SALIDA']['CANTIDAD'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("MOVIMIENTOS", len(df_hist))
        c2.metric("TOTAL ENTRADAS", f"+{entradas:,}")
        c3.metric("TOTAL SALIDAS",  f"-{salidas:,}")

        def color_tipo(row):
            if row['TIPO'] == 'ENTRADA':
                return ['color: #3fb950'] * len(row)
            return ['color: #f85149'] * len(row)

        st.dataframe(
            df_hist.style.apply(color_tipo, axis=1),
            use_container_width=True,
            hide_index=True
        )

# --- MÓDULO: PRODUCTOS ---
elif menu == "PRODUCTOS":
    st.markdown("""
    <div class='header-strip'>
        <h1>GESTIÓN DE PRODUCTOS</h1>
        <span>catálogo de piezas · bodega</span>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["AGREGAR PRODUCTO", "EDITAR / ELIMINAR"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            codigo = st.text_input("CÓDIGO", placeholder="Ej: K003")
            nombre = st.text_input("NOMBRE", placeholder="Ej: Filtro de Aire")
            marca  = st.text_input("MARCA",  placeholder="Ej: Italika")
        with c2:
            modelo  = st.text_input("MODELO COMPATIBLE", placeholder="Ej: FT150 / Universal")
            stock   = st.number_input("STOCK INICIAL", min_value=0, value=0)
            reorden = st.number_input("PUNTO DE REORDEN", min_value=0, value=5)

        if st.button("GUARDAR PRODUCTO", use_container_width=True):
            if not codigo or not nombre:
                st.error("Código y nombre son obligatorios.")
            else:
                try:
                    c = conn.cursor()
                    c.execute("INSERT INTO productos (codigo, nombre, marca, modelo, stock, reorden) VALUES (?,?,?,?,?,?)",
                              (codigo.upper(), nombre, marca, modelo, stock, reorden))
                    conn.commit()
                    st.success(f"Producto '{nombre}' agregado correctamente.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(f"El código '{codigo}' ya existe.")

    with tab2:
        df_edit = pd.read_sql_query("SELECT id, codigo, nombre, marca, modelo, stock, reorden FROM productos ORDER BY nombre", conn)
        opciones_edit = [f"{r['codigo']} — {r['nombre']}" for _, r in df_edit.iterrows()]
        sel_edit = st.selectbox("SELECCIONAR PRODUCTO", opciones_edit)
        idx_e = opciones_edit.index(sel_edit)
        row   = df_edit.iloc[idx_e]

        c1, c2 = st.columns(2)
        with c1:
            e_nombre  = st.text_input("NOMBRE",  value=row['nombre'],  key="e_nom")
            e_marca   = st.text_input("MARCA",   value=row['marca'],   key="e_mar")
            e_modelo  = st.text_input("MODELO",  value=row['modelo'],  key="e_mod")
        with c2:
            e_stock   = st.number_input("STOCK",          value=int(row['stock']),   min_value=0, key="e_stk")
            e_reorden = st.number_input("PUNTO REORDEN",  value=int(row['reorden']), min_value=0, key="e_reo")

        col_save, col_del = st.columns(2)
        with col_save:
            if st.button("GUARDAR CAMBIOS", use_container_width=True):
                c = conn.cursor()
                c.execute("UPDATE productos SET nombre=?, marca=?, modelo=?, stock=?, reorden=? WHERE id=?",
                          (e_nombre, e_marca, e_modelo, e_stock, e_reorden, int(row['id'])))
                conn.commit()
                st.success("Producto actualizado.")
                st.rerun()
        with col_del:
            if st.button("ELIMINAR PRODUCTO", use_container_width=True):
                c = conn.cursor()
                c.execute("DELETE FROM productos WHERE id=?", (int(row['id']),))
                conn.commit()
                st.warning(f"Producto '{row['nombre']}' eliminado.")
                st.rerun()

# --- MÓDULO: ASISTENTE ---
elif menu == "ASISTENTE":
    st.markdown("""
    <div class='header-strip'>
        <h1>ASISTENTE DE BODEGA</h1>
        <span>consultas en lenguaje natural · groq ai</span>
    </div>
    """, unsafe_allow_html=True)

    df_ctx = pd.read_sql_query("SELECT codigo, nombre, marca, modelo, stock, reorden FROM productos", conn)
    df_mov = pd.read_sql_query("""
        SELECT m.fecha, m.tipo, m.motivo, p.codigo, p.nombre, p.marca, m.cantidad, m.notas
        FROM movimientos m JOIN productos p ON m.producto_id = p.id
        ORDER BY m.fecha DESC, m.id DESC LIMIT 100
    """, conn)

    SYSTEM_PROMPT = f"""Eres el asistente de bodega del Taller de Perico, una refaccionaria de motocicletas.
Respondes preguntas sobre el inventario y movimientos de bodega de forma clara y directa en español.
Solo respondes preguntas relacionadas al inventario y la bodega.

INVENTARIO ACTUAL:
{df_ctx.to_string(index=False)}

ÚLTIMOS 100 MOVIMIENTOS:
{df_mov.to_string(index=False)}

Si no encuentras la información exacta, dilo claramente. Sé conciso."""

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            st.markdown(f"""
            <div style='background:#161b22; border-left:3px solid #1f6feb;
                        padding:10px 14px; margin:8px 0; border-radius:2px;'>
                <span style='color:#8b949e; font-size:11px; letter-spacing:1px;'>TÚ</span><br>
                <span style='color:#c9d1d9;'>{msg['content']}</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='background:#0d1f0d; border-left:3px solid #3fb950;
                        padding:10px 14px; margin:8px 0; border-radius:2px;'>
                <span style='color:#8b949e; font-size:11px; letter-spacing:1px;'>ASISTENTE</span><br>
                <span style='color:#c9d1d9;'>{msg['content']}</span>
            </div>""", unsafe_allow_html=True)

    with st.form(key='chat_form', clear_on_submit=True):
        col_inp, col_btn = st.columns([5, 1])
        with col_inp:
            pregunta = st.text_input("", placeholder="Ej: ¿Hay kit de arrastre? ¿Cuántas bujías NGK hay?")
        with col_btn:
            enviar = st.form_submit_button("ENVIAR", use_container_width=True)

    if enviar and pregunta.strip():
        st.session_state.chat_history.append({'role': 'user', 'content': pregunta})
        try:
            client = Groq(api_key=get_groq_key())
            messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
            for m in st.session_state.chat_history[-6:]:
                messages.append({'role': m['role'], 'content': m['content']})
            response = client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=messages,
                temperature=0.2,
                max_tokens=512
            )
            respuesta = response.choices[0].message.content
        except Exception as e:
            respuesta = f"Error al conectar con el asistente: {e}"
        st.session_state.chat_history.append({'role': 'assistant', 'content': respuesta})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("LIMPIAR CONVERSACIÓN"):
            st.session_state.chat_history = []
            st.rerun()

conn.close()
