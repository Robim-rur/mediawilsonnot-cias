# app.py
# BUY SIDE TERMINAL V4 ELITE HC - FIXED + 60% FILTER

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
# FUNÇÕES
# =====================================================

def ema(series, n):
    return series.ewm(span=n, adjust=False).mean()

def historical_calibration(close, signal):

    wins = 0
    total = 0

    close = np.array(close).flatten()
    signal = np.array(signal).flatten()

    for i in range(30, len(close) - 5):

        if i >= len(signal):
            continue

        if signal[i] > 0.5:

            entry = close[i]
            future = close[i+5]

            ret = (future / entry - 1) * 100

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

    close = close[~np.isnan(close)]
    volume = volume[~np.isnan(volume)]

    if len(close) < 150:
        return None

    preco = close[-1]

    ema21 = ema(pd.Series(close), 21).values
    ema72 = ema(pd.Series(close), 72).values

    # =====================================================
    # SCORE + SIGNAL
    # =====================================================

    score = 0
    signal = []

    for i in range(len(close)):

        if i < 30:
            signal.append(0)
            continue

        s = 0

        if close[i] > ema21[i]:
            s += 1

        if ema21[i] > ema72[i]:
            s += 1

        if volume[i] > np.mean(volume[i-20:i]):
            s += 1

        signal.append(s / 3)

    signal = np.array(signal)

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
    # PROBABILIDADE BASE
    # =====================================================

    prob = 1 / (1 + np.exp(-score_norm * 2))

    # =====================================================
    # CALIBRAÇÃO HISTÓRICA
    # =====================================================

    calib = historical_calibration(close, signal)

    prob = prob * calib

    # =====================================================
    # VOLATILIDADE (CORRIGIDO)
    # =====================================================

    window = np.array(close[-21:]).flatten()
    window = window[~np.isnan(window)]

    if len(window) < 21:
        return None

    window = window[-21:]

    ret = np.diff(window) / window[:-1]

    vol = np.std(ret) * 100

    if vol < 1.2:
        conf = 1.10
    elif vol < 2.5:
        conf = 1.00
    else:
        conf = 0.85

    prob = prob * conf

    prob = max(0, min(prob * 100, 100))

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

st.title("🏹 V4 ELITE HC - FILTRO 60% ATIVO")

if st.button("ESCANEAR MERCADO"):

    resultados = []

    barra = st.progress(0)

    total = len(ATIVOS)

    for i, t in enumerate(ATIVOS):

        r = analisar(t)

        # ✔ FILTRO CORRETO AQUI (60%)
        if r and r["Prob"] >= 60:
            resultados.append(r)

        barra.progress((i+1)/total)

    if len(resultados) == 0:
        st.warning("Nenhum ativo acima de 60% encontrado.")
        st.stop()

    df = pd.DataFrame(resultados)

    df = df.sort_values("EDGE", ascending=False)

    top8 = df.head(8)

    st.subheader("🏆 TOP 8 TRADES (FILTRADOS > 60%)")

    st.dataframe(top8, use_container_width=True)

    # =====================================================
    # EXPECTATIVA
    # =====================================================

    ev = np.mean(top8["EDGE"])

    st.subheader("📊 EXPECTATIVA DO SISTEMA")

    st.write(f"Edge médio: {ev:.4f}")

    if ev > 0:
        st.success("Sistema com vantagem estatística positiva")
    else:
        st.warning("Sistema neutro ou sem edge claro")
