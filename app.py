# =====================================================
# V4 ELITE PRO - FINAL DECISION ENGINE
# =====================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="V4 ELITE PRO", layout="wide")

SENHA = "LUCRO5"

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🏹 V4 ELITE PRO FINAL")

    senha = st.text_input("Senha:", type="password")

    if st.button("ENTRAR"):
        if senha == SENHA:
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
# SAFE
# =====================================================

def safe(x):
    x = np.array(x, dtype=float).reshape(-1)
    x = x[~np.isnan(x)]
    return x if len(x) > 5 else None

def ema(s, n):
    s = safe(s)
    if s is None:
        return np.zeros(10)
    return pd.Series(s).ewm(span=n).mean().values

# =====================================================
# SETUP DETECTOR
# =====================================================

def setup(close, ema21, ema72):

    if close[-1] > ema21[-1] > ema72[-1]:
        return "TREND"

    if close[-1] < ema21[-1] and close[-1] > close[-5]:
        return "REVERSÃO"

    return "MOMENTUM"

# =====================================================
# ANALISE
# =====================================================

def analisar(t):

    df = yf.download(t+".SA", period="300d", interval="1d",
                     auto_adjust=True, progress=False)

    if df is None or df.empty:
        return None

    close = safe(df["Close"])
    volume = safe(df["Volume"])

    if close is None:
        return None

    preco = close[-1]

    ema21 = ema(close, 21)
    ema72 = ema(close, 72)

    setup_type = setup(close, ema21, ema72)

    trend = preco > ema21[-1] > ema72[-1]
    mom = preco / close[-5] - 1

    score = 0
    if trend: score += 1
    score += mom * 5

    vol = np.std(np.diff(close)/close[:-1])

    # =================================================
    # PROBABILIDADE
    # =================================================

    z = score
    prob = 1 / (1 + np.exp(-z * 2)) * 100

    # =================================================
    # GAIN / LOSS (RESTAURADO)
    # =================================================

    gain = vol * 2.8
    stop = vol * 1.6

    # =================================================
    # EDGE
    # =================================================

    edge = (prob/100 * gain) - ((1 - prob/100) * stop)

    return {
        "Ativo": t,
        "Preço": preco,
        "Prob": prob,
        "Edge": edge,
        "Gain": gain,
        "Stop": stop,
        "Setup": setup_type
    }

# =====================================================
# SCANNER
# =====================================================

st.title("🏹 V4 ELITE PRO - DECISION TABLE")

if st.button("ESCANEAR"):

    data = []

    for t in ATIVOS:
        r = analisar(t)
        if r:
            data.append(r)

    df = pd.DataFrame(data)

    # =================================================
    # RANKING REAL
    # =================================================

    df["rank_score"] = 0.6 * df["Edge"] + 0.4 * df["Prob"]

    df = df.sort_values("rank_score", ascending=False).reset_index(drop=True)

    df.index = df.index + 1   # 🔥 ranking 1,2,3...

    df.insert(0, "Rank", df.index)

    st.subheader("🏆 TOP SETUPS")

    st.dataframe(
        df[["Rank","Ativo","Setup","Preço","Prob","Edge","Gain","Stop"]],
        use_container_width=True
    )
