import streamlit as st
st.components.v1.html("""
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3410419794913660"
     crossorigin="anonymous"></script>
""", height=0, width=0)
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime
import pytz
import plotly.graph_objects as go
import xml.etree.ElementTree as ET
import re
import json
import os
import uuid
import hashlib

# ============================================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y BASE DE DATOS LOCAL
# ============================================================

st.set_page_config(
    page_title="Monitor Financiero",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

DB_FILE = "usuarios_carteras.json"

def default_user_data():
    return {
        "password": "",
        "session_token": "", # NUEVO: Para que no te desloguee al cambiar de pantalla
        "efectivo_ars": 0.0,
        "efectivo_usd": 0.0,
        "inversiones": [], 
        "watchlist": [], 
        "activos_manuales": {}, 
        "movimientos": [] 
    }

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def es_correo_valido(correo):
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(patron, correo) is not None

def cargar_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def guardar_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

def sincronizar_datos():
    if "user_email" in st.session_state and st.session_state.user_email:
        db = cargar_db()
        db[st.session_state.user_email] = st.session_state.user_data
        guardar_db(db)

# Cargar la base de datos para verificar el token
db_general = cargar_db()
token_url = st.query_params.get("t", None)

# SISTEMA ANTI-DESLOGUEO: Si hay un token en la URL, auto-iniciamos sesión
if token_url and "user_email" not in st.session_state:
    for email, data in db_general.items():
        if data.get("session_token") == token_url:
            st.session_state.user_email = email
            st.session_state.user_data = data
            break

if 'user_data' not in st.session_state:
    st.session_state.user_data = default_user_data()


# ============================================================
# 2. INYECCIÓN DE CSS Y HTML (NAVBAR Y FOOTER FIJOS)
# ============================================================

# Preparamos el token para inyectarlo en los links del menú
token_actual = st.query_params.get("t", "")
base_qs = f"&t={token_actual}" if token_actual else ""

if st.session_state.get("user_email"):
    nav_login_text = f"👤 Mi Cuenta"
    nav_login_link = f"?nav=login{base_qs}"
else:
    nav_login_text = "🔑 Iniciar Sesión"
    nav_login_link = f"?nav=login{base_qs}"

st.markdown(f"""
<style>
    [data-testid="collapsedControl"] {{ display: none; }}
    header {{ display: none !important; }}
    
    .block-container {{
        padding-top: 90px !important;
        padding-bottom: 70px !important;
    }}

    /* Barra Superior con altura fija */
    .navbar {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 60px; 
        background-color: #0d1117;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        display: flex;
        align-items: center;
        padding: 0 24px;
        border-bottom: 1px solid #30363d;
        z-index: 99999;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }}

    .navbar a.brand {{
        font-size: 20px;
        font-weight: 700;
        color: #00e676;
        text-decoration: none;
        padding: 0;
        margin-right: 20px;
        letter-spacing: 0.5px;
    }}

    .dropdown {{
        float: left;
        position: relative; 
        height: 100%; 
        display: flex;
        align-items: center; 
    }}

    .dropdown .dropbtn {{
        font-size: 15px;
        border: none;
        outline: none;
        color: #c9d1d9;
        padding: 0 18px;
        background-color: inherit;
        font-family: inherit;
        margin: 0;
        cursor: pointer;
        height: 100%; 
        transition: color 0.2s;
    }}

    .navbar a:hover, .dropdown:hover .dropbtn {{
        color: #00e676;
        background-color: #161b22;
    }}

    .dropdown-content {{
        display: none;
        position: absolute;
        background-color: #161b22;
        min-width: 240px;
        box-shadow: 0px 10px 24px 0px rgba(0,0,0,0.6);
        z-index: 100000;
        border: 1px solid #30363d;
        border-radius: 0 0 6px 6px;
        top: 100%; 
        left: 0;
    }}

    .dropdown-content a {{
        float: none;
        color: #c9d1d9;
        padding: 14px 18px;
        text-decoration: none;
        display: block;
        text-align: left;
        font-size: 14px;
        transition: background 0.2s, color 0.2s;
    }}

    .dropdown-content a:hover {{
        background-color: #1f6feb33;
        color: #00e676;
        font-weight: 600;
    }}

    .dropdown:hover .dropdown-content {{
        display: block;
    }}

    .login-btn {{
        margin-left: auto;
        color: #00e676 !important;
        text-decoration: none;
        font-weight: bold;
        padding: 8px 16px;
        border: 1px solid #00e676;
        border-radius: 5px;
        transition: all 0.2s;
        font-size: 14px;
    }}
    .login-btn:hover {{
        background-color: #00e676;
        color: #0d1117 !important;
    }}

    .fixed-footer {{
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0d1117;
        color: #8b949e;
        text-align: center;
        padding: 10px 0;
        font-size: 12px;
        border-top: 1px solid #30363d;
        z-index: 9998;
        letter-spacing: 0.3px;
    }}
    
    .news-card {{
        background-color: #161b22;
        padding: 22px;
        border-radius: 8px;
        border: 1px solid #30363d;
        border-left: 4px solid #00e676;
        height: 100%;
        display: flex;
        flex-direction: column;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}

    .news-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(0,230,118,0.1);
    }}
    
    .news-card a {{
        color: #58a6ff;
        text-decoration: none;
        margin-top: auto;
        font-weight: 600;
        font-size: 0.9rem;
        transition: color 0.2s;
    }}
    
    .news-card a:hover {{
        color: #00e676;
        text-decoration: underline;
    }}
</style>

<div class="navbar">
<a class="brand" href="?nav=inicio{base_qs}" target="_top">📊 Monitor Financiero</a>

<div class="dropdown">
<button class="dropbtn">💼 Mi Gestión ▾</button>
<div class="dropdown-content">
<a href="?nav=finanzas{base_qs}" target="_top">💰 Finanzas y Patrimonio</a>
<a href="?nav=portfolio{base_qs}" target="_top">👀 Watchlist (Seguimiento)</a>
</div>
</div>

<div class="dropdown">
<button class="dropbtn">Internacional ▾</button>
<div class="dropdown-content">
<a href="?nav=int_acciones{base_qs}" target="_top">📈 Acciones Internacionales</a>
<a href="?nav=int_bonos{base_qs}" target="_top">📄 Bonos Internacionales</a>
<a href="?nav=int_commodities{base_qs}" target="_top">🛢️ Commodities</a>
<a href="?nav=int_etfs{base_qs}" target="_top">📊 ETFs Globales</a>
<a href="?nav=int_datos{base_qs}" target="_top">🏦 Datos Macroeconómicos</a>
</div>
</div>
<div class="dropdown">
<button class="dropbtn">Argentina ▾</button>
<div class="dropdown-content">
<a href="?nav=arg_acciones{base_qs}" target="_top">📈 Acciones Locales (Pesos)</a>
<a href="?nav=arg_ons{base_qs}" target="_top">📄 Obligaciones Negociables</a>
<a href="?nav=arg_bonos{base_qs}" target="_top">📄 Bonos Argentinos</a>
<a href="?nav=arg_etfs{base_qs}" target="_top">📊 Índices y ETFs</a>
<a href="?nav=arg_datos{base_qs}" target="_top">🏦 Datos Económicos</a>
</div>
</div>
<div class="dropdown">
<button class="dropbtn">🧮 Herramientas ▾</button>
<div class="dropdown-content">
<a href="?nav=calc_interes{base_qs}" target="_top">📈 Calc. Interés Compuesto</a>
<a href="?nav=calc_francesa{base_qs}" target="_top">🏛️ Amortización Francesa</a>
</div>
</div>
<div class="dropdown">
<button class="dropbtn">⚖️ Legal ▾</button>
<div class="dropdown-content">
<a href="?nav=legal{base_qs}" target="_top">📜 Términos y Condiciones</a>
</div>
</div>

<a class="login-btn" href="{nav_login_link}" target="_top">{nav_login_text}</a>
</div>
""", unsafe_allow_html=True)

nav = st.query_params.get("nav", "inicio")


# ============================================================
# 3. EXTRACCIÓN DE DATOS Y NOTICIAS
# ============================================================

@st.cache_data(ttl=300)
def obtener_datos_globales():
    tickers = {
        "Treasury 2Y": "^IRX", "Treasury 5Y": "^FVX", "Treasury 10Y": "^TNX", "Treasury 30Y": "^TYX",
        "Oro": "GC=F", "WTI": "CL=F", "Bitcoin": "BTC-USD",
        "S&P 500 (Índice)": "^GSPC", "SPY (ETF)": "SPY", "QQQ (ETF Nasdaq)": "QQQ", "DIA (ETF Dow)": "DIA",
        "Apple": "AAPL", "Nvidia": "NVDA", "Tesla": "TSLA", "Microsoft": "MSFT",
        "Amazon": "AMZN", "Google": "GOOGL", "Meta": "META", "Nestlé": "NSRGY",
        "Johnson & Johnson": "JNJ", "Coca-Cola": "KO", "Visa": "V", "Walmart": "WMT",
        "JPMorgan": "JPM", "Procter & Gamble": "PG", "Disney": "DIS",
        "Merval ARS": "^MERV", "SPY (CEDEAR)": "SPY.BA", "QQQ (CEDEAR)": "QQQ.BA",
        "YPF": "YPFD.BA", "Galicia": "GGAL.BA", "Pampa Energía": "PAMP.BA",
        "Banco Macro": "BMA.BA", "Central Puerto": "CEPU.BA", "Aluar": "ALUA.BA",
        "Ternium": "TXAR.BA", "Loma Negra": "LOMA.BA", "Trans. Gas del Norte": "TGNO4.BA",
        "Trans. Gas del Sur": "TGSU2.BA", "Edenor": "EDN.BA", "Transener": "TRAN.BA",
        "BYMA": "BYMA.BA", "Valo": "VALO.BA", "Mirgor": "MIRG.BA",
        "Supervielle": "SUPV.BA", "BBVA AR": "BBAR.BA", "Cablevisión": "CVH.BA",
        "Richmond": "RICH.BA", "Agrometal": "AGRO.BA"
    }
    
    simbolos = list(tickers.values())
    resultado = {}
    
    try:
        datos = yf.download(simbolos, period="1mo", progress=False, auto_adjust=False)
        for nombre, ticker in tickers.items():
            try:
                cierres = datos["Close"][ticker].ffill().dropna()
                if len(cierres) >= 2:
                    ultimo = float(cierres.iloc[-1])
                    previo = float(cierres.iloc[-2])
                    resultado[nombre] = {"precio": ultimo, "var_pct": ((ultimo - previo) / previo) * 100, "ticker": ticker}
                elif len(cierres) == 1:
                    resultado[nombre] = {"precio": float(cierres.iloc[-1]), "var_pct": 0.0, "ticker": ticker}
                else:
                    resultado[nombre] = None
            except:
                resultado[nombre] = None
    except:
        for nombre in tickers:
            resultado[nombre] = None
            
    return resultado

@st.cache_data(ttl=300)
def obtener_bonos_argentinos():
    bonos_tickers = {"AL29": "AL29.BA", "AL30": "AL30.BA", "AE38": "AE38.BA", "GD30": "GD30.BA", "GD35": "GD35.BA"}
    resultado = {k: None for k in bonos_tickers.keys()}
    
    for nombre, ticker in bonos_tickers.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="1mo")
            if not hist.empty and len(hist) >= 2:
                hist_close = hist['Close'].ffill().dropna()
                u = float(hist_close.iloc[-1])
                p = float(hist_close.iloc[-2])
                resultado[nombre] = {"precio": u, "var_pct": ((u - p) / p) * 100}
        except: pass

    try:
        r = requests.get("https://api.argentinadatos.com/v1/finanzas/cotizaciones/bonos", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            for bono in bonos_tickers.keys():
                if resultado[bono] is None: 
                    df_bono = df[df["ticker"] == bono].copy()
                    if not df_bono.empty:
                        df_bono = df_bono.sort_values("fecha")
                        if len(df_bono) >= 2:
                            u = float(df_bono.iloc[-1]["cierre"])
                            p = float(df_bono.iloc[-2]["cierre"])
                            resultado[bono] = {"precio": u, "var_pct": ((u - p) / p) * 100}
    except: pass
        
    return resultado

@st.cache_data(ttl=300)
def obtener_macro_argentina():
    datos = {"dolares": {}, "uva": None, "riesgo_pais": "N/D"}
    try:
        r = requests.get("https://dolarapi.com/v1/dolares", headers=HEADERS, timeout=5)
        datos["dolares"] = {item["casa"]: float(item["venta"]) for item in r.json()}
    except: pass
    
    try:
        r = requests.get("https://api.argentinadatos.com/v1/finanzas/indices/uva", headers=HEADERS, timeout=5)
        df_uva = pd.DataFrame(r.json()).sort_values("fecha")
        if not df_uva.empty:
            u = float(df_uva.iloc[-1]["valor"])
            datos["uva"] = {"valor": u, "fecha": df_uva.iloc[-1]["fecha"]}
    except: pass

    try:
        r = requests.get("https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais", headers=HEADERS, timeout=5)
        df_rp = pd.DataFrame(r.json()).sort_values("fecha")
        if not df_rp.empty:
            rp = float(df_rp.iloc[-1]["valor"])
            datos["riesgo_pais"] = f"{rp:,.0f} pb"
    except: pass
    
    return datos

@st.cache_data(ttl=1800)
def obtener_noticias_dinamicas():
    noticias_int = []
    noticias_arg = []
    
    def limpiar_html(raw_html):
        cleanr = re.compile('<.*?>')
        text = re.sub(cleanr, '', raw_html) if raw_html else ""
        text = text.replace("&nbsp;", " ").replace("&#39;", "'").replace("&quot;", '"').strip()
        return text[:160] + "..." if len(text) > 160 else text

    try:
        url_int = "https://news.google.com/rss/search?q=wall+street+markets+finance&hl=es-419&gl=US&ceid=US:es"
        r = requests.get(url_int, headers=HEADERS, timeout=5)
        root = ET.fromstring(r.content)
        for idx, item in enumerate(root.findall('./channel/item')[:6]):
            titulo = item.find('title').text
            link = item.find('link').text
            desc = limpiar_html(item.find('description').text if item.find('description') is not None else "")
            noticias_int.append({"categoria": "INTERNACIONAL", "titulo": titulo, "desc": desc, "link": link})
    except: pass

    try:
        url_arg = "https://news.google.com/rss/search?q=economia+finanzas+argentina+merval+dolar&hl=es-419&gl=AR&ceid=AR:es-419"
        r = requests.get(url_arg, headers=HEADERS, timeout=5)
        root = ET.fromstring(r.content)
        for idx, item in enumerate(root.findall('./channel/item')[:6]):
            titulo = item.find('title').text
            link = item.find('link').text
            desc = limpiar_html(item.find('description').text if item.find('description') is not None else "")
            noticias_arg.append({"categoria": "ARGENTINA", "titulo": titulo, "desc": desc, "link": link})
    except: pass

    noticias_combinadas = []
    max_len = max(len(noticias_int), len(noticias_arg))
    for i in range(max_len):
        if i < len(noticias_int): noticias_combinadas.append(noticias_int[i])
        if i < len(noticias_arg): noticias_combinadas.append(noticias_arg[i])

    if not noticias_combinadas:
        noticias_combinadas = [{"categoria": "MERCADO", "titulo": "Actualización de Mercado", "desc": "Revisa los últimos movimientos en los indicadores globales.", "link": "#"}]
        
    return noticias_combinadas
@st.cache_data(ttl=86400) # Se actualiza una vez al día para no saturar
def obtener_historico_ccl():
    try:
        r = requests.get("https://api.argentinadatos.com/v1/cotizaciones/dolares", timeout=5)
        df = pd.DataFrame(r.json())
        df_ccl = df[df['casa'] == 'contadoconliqui'].copy()
        df_ccl['fecha'] = pd.to_datetime(df_ccl['fecha']).dt.date
        df_ccl = df_ccl.sort_values('fecha')
        return df_ccl
    except:
        return None

def get_ccl_en_fecha(fecha_str, df_ccl, ccl_actual):
    if df_ccl is None or df_ccl.empty: return ccl_actual
    try:
        # Convertimos el string a objeto date
        if isinstance(fecha_str, str):
            fecha_buscada = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        else:
            fecha_buscada = fecha_str
            
        df_filtrado = df_ccl[df_ccl['fecha'] <= fecha_buscada]
        if not df_filtrado.empty:
            return float(df_filtrado.iloc[-1]['venta'])
        return ccl_actual
    except:
        return ccl_actual
globales = obtener_datos_globales()
bonos_arg = obtener_bonos_argentinos()
macro_arg = obtener_macro_argentina()
noticias_feed = obtener_noticias_dinamicas()

def get_precio_actual(ticker):
    try:
        # Si el ticker no tiene punto, intentamos primero buscarlo como activo local con .BA (CEDEAR / Bono / Acción Local)
        if not ticker.endswith(".BA") and not ticker.endswith("D"):
            t_local = f"{ticker}.BA"
            p_local = yf.Ticker(t_local).fast_info.last_price
            if p_local and p_local > 0:
                return float(p_local)
        
        # Si falla o es un ticker directo de EE.UU.
        p = yf.Ticker(ticker).fast_info.last_price
        return float(p) if p and p > 0 else 0.0
    except:
        return 0.0

def format_metric(val, is_pct=False):
    if val is None or val == "-":
        return "-"
    try:
        if is_pct:
            return f"{(val * 100):.2f}%"
        if val > 1000000000:
            return f"${val/1000000000:,.2f} B"
        if val > 1000000:
            return f"${val/1000000:,.2f} M"
        return f"{val:.2f}"
    except:
        return str(val)

# ============================================================
# 4. RENDERIZADO DE LAS PÁGINAS SEGÚN EL MENÚ
# ============================================================

if nav == "login":
    st.title("👤 Acceso a Mi Cuenta")
    
    if "user_email" not in st.session_state:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🔑 Iniciar Sesión")
            with st.form("login_form"):
                login_email = st.text_input("Email:")
                login_pass = st.text_input("Contraseña:", type="password")
                btn_login = st.form_submit_button("Entrar", use_container_width=True)
                
                if btn_login:
                    db = cargar_db()
                    if login_email in db:
                        if db[login_email].get("password") == hash_password(login_pass):
                            st.session_state.user_email = login_email
                            
                            # CÓDIGO CLAVE: Generar el token de sesión seguro
                            new_token = str(uuid.uuid4())
                            db[login_email]["session_token"] = new_token
                            
                            user_data = db[login_email]
                            st.session_state.user_data = user_data
                            guardar_db(db)
                            
                            # Inyectar el token en la URL de inmediato
                            st.query_params["t"] = new_token
                            
                            st.success("✅ Sesión iniciada. Navega por el menú superior libremente.")
                            st.rerun()
                        else:
                            st.error("❌ Contraseña incorrecta.")
                    else:
                        st.error("❌ El usuario no existe. Regístrate en el panel derecho.")
                        
        with c2:
            st.subheader("📝 Registrar Nueva Cuenta")
            with st.form("register_form"):
                reg_email = st.text_input("Nuevo Email:")
                reg_pass = st.text_input("Nueva Contraseña:", type="password")
                reg_pass2 = st.text_input("Repetir Contraseña:", type="password")
                btn_reg = st.form_submit_button("Crear Cuenta", use_container_width=True)
                
                if btn_reg:
                    if not es_correo_valido(reg_email):
                        st.error("❌ Por favor, ingresa un formato de correo válido.")
                    elif reg_pass != reg_pass2:
                        st.error("❌ Las contraseñas no coinciden.")
                    elif len(reg_pass) < 6:
                        st.error("❌ La contraseña debe tener al menos 6 caracteres.")
                    else:
                        db = cargar_db()
                        if reg_email in db:
                            st.error("❌ Este correo ya está registrado.")
                        else:
                            nuevo_usuario = default_user_data()
                            nuevo_usuario["password"] = hash_password(reg_pass)
                            db[reg_email] = nuevo_usuario
                            guardar_db(db)
                            st.success("✅ Cuenta creada con éxito. Inicia sesión a la izquierda.")

    else:
        st.success("✅ Estás conectado de forma segura.")
        st.markdown(f"**Usuario Logueado:** `{st.session_state.user_email}`")
        if st.button("🚪 Cerrar Sesión", type="primary"):
            # Borrar el token de la DB y de la sesión local
            email = st.session_state.user_email
            db = cargar_db()
            if email in db:
                db[email]["session_token"] = ""
                guardar_db(db)
                
            del st.session_state.user_email
            del st.session_state.user_data
            if "t" in st.query_params:
                del st.query_params["t"]
            st.rerun()

elif nav == "inicio":
    st.title("📰 Titulares Globales y Locales")
    st.markdown("Revisión de las últimas noticias económicas, puramente informativas y con un diseño centrado en la lectura.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    for i in range(0, len(noticias_feed), 3):
        cols = st.columns(3)
        fila_noticias = noticias_feed[i:i+3]
        for index, articulo in enumerate(fila_noticias):
            with cols[index]:
                card_html = f"""
                <div class="news-card">
                    <span style='color:#00e676; font-size:0.75rem; font-weight:700; letter-spacing: 1.5px;'>{articulo['categoria']}</span>
                    <h3 style='margin-top: 0.8rem; margin-bottom: 0.8rem; font-size: 1.15rem; color: #f0f6fc; font-weight: 600; line-height: 1.3;'>{articulo['titulo']}</h3>
                    <p style="color:#8b949e; font-size: 0.9rem; margin-bottom: 1.2rem; line-height: 1.5;">{articulo.get('desc', '')}</p>
                    <a href='{articulo['link']}' target='_blank'>Leer artículo completo →</a>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                st.markdown('<div style="margin-bottom: 15px;"></div>', unsafe_allow_html=True)

elif nav == "finanzas":
    if not st.session_state.get("user_email"):
        st.warning("⚠️ Debes iniciar sesión (botón arriba a la derecha) para gestionar tus finanzas personales.")
    else:
        st.title("💰 Finanzas, Presupuesto y Patrimonio")
        user_data = st.session_state.user_data
        
        ccl_actual = macro_arg["dolares"].get("contadoconliqui", 1200.0)
        mep_actual = macro_arg["dolares"].get("mep", macro_arg["dolares"].get("bolsa", 1180.0))
        df_ccl_hist = obtener_historico_ccl()

        # INICIALIZAR VARIABLES DE ESTADO
        if "edit_inv_id" not in st.session_state:
            st.session_state.edit_inv_id = None
        if "vender_inv_ticker" not in st.session_state:
            st.session_state.vender_inv_ticker = None

        # SELECTOR GLOBAL DE MONEDA (USD / ARS)
        st.markdown("### ⚙️ Preferencia de Visualización")
        modo_moneda_global = st.radio("Mostrar toda la pantalla en:", ["Dólares (USD)", "Pesos Argentinos (ARS)"], horizontal=True, key="global_currency_selector")

        # CÁLCULO DE SALDOS NETOS
        apps_ars = 0.0
        apps_usd = 0.0
        efectivo_ars = 0.0
        efectivo_usd = 0.0
        
        for m in user_data.get("movimientos", []):
            cat = m.get("tipo")
            monto = m.get("monto", 0.0)
            moneda = m.get("moneda", "ARS")
            descuenta_efectivo = m.get("descuenta_efectivo", True)
            
            if cat == "Sueldo / Ingreso":
                if moneda == "ARS": efectivo_ars += monto
                else: efectivo_usd += monto
            elif cat == "Gasto":
                if moneda == "ARS": efectivo_ars -= abs(monto)
                else: efectivo_usd -= abs(monto)
            elif cat == "Transferencia a App (Fondeo)":
                if descuenta_efectivo:
                    if moneda == "ARS": efectivo_ars -= abs(monto)
                    else: efectivo_usd -= abs(monto)
                if moneda == "ARS": apps_ars += abs(monto)
                else: apps_usd += abs(monto)
            elif cat == "Inversión (Compra de Activo)":
                if moneda == "ARS": apps_ars -= abs(monto)
                else: apps_usd -= abs(monto)
            elif cat in ["Ingreso Extraordinario", "Venta de Activo"]:
                if moneda == "ARS": apps_ars += monto
                else: apps_usd += monto

        # VALOR ACTUAL DE ACTIVOS EN BROKERS (SOLO ACTIVOS)
        valor_portafolio_usd = 0.0
        inversiones_activas = [i for i in user_data.get("inversiones", []) if i.get("estado", "activo") == "activo"]
        
        for inv in inversiones_activas:
            t = inv["ticker"]
            p_act = get_precio_actual(t)
            if p_act == 0.0:
                p_act = inv["precio_compra"]

            tipo_dolar_inv = inv.get("tipo_dolar", "CCL")
            tasa_ref = mep_actual if tipo_dolar_inv == "MEP" else ccl_actual

            if inv.get("es_cedear") and inv["moneda"] == "ARS":
                valor_portafolio_usd += (inv["cantidad"] * p_act) / tasa_ref
            else:
                val_orig = inv["cantidad"] * p_act
                valor_portafolio_usd += val_orig if inv["moneda"] in ['USD', 'MEP'] else val_orig / tasa_ref

        # PATRIMONIO NETO TOTAL
        efectivo_total_usd_eq = efectivo_usd + (efectivo_ars / ccl_actual) + apps_usd + (apps_ars / ccl_actual)
        patrimonio_total_usd = efectivo_total_usd_eq + valor_portafolio_usd
        patrimonio_total_ars = patrimonio_total_usd * ccl_actual

        # 4 TARJETAS SUPERIORES
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        with col_m1:
            val_mo = patrimonio_total_usd if modo_moneda_global == "Dólares (USD)" else patrimonio_total_ars
            sim_mo = "USD" if modo_moneda_global == "Dólares (USD)" else "ARS $"
            st.markdown(f"""
            <div style="background-color: #161b22; padding: 12px; border-radius: 10px; border: 1px solid #30363d; text-align: center;">
                <p style="color: #8b949e; margin: 0; font-size: 0.75rem; text-transform: uppercase;">Patrimonio Neto</p>
                <h4 style="color: #00e676; margin: 5px 0;">{sim_mo} {val_mo:,.2f}</h4>
            </div>""", unsafe_allow_html=True)
                
        with col_m2:
            val_ef = (efectivo_usd + (efectivo_ars / ccl_actual)) if modo_moneda_global == "Dólares (USD)" else (efectivo_ars + (efectivo_usd * ccl_actual))
            sim_ef = "USD" if modo_moneda_global == "Dólares (USD)" else "ARS $"
            st.markdown(f"""
            <div style="background-color: #161b22; padding: 12px; border-radius: 10px; border: 1px solid #30363d; text-align: center;">
                <p style="color: #8b949e; margin: 0; font-size: 0.75rem; text-transform: uppercase;">Efectivo / Sueldo</p>
                <h4 style="color: #58a6ff; margin: 5px 0;">{sim_ef} {val_ef:,.2f}</h4>
            </div>""", unsafe_allow_html=True)

        with col_m3:
            val_app = (apps_usd + (apps_ars / ccl_actual)) if modo_moneda_global == "Dólares (USD)" else (apps_ars + (apps_usd * ccl_actual))
            sim_app = "USD" if modo_moneda_global == "Dólares (USD)" else "ARS $"
            st.markdown(f"""
            <div style="background-color: #161b22; padding: 12px; border-radius: 10px; border: 1px solid #30363d; text-align: center;">
                <p style="color: #8b949e; margin: 0; font-size: 0.75rem; text-transform: uppercase;">Efectivo en Broker</p>
                <h4 style="color: #d29922; margin: 5px 0;">{sim_app} {val_app:,.2f}</h4>
            </div>""", unsafe_allow_html=True)

        with col_m4:
            val_act = valor_portafolio_usd if modo_moneda_global == "Dólares (USD)" else (valor_portafolio_usd * ccl_actual)
            sim_act = "USD" if modo_moneda_global == "Dólares (USD)" else "ARS $"
            st.markdown(f"""
            <div style="background-color: #161b22; padding: 12px; border-radius: 10px; border: 1px solid #30363d; text-align: center;">
                <p style="color: #8b949e; margin: 0; font-size: 0.75rem; text-transform: uppercase;">Activos en Broker</p>
                <h4 style="color: #bc8cff; margin: 5px 0;">{sim_act} {val_act:,.2f}</h4>
            </div>""", unsafe_allow_html=True)

        tab_caja, tab_inversiones = st.tabs(["📅 Flujo de Caja y Transferencias", "💼 Cartera Bursátil y Rendimiento"])

        # ==========================================
        # PESTAÑA 1: MOVIMIENTOS Y TRANSFERENCIAS
        # ==========================================
        with tab_caja:
            col_caja1, col_caja2 = st.columns([1, 2])
            
            with col_caja1:
                st.markdown("### 📥 Registrar Movimiento / Transferencia")
                with st.form("mov_mensual_form"):
                    fecha_mov = st.date_input("Fecha del movimiento")
                    tipo_mov = st.selectbox("Categoría:", ["Sueldo / Ingreso", "Gasto", "Transferencia a App (Fondeo)", "Ingreso Extraordinario"])
                    monto_mov = st.number_input("Monto:", min_value=0.01, value=1000.0, step=1000.0)
                    moneda_mov = st.radio("Moneda:", ["ARS", "USD"], horizontal=True)
                    detalle_mov = st.text_input("Descripción (Ej. Sueldo, Fondeo IOL):")
                    
                    descuenta_efec = False
                    if tipo_mov == "Transferencia a App (Fondeo)":
                        descuenta_efec = st.checkbox("Descontar este monto de mi Efectivo / Sueldo común", value=False)
                    
                    if st.form_submit_button("Guardar Movimiento"):
                        monto_guardar = abs(monto_mov) if tipo_mov in ["Sueldo / Ingreso", "Transferencia a App (Fondeo)", "Ingreso Extraordinario"] else -abs(monto_mov)
                        user_data["movimientos"].append({
                            "id": str(uuid.uuid4()), "fecha": str(fecha_mov),
                            "tipo": tipo_mov, "monto": monto_guardar, 
                            "moneda": moneda_mov, "detalle": detalle_mov,
                            "descuenta_efectivo": descuenta_efec
                        })
                        sincronizar_datos()
                        st.success("✅ Registrado con éxito.")
                        st.rerun()

            with col_caja2:
                st.markdown("### 📋 Historial de Movimientos")
                if user_data.get("movimientos"):
                    for m in sorted(user_data["movimientos"], key=lambda x: x['fecha']):
                        with st.container(border=True):
                            c_t, c_e = st.columns([4, 1])
                            with c_t:
                                monto_visual = abs(m['monto'])
                                color_m = "#00e676" if (m['monto'] > 0 or m['tipo'] == "Transferencia a App (Fondeo)") else "#ff4b4b"
                                st.markdown(f"**{m['fecha']}** | {m['detalle']} (`{m['tipo']}`)")
                                st.markdown(f"<span style='color:{color_m}; font-weight:bold;'>{m['moneda']} {monto_visual:,.2f}</span>", unsafe_allow_html=True)
                            with c_e:
                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("🗑️", key=f"del_btn_{m['id']}"):
                                    mov_id = m['id']
                                    user_data["movimientos"] = [x for x in user_data["movimientos"] if x["id"] != mov_id]
                                    user_data["inversiones"] = [i for i in user_data.get("inversiones", []) if i.get("mov_id") != mov_id]
                                    sincronizar_datos()
                                    st.success("Eliminado y sincronizado.")
                                    st.rerun()
                else:
                    st.info("No hay movimientos registrados.")

        # ==========================================
        # PESTAÑA 2: CARTERA BURSÁTIL Y RENDIMIENTO
        # ==========================================
        with tab_inversiones:
            st.markdown("### 📈 Registro de Activos Bursátiles")
            
            with st.expander("➕ Registrar Compra de Activo", expanded=False):
                with st.form("inv_form_ccl"):
                    diccionario_activos = {
                        "Bono Bonares AL29 (AL29)": "AL29.BA",
                        "Bono Bonares AL30 (AL30)": "AL30.BA",
                        "Bono Bonares AL30D (AL30D)": "AL30D",
                        "Bono Global GD30 (GD30)": "GD30.BA",
                        "Bono Global GD30D (GD30D)": "GD30D",
                        "Bono Global GD35 (GD35)": "GD35.BA",
                        "Bono Global GD38 (GD38)": "GD38.BA",
                        "Bono Global GD41 (GD41)": "GD41.BA",
                        "Meta Platforms - CEDEAR (META)": "META",
                        "Apple - CEDEAR (AAPL)": "AAPL",
                        "Nvidia - CEDEAR (NVDA)": "NVDA",
                        "Tesla - CEDEAR (TSLA)": "TSLA",
                        "Microsoft - CEDEAR (MSFT)": "MSFT",
                        "Amazon - CEDEAR (AMZN)": "AMZN",
                        "Alphabet / Google - CEDEAR (GOOGL)": "GOOGL",
                        "Mercado Libre - CEDEAR (MELI)": "MELI",
                        "Johnson & Johnson - CEDEAR (JNJ)": "JNJ",
                        "Starbucks - CEDEAR (SBUX)": "SBUX",
                        "AMD - CEDEAR (AMD)": "AMD",
                        "Intel - CEDEAR (INTC)": "INTC",
                        "Coca-Cola - CEDEAR (KO)": "KO",
                        "Disney - CEDEAR (DIS)": "DIS",
                        "Netflix - CEDEAR (NFLX)": "NFLX",
                        "Visa - CEDEAR (V)": "V",
                        "Mastercard - CEDEAR (MA)": "MA",
                        "JPMorgan Chase - CEDEAR (JPM)": "JPM",
                        "Procter & Gamble - CEDEAR (PG)": "PG",
                        "Walmart - CEDEAR (WMT)": "WMT",
                        "Berkshire Hathaway - CEDEAR (BRK.B)": "BRK.B",
                        "Pfizer - CEDEAR (PFE)": "PFE",
                        "Bank of America - CEDEAR (BAC)": "BAC",
                        "Citigroup - CEDEAR (C.BA)": "C.BA",
                        "S&P 500 ETF (SPY.BA)": "SPY.BA",
                        "Invesco Nasdaq (QQQ.BA)": "QQQ.BA",
                        "YPF - Acción Local (YPFD.BA)": "YPFD.BA",
                        "Grupo Financiero Galicia - Acción Local (GGAL.BA)": "GGAL.BA",
                        "Pampa Energía - Acción Local (PAMP.BA)": "PAMP.BA",
                        "Banco Macro - Acción Local (BMA.BA)": "BMA.BA",
                        "Aluar - Acción Local (ALUA.BA)": "ALUA.BA",
                        "Ternium - Acción Local (TXAR.BA)": "TXAR.BA"
                    }
                    
                    busqueda_input = st.selectbox("🔍 Buscar Activo:", list(diccionario_activos.keys()))
                    ticker_inv = diccionario_activos[busqueda_input]
                    
                    c_i2, c_i3 = st.columns(2)
                    with c_i2: 
                        cant_inv = st.number_input("Cantidad / Nominal:", min_value=1, value=1, step=1, format="%d")
                    with c_i3: 
                        fecha_inv = st.date_input("Fecha de Compra:")
                    
                    modo_precio = st.radio("¿Cómo deseas ingresar el valor de compra?", ["Precio Unitario", "Monto Total de la Operación"], horizontal=True, key="modo_precio_radio")
                    
                    c_i4, c_i5, c_i6, c_i7 = st.columns(4)
                    
                    if modo_precio == "Precio Unitario":
                        with c_i4: 
                            p_unit = st.number_input("Precio Unitario:", min_value=0.01, value=1000.0, step=100.0, key="input_precio_unitario_real")
                        precio_inv = p_unit
                    else:
                        with c_i4: 
                            m_total = st.number_input("Monto Total de la Operación:", min_value=0.01, value=10000.0, step=1000.0, key="input_monto_total_real")
                        precio_inv = m_total / cant_inv

                    with c_i5: mon_inv = st.selectbox("Moneda:", ["ARS", "USD", "MEP"])
                    with c_i6: tipo_dolar_op = st.selectbox("Tipo de Dólar:", ["CCL", "MEP"])
                    
                    es_cedear_default = "CEDEAR" in busqueda_input or "Acción Local" in busqueda_input or "Bono" in busqueda_input
                    with c_i7: es_cedear = st.checkbox("Ajustar", value=es_cedear_default)

                    # 💡 Calcular y mostrar el precio actual de mercado ya con los selectores definidos
                    p_bruto = get_precio_actual(ticker_inv)
                    tasa_conv = ccl_actual if tipo_dolar_op == "CCL" else mep_actual
                    
                    if p_bruto > 0:
                        if ".BA" in ticker_inv or not ticker_inv.endswith("D") and ticker_inv not in ["META", "AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "GOOGL", "MELI", "JNJ", "SBUX", "AMD", "INTC", "KO", "DIS", "NFLX", "V", "MA", "JPM", "PG", "WMT", "BRK.B", "PFE", "BAC"]:
                            precio_previo = p_bruto / tasa_conv
                            simbolo_precio = f"USD (convertido con {tipo_dolar_op})"
                        else:
                            precio_previo = p_bruto
                            simbolo_precio = "USD"
                            
                        st.info(f"💡 **Precio actual de mercado:** `{simbolo_precio} {precio_previo:,.2f}` (Valor local: $ {p_bruto:,.2f} ARS)")
                    else:
                        st.warning("⚠️ No se pudo obtener la cotización en vivo de este activo en este momento.")

                    c_i2, c_i3 = st.columns(2)
                    with c_i2: 
                        cant_inv = st.number_input("Cantidad / Nominal:", min_value=1, value=1, step=1, format="%d", key="input_cantidad_nominal")
                    with c_i3: 
                        fecha_inv = st.date_input("Fecha de Compra:", key="input_fecha_compra_activa")
                    
                    modo_precio = st.radio("¿Cómo deseas ingresar el valor de compra?", ["Precio Unitario", "Monto Total de la Operación"], horizontal=True, key="modo_precio_compra_activo_nuevo")
                    
                    c_i4, c_i5, c_i6, c_i7 = st.columns(4)
                    
                    if modo_precio == "Precio Unitario":
                        with c_i4: 
                            p_unit = st.number_input("Precio Unitario:", min_value=0.01, value=1000.0, step=100.0, key="input_precio_unitario_compra_nueva")
                        precio_inv = p_unit
                    else:
                        with c_i4: 
                            m_total = st.number_input("Monto Total de la Operación:", min_value=0.01, value=10000.0, step=1000.0, key="input_monto_total_compra_nueva")
                        precio_inv = m_total / cant_inv

                    with c_i5: mon_inv = st.selectbox("Moneda:", ["ARS", "USD", "MEP"], key="selectbox_moneda_compra_nueva")
                    with c_i6: tipo_dolar_op = st.selectbox("Tipo de Dólar:", ["CCL", "MEP"], key="selectbox_tipo_dolar_compra_nueva")
                    
                    es_cedear_default = "CEDEAR" in busqueda_input or "Acción Local" in busqueda_input or "Bono" in busqueda_input
                    with c_i7: es_cedear = st.checkbox("Ajustar", value=es_cedear_default, key="checkbox_ajustar_compra_nueva")
                    
                    st.markdown("---")
                    nota_compra = st.text_input("💬 Nota / Motivo:")
                    descontar_app = st.checkbox("💳 Descontar costo total de Efectivo en Broker", value=True)
                    
                    if st.form_submit_button("Guardar Compra"):
                        if ticker_inv:
                            costo_total = precio_inv * cant_inv
                            mov_id = str(uuid.uuid4())
                            inv_id = str(uuid.uuid4())
                            
                            if descontar_app:
                                user_data["movimientos"].append({
                                    "id": mov_id, "fecha": str(fecha_inv),
                                    "tipo": "Inversión (Compra de Activo)", "monto": -costo_total, 
                                    "moneda": mon_inv, "detalle": f"Compra {busqueda_input}"
                                })

                            user_data["inversiones"].append({
                                "id": inv_id, "mov_id": mov_id, "ticker": ticker_inv, "cantidad": float(cant_inv),
                                "precio_compra": precio_inv, "moneda": mon_inv, "tipo_dolar": tipo_dolar_op,
                                "fecha": str(fecha_inv), "es_cedear": es_cedear, "nota": nota_compra, "estado": "activo", "nombre_completo": busqueda_input
                            })
                            sincronizar_datos()
                            st.success(f"✅ Compra registrada correctamente.")
                            st.rerun()

            # ACTIVOS ACTIVOS EN CARTERA CON CÁLCULO HISTÓRICO Y SELECCIÓN DE DÓLAR
            inversiones_activas = [i for i in user_data.get("inversiones", []) if i.get("estado", "activo") == "activo"]
            if inversiones_activas:
                st.markdown("#### 📊 Consolidado de Activos Activos")
                activos_agrupados = {}
                for inv in inversiones_activas:
                    t = inv.get("nombre_completo", inv["ticker"])
                    if t not in activos_agrupados:
                        activos_agrupados[t] = []
                    activos_agrupados[t].append(inv)

                for ticker_label, compras in activos_agrupados.items():
                    ticker_real = compras[0]["ticker"]
                    p_actual_mercado = get_precio_actual(ticker_real)
                    if p_actual_mercado == 0.0:
                        p_actual_mercado = compras[0]["precio_compra"]

                    cantidad_total = sum(c['cantidad'] for c in compras)
                    inversion_total_ars = sum(c['cantidad'] * c['precio_compra'] for c in compras if c['moneda'] == 'ARS')
                    
                    inversion_total_usd_hist = 0.0
                    for c in compras:
                        monto_c = c['cantidad'] * c['precio_compra']
                        tipo_d = c.get("tipo_dolar", "CCL")
                        tasa_ref_hist = mep_actual if tipo_d == "MEP" else ccl_actual

                        if c.get('es_cedear') and c['moneda'] == 'ARS':
                            ccl_c = get_ccl_en_fecha(c['fecha'], df_ccl_hist, tasa_ref_hist)
                            inversion_total_usd_hist += monto_c / ccl_c
                        elif c['moneda'] in ['USD', 'MEP']:
                            inversion_total_usd_hist += monto_c
                        else:
                            inversion_total_usd_hist += monto_c / tasa_ref_hist

                    es_cedear_activo = compras[0].get('es_cedear', True) and compras[0]['moneda'] == 'ARS'
                    tipo_d_activo = compras[0].get("tipo_dolar", "CCL")
                    tasa_ref_act = mep_actual if tipo_d_activo == "MEP" else ccl_actual

                    if es_cedear_activo:
                        valor_actual_usd_tot = (cantidad_total * p_actual_mercado) / tasa_ref_act
                    else:
                        valor_actual_usd_tot = (cantidad_total * p_actual_mercado) if compras[0]['moneda'] in ['USD', 'MEP'] else (cantidad_total * p_actual_mercado) / tasa_ref_act

                    rend_total_pct = ((valor_actual_usd_tot - inversion_total_usd_hist) / inversion_total_usd_hist) * 100 if inversion_total_usd_hist > 0 else 0
                    color_rend = "#00e676" if (valor_actual_usd_tot - inversion_total_usd_hist) >= 0 else "#ff4b4b"

                    with st.container(border=True):
                        c_tit, c_vend, c_del = st.columns([2.5, 1, 0.8])
                        with c_tit:
                            st.markdown(f"### 🏷️ {ticker_label} (Total un: {int(cantidad_total)})")
                        with c_vend:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button(f"💵 Vender", key=f"btn_vender_{ticker_real}_{ticker_label}"):
                                st.session_state.vender_inv_ticker = (ticker_real, ticker_label)
                                st.rerun()
                        with c_del:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("🗑️ Borrar", key=f"btn_del_inv_directo_{ticker_real}_{ticker_label}"):
                                ids_a_borrar = [c['id'] for c in compras]
                                mov_ids_a_borrar = [c.get('mov_id') for c in compras if c.get('mov_id')]
                                
                                user_data["inversiones"] = [i for i in user_data["inversiones"] if i['id'] not in ids_a_borrar]
                                user_data["movimientos"] = [m for m in user_data.get("movimientos", []) if m['id'] not in mov_ids_a_borrar]
                                
                                sincronizar_datos()
                                st.success("✅ Activo eliminado correctamente.")
                                st.rerun()
                        
                        if modo_moneda_global == "Dólares (USD)":
                            val_act_str = f"USD {valor_actual_usd_tot:,.2f}"
                            inv_str = f"USD {inversion_total_usd_hist:,.2f}"
                        else:
                            inv_tot_ars_most = inversion_total_ars if compras[0]['moneda'] == 'ARS' else inversion_total_usd_hist * tasa_ref_act
                            val_act_ars_most = cantidad_total * p_actual_mercado if es_cedear_activo else valor_actual_usd_tot * tasa_ref_act
                            inv_str = f"ARS ${inv_tot_ars_most:,.2f}"
                            val_act_str = f"ARS ${val_act_ars_most:,.2f}"

                        st.markdown(
                            f"💰 **Invertido:** {inv_str} | "
                            f"📈 **Valor Actual:** <span style='color:{color_rend}; font-weight:bold;'>{val_act_str} ({rend_total_pct:+.2f}%)</span>",
                            unsafe_allow_html=True
                        )

            # FORMULARIO DE VENTA CON SLIDER ENTERO
            if st.session_state.get("vender_inv_ticker"):
                t_real, t_label = st.session_state.vender_inv_ticker
                compras_activas_ticker = [i for i in user_data.get("inversiones", []) if i["ticker"] == t_real and i.get("nombre_completo", i["ticker"]) == t_label and i.get("estado", "activo") == "activo"]
                max_unidades = int(sum(c['cantidad'] for c in compras_activas_ticker))
                
                st.markdown("---")
                st.markdown(f"#### 💸 Registrar Venta de {t_label}")
                
                if max_unidades > 0:
                    with st.form("form_vender_activo"):
                        fecha_venta = st.date_input("Fecha de venta:")
                        cant_a_vender = st.slider("Unidades a vender:", min_value=1, max_value=max_unidades, value=max_unidades, step=1)
                        monto_recibido = st.number_input("Dinero total recibido:", min_value=0.01, value=1000.0, step=100.0)
                        moneda_venta = st.radio("Moneda:", ["ARS", "USD", "MEP"], horizontal=True)
                        
                        if st.form_submit_button("Confirmar Venta y Sumar a Efectivo en Broker"):
                            user_data["movimientos"].append({
                                "id": str(uuid.uuid4()), "fecha": str(fecha_venta),
                                "tipo": "Venta de Activo", "monto": monto_recibido, 
                                "moneda": moneda_venta, "detalle": f"Venta de {cant_a_vender} un. de {t_label}"
                            })
                            
                            res = float(cant_a_vender)
                            for c in compras_activas_ticker:
                                if res <= 0: break
                                if c['cantidad'] <= res:
                                    res -= c['cantidad']
                                    c['estado'] = 'vendido'
                                    c['fecha_venta'] = str(fecha_venta)
                                    c['monto_venta'] = monto_recibido
                                    c['moneda_venta'] = moneda_venta
                                else:
                                    c['cantidad'] -= res
                                    res = 0
                                    
                            sincronizar_datos()
                            st.session_state.vender_inv_ticker = None
                            st.success("✅ Venta registrada y sumada a tu efectivo en broker.")
                            st.rerun()

            # HISTORIAL DE INVERSIONES VENDIDAS
            inversiones_vendidas = [i for i in user_data.get("inversiones", []) if i.get("estado") == "vendido"]
            if inversiones_vendidas:
                st.markdown("---")
                st.markdown("#### 🏆 Historial de Inversiones Vendidas (Rendimiento Realizado)")
                for vend in inversiones_vendidas:
                    with st.container(border=True):
                        m_compra = vend['cantidad'] * vend['precio_compra']
                        m_venta = vend.get('monto_venta', 0.0)
                        ganancia = m_venta - m_compra
                        color_g = "#00e676" if ganancia >= 0 else "#ff4b4b"
                        label_v = vend.get("nombre_completo", vend["ticker"])
                        
                        st.markdown(f"**{label_v}** | Vendido el {vend.get('fecha_venta', 'N/A')}")
                        st.markdown(f"• **Compra:** {vend['fecha']} ({int(vend['cantidad'])} un. a {vend['moneda']} {vend['precio_compra']:,.2f})")
                        st.markdown(f"• **Resultado Realizado:** <span style='color:{color_g}; font-weight:bold;'>{vend.get('moneda_venta', 'ARS')} {ganancia:+,.2f}</span>", unsafe_allow_html=True)

elif nav == "portfolio":
    if not st.session_state.get("user_email"):
        st.warning("⚠️ Debes iniciar sesión para guardar tu Watchlist de seguimiento.")
    else:
        st.title("👀 Watchlist (Seguimiento de Activos)")
        st.markdown("Agrega empresas o bonos que quieras vigilar periódicamente. Para registrar compras que afecten tu patrimonio, usa la pestaña de **Finanzas**.")
        user_data = st.session_state.user_data
        
        col_w1, col_w2 = st.columns([3, 1])
        with col_w1:
            nuevo_ticker_w = st.text_input("🔍 Ticker a vigilar (Ej. TSLA, YPFD.BA):").upper().strip()
        with col_w2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Añadir a Watchlist", use_container_width=True):
                if nuevo_ticker_w:
                    with st.spinner("Verificando..."):
                        if get_precio_actual(nuevo_ticker_w) > 0:
                            if nuevo_ticker_w not in user_data.get("watchlist", []):
                                user_data.setdefault("watchlist", []).append(nuevo_ticker_w)
                                sincronizar_datos()
                                st.success("Añadido a la Watchlist.")
                                st.rerun()
                        else:
                            st.error("No se encontró el activo.")

        if user_data.get("watchlist"):
            st.markdown("### 📊 Tablero de Cotizaciones")
            datos_wl = []
            for t in user_data["watchlist"]:
                try:
                    hist = yf.Ticker(t).history(period="2d")
                    if len(hist) >= 2:
                        p_act = float(hist['Close'].iloc[-1])
                        p_prev = float(hist['Close'].iloc[-2])
                        var_pct = ((p_act - p_prev) / p_prev) * 100
                    else:
                        p_act = get_precio_actual(t)
                        var_pct = 0.0
                    datos_wl.append({"Activo": t, "Precio Mercado": p_act, "Variación 24hs (%)": var_pct, "Quitar": t})
                except:
                    pass

            if datos_wl:
                df_wl = pd.DataFrame(datos_wl)
                
                cols_w = st.columns(4)
                for idx, row in df_wl.iterrows():
                    with cols_w[idx % 4]:
                        color_w = "#00e676" if row['Variación 24hs (%)'] >= 0 else "#ff4b4b"
                        st.markdown(f"""
                        <div style="background-color: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 15px;">
                            <h4 style="margin:0; color:#c9d1d9;">{row['Activo']}</h4>
                            <h2 style="margin:5px 0; color:#f0f6fc;">${row['Precio Mercado']:,.2f}</h2>
                            <p style="margin:0; color:{color_w}; font-weight:bold;">{row['Variación 24hs (%)']:+.2f}%</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("#### Eliminar de Watchlist")
                quitar_t = st.selectbox("Selecciona un activo para dejar de vigilar:", ["-"] + user_data["watchlist"])
                if quitar_t != "-" and st.button("Eliminar"):
                    user_data["watchlist"].remove(quitar_t)
                    sincronizar_datos()
                    st.rerun()

elif nav == "int_acciones":
    if "empresa_seleccionada" not in st.session_state:
        st.session_state.empresa_seleccionada = None

    if st.session_state.empresa_seleccionada:
        emp = st.session_state.empresa_seleccionada
        
        if st.button("⬅️ Volver al listado de acciones"):
            st.session_state.empresa_seleccionada = None
            st.rerun()
            
        st.title(f"📊 Análisis Detallado: {emp}")
        datos_globales = obtener_datos_globales()
        ticker_info = datos_globales.get(emp)
        
        if ticker_info:
            ticker_str = ticker_info["ticker"]
            with st.spinner(f"Descargando datos financieros de {ticker_str}..."):
                try:
                    tk = yf.Ticker(ticker_str)
                    info = tk.info
                    
                    tab_info, tab_fin, tab_news = st.tabs(["📋 Ratios y Métricas", "📊 Información Contable", "📰 Noticias"])
                    
                    with tab_info:
                        st.subheader("🔍 Ratios Clave de Rentabilidad y Valoración")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("P/E (Price to Earnings)", format_metric(info.get('trailingPE')))
                        c2.metric("P/B (Price to Book)", format_metric(info.get('priceToBook')))
                        c3.metric("BPA / EPS", format_metric(info.get('trailingEps')))
                        c4.metric("Capitalización (Mcap)", format_metric(info.get('marketCap')))
                        
                        c5, c6, c7, c8 = st.columns(4)
                        c5.metric("ROE (Rent. Capital)", format_metric(info.get('returnOnEquity'), True))
                        c6.metric("ROA (Rent. Activos)", format_metric(info.get('returnOnAssets'), True))
                        c7.metric("Margen Neto", format_metric(info.get('profitMargins'), True))
                        c8.metric("ROIC (Est.)", format_metric(info.get('operatingMargins'), True))

                    with tab_fin:
                        st.subheader("📋 Estado de Resultados")
                        df_fin = tk.financials
                        if df_fin is not None and not df_fin.empty:
                            st.dataframe(df_fin.style.format("{:,.0f}", na_rep="-"), use_container_width=True)
                        else:
                            st.info("Estados contables no disponibles de forma directa.")

                    with tab_news:
                        st.subheader("📰 Últimas Noticias")
                        try:
                            noticias = tk.news
                            if noticias:
                                for n in noticias[:6]:
                                    titulo_nota = n.get('title') or "Ver noticia"
                                    link_nota = n.get('link') or "#"
                                    editor = n.get('publisher') or "Yahoo Finance"
                                    
                                    img_url = None
                                    try:
                                        img_url = n['thumbnail']['resolutions'][0]['url']
                                    except:
                                        pass
                                    
                                    col_img, col_txt = st.columns([1, 4])
                                    with col_img:
                                        if img_url:
                                            st.image(img_url, use_container_width=True)
                                        else:
                                            st.markdown("📰")
                                    with col_txt:
                                        st.markdown(f"**[{titulo_nota}]({link_nota})**")
                                        st.caption(f"Fuente: {editor}")
                                    st.markdown("---")
                            else:
                                st.info("No hay noticias recientes disponibles.")
                        except:
                            st.info("Sección de noticias temporalmente no disponible.")
                except Exception as e:
                    st.info("Datos resumidos temporalmente.")
        else:
            st.error("No se encontraron datos para esta empresa.")
            
    else:
        st.title("📈 Acciones Internacionales")
        filtro = st.text_input("🔍 Buscar por Nombre de Empresa o Ticker:", "").strip().lower()
        
        datos_globales = obtener_datos_globales()
        int_keys = ["Apple", "Nvidia", "Tesla", "Microsoft", "Amazon", "Google", "Meta", "Nestlé", "Johnson & Johnson", "Coca-Cola", "Visa", "Walmart", "JPMorgan", "Procter & Gamble", "Disney"]
        
        st.markdown("---")
        for emp in int_keys:
            ticker_info = datos_globales.get(emp)
            if ticker_info:
                ticker = ticker_info["ticker"]
                precio = ticker_info["precio"]
                var = ticker_info["var_pct"]
                color = "#00e676" if var >= 0 else "#ff1744"
                
                if filtro in emp.lower() or filtro in ticker.lower():
                    col_name, col_price, col_var, col_btn = st.columns(4)
                    with col_name:
                        st.markdown(f"**{emp}** `({ticker})`")
                    with col_price:
                        st.markdown(f"${precio:,.2f}")
                    with col_var:
                        st.markdown(f"<span style='color:{color}; font-weight:bold;'>{var:+.2f}%</span>", unsafe_allow_html=True)
                    with col_btn:
                        if st.button("ℹ️ Más info", key=f"btn_{ticker}"):
                            st.session_state.empresa_seleccionada = emp
                            st.rerun()
                    
                    st.markdown("<hr style='margin: 8px 0; border: 0.5px solid #30363d;'>", unsafe_allow_html=True)

elif nav == "arg_acciones":
    if "empresa_arg_seleccionada" not in st.session_state:
        st.session_state.empresa_arg_seleccionada = None

    if st.session_state.empresa_arg_seleccionada:
        emp = st.session_state.empresa_arg_seleccionada
        
        if st.button("⬅️ Volver al listado local"):
            st.session_state.empresa_arg_seleccionada = None
            st.rerun()
            
        st.title(f"📊 Análisis Detallado Local: {emp}")
        datos_globales = obtener_datos_globales()
        ticker_info = datos_globales.get(emp)
        
        if ticker_info:
            ticker_str = ticker_info["ticker"]
            with st.spinner(f"Descargando balances de {ticker_str}..."):
                try:
                    tk = yf.Ticker(ticker_str)
                    info = tk.info
                    
                    tab_info, tab_fin, tab_news = st.tabs(["📋 Ratios y Métricas", "📊 Información Contable", "📰 Noticias Locales"])
                    
                    with tab_info:
                        st.subheader("🔍 Ratios Clave de Rentabilidad y Valoración")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("P/E (Price to Earnings)", format_metric(info.get('trailingPE')))
                        c2.metric("P/B (Price to Book)", format_metric(info.get('priceToBook')))
                        c3.metric("BPA / EPS", format_metric(info.get('trailingEps')))
                        c4.metric("Capitalización (Mcap)", format_metric(info.get('marketCap')))
                        
                        c5, c6, c7, c8 = st.columns(4)
                        c5.metric("ROE (Rent. Capital)", format_metric(info.get('returnOnEquity'), True))
                        c6.metric("ROA (Rent. Activos)", format_metric(info.get('returnOnAssets'), True))
                        c7.metric("Margen Neto", format_metric(info.get('profitMargins'), True))
                        c8.metric("ROIC (Est.)", format_metric(info.get('operatingMargins'), True))

                    with tab_fin:
                        st.subheader("📋 Estado de Resultados")
                        df_fin = tk.financials
                        if df_fin is not None and not df_fin.empty:
                            st.dataframe(df_fin.style.format("{:,.0f}", na_rep="-"), use_container_width=True)
                        else:
                            st.info("Balances oficiales no cargados en formato internacional.")

                    with tab_news:
                        st.subheader("📰 Últimas Noticias")
                        try:
                            noticias = tk.news
                            if noticias:
                                for n in noticias[:6]:
                                    titulo_nota = n.get('title') or "Ver noticia"
                                    link_nota = n.get('link') or "#"
                                    editor = n.get('publisher') or "Yahoo Finance"
                                    img_url = None
                                    try:
                                        img_url = n['thumbnail']['resolutions'][0]['url']
                                    except:
                                        pass
                                    col_img, col_txt = st.columns([1, 4])
                                    with col_img:
                                        if img_url:
                                            st.image(img_url, use_container_width=True)
                                        else:
                                            st.markdown("📰")
                                    with col_txt:
                                        st.markdown(f"**[{titulo_nota}]({link_nota})**")
                                        st.caption(f"Fuente: {editor}")
                                    st.markdown("---")
                            else:
                                st.info("No hay noticias recientes disponibles.")
                        except:
                            st.info("Sección de noticias en mantenimiento.")
                except:
                    st.info("Datos resumidos temporalmente.")
        else:
            st.error("No se encontraron datos para este ticker local.")
            
    else:
        st.title("📈 Acciones Locales (Merval)")
        filtro = st.text_input("🔍 Buscar Acción Argentina por Nombre o Ticker:", "").strip().lower()
        
        datos_globales = obtener_datos_globales()
        empresas_argentinas = [
            "YPF", "Galicia", "Pampa Energía", "Banco Macro", "Central Puerto", 
            "Aluar", "Ternium", "Loma Negra", "Trans. Gas del Norte", "Trans. Gas del Sur", 
            "Edenor", "Transener", "BYMA", "Valo", "Mirgor", "Supervielle", 
            "BBVA AR", "Cablevisión", "Richmond", "Agrometal"
        ]
        
        st.markdown("---")
        for emp in empresas_argentinas:
            ticker_info = datos_globales.get(emp)
            if ticker_info:
                ticker = ticker_info["ticker"]
                precio = ticker_info["precio"]
                var = ticker_info["var_pct"]
                color = "#00e676" if var >= 0 else "#ff1744"
                
                if filtro in emp.lower() or filtro in ticker.lower():
                    col_name, col_price, col_var, col_btn = st.columns(4)
                    with col_name:
                        st.markdown(f"**{emp}** `({ticker})`")
                    with col_price:
                        st.markdown(f"${precio:,.2f} ARS")
                    with col_var:
                        st.markdown(f"<span style='color:{color}; font-weight:bold;'>{var:+.2f}%</span>", unsafe_allow_html=True)
                    with col_btn:
                        if st.button("ℹ️ Más info", key=f"btn_{ticker}"):
                            st.session_state.empresa_arg_seleccionada = emp
                            st.rerun()
                    
                    st.markdown("<hr style='margin: 8px 0; border: 0.5px solid #30363d;'>", unsafe_allow_html=True)

elif nav == "arg_ons":
    st.title("📄 Obligaciones Negociables (ONs Corporativas)")
    st.markdown("Información de flujo de fondos y estructura de las principales ONs en el mercado.")
    
    ons_db = {
        "YCA6O (YPF 2025)": {"TIR Estimada": "8.1%", "Tasa Cupón": "8.50% Anual", "Frecuencia Pago": "Semestral", "Moneda": "USD Cable", "Estructura": "Amortización Bullet (100% al final)", "Calificación": "AAA (Arg)"},
        "YFC2O (YPF 2029)": {"TIR Estimada": "9.4%", "Tasa Cupón": "9.00% Anual", "Frecuencia Pago": "Semestral", "Moneda": "USD MEP/Cable", "Estructura": "Amortización en Cuotas (2027, 2028, 2029)", "Calificación": "AAA (Arg)"},
        "IRC1O (IRSA 2028)": {"TIR Estimada": "8.8%", "Tasa Cupón": "8.75% Anual", "Frecuencia Pago": "Semestral", "Moneda": "USD MEP", "Estructura": "Amortización en Cuotas", "Calificación": "AA+ (Arg)"},
        "MRCE1 (Pampa Energía 2027)": {"TIR Estimada": "7.5%", "Tasa Cupón": "7.50% Anual", "Frecuencia Pago": "Semestral", "Moneda": "USD Cable", "Estructura": "Amortización Bullet", "Calificación": "AAA (Arg)"},
        "MGC3O (Pampa Energía 2026)": {"TIR Estimada": "6.8%", "Tasa Cupón": "9.50% Anual", "Frecuencia Pago": "Semestral", "Moneda": "USD MEP", "Estructura": "Bullet", "Calificación": "AAA (Arg)"},
        "GNCXO (Genneia 2027)": {"TIR Estimada": "8.3%", "Tasa Cupón": "8.75% Anual", "Frecuencia Pago": "Semestral", "Moneda": "USD MEP", "Estructura": "Bullet (Verde)", "Calificación": "AA (Arg)"},
        "AEC1O (Aeropuertos AR 2031)": {"TIR Estimada": "8.9%", "Tasa Cupón": "8.50% Anual", "Frecuencia Pago": "Trimestral", "Moneda": "USD Cable", "Estructura": "Amortización Trimestral desde 2025", "Calificación": "AA+ (Arg)"},
        "TLC5O (Telecom 2025)": {"TIR Estimada": "7.2%", "Tasa Cupón": "8.50% Anual", "Frecuencia Pago": "Semestral", "Moneda": "USD MEP", "Estructura": "Amortización Bullet", "Calificación": "AAA (Arg)"}
    }
    
    df_ons = pd.DataFrame.from_dict(ons_db, orient='index').reset_index()
    df_ons.columns = ["Ticker Corporativo", "TIR Aprox.", "Tasa Cupón", "Pago", "Moneda de Emisión/Pago", "Estructura de Capital", "Riesgo Local"]
    
    st.dataframe(df_ons, use_container_width=True, hide_index=True)

elif nav == "int_bonos":
    st.title("📄 Bonos Internacionales (Rendimientos del Tesoro)")
    c1, c2, c3, c4 = st.columns(4)
    with c1: d = globales.get("Treasury 2Y"); st.metric("🇺🇸 Tesoro a 2 Años", f"{d['precio']:.2f}%" if d else "-", delta=f"{d['var_pct']:.2f}%" if d else None)
    with c2: d = globales.get("Treasury 5Y"); st.metric("🇺🇸 Tesoro a 5 Años", f"{d['precio']:.2f}%" if d else "-", delta=f"{d['var_pct']:.2f}%" if d else None)
    with c3: d = globales.get("Treasury 10Y"); st.metric("🇺🇸 Tesoro a 10 Años", f"{d['precio']:.2f}%" if d else "-", delta=f"{d['var_pct']:.2f}%" if d else None)
    with c4: d = globales.get("Treasury 30Y"); st.metric("🇺🇸 Tesoro a 30 Años", f"{d['precio']:.2f}%" if d else "-", delta=f"{d['var_pct']:.2f}%" if d else None)

elif nav == "int_commodities":
    st.title("🛢️ Commodities")
    c1, c2 = st.columns(2)
    with c1: d = globales.get("Oro"); st.metric("🥇 Oro", f"USD {d['precio']:,.2f}" if d else "-", delta=f"{d['var_pct']:.2f}%" if d else None)
    with c2: d = globales.get("WTI"); st.metric("🛢️ Petróleo WTI", f"USD {d['precio']:,.2f}" if d else "-", delta=f"{d['var_pct']:.2f}%" if d else None)

elif nav == "int_etfs":
    st.title("📊 Índices y ETFs Globales")
    d_index = globales.get("S&P 500 (Índice)")
    st.metric("📈 S&P 500 (Puntos del Índice)", f"{d_index['precio']:,.2f}" if d_index else "-", delta=f"{d_index['var_pct']:.2f}%" if d_index else None)
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1: d = globales.get("SPY (ETF)"); st.metric("🇺🇸 SPY (S&P 500)", f"USD {d['precio']:,.2f}" if d else "-", delta=f"{d['var_pct']:.2f}%" if d else None)
    with c2: d = globales.get("QQQ (ETF Nasdaq)"); st.metric("💻 QQQ (Nasdaq)", f"USD {d['precio']:,.2f}" if d else "-", delta=f"{d['var_pct']:.2f}%" if d else None)
    with c3: d = globales.get("DIA (ETF Dow)"); st.metric("🏭 DIA (Dow Jones)", f"USD {d['precio']:,.2f}" if d else "-", delta=f"{d['var_pct']:.2f}%" if d else None)

elif nav == "int_datos":
    st.title("🏦 Datos Macroeconómicos (EE.UU.)")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("🏦 Tasa de Interés (Fed Funds Rate)", "3.63%")
    with c2: st.metric("🛒 Inflación Anual EE.UU. (CPI)", "3.36%")
    with c3: st.metric("👥 Tasa de Desempleo (EE.UU.)", "4.3%")

elif nav == "arg_bonos":
    st.title("📄 Bonos Argentinos (Soberanos)")
    c1, c2, c3 = st.columns(3)
    with c1: d = bonos_arg.get("AL29"); st.metric("🇦🇷 AL29 (Ley Local)", f"$ {d['precio']:,.2f}" if d and d.get('precio') else "-", delta=f"{d['var_pct']:.2f}%" if d and d.get('var_pct') else None)
    with c2: d = bonos_arg.get("AL30"); st.metric("🇦🇷 AL30 (Ley Local)", f"$ {d['precio']:,.2f}" if d and d.get('precio') else "-", delta=f"{d['var_pct']:.2f}%" if d and d.get('var_pct') else None)
    with c3: d = bonos_arg.get("AE38"); st.metric("🇦🇷 AE38 (Ley Local)", f"$ {d['precio']:,.2f}" if d and d.get('precio') else "-", delta=f"{d['var_pct']:.2f}%" if d and d.get('var_pct') else None)
    st.divider()
    c4, c5 = st.columns(2)
    with c4: d = bonos_arg.get("GD30"); st.metric("🗽 GD30 (Ley NY)", f"$ {d['precio']:,.2f}" if d and d.get('precio') else "-", delta=f"{d['var_pct']:.2f}%" if d and d.get('var_pct') else None)
    with c5: d = bonos_arg.get("GD35"); st.metric("🗽 GD35 (Ley NY)", f"$ {d['precio']:,.2f}" if d and d.get('precio') else "-", delta=f"{d['var_pct']:.2f}%" if d and d.get('var_pct') else None)

elif nav == "arg_etfs":
    st.title("📊 Índices y CEDEARs")
    d = globales.get("Merval ARS"); st.metric("🇦🇷 Índice S&P Merval (Pesos)", f"$ {d['precio']:,.0f}" if d else "-", delta=f"{d['var_pct']:.2f}%" if d else None)
    st.divider()
    c1, c2 = st.columns(2)
    with c1: d = globales.get("SPY (CEDEAR)"); st.metric("🇺🇸 CEDEAR SPY", f"$ {d['precio']:,.2f}" if d else "-", delta=f"{d['var_pct']:.2f}%" if d else None)
    with c2: d = globales.get("QQQ (CEDEAR)"); st.metric("💻 CEDEAR QQQ", f"$ {d['precio']:,.2f}" if d else "-", delta=f"{d['var_pct']:.2f}%" if d else None)

elif nav == "arg_datos":
    st.title("🏦 Datos Económicos y Financiamiento")
    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1: st.metric("📉 Inflación Mensual (IPC)", "2.1%")
    with c_m2: st.metric("⚠️ Riesgo País", macro_arg.get("riesgo_pais", "-"))
    with c_m3: st.metric("👥 Tasa de Desempleo (AR)", "7.6%")
    st.divider()
    a1, a2, a3 = st.columns(3)
    mep_val = macro_arg["dolares"].get("bolsa")
    ccl_val = macro_arg["dolares"].get("contadoconliqui")
    oficial_val = macro_arg["dolares"].get("oficial")
    with a1: st.metric("💵 Dólar MEP", f"$ {mep_val:,.2f}" if mep_val else "-")
    with a2: st.metric("🗽 Dólar CCL", f"$ {ccl_val:,.2f}" if ccl_val else "-")
    with a3: st.metric("🏦 Dólar Oficial", f"$ {oficial_val:,.2f}" if oficial_val else "-")
    st.divider()
    uva = macro_arg.get("uva")
    st.metric("🏠 Valor UVA", f"$ {uva['valor']:,.2f}" if uva else "-")
    st.metric("🔑 Tasa Hipotecaria Bancaria", "UVA + 4.5% / 8.5%")

elif nav == "calc_interes":
    st.title("🧮 Calculadora de Interés Compuesto")
    c1, c2 = st.columns([1, 2.5])
    with c1:
        st.markdown("### Parámetros")
        p_inicial = st.number_input("Inversión Inicial ($)", min_value=0.0, value=10000.0, step=1000.0)
        p_mensual = st.number_input("Adición Mensual ($)", min_value=0.0, value=500.0, step=100.0)
        p_anios = st.number_input("Tiempo en Años", min_value=1, value=10, step=1)
        p_tasa = st.number_input("Tasa de Interés Base Estimada (%)", min_value=0.0, value=8.0, step=0.1)
        p_desv = st.number_input("Desviación Esperada (±%)", min_value=0.0, value=2.0, step=0.1, help="Simula un escenario optimista (+%) y uno pesimista (-%)")
        p_freq = st.selectbox("Frecuencia de Capitalización", ["Anual", "Semestral", "Trimestral", "Mensual", "Diaria"], index=0)
    
    with c2:
        r_nominal = p_tasa / 100.0
        r_desv = p_desv / 100.0
        n_per_year = {"Anual": 1, "Semestral": 2, "Trimestral": 4, "Mensual": 12, "Diaria": 365}[p_freq]
        pmt_period = (p_mensual * 12) / n_per_year
        
        historial = [{"Año": 0, "Aportes": p_inicial, "Base": p_inicial, "Optimista": p_inicial, "Pesimista": p_inicial}]
        
        for anio in range(1, int(p_anios) + 1):
            n_totales = anio * n_per_year
            aportes = p_inicial + (p_mensual * 12 * anio)
            
            def calc_fv(p, pmt, r, n_tot):
                if r == 0: return p + pmt * n_tot
                return p * (1 + r)**n_tot + pmt * (((1 + r)**n_tot - 1) / r)
            
            bal_base = calc_fv(p_inicial, pmt_period, r_nominal / n_per_year, n_totales)
            bal_opt = calc_fv(p_inicial, pmt_period, (r_nominal + r_desv) / n_per_year, n_totales)
            r_pes = max(0, r_nominal - r_desv)
            bal_pes = calc_fv(p_inicial, pmt_period, r_pes / n_per_year, n_totales)
            
            historial.append({"Año": anio, "Aportes": aportes, "Base": bal_base, "Optimista": bal_opt, "Pesimista": bal_pes})
            
        df_chart = pd.DataFrame(historial)
        valor_final_exacto = historial[-1]["Base"]
        
        st.markdown(f"""
        <div style="background-color: #161b22; padding: 25px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 25px;">
            <p style="color: #8b949e; margin: 0; font-size: 1.1rem; font-weight: 500; text-transform: uppercase; letter-spacing: 1px;">Valor Final Estimado (Proyección Base)</p>
            <h1 style="color: #00e676; margin: 5px 0 0 0; font-size: 3.5rem; font-weight: 800;">$ {valor_final_exacto:,.2f}</h1>
            <p style="color: #8b949e; margin: 8px 0 0 0; font-size: 0.95rem;">
                🔽 Pesimista: <strong>$ {historial[-1]["Pesimista"]:,.2f}</strong> &nbsp; | &nbsp; 🔼 Optimista: <strong>$ {historial[-1]["Optimista"]:,.2f}</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_chart["Año"], y=df_chart["Aportes"], name="Aportes Totales", marker_color="#1f6feb"))
        fig.add_trace(go.Scatter(x=df_chart["Año"], y=df_chart["Pesimista"], mode='lines', line=dict(color='rgba(255, 99, 132, 0)'), name="Escenario Pesimista", showlegend=False))
        fig.add_trace(go.Scatter(x=df_chart["Año"], y=df_chart["Optimista"], mode='lines', fill='tonexty', fillcolor='rgba(0, 230, 118, 0.15)', line=dict(color='rgba(0, 230, 118, 0)'), name="Franja de Desviación", showlegend=True))
        fig.add_trace(go.Scatter(x=df_chart["Año"], y=df_chart["Base"], mode='lines+markers', name="Crecimiento Base", line=dict(color="#00e676", width=3), marker=dict(size=8)))
        fig.update_layout(barmode='overlay', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#c9d1d9'), xaxis=dict(title="Años", dtick=1), yaxis=dict(title="Monto ($)"), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

elif nav == "calc_francesa":
    st.title("🏛️ Sistema de Amortización Francés")
    c1, c2 = st.columns([1, 2.5])
    with c1:
        st.markdown("### Parámetros del Préstamo")
        prestamo = st.number_input("Monto del Préstamo ($)", min_value=0.0, value=1000000.0, step=50000.0)
        tasa_anual = st.number_input("Tasa Nominal Anual (TNA %)", min_value=0.0, value=45.0, step=0.5)
        meses = st.number_input("Plazo en Meses", min_value=1, value=12, step=1)
        
    with c2:
        tasa_mensual = (tasa_anual / 100.0) / 12.0
        if tasa_mensual > 0:
            cuota = prestamo * (tasa_mensual * (1 + tasa_mensual)**meses) / ((1 + tasa_mensual)**meses - 1)
        else:
            cuota = prestamo / meses
            
        saldo = prestamo
        detalle = []
        for mes in range(1, int(meses) + 1):
            interes = saldo * tasa_mensual
            amortizacion = cuota - interes
            saldo -= amortizacion
            detalle.append({"Mes": mes, "Cuota": cuota, "Interés": interes, "Amortización": amortizacion, "Saldo Restante": max(0.0, saldo)})
            
        df_frances = pd.DataFrame(detalle)
        
        st.markdown(f"""
        <div style="background-color: #161b22; padding: 25px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 25px;">
            <p style="color: #8b949e; margin: 0; font-size: 1.1rem; font-weight: 500; text-transform: uppercase; letter-spacing: 1px;">Cuota Mensual Fija</p>
            <h1 style="color: #00e676; margin: 5px 0 0 0; font-size: 3.5rem; font-weight: 800;">$ {cuota:,.2f}</h1>
        </div>
        """, unsafe_allow_html=True)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_frances["Mes"], y=df_frances["Saldo Restante"], mode='lines+markers', name="Saldo Restante", line=dict(color="#00e676", width=3)))
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#c9d1d9'), xaxis=dict(title="Mes"), yaxis=dict(title="Saldo ($)"), margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### Tabla de Amortización")
        st.dataframe(df_frances.style.format({"Cuota": "${:,.2f}", "Interés": "${:,.2f}", "Amortización": "${:,.2f}", "Saldo Restante": "${:,.2f}"}), use_container_width=True)

elif nav == "legal":
    st.title("📜 Términos, Condiciones y Cumplimiento Regulatorio (Argentina)")
    st.markdown("""
    **1. Aviso de la Comisión Nacional de Valores (CNV)**  
    Este sitio web y sus desarrolladores **NO son un Agente de Liquidación y Compensación (ALyC)**, ni un Agente de Negociación, ni un Asesor Global de Inversiones registrado ante la Comisión Nacional de Valores (CNV) de la República Argentina. Todo el contenido, incluyendo datos contables, métricas y noticias, tiene un propósito **estricta y exclusivamente informativo y educativo**. No se efectúan recomendaciones de compra, retención o venta de ningún título valor (acciones, CEDEARs, ONs, Bonos) bajo la Ley N° 26.831 (Ley de Mercado de Capitales).

    **2. Asunción de Riesgos**  
    Las inversiones en el mercado de capitales están sujetas a riesgos de mercado, incluyendo la posible pérdida del capital invertido. El usuario asume total y absoluta responsabilidad por las decisiones financieras que tome basándose en la información proporcionada en esta plataforma. Se sugiere enfáticamente consultar a un profesional o idóneo certificado en mercado de capitales antes de invertir.

    **3. Origen, Retraso y Naturaleza de los Datos**  
    Los datos de mercado exhibidos no son producidos ni auditados por esta plataforma. Se nutren de APIs públicas y de terceros (*Yahoo Finance*, *ArgentinaDatos*, *DolarApi*). 
    * Los datos contables y flujos de fondos de Obligaciones Negociables provienen de prospectos históricos y pueden no reflejar eventos corporativos recientes.
    * Puede existir un retraso normativo de hasta 20 minutos en las cotizaciones bursátiles.

    **4. Privacidad y Protección de Datos Personales (Ley 25.326)**  
    En cumplimiento de la Ley de Protección de Datos Personales de Argentina (Ley N° 25.326), se informa que los correos electrónicos o datos suministrados para guardar portafolios son utilizados únicamente con fines técnicos de autenticación. El usuario tiene derecho a solicitar el acceso, rectificación y supresión de sus datos en cualquier momento.

    **5. Procesamiento de Pagos y Terceros**  
    Cualquier transacción monetaria (como suscripciones o donaciones) se realiza a través de pasarelas de pago de terceros reguladas (ej. Mercado Pago). Este sitio no capta, retiene ni transfiere fondos de inversión ni depósitos, eximiéndose de las obligaciones ante la Unidad de Información Financiera (UIF) correspondientes a entidades financieras tradicionales.
    """)

# ============================================================
# 5. RENDERIZAR PIE DE PÁGINA DINÁMICO
# ============================================================
tz_ar = pytz.timezone("America/Argentina/Buenos_Aires")
hora_actual = datetime.now(tz_ar).strftime('%d/%m/%Y %H:%M:%S')

footer_html = f"""
<div class="fixed-footer">
    ℹ️ <strong>Fuentes:</strong> Yahoo Finance, DolarApi.com y ArgentinaDatos. &nbsp;&nbsp;|&nbsp;&nbsp; ⚠️ <strong>Aviso legal:</strong> Fines informativos. No somos un ALyC (CNV). &nbsp;&nbsp;|&nbsp;&nbsp; 🕒 Última actualización: {hora_actual}
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)