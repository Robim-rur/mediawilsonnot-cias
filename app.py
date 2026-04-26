# app.py
# BUY SIDE TERMINAL V4 ELITE - EDGE ENGINE + SIMULADOR + ZERO CRASH

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
# CSS
# =====================================================

st.markdown("""
<style>
.main {background:#0e1117;}
.stTextInput input {
    background:#161b22 !important;
    color:white !important;
}
.stButton button {
    width:100%;
    height:44px;
    border-radius:10px;
}
.stMetric {
    background:#161b22;
    padding:14px;
    border-radius:10px;
    border:1px solid #30363d;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# LOGIN
# =====================================================

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    st.title("🏹 BUY SIDE TERMINAL V4 ELITE")

    senha = st.text_input("Senha:", type="password")

    if st.button("ENTRAR"):
        if senha == SENHA:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")

    st.stop()

# =====================================================
# UNIVERSO (INSIRA SUA LISTA COMPLETA 178 AQUI)
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


def analisar(ticker):

    df = yf.download(
        ticker + ".SA",
        period="260d",
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if df is None or df.empty:
        return None

    if len(df) < 130:
        return None

    close = df["Close"].dropna().values.astype(float)
    volume = df["Volume"].dropna().values.astype(float)

    if len(close) < 130:
        return None

    preco = close[-1]

    ema21 = ema(df["Close"], 21).values
    ema72 = ema(df["Close"], 72).values

    # =====================================================
    # SCORE BASE
    # =====================================================

    score = 0

    if preco > ema21[-1]:
        score += 15

    if ema21[-1] > ema72[-1]:
        score += 15

    ret5 = (preco / close[-6] - 1) * 100

    if ret5 > 0:
        score += min(ret5 * 2, 15)

    vol_media = np.mean(volume[-20:])

    if volume[-1] > vol_media:
        score += 10

    # =====================================================
    # WILSON SCORE
    # =====================================================

    checks = [
        preco > ema21[-1],
        ema21[-1] > ema72[-1],
        ret5 > 0,
        volume[-1] > vol_media
    ]

    pos = sum(checks)

    wil = (pos / len(checks)) * 100

    prob = wil

    # =====================================================
    # REGIME DE VOLATILIDADE (CORRIGIDO DEFINITIVO)
    # =====================================================

    window_raw = close[-25:]
    window = pd.Series(window_raw).dropna().values

    if len(window) < 21:
        return None

    window = window[-21:]

    if len(window) < 21:
        return None

    ret = np.diff(window) / window[:-1]
    vol = np.std(ret) * 100

    if vol < 1.2:
        adj = 1.15
    elif vol < 2.5:
        adj = 1.0
    else:
        adj = 0.75

    prob_adj = prob * adj

    # =====================================================
    # RISCO / RETORNO
    # =====================================================

    stop = preco * 0.965
    atr = np.std(close[-14:])

    gain = atr * 2.2 * (prob_adj / 100)

    rr = gain / (preco - stop) if (preco - stop) != 0 else 0

    # =====================================================
    # EDGE REAL
    # =====================================================

    risco = preco - stop

    edge = (prob_adj / 100 * gain) - ((1 - prob_adj / 100) * risco)

    return {
        "Ativo": ticker,
        "Preço": round(preco,2),
        "Prob": round(prob_adj,2),
        "Gain": round(gain,2),
        "RR": round(rr,2),
        "EDGE": round(edge,4),
        "Stop": round(stop,2)
    }

# =====================================================
# SCANNER
# =====================================================

st.title("🏹 V4 ELITE EDGE SYSTEM")

if st.button("ESCANEAR MERCADO"):

    resultados = []

    barra = st.progress(0)

    total = len(ATIVOS)

    for i, t in enumerate(ATIVOS):

        r = analisar(t)

        if r is not None:
            resultados.append(r)

        barra.progress((i+1)/total)

    if len(resultados) == 0:
        st.warning("Nenhum ativo válido encontrado.")
        st.stop()

    df = pd.DataFrame(resultados)

    df = df.sort_values("EDGE", ascending=False)

    top8 = df.head(8)

    st.subheader("🏆 TOP 8 TRADES (EDGE REAL)")

    st.dataframe(top8, use_container_width=True)

    # =====================================================
    # SIMULADOR MENSAL
    # =====================================================

    ev_list = []

    for _, row in top8.iterrows():

        prob = row["Prob"] / 100
        gain = row["Gain"]
        stop = row["Stop"]

        ev = (prob * gain) - ((1 - prob) * (stop * 0.035))

        ev_list.append(ev)

    ev_total = np.sum(ev_list)

    st.subheader("📊 SIMULAÇÃO MENSAL (8 TRADES)")

    st.write(f"Expectativa mensal: {ev_total * 100:.2f}%")

    if ev_total >= 0.05:
        st.success("Meta de +5% ao mês estatisticamente viável")
    else:
        st.warning("Meta de +5% ainda abaixo da expectativa atual")
