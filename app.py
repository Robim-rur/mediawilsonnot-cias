# app.py
# BUY SIDE TERMINAL V4 ELITE HC - REGIME + STRATEGY OPTIMIZER

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

    st.title("🏹 BUY SIDE TERMINAL V4 ELITE HC")

    senha = st.text_input("Senha:", type="password")

    if st.button("ENTRAR"):
        if senha == SENHA:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")

    st.stop()

# =====================================================
# UNIVERSO
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
# UTIL
# =====================================================

def ema(series, n):
    return series.ewm(span=n, adjust=False).mean()

# =====================================================
# REGIME DETECTOR
# =====================================================

def detectar_regime(df):

    close = df["Close"].values

    ema21 = ema(df["Close"], 21).values
    ema72 = ema(df["Close"], 72).values

    # volatilidade
    returns = np.diff(close) / close[:-1]
    vol = np.std(returns[-20:]) * 100

    # tendência
    slope = ema21[-1] - ema21[-5]
    adx_proxy = abs(slope) * 10

    # range
    high = np.max(close[-20:])
    low = np.min(close[-20:])
    range_pct = (high - low) / close[-1] * 100

    if adx_proxy > 25 and slope > 0:
        return "TREND"

    if range_pct < 2:
        return "COMPRESSION"

    if vol > 2.5:
        return "VOLATILE"

    return "LATERAL"

# =====================================================
# STRATEGY OPTIMIZER (POR REGIME)
# =====================================================

def strategy_weights(regime):

    if regime == "TREND":
        return {
            "trend": 0.55,
            "volume": 0.25,
            "mean_reversion": 0.10,
            "risk": 0.10
        }

    if regime == "LATERAL":
        return {
            "trend": 0.20,
            "volume": 0.20,
            "mean_reversion": 0.50,
            "risk": 0.10
        }

    if regime == "VOLATILE":
        return {
            "trend": 0.30,
            "volume": 0.20,
            "mean_reversion": 0.10,
            "risk": 0.40
        }

    if regime == "COMPRESSION":
        return {
            "trend": 0.20,
            "volume": 0.10,
            "mean_reversion": 0.10,
            "risk": 0.60
        }

    return {
        "trend": 0.3,
        "volume": 0.3,
        "mean_reversion": 0.2,
        "risk": 0.2
    }

# =====================================================
# ANÁLISE
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

    if len(df) < 120:
        return None

    close = df["Close"].values
    volume = df["Volume"].values

    preco = close[-1]

    ema21 = ema(df["Close"], 21).values
    ema72 = ema(df["Close"], 72).values

    regime = detectar_regime(df)
    weights = strategy_weights(regime)

    # =====================================================
    # COMPONENTES DE SCORE
    # =====================================================

    trend_score = 0
    volume_score = 0
    mean_rev = 0
    risk_score = 0

    if preco > ema21[-1] > ema72[-1]:
        trend_score = 1

    if volume[-1] > np.mean(volume[-20:]):
        volume_score = 1

    if close[-1] < ema21[-1]:
        mean_rev = 1

    returns = np.diff(close[-10:]) / close[-11:-1]
    risk_score = 1 - np.std(returns)

    # =====================================================
    # SCORE FINAL ADAPTATIVO
    # =====================================================

    score = (
        trend_score * weights["trend"] +
        volume_score * weights["volume"] +
        mean_rev * weights["mean_reversion"] +
        risk_score * weights["risk"]
    )

    prob = 1 / (1 + np.exp(-score * 5))
    prob = prob * 100

    stop = preco * 0.965
    gain = preco * 1.05

    edge = (prob/100 * gain) - ((1 - prob/100) * (preco - stop))

    return {
        "Ativo": ticker,
        "Preço": round(preco,2),
        "Prob": round(prob,2),
        "Regime": regime,
        "EDGE": round(edge,4),
        "Stop": round(stop,2),
        "Gain": round(gain,2)
    }

# =====================================================
# SCANNER
# =====================================================

st.title("🏹 V4 ELITE HC - REGIME + STRATEGY ENGINE")

if st.button("ESCANEAR MERCADO"):

    resultados = []
    barra = st.progress(0)

    for i, t in enumerate(ATIVOS):

        r = analisar(t)

        if r and r["Prob"] >= 60:
            resultados.append(r)

        barra.progress((i+1)/len(ATIVOS))

    if len(resultados) == 0:
        st.warning("Nenhum ativo elegível encontrado.")
        st.stop()

    df = pd.DataFrame(resultados)

    df = df.sort_values("EDGE", ascending=False)

    top8 = df.head(8)

    st.subheader("🏆 TOP 8 ADAPTATIVO POR REGIME")

    st.dataframe(top8, use_container_width=True)

    st.subheader("📊 DISTRIBUIÇÃO DE REGIMES")

    st.bar_chart(df["Regime"].value_counts())
