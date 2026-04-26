# app.py
# BUY SIDE TERMINAL V4 ELITE HC - FILTRO 60% + BACKTEST + WEEKLY CONFIRM

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
# ATIVOS
# =====================================================

ATIVOS = [
"RRRP3","ALOS3","ALPA4","ABEV3","ARZZ3","ASAI3","AZUL4",
"B3SA3","BBAS3","BBDC3","BBDC4","BBSE3","BEEF3","BPAC11",
"BRAP4","BRFS3","BRKM5","CCRO3","CMIG4","CMIN3","COGN3",
"CPFE3","CPLE6","CRFB3","CSAN3","CSNA3","CYRE3","DXCO3",
"EGIE3","ELET3","ELET6","EMBR3","ENEV3","ENGI11","EQTL3",
"EZTC3","FLRY3","GGBR4","GOAU4","GOLL4","HAPV3","HYPE3",
"ITSA4","ITUB4","JBSS3","KLBN11","LREN3","LWSA3","MGLU3",
"MRFG3","MRVE3","MULT3","NTCO3","PETR3","PETR4","PRIO3",
"RADL3","RAIL3","RAIZ4","RENT3","RECV3","SANB11","SBSP3",
"SLCE3","SMTO3","SUZB3","TAEE11","TIMS3","TTEN3","TOTS3",
"TRPL4","UGPA3","USIM5","VALE3","VIVT3","VIVA3","WEGE3",
"YDUQ3","AURE3","BHIA3","CASH3","CVCB3","DIRR3","ENAT3",
"GMAT3","IFCM3","INTB3","JHSF3","KEPL3","MOVI3","ORVR3",
"PETZ3","PLAS3","POMO4","POSI3","RANI3","RAPT4","STBP3",
"TEND3","TUPY3","BRSR6","CXSE3",

"AAPL34","AMZO34","GOGL34","MSFT34","TSLA34","META34",
"NFLX34","NVDC34","MELI34","BABA34","DISB34","PYPL34",
"JNJB34","PGCO34","KOCH34","VISA34","WMTB34","NIKE34",
"ADBE34","AVGO34","CSCO34","COST34","CVSH34","GECO34",
"GSGI34","HDCO34","INTC34","JPMC34","MAEL34","MCDP34",
"MDLZ34","MRCK34","ORCL34","PEP334","PFIZ34","PMIC34",
"QCOM34","SBUX34","TGTB34","TMOS34","TXN34","UNHH34",
"UPSB34","VZUA34","ABTT34","AMGN34","AXPB34","BAOO34",
"C2OL34","HONB34","BICE34","BERK34","GOGL35",

"BOVA11","IVVB11","SMAL11","HASH11","GOLD11","DIVO11",
"NDIV11","SPUB11",

"GARE11","HGLG11","XPLG11","VILG11","BRCO11","BTLG11",
"XPML11","VISC11","HSML11","MALL11","KNRI11","JSRE11",
"PVBI11","HGRE11","MXRF11","KNCR11","KNIP11","CPTS11",
"IRDM11","TGAR11","TRXF11","HGRU11","ALZR11","XPCA11",
"VGIA11","RBRR11","KNSC11","CACR11","HABT11","DEVA11",
"HGCR11","MCCI11","RECR11","VRTA11","BCFF11","HFOF11",
"XPSF11","RBRP11","RBRF11","URIT11","RZTR11","RURA11",
"VGIR11","CVBI11"

]

# =====================================================
# UTIL
# =====================================================

def ema(series, n):
    return series.ewm(span=n, adjust=False).mean()

# =====================================================
# CONFIRMAÇÃO SEMANAL (NOVO - SEM MEXER NO RESTO)
# =====================================================

def weekly_confirmation(ticker):

    try:

        df = yf.download(
            ticker + ".SA",
            period="2y",
            interval="1wk",
            auto_adjust=True,
            progress=False
        )

        if df is None or df.empty:
            return False

        close = df["Close"].dropna()

        if len(close) < 30:
            return False

        ema21 = ema(close, 21)
        ema50 = ema(close, 50)

        # tendência semanal simples (institucional)
        if close.iloc[-1] > ema21.iloc[-1] > ema50.iloc[-1]:
            return True

        return False

    except:
        return False

# =====================================================
# BACKTEST 12M (CURVA + DRAWDOWN)
# =====================================================

def backtest_12m(ticker):

    try:

        df = yf.download(
            ticker + ".SA",
            period="12mo",
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        if df is None or df.empty:
            return 0, 0

        close = df["Close"].dropna().values

        if len(close) < 200:
            return 0, 0

        capital = 10000
        peak = capital
        max_dd = 0

        equity = []

        for i in range(50, len(close)-5):

            entry = close[i]
            exit = close[i+5]

            ret = (exit / entry - 1)

            # regra simples de edge (mesma lógica do sistema)
            if entry > np.mean(close[i-20:i]):

                capital *= (1 + ret)

                if capital > peak:
                    peak = capital

                dd = (peak - capital) / peak

                if dd > max_dd:
                    max_dd = dd

            equity.append(capital)

        return capital, max_dd

    except:
        return 0, 0

# =====================================================
# ANÁLISE (NÃO ALTERADA LOGICAMENTE)
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

    if preco > ema21[-1]:
        score += 1

    if ema21[-1] > ema72[-1]:
        score += 1

    if volume[-1] > np.mean(volume[-20:]):
        score += 1

    score_norm = score / 3

    prob = 1 / (1 + np.exp(-score_norm * 2))

    calib = np.mean(signal[-50:]) if len(signal) > 50 else 0.5

    prob = prob * calib

    window = np.array(close[-21:]).flatten()
    window = window[~np.isnan(window)]

    if len(window) < 21:
        return None

    window = window[-21:]

    ret = np.diff(window) / window[:-1]

    vol = np.std(ret) * 100

    conf = 1.10 if vol < 1.2 else 1.0 if vol < 2.5 else 0.85

    prob = prob * conf

    prob = max(0, min(prob * 100, 100))

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

st.title("🏹 V4 ELITE HC - FINAL ADD-ON SYSTEM")

if st.button("ESCANEAR MERCADO"):

    resultados = []
    barra = st.progress(0)

    for i, t in enumerate(ATIVOS):

        r = analisar(t)

        # filtro 60%
        if r and r["Prob"] >= 60:

            # CONFIRMAÇÃO SEMANAL (NOVO)
            if weekly_confirmation(t):
                resultados.append(r)

        barra.progress((i+1)/len(ATIVOS))

    if len(resultados) == 0:
        st.warning("Nenhuma oportunidade confirmada semanalmente.")
        st.stop()

    df = pd.DataFrame(resultados)

    df = df.sort_values("EDGE", ascending=False)

    top8 = df.head(8)

    st.subheader("🏆 TOP 8 (FILTRADO + SEMANAL CONFIRMADO)")

    st.dataframe(top8, use_container_width=True)

    # =====================================================
    # BACKTEST PORTFÓLIO
    # =====================================================

    st.subheader("📊 BACKTEST 12 MESES + DRAWDOWN")

    bt_results = []

    for t in top8["Ativo"]:

        final_cap, dd = backtest_12m(t)

        bt_results.append({
            "Ativo": t,
            "Capital Final": round(final_cap,2),
            "Drawdown": round(dd*100,2)
        })

    st.dataframe(pd.DataFrame(bt_results), use_container_width=True)
