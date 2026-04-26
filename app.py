# app.py
# BUY SIDE TERMINAL V4 ELITE - PRICE TARGET FIX

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
    page_title="BUY SIDE TERMINAL V4 ELITE",
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

    st.title("🏹 BUY SIDE TERMINAL V4 ELITE")

    senha_input = st.text_input("Digite a senha:", type="password")

    if st.button("ENTRAR"):
        if senha_input == SENHA:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta")

    st.stop()

# =====================================================
# ATIVOS
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
# FUNÇÕES SEGURAS
# =====================================================

def safe_array(x):
    x = np.array(x, dtype=float).reshape(-1)
    x = x[~np.isnan(x)]
    return x if len(x) > 10 else None


def ema(s, n):
    s = safe_array(s)
    if s is None:
        return np.zeros(10)
    return pd.Series(s).ewm(span=n, adjust=False).mean().values


def atr(close):
    close = safe_array(close)
    if close is None or len(close) < 15:
        return 0
    return np.mean(np.abs(np.diff(close[-14:])))

# =====================================================
# TARGETS EM PREÇO (VERSÃO CORRIGIDA)
# =====================================================

def targets_preco(close):

    close = safe_array(close)
    if close is None:
        return None, None

    atual = close[-1]

    high20 = np.max(close[-20:])
    low20 = np.min(close[-20:])

    volatility = atr(close)

    # =========================
    # STOP (PREÇO REAL)
    # =========================

    stop = low20 - volatility

    # =========================
    # GAIN (PREÇO REAL)
    # =========================

    gain = high20 + volatility

    return round(gain, 2), round(stop, 2)

# =====================================================
# ANALISAR ATIVO
# =====================================================

def analisar(ticker):

    df = yf.download(ticker + ".SA", period="300d", interval="1d",
                     auto_adjust=True, progress=False)

    if df is None or df.empty:
        return None

    close = safe_array(df["Close"])
    volume = safe_array(df["Volume"])

    if close is None:
        return None

    preco = close[-1]

    ema21 = ema(close, 21)
    ema72 = ema(close, 72)

    trend = preco > ema21[-1] > ema72[-1]

    momentum = preco / close[-5] - 1

    score = 0
    if trend:
        score += 1
    score += momentum * 5

    vol = np.std(np.diff(close) / close[:-1])

    # =========================
    # PROBABILIDADE (NORMALIZADA)
    # =========================

    prob = 1 / (1 + np.exp(-score * 2)) * 100

    # =========================
    # TARGETS EM PREÇO
    # =========================

    gain, stop = targets_preco(close)

    return {
        "Ativo": ticker,
        "Preço": round(preco,2),
        "Prob": round(prob,2),
        "Gain": gain,
        "Stop": stop,
        "score": score
    }

# =====================================================
# SCANNER
# =====================================================

st.title("🏹 SCANNER V4 ELITE - PRICE TARGET")

if st.button("ESCANEAR MERCADO"):

    resultados = []

    for t in ATIVOS:
        r = analisar(t)
        if r:
            resultados.append(r)

    df = pd.DataFrame(resultados)

    if df.empty:
        st.warning("Sem dados suficientes")
        st.stop()

    # =========================
    # RANKING
    # =========================

    df["rank_score"] = df["Prob"] * 0.6 + df["score"] * 10

    df = df.sort_values("rank_score", ascending=False).reset_index(drop=True)

    df.index = df.index + 1
    df.insert(0, "Rank", df.index)

    # =========================
    # RESULTADO FINAL
    # =========================

    st.dataframe(
        df[["Rank","Ativo","Preço","Prob","Gain","Stop"]],
        use_container_width=True
    )
