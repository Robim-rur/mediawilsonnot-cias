# app.py
# BUY SIDE TERMINAL V4 ELITE - EDGE ENGINE + SIMULADOR
# COMPLETO E CORRIGIDO

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
# UNIVERSO (INSIRA SUA LISTA COMPLETA AQUI)
# =====================================================

ATIVOS = [
"PETR4","VALE3","BBAS3","ITUB4","WEGE3","PRIO3","RENT3",
"BOVA11","IVVB11","SMAL11","GOLD11","DIVO11","NDIV11",
"HGLG11","XPLG11","VISC11","MXRF11","KNRI11",
"AAPL34","MSFT34","TSLA34","AMZO34","META34",
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

    if df.empty or len(df) < 120:
        return None

    close = df["Close"].values.astype(float)
    volume = df["Volume"].values.astype(float)

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
    # REGIME DE VOLATILIDADE (CORRIGIDO)
    # =====================================================

    window = close[-21:]

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

    rr = gain / (preco - stop)

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

    for i, t in enumerate(ATIVOS):

        r = analisar(t)

        if r:
            resultados.append(r)

        barra.progress((i+1)/len(ATIVOS))

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

    evs = []

    for _, row in top8.iterrows():

        prob = row["Prob"] / 100
        gain = row["Gain"]
        stop = row["Stop"]

        ev = (prob * gain) - ((1 - prob) * (stop * 0.035))

        evs.append(ev)

    ev_total = np.sum(evs)

    st.subheader("📊 SIMULAÇÃO MENSAL (8 TRADES)")

    st.write(f"Expectativa mensal estimada: {ev_total * 100:.2f}%")

    if ev_total >= 0.05:
        st.success("Sistema estatisticamente compatível com meta de +5% ao mês")
    else:
        st.warning("Meta de +5% ainda abaixo da expectativa atual")
