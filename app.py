# =====================================================
# BUY SIDE TERMINAL V4 ELITE + SIMULADOR
# =====================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import math

st.set_page_config(page_title="V4 ELITE SIMULATOR", layout="wide")

SENHA = "LUCRO5"

# =====================================================
# LOGIN
# =====================================================

if "ok" not in st.session_state:
    st.session_state.ok = False

if not st.session_state.ok:
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if senha == SENHA:
            st.session_state.ok = True
            st.rerun()
        else:
            st.error("Senha inválida")

    st.stop()

# =====================================================
# ATIVOS (INSERIR SUA LISTA COMPLETA AQUI)
# =====================================================

ATIVOS = [
"PETR4","VALE3","BBAS3","ITUB4","WEGE3","PRIO3","RENT3",
"BOVA11","IVVB11"
]

# =====================================================
# FUNÇÕES
# =====================================================

def ema(s,n):
    return s.ewm(span=n,adjust=False).mean()


def analisar(t):

    df = yf.download(t+".SA", period="250d", interval="1d", auto_adjust=True, progress=False)

    if df.empty:
        return None

    c = df["Close"].values
    h = df["High"].values
    v = df["Volume"].values

    price = c[-1]

    e21 = ema(df["Close"],21).values
    e72 = ema(df["Close"],72).values

    # =========================
    # SCORE BASE
    # =========================

    score = 0

    if price > e21[-1]:
        score += 15

    if e21[-1] > e72[-1]:
        score += 15

    ret5 = (price/c[-6]-1)*100

    if ret5 > 0:
        score += 10

    vol_ok = v[-1] > np.mean(v[-20:])
    if vol_ok:
        score += 10

    # =========================
    # WILSON
    # =========================

    checks = [
        price > e21[-1],
        e21[-1] > e72[-1],
        ret5 > 0,
        vol_ok
    ]

    pos = sum(checks)

    wil = (pos/len(checks))*100

    prob = wil

    # =========================
    # VOLATILIDADE REGIME
    # =========================

    ret = np.diff(c[-20:])/c[-20:-1]
    vol = np.std(ret)*100

    if vol < 1.2:
        adj = 1.15
    elif vol < 2.5:
        adj = 1.0
    else:
        adj = 0.75

    prob_adj = prob * adj

    # =========================
    # RISCO / RETORNO
    # =========================

    stop = price*0.965
    atr = np.std(c[-14:])

    gain = atr*2.2*(prob_adj/100)

    rr = gain/(price-stop)

    # =========================
    # EDGE REAL
    # =========================

    risk = price-stop

    edge = (prob_adj/100 * gain) - ((1-prob_adj/100)*risk)

    return {
        "Ativo": t,
        "Preço": price,
        "Prob": prob_adj,
        "Gain": gain,
        "RR": rr,
        "EDGE": edge,
        "Stop": stop
    }

# =====================================================
# SCANNER
# =====================================================

if st.button("ESCANEAR"):

    res = []

    bar = st.progress(0)

    for i,t in enumerate(ATIVOS):

        r = analisar(t)

        if r:
            res.append(r)

        bar.progress((i+1)/len(ATIVOS))

    df = pd.DataFrame(res)

    df = df.sort_values("EDGE",ascending=False)

    top8 = df.head(8)

    st.subheader("TOP 8 TRADES")

    st.dataframe(top8)

    # =====================================================
    # SIMULADOR MENSAL
    # =====================================================

    ev_list = []

    for _,row in top8.iterrows():

        prob = row["Prob"]/100
        gain = row["Gain"]
        stop = row["Stop"]

        ev = (prob*gain) - ((1-prob)*(stop*0.035))

        ev_list.append(ev)

    ev_total = np.sum(ev_list)

    st.subheader("📊 SIMULAÇÃO MENSAL (8 TRADES)")

    st.write(f"Expectativa mensal: {ev_total*100:.2f}%")

    if ev_total > 0.05:
        st.success("Meta de +5%/mês estatisticamente viável")
    else:
        st.warning("Meta de +5% ainda abaixo da expectativa atual")
