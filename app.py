# app.py
# BUY SIDE TERMINAL V4 ELITE - HISTORICAL CALIBRATION ENGINE

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
"PETR4","VALE3","BBAS3","ITUB4","WEGE3","PRIO3","RENT3",
"BOVA11","IVVB11","SMAL11","GOLD11","DIVO11","NDIV11",
"HGLG11","XPLG11","VISC11","MXRF11","KNRI11",
"AAPL34","MSFT34","TSLA34","AMZO34","META34",
"C2OL34"
]

# =====================================================
# UTIL
# =====================================================

def ema(series, n):
    return series.ewm(span=n, adjust=False).mean()

# =====================================================
# CALIBRAÇÃO HISTÓRICA (CORE QUANT)
# =====================================================

def historical_calibration(close, signal_strength):

    """
    Simula performance histórica do mesmo tipo de setup
    usando janelas deslizantes.
    """

    closes = np.array(close)

    wins = 0
    total = 0

    for i in range(30, len(closes) - 5):

        window = closes[i-20:i]

        entry = closes[i]
        future = closes[i+5]

        ret = (future / entry - 1) * 100

        # regra: só conta setups com força semelhante
        if signal_strength[i] > 0.5:

            total += 1

            if ret > 0:
                wins += 1

    if total == 0:
        return 0.5

    return wins / total

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

    if len(df) < 150:
        return None

    close = np.array(df["Close"]).flatten()
    volume = np.array(df["Volume"]).flatten()

    preco = close[-1]

    ema21 = ema(pd.Series(close), 21).values
    ema72 = ema(pd.Series(close), 72).values

    # =====================================================
    # SCORE BASE (EDGE SIGNAL)
    # =====================================================

    score = 0
    signal_strength = []

    for i in range(len(close)):

        s = 0

        if i < 30:
            signal_strength.append(0)
            continue

        if close[i] > ema21[i]:
            s += 1

        if ema21[i] > ema72[i]:
            s += 1

        if volume[i] > np.mean(volume[i-20:i]):
            s += 1

        signal_strength.append(s / 3)

    signal_strength = np.array(signal_strength)

    # =====================================================
    # SCORE ATUAL
    # =====================================================

    if preco > ema21[-1]:
        score += 1

    if ema21[-1] > ema72[-1]:
        score += 1

    if volume[-1] > np.mean(volume[-20:]):
        score += 1

    score_norm = score / 3

    # =====================================================
    # PROBABILIDADE BASE LOGÍSTICA
    # =====================================================

    prob_base = 1 / (1 + np.exp(-score_norm * 2))

    # =====================================================
    # CALIBRAÇÃO HISTÓRICA REAL
    # =====================================================

    calib = historical_calibration(close, signal_strength)

    prob = prob_base * calib

    # =====================================================
    # VOLATILIDADE REGIME
    # =====================================================

    ret = np.diff(close[-21:]) / close[-20:-1]
    vol = np.std(ret) * 100

    if vol < 1.2:
        conf = 1.10
    elif vol < 2.5:
        conf = 1.00
    else:
        conf = 0.85

    prob = prob * conf

    prob = min(max(prob * 100, 0), 100)

    # =====================================================
    # RISCO / RETORNO
    # =====================================================

    stop = preco * 0.965
    atr = np.std(close[-14:])

    gain = atr * 2.2 * prob / 100

    rr = gain / (preco - stop) if preco != stop else 0

    edge = (prob/100 * gain) - ((1 - prob/100) * (preco - stop))

    return {
        "Ativo": ticker,
        "Preço": round(preco,2),
        "Prob": round(prob,2),
        "Gain": round(gain,2),
        "RR": round(rr,2),
        "EDGE": round(edge,4),
        "Stop": round(stop,2)
    }

# =====================================================
# SCANNER
# =====================================================

st.title("🏹 V4 ELITE HC - HISTORICAL CALIBRATED")

if st.button("ESCANEAR MERCADO"):

    resultados = []

    barra = st.progress(0)

    total = len(ATIVOS)

    for i, t in enumerate(ATIVOS):

        r = analisar(t)

        if r:
            resultados.append(r)

        barra.progress((i+1)/total)

    if len(resultados) == 0:
        st.warning("Nenhum ativo válido.")
        st.stop()

    df = pd.DataFrame(resultados)

    df = df.sort_values("EDGE", ascending=False)

    top8 = df.head(8)

    st.subheader("🏆 TOP 8 TRADES")

    st.dataframe(top8, use_container_width=True)

    # =====================================================
    # EXPECTATIVA
    # =====================================================

    ev = np.mean(top8["EDGE"])

    st.subheader("📊 EXPECTATIVA")

    st.write(f"Edge médio: {ev:.4f}")

    if ev > 0:
        st.success("Sistema com vantagem estatística positiva")
    else:
        st.warning("Sistema neutro ou negativo")
