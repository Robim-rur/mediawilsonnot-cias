import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import math
import time

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="BUY SIDE TERMINAL V4 ELITE HC",
    page_icon="🏹",
    layout="wide"
)

SENHA = "LUCRO5"

# =====================================================
# LOGIN
# =====================================================

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    st.title("🏹 V4 ELITE HC - INSTITUTIONAL FULL ENGINE")

    senha = st.text_input("Senha:", type="password")

    if st.button("ENTRAR"):
        if senha == SENHA:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")

    st.stop()

# =====================================================
# UNIVERSO (MANTIDO CONFORME SUA BASE)
# =====================================================

ATIVOS = [
"PETR4","VALE3","BBAS3","ITUB4","BBDC4","WEGE3","PRIO3","RENT3",
"ELET3","ELET6","CPLE6","CMIG4","TAEE11","EGIE3","VIVT3","TIMS3",
"ABEV3","RADL3","SUZB3","GGBR4","GOAU4","USIM5","CSNA3","RAIL3",
"SBSP3","EQTL3","HYPE3","MULT3","LREN3","ARZZ3","TOTS3","EMBR3",
"JBSS3","BEEF3","MRFG3","BRFS3","SLCE3","SMTO3","B3SA3","BBSE3",
"BPAC11","SANB11","ITSA4","BRSR6","CXSE3","POMO4","STBP3","TUPY3",
"DIRR3","CYRE3","EZTC3","JHSF3","KEPL3","POSI3","MOVI3","PETZ3",
"COGN3","YDUQ3","MGLU3","NTCO3","AZUL4","GOLL4","CVCB3","RRRP3",
"RECV3","ENAT3","ORVR3","AURE3","ENEV3","UGPA3",

"BOVA11","IVVB11","SMAL11","HASH11","GOLD11","DIVO11","NDIV11",

"HGLG11","XPLG11","VISC11","MXRF11","KNRI11","KNCR11","KNIP11",
"CPTS11","IRDM11","TRXF11","TGAR11","HGRU11","ALZR11",

"AAPL34","AMZO34","GOGL34","MSFT34","TSLA34","META34","NFLX34",
"NVDC34","MELI34","BABA34","DISB34","PYPL34","JNJB34","VISA34",
"WMTB34","NIKE34","ADBE34","CSCO34","INTC34","JPMC34","ORCL34",
"QCOM34","SBUX34","TXN34","ABTT34","AMGN34","AXPB34","BERK34",

"C2OL34"
]

# =====================================================
# SAFE DATA ENGINE (CRÍTICO)
# =====================================================

def safe_array(x):

    x = np.array(x, dtype=float)

    # garante 1D
    x = x.reshape(-1)

    # remove NaN
    x = x[~np.isnan(x)]

    if len(x) < 5:
        return None

    return x

# =====================================================
# EMA SAFE (CORRIGIDA DEFINITIVA)
# =====================================================

def ema(series, n):

    s = safe_array(series)

    if s is None or len(s) < n:
        return np.zeros(len(series))

    return pd.Series(s).ewm(span=n, adjust=False).mean().values

# =====================================================
# SAFE RETURNS
# =====================================================

def safe_returns(close):

    c = safe_array(close)

    if c is None or len(c) < 2:
        return None

    denom = np.where(c[:-1] == 0, np.nan, c[:-1])

    r = np.diff(c) / denom

    r = r[~np.isnan(r)]

    if len(r) == 0:
        return None

    return r

# =====================================================
# REGIME DETECTOR (MANTIDO + ESTABILIZADO)
# =====================================================

def detectar_regime(df):

    close = safe_array(df["Close"].values)

    if close is None:
        return "LATERAL"

    ema21 = ema(close, 21)

    ret = safe_returns(close[-25:])
    vol = np.std(ret) * 100 if ret is not None else 0

    slope = ema21[-1] - ema21[-5] if len(ema21) > 5 else 0

    high = np.max(close[-20:])
    low = np.min(close[-20:])

    range_pct = ((high - low) / close[-1]) * 100

    if slope > 0 and vol < 3 and range_pct > 3:
        return "TREND"

    if range_pct < 2:
        return "COMPRESSION"

    if vol > 3:
        return "VOLATILE"

    return "LATERAL"

