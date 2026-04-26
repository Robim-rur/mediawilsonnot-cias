# BUY SIDE TERMINAL V4 ELITE HC - FIX PROB + EDGE DIVERGENTE

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import math

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(page_title="V4 ELITE FIX", layout="wide")

SENHA = "LUCRO5"

# =====================================================
# LOGIN
# =====================================================

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("V4 ELITE FIX")

    s = st.text_input("Senha:", type="password")

    if st.button("ENTRAR"):
        if s == SENHA:
            st.session_state.logado = True
            st.rerun()
    st.stop()

# =====================================================
# UNIVERSO
# =====================================================

ATIVOS = ["PETR4","VALE3","BBAS3","ITUB4","BBDC4","WEGE3","PRIO3","RENT3",
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

"C2OL34"]

# =====================================================
# UTIL
# =====================================================

def ema(s, n):
    return pd.Series(s).ewm(span=n, adjust=False).mean().values

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

# =====================================================
# SAFE SCORE BASE
# =====================================================

def score_base(df):

    close = df["Close"].values
    vol = df["Volume"].values

    ema21 = ema(close, 21)
    ema72 = ema(close, 72)

    trend = close[-1] > ema21[-1] > ema72[-1]
    volume = vol[-1] > np.mean(vol[-20:])

    momentum = close[-1] > close[-5]

    score = 0
    if trend: score += 1
    if volume: score += 1
    if momentum: score += 1

    return score

# =====================================================
# ANALISADOR
# =====================================================

def analisar(t):

    df = yf.download(t+".SA", period="250d", interval="1d", auto_adjust=True, progress=False)

    if df is None or df.empty:
        return None

    close = df["Close"].values

    scores = []

    # =================================================
    # SCORE INDIVIDUAL SIMPLES
    # =================================================

    ema21 = ema(close, 21)
    ema72 = ema(close, 72)

    trend = close[-1] > ema21[-1] > ema72[-1]
    mom = close[-1] / close[-5] - 1

    score = 0
    score += 1 if trend else 0
    score += mom * 10

    scores.append(score)

    base = np.mean(scores)
    std = np.std(scores) if np.std(scores) != 0 else 1

    # =================================================
    # NORMALIZAÇÃO CROSS SECTION (CORREÇÃO PRINCIPAL)
    # =================================================

    z = (score - base) / std

    prob = sigmoid(z * 1.2) * 100

    # =================================================
    # VOLATILIDADE DINÂMICA
    # =================================================

    returns = np.diff(close[-20:]) / close[-21:-1]
    vol = np.std(returns)

    gain = vol * 100 * 2
    stop = vol * 100 * 1.2

    # =================================================
    # EDGE REAL
    # =================================================

    edge = (prob/100 * gain) - ((1 - prob/100) * stop)

    return {
        "Ativo": t,
        "Preço": close[-1],
        "Prob": round(prob,2),
        "EDGE": round(edge,4)
    }

# =====================================================
# SCANNER
# =====================================================

st.title("V4 ELITE FIX - PROB CORRIGIDA")

if st.button("ESCANEAR"):

    res = []

    for t in ATIVOS:

        r = analisar(t)

        if r:
            res.append(r)

    df = pd.DataFrame(res)

    df = df.sort_values("EDGE", ascending=False)

    st.dataframe(df, use_container_width=True)
