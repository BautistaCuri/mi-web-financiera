import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
import plotly.graph_objects as go
import xml.etree.ElementTree as ET
import re
import json
import os

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

def sincronizar_cartera():
    if "user_email" in st.session_state and st.session_state.user_email:
        db = cargar_db()
        db[st.session_state.user_email] = st.session_state.portfolio
        guardar_db(db)

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}

# ============================================================
# 2. INYECCIÓN DE CSS Y HTML (NAVBAR Y FOOTER FIJOS)
# ============================================================

st.markdown("""
<style>
    [data-testid="collapsedControl"] { display: none; }
    header { display: none !important; }
    
    .block-container {
        padding-top: 90px !important;
        padding-bottom: 70px !important;
    }

    /* Navbar Profesional Estilo Terminal */
    .navbar {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #0d1117;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        display: flex;
        align-items: center;
        padding: 0 24px;
        border-bottom: 1px solid #30363d;
        z-index: 9999;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }

    .navbar a.brand {
        font-size: 20px;
        font-weight: 700;
        color: #00e676;
        text-decoration: none;
        padding: 12px 16px;
        margin-right: 20px;
        letter-spacing: 0.5px;
    }

    .dropdown {
        float: left;
        overflow: hidden;
        height: 100%;
    }

    .dropdown .dropbtn {
        font-size: 15px;
        border: none;
        outline: none;
        color: #c9d1d9;
        padding: 16px 18px;
        background-color: inherit;
        font-family: inherit;
        margin: 0;
        cursor: pointer;
        transition: color 0.2s;
    }

    .navbar a:hover, .dropdown:hover .dropbtn {
        color: #00e676;
        background-color: #161b22;
    }

    .dropdown-content {
        display: none;
        position: absolute;
        background-color: #161b22;
        min-width: 240px;
        box-shadow: 0px 10px 24px 0px rgba(0,0,0,0.6);
        z-index: 10000;
        border: 1px solid #30363d;
        border-radius: 6px;
        margin-top: 2px;
    }

    .dropdown-content a {
        float: none;
        color: #c9d1d9;
        padding: 12px 18px;
        text-decoration: none;
        display: block;
        text-align: left;
        font-size: 14px;
        transition: background 0.2s, color 0.2s;
    }

    .dropdown-content a:hover {
        background-color: #1f6feb33;
        color: #00e676;
        font-weight: 600;
    }

    .dropdown:hover .dropdown-content {
        display: block;
    }

    /* Footer Profesional */
    .fixed-footer {
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
    }
    
    /* Diseño Minimalista para Tarjetas de Noticias */
    .news-card {
        background-color: #161b22;
        padding: 22px;
        border-radius: 8px;
        border: 1px solid #30363d;
        border-left: 4px solid #00e676;
        height: 100%;
        display: flex;
        flex-direction: column;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .news-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(0,230,118,0.1);
    }
    
    .news-card a {
        color: #58a6ff;
        text-decoration: none;
        margin-top: auto;
        font-weight: 600;
        font-size: 0.9rem;
        transition: color 0.2s;
    }
    
    .news-card a:hover {
        color: #00e676;
        text-decoration: underline;
    }
    
    .stButton > button {
        border-radius: 6px;
    }
</style>

<div class="navbar">
<a class="brand" href="/?nav=inicio" target="_self">📊 Monitor Financiero</a>

<div class="dropdown">
<button class="dropbtn">💼 Mi Portafolio ▾</button>
<div class="dropdown-content">
<a href="/?nav=portfolio" target="_self">📈 Ver Portafolio</a>
</div>
</div>

<div class="dropdown">
<button class="dropbtn">Internacional ▾</button>
<div class="dropdown-content">
<a href="/?nav=int_acciones" target="_self">📈 Acciones Internacionales</a>
<a href="/?nav=int_bonos" target="_self">📄 Bonos Internacionales</a>
<a href="/?nav=int_commodities" target="_self">🛢️ Commodities</a>
<a href="/?nav=int_etfs" target="_self">📊 ETFs Globales</a>
<a href="/?nav=int_datos" target="_self">🏦 Datos Macroeconómicos</a>
</div>
</div>
<div class="dropdown">
<button class="dropbtn">Argentina ▾</button>
<div class="dropdown-content">
<a href="/?nav=arg_acciones" target="_self">📈 Acciones Locales (Pesos)</a>
<a href="/?nav=arg_ons" target="_self">📄 Obligaciones Negociables</a>
<a href="/?nav=arg_bonos" target="_self">📄 Bonos Argentinos</a>
<a href="/?nav=arg_etfs" target="_self">📊 Índices y ETFs</a>
<a href="/?nav=arg_datos" target="_self">🏦 Datos Económicos</a>
</div>
</div>
<div class="dropdown">
<button class="dropbtn">🧮 Herramientas ▾</button>
<div class="dropdown-content">
<a href="/?nav=calc_interes" target="_self">📈 Calc. Interés Compuesto</a>
<a href="/?nav=calc_francesa" target="_self">🏛️ Amortización Francesa</a>
</div>
</div>
<div class="dropdown">
<button class="dropbtn">⚖️ Legal ▾</button>
<div class="dropdown-content">
<a href="/?nav=legal" target="_self">📜 Términos y Condiciones</a>
</div>
</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 3. RUTEO DE LA APLICACIÓN
# ============================================================
nav = st.query_params.get("nav", "inicio")# ============================================================
# BOTÓN DE PAGO PREMIUM (STRIPE)
# ============================================================
st.markdown("---")
st.subheader("🔓 Acceso Completo y Herramientas Premium")
st.write("Obtén acceso ilimitado a todos nuestros modelos de amortización y monitores avanzados.")

# AQUÍ PEGAS TU ENLACE DE STRIPE ENTRE LAS COMILLAS
st.link_button("👉 Suscribirse a Premium Aquí", "https://buy.stripe.com/test_dRmfZ98gH27Q3toh002kw00")
st.markdown("---")


# ============================================================
# 4. EXTRACCIÓN DE DATOS Y NOTICIAS
# ============================================================

@st.cache_data(ttl=300)
def obtener_datos_globales():
    tickers = {
        # MACRO Y TASAS
        "Treasury 2Y": "^IRX", "Treasury 5Y": "^FVX", "Treasury 10Y": "^TNX", "Treasury 30Y": "^TYX",
        "Oro": "GC=F", "WTI": "CL=F", "Bitcoin": "BTC-USD",
        "S&P 500 (Índice)": "^GSPC", "SPY (ETF)": "SPY", "QQQ (ETF Nasdaq)": "QQQ", "DIA (ETF Dow)": "DIA",
        
        # INTERNACIONALES (Ampliadas)
        "Apple": "AAPL", "Nvidia": "NVDA", "Tesla": "TSLA", "Microsoft": "MSFT",
        "Amazon": "AMZN", "Google": "GOOGL", "Meta": "META", "Nestlé": "NSRGY",
        "Johnson & Johnson": "JNJ", "Coca-Cola": "KO", "Visa": "V", "Walmart": "WMT",
        "JPMorgan": "JPM", "Procter & Gamble": "PG", "Disney": "DIS",
        
        # ARGENTINAS (Más de 15)
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
        except:
            pass

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
    except:
        pass
        
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
        noticias_combinadas = [{
            "categoria": "MERCADO", "titulo": "Actualización de Mercado", 
            "desc": "Revisa los últimos movimientos en los indicadores globales.", "link": "#"
        }]
        
    return noticias_combinadas

# ============================================================
# 5. CARGA DE DATOS
# ============================================================

globales = obtener_datos_globales()
bonos_arg = obtener_bonos_argentinos()
macro_arg = obtener_macro_argentina()
noticias_feed = obtener_noticias_dinamicas()

# ============================================================
# 6. RENDERIZADO DE LAS PÁGINAS SEGÚN EL MENÚ
# ============================================================

def formatear_variacion(val):
    if val > 0: return f"color: #00e676;"
    elif val < 0: return f"color: #ff4b4b;"
    return ""

if nav == "inicio":
    st.title("📰 Titulares Globales y Locales")
    st.markdown("Revisión de las últimas noticias económicas, puramente informativas y con un diseño centrado en la lectura.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    for i in range(0, len(noticias_feed), 3):
        cols = st.columns(3)
        fila_noticias = noticias_feed[i:i+3]
        
        for index, articulo in enumerate(fila_noticias):
            with cols[index]:
                # Diseño minimalista, sin imágenes externas que se rompan
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

elif nav == "portfolio":
    st.title("💼 Mi Portafolio de Inversión")
    st.markdown("Busca y agrega activos para ver su valuación en tiempo real y sus fechas importantes.")
    
    st.markdown("##### 👤 Inicia Sesión para Guardar tu Portafolio")
    col_login, col_empty = st.columns([1, 1])
    with col_login:
        email_usuario = st.text_input("Ingresa tu email para no perder tu progreso:", 
                                     value=st.session_state.get("user_email", ""),
                                     placeholder="ejemplo@correo.com")
        
        if email_usuario and email_usuario != st.session_state.get("user_email", ""):
            st.session_state.user_email = email_usuario
            db = cargar_db()
            if email_usuario not in db:
                db[email_usuario] = {}
                guardar_db(db)
            st.session_state.portfolio = db[email_usuario]
            st.success("✅ Portafolio cargado exitosamente.")
            st.rerun()

    st.divider()
    
    with st.expander("➕ Buscar y Agregar Activo (Presiona Enter para buscar)", expanded=True):
        query = st.text_input("🔍 Escribe el nombre o ticker y presiona Enter (ej. Apple, Galicia, BTC):")
        opciones_encontradas = {}
        if query:
            try:
                url_search = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=6"
                res = requests.get(url_search, headers=HEADERS, timeout=5).json()
                for q in res.get('quotes', []):
                    simbolo = q.get('symbol')
                    nombre = q.get('shortname', q.get('longname', 'Desconocido'))
                    tipo = q.get('quoteType', 'Asset')
                    if simbolo:
                        opciones_encontradas[f"{simbolo} | {nombre} ({tipo})"] = simbolo
            except:
                pass

        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            if opciones_encontradas:
                seleccion = st.selectbox("Selecciona el activo exacto:", list(opciones_encontradas.keys()))
                nuevo_ticker = opciones_encontradas[seleccion]
            else:
                nuevo_ticker = query.upper().strip()
                if query: st.caption("No hay sugerencias. Se buscará exactamente este Ticker.")

        with c2:
            nueva_cantidad = st.number_input("Cantidad", min_value=0.01, value=1.0, step=0.1)
            
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Agregar a Portafolio", use_container_width=True):
                if nuevo_ticker:
                    with st.spinner(f"Verificando cotización de {nuevo_ticker}..."):
                        try:
                            precio_test = yf.Ticker(nuevo_ticker).fast_info.last_price
                            if precio_test and precio_test > 0:
                                st.session_state.portfolio[nuevo_ticker] = st.session_state.portfolio.get(nuevo_ticker, 0) + nueva_cantidad
                                sincronizar_cartera() 
                                st.success(f"¡{nuevo_ticker} agregado con éxito!")
                                st.rerun()
                            else:
                                st.error(f"❌ El activo '{nuevo_ticker}' cotiza a $0.00 o está inactivo.")
                        except:
                            st.error(f"❌ No se encontró cotización para el ticker '{nuevo_ticker}'.")

    if st.session_state.portfolio:
        st.markdown("### 📊 Composición Actual")
        tickers = list(st.session_state.portfolio.keys())
        precios = {}
        
        with st.spinner("Actualizando cotizaciones..."):
            for t in tickers:
                try: precios[t] = yf.Ticker(t).fast_info.last_price
                except: precios[t] = 0.0
                    
        total_value = 0.0
        datos_tabla = []
        
        for t, qty in list(st.session_state.portfolio.items()):
            precio_actual = precios.get(t, 0.0)
            if precio_actual == 0:
                del st.session_state.portfolio[t]
                sincronizar_cartera()
                continue
                
            valor_posicion = precio_actual * qty
            total_value += valor_posicion
            datos_tabla.append({
                "Activo (Ticker)": t,
                "Cantidad": qty,
                "Precio Mercado": precio_actual,
                "Valor de la Posición": valor_posicion
            })
            
        if datos_tabla:
            df_port = pd.DataFrame(datos_tabla)
            col_tabla, col_grafico = st.columns([1.5, 1])
            
            with col_tabla:
                st.dataframe(df_port.style.format({"Precio Mercado": "${:,.2f}", "Valor de la Posición": "${:,.2f}"}), use_container_width=True, hide_index=True)
                
                st.markdown("#### ✏️ Modificar o Quitar Activos")
                e1, e2, e3 = st.columns([2, 1, 1.5])
                with e1: activo_a_editar = st.selectbox("Activo a editar:", list(st.session_state.portfolio.keys()))
                with e2:
                    cantidad_actual = st.session_state.portfolio.get(activo_a_editar, 1.0)
                    nueva_cantidad_edit = st.number_input("Nueva cant.", min_value=0.0, value=float(cantidad_actual), step=0.1, help="Pon 0 para eliminar")
                with e3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Actualizar / Eliminar", use_container_width=True):
                        if nueva_cantidad_edit <= 0: del st.session_state.portfolio[activo_a_editar]
                        else: st.session_state.portfolio[activo_a_editar] = nueva_cantidad_edit
                        sincronizar_cartera()
                        st.rerun()
                        
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Vaciar Todo el Portafolio", use_container_width=False):
                    st.session_state.portfolio = {}
                    sincronizar_cartera()
                    st.rerun()
                    
            with col_grafico:
                st.metric("Valuación Total Estimada", f"${total_value:,.2f}")
                if total_value > 0:
                    fig = go.Figure(data=[go.Pie(labels=df_port["Activo (Ticker)"], values=df_port["Valor de la Posición"], hole=.45, marker_colors=['#00e676', '#58a6ff', '#1f6feb', '#8b949e', '#f0f6fc'])])
                    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#c9d1d9'), margin=dict(t=10, b=10, l=10, r=10), showlegend=True)
                    st.plotly_chart(fig, use_container_width=True)

# ----------------- SECCIÓN INTERNACIONAL CON TABLA Y RATIOS SEPARADOS -----------------
elif nav == "int_acciones":
    st.title("📈 Acciones Internacionales")
    
    int_keys = ["Apple", "Nvidia", "Tesla", "Microsoft", "Amazon", "Google", "Meta", "Nestlé", "Johnson & Johnson", "Coca-Cola", "Visa", "Walmart", "JPMorgan", "Procter & Gamble", "Disney"]
    
    st.markdown("### 🌐 Panel General de Cotizaciones")
    
    data_int = []
    for key in int_keys:
        d = globales.get(key)
        if d:
            data_int.append({
                "Activo": key,
                "Precio": d['precio'],
                "Variación (%)": d['var_pct']
            })
            
    if data_int:
        df_int = pd.DataFrame(data_int)
        st.dataframe(
            df_int.style.format({"Precio": "USD {:,.2f}", "Variación (%)": "{:,.2f}%"})
            .map(lambda x: formatear_variacion(x), subset=['Variación (%)']),
            use_container_width=True, hide_index=True
        )
                
    st.divider()
    st.subheader("🔎 Análisis Detallado por Empresa")
    activo_seleccionado = st.selectbox("Selecciona una empresa internacional para ver su información financiera contable y noticias:", int_keys)
    
    if activo_seleccionado and globales.get(activo_seleccionado):
        ticker_str = globales[activo_seleccionado]['ticker']
        with st.spinner(f"Descargando datos de {activo_seleccionado}..."):
            try:
                tk = yf.Ticker(ticker_str)
                info = tk.info
                
                tab_info, tab_fin, tab_news = st.tabs(["📊 Perfil y Ratios", "📉 Información Contable", "📰 Noticias"])
                
                with tab_info:
                    st.write(f"**Sector:** {info.get('sector', '-')} | **Industria:** {info.get('industry', '-')}")
                    st.write(info.get('longBusinessSummary', 'Sin descripción disponible.'))
                    
                    st.markdown("<br>#### Ratios y Métricas Clave", unsafe_allow_html=True)
                    c1, c2, c3, c4 = st.columns(4)
                    
                    mcap = info.get('marketCap')
                    c1.metric("Market Cap", f"$ {mcap:,}" if mcap else "-")
                    
                    pe = info.get('trailingPE')
                    c2.metric("P/E (Price to Earnings)", round(pe, 2) if pe else "-")
                    
                    pb = info.get('priceToBook')
                    c3.metric("P/B (Price to Book)", round(pb, 2) if pb else "-")
                    
                    eps = info.get('trailingEps')
                    c4.metric("BPA / EPS", f"$ {eps:.2f}" if eps else "-")
                    
                with tab_fin:
                    st.markdown("*(Estado de Resultados. Valores expresados en la moneda original del reporte, con separadores de miles)*")
                    df_fin = tk.financials
                    if df_fin is not None and not df_fin.empty:
                        # Formato limpio con comas (Ej: 112,010,000,000)
                        st.dataframe(df_fin.style.format("{:,.0f}", na_rep="-"), use_container_width=True)
                    else:
                        st.info("Estados contables no disponibles temporalmente.")
                    
                with tab_news:
                    noticias = tk.news
                    if noticias:
                        for n in noticias[:5]:
                            st.markdown(f"**[{n['title']}]({n['link']})**")
                    else:
                        st.info("No hay noticias recientes para mostrar.")
            except Exception:
                st.info("No se pudieron obtener todos los detalles de este activo en este momento.")

# ----------------- SECCIÓN ARGENTINA CON TABLA Y RATIOS SEPARADOS -----------------
elif nav == "arg_acciones":
    st.title("📈 Acciones Locales (Merval)")
    
    arg_keys = ["YPF", "Galicia", "Pampa Energía", "Banco Macro", "Central Puerto", "Aluar", "Ternium", "Loma Negra", "Trans. Gas del Norte", "Trans. Gas del Sur", "Edenor", "Transener", "BYMA", "Valo", "Mirgor", "Supervielle", "BBVA AR", "Cablevisión", "Richmond", "Agrometal"]
    
    st.markdown("### 🇦🇷 Panel General de Cotizaciones (Pesos)")
    
    data_arg = []
    for key in arg_keys:
        d = globales.get(key)
        if d:
            data_arg.append({
                "Activo": key,
                "Precio": d['precio'],
                "Variación (%)": d['var_pct']
            })
            
    if data_arg:
        df_arg = pd.DataFrame(data_arg)
        st.dataframe(
            df_arg.style.format({"Precio": "$ {:,.2f}", "Variación (%)": "{:,.2f}%"})
            .map(lambda x: formatear_variacion(x), subset=['Variación (%)']),
            use_container_width=True, hide_index=True
        )
                
    st.divider()
    st.subheader("🔎 Análisis Detallado por Empresa")
    activo_seleccionado = st.selectbox("Selecciona una empresa argentina para ver su información financiera contable y noticias:", arg_keys)
    
    if activo_seleccionado and globales.get(activo_seleccionado):
        ticker_str = globales[activo_seleccionado]['ticker']
        with st.spinner(f"Descargando datos de {activo_seleccionado}..."):
            try:
                tk = yf.Ticker(ticker_str)
                info = tk.info
                
                tab_info, tab_fin, tab_news = st.tabs(["📊 Perfil y Ratios", "📉 Información Contable", "📰 Noticias"])
                
                with tab_info:
                    st.write(f"**Sector:** {info.get('sector', '-')} | **Industria:** {info.get('industry', '-')}")
                    st.write(info.get('longBusinessSummary', 'Sin descripción disponible.'))
                    
                    st.markdown("<br>#### Ratios y Métricas Clave", unsafe_allow_html=True)
                    c1, c2, c3, c4 = st.columns(4)
                    
                    mcap = info.get('marketCap')
                    c1.metric("Market Cap", f"$ {mcap:,}" if mcap else "-")
                    
                    pe = info.get('trailingPE')
                    c2.metric("P/E (Price to Earnings)", round(pe, 2) if pe else "-")
                    
                    pb = info.get('priceToBook')
                    c3.metric("P/B (Price to Book)", round(pb, 2) if pb else "-")
                    
                    eps = info.get('trailingEps')
                    c4.metric("BPA / EPS", f"$ {eps:.2f}" if eps else "-")
                    
                with tab_fin:
                    st.markdown("*(Estado de Resultados. Valores en ARS, ajustados por inflación corporativa)*")
                    df_fin = tk.financials
                    if df_fin is not None and not df_fin.empty:
                        # Formato limpio con comas
                        st.dataframe(df_fin.style.format("{:,.0f}", na_rep="-"), use_container_width=True)
                    else:
                        st.info("Estados contables no disponibles temporalmente.")
                    
                with tab_news:
                    noticias = tk.news
                    if noticias:
                        for n in noticias[:5]:
                            st.markdown(f"**[{n['title']}]({n['link']})**")
                    else:
                        st.info("No hay noticias recientes para mostrar.")
            except Exception:
                st.info("No se pudieron obtener todos los detalles de este activo en este momento.")


# ----------------- NUEVA SECCIÓN: OBLIGACIONES NEGOCIABLES -----------------
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
    
    st.info("💡 **Nota Educativa:** Las Obligaciones Negociables (ONs) son deuda corporativa. La TIR (Tasa Interna de Retorno) es estimativa y depende del precio de compra en el mercado secundario. La información de flujo de fondos mostrada corresponde al prospecto original de emisión de cada compañía.")

# ----------------- RESTO DE VISTAS (BONOS, ETFs, HERRAMIENTAS, LEGAL) -----------------
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
# 7. RENDERIZAR PIE DE PÁGINA DINÁMICO
# ============================================================

tz_ar = pytz.timezone("America/Argentina/Buenos_Aires")
hora_actual = datetime.now(tz_ar).strftime('%d/%m/%Y %H:%M:%S')

footer_html = f"""
<div class="fixed-footer">
    ℹ️ <strong>Fuentes:</strong> Yahoo Finance, DolarApi.com y ArgentinaDatos. &nbsp;&nbsp;|&nbsp;&nbsp; ⚠️ <strong>Aviso legal:</strong> Fines informativos. No somos un ALyC (CNV). &nbsp;&nbsp;|&nbsp;&nbsp; 🕒 Última actualización: {hora_actual}
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