# =====================================================
# STRATEGY ENGINE (INALTERADO CONCEITUALMENTE)
# =====================================================

def strategy_weights(regime):

    if regime == "TREND":
        return {"trend":0.55,"volume":0.25,"mean":0.1,"risk":0.1}

    if regime == "LATERAL":
        return {"trend":0.2,"volume":0.2,"mean":0.5,"risk":0.1}

    if regime == "VOLATILE":
        return {"trend":0.3,"volume":0.2,"mean":0.1,"risk":0.4}

    if regime == "COMPRESSION":
        return {"trend":0.2,"volume":0.1,"mean":0.1,"risk":0.6}

    return {"trend":0.3,"volume":0.3,"mean":0.2,"risk":0.2}

# =====================================================
# ANALISADOR PRINCIPAL
# =====================================================

def analisar(ticker):

    df = yf.download(
        ticker + ".SA",
        period="300d",
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if df is None or df.empty:
        return None

    # =========================
    # SAFE CLEAN (CRÍTICO)
    # =========================

    close = safe_array(df["Close"].values)
    volume = safe_array(df["Volume"].values)

    if close is None or volume is None:
        return None

    if len(close) < 120:
        return None

    preco = close[-1]

    ema21 = ema(close, 21)
    ema72 = ema(close, 72)

    regime = detectar_regime(df)
    weights = strategy_weights(regime)

    # =========================
    # SINAIS
    # =========================

    trend = int(preco > ema21[-1] > ema72[-1])
    volume_sig = int(volume[-1] > np.mean(volume[-20:]))
    mean_rev = int(preco < ema21[-1])

    ret = safe_returns(close[-10:])
    risk = 1 - np.std(ret) if ret is not None else 0.5

    score = (
        trend * weights["trend"] +
        volume_sig * weights["volume"] +
        mean_rev * weights["mean"] +
        risk * weights["risk"]
    )

    # =========================
    # PROBABILIDADE CALIBRADA (SEM COLAPSO)
    # =========================

    prob = 1 / (1 + np.exp(-score * 3.5))
    prob = prob * 100

    # =========================
    # EDGE INSTITUCIONAL (CORRETO E ESTÁVEL)
    # =========================

    gain_pct = 0.05
    stop_pct = 0.035

    edge = (prob/100 * gain_pct) - ((1 - prob/100) * stop_pct)

    edge_pct = edge * 100

    return {
        "Ativo": ticker,
        "Preço": round(preco,2),
        "Prob": round(prob,2),
        "Regime": regime,
        "EDGE (%)": round(edge_pct,3),
        "Gain (%)": round(gain_pct*100,2),
        "Stop (%)": round(stop_pct*100,2)
    }

# =====================================================
# SCANNER
# =====================================================

st.title("🏹 V4 ELITE HC - INSTITUTIONAL FINAL ENGINE")

if st.button("ESCANEAR MERCADO"):

    resultados = []
    barra = st.progress(0)

    for i, t in enumerate(ATIVOS):

        r = analisar(t)

        if r and r["Prob"] >= 60:
            resultados.append(r)

        barra.progress((i+1)/len(ATIVOS))

    if len(resultados) == 0:
        st.warning("Nenhum ativo encontrado.")
        st.stop()

    df = pd.DataFrame(resultados)

    df = df.sort_values("EDGE (%)", ascending=False)

    st.subheader("🏆 TOP OPPORTUNITIES")

    st.dataframe(df.head(10), use_container_width=True)

    st.subheader("📊 REGIMES")

    st.bar_chart(df["Regime"].value_counts())
