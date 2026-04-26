import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="PRO DESK FIXED FINAL", layout="wide")

SENHA = "LUCRO5"

# =====================================================
# LOGIN
# =====================================================

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🏦 PRO DESK FINAL FIXED")

    senha = st.text_input("Senha:", type="password")

    if st.button("ENTRAR"):
        if senha == SENHA:
            st.session_state.logado = True
            st.rerun()

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
"RECV3","ENAT3","ORVR3","AURE3","ENEV3","UGPA3","CMIG4",

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
    return x if len(x) > 10 else None

def ema(s, n):
    s = safe(s)
    if s is None:
        return np.zeros(10)
    return pd.Series(s).ewm(span=n, adjust=False).mean().values

# =====================================================
# REGIME (QUALITATIVO)
# =====================================================

def regime(close):

    close = safe(close)
    if close is None:
        return "NEUTRO"

    ret = np.diff(close[-20:]) / close[-20:-1]

    vol = np.std(ret)
    trend = np.mean(ret)

    if vol > 0.02:
        return "VOLATIL"
    if trend > 0.001:
        return "TENDENCIA"
    return "LATERAL"

# =====================================================
# SETUP SCORE
# =====================================================

def setup_score(preco, ema21, ema72, close):

    score = 0

    if preco > ema21:
        score += 35
    if ema21 > ema72:
        score += 35

    ret5 = (preco / close[-6]) - 1
    if ret5 > 0:
        score += min(ret5 * 80, 20)

    dist = (preco / ema21) - 1
    if dist > 0.08:
        score -= 20
    elif dist > 0.05:
        score -= 10

    return max(0, min(score, 100))

# =====================================================
# PROBABILIDADE (CALIBRADA)
# =====================================================

def probabilidade(setup):

    return (1 / (1 + np.exp(-0.08 * (setup - 50)))) * 100

# =====================================================
# EDGE (CORRIGIDO)
# =====================================================

def edge(setup, prob):

    return (setup * prob) / 120

# =====================================================
# SETUP LABEL
# =====================================================

def setup_label(s):

    if s < 40:
        return "FRACO"
    elif s < 60:
        return "NEUTRO"
    elif s < 80:
        return "FORTE"
    return "INSTITUCIONAL"

# =====================================================
# TARGET FIXO
# =====================================================

def targets(preco):
    return round(preco * 1.06, 2), round(preco * 0.96, 2)

# =====================================================
# ANALISAR
# =====================================================

def analisar(t):

    df = yf.download(t + ".SA",
                     period="300d",
                     interval="1d",
                     auto_adjust=True,
                     progress=False)

    if df is None or df.empty:
        return None

    close = safe(df["Close"])
    if close is None:
        return None

    preco = close[-1]

    ema21 = ema(close, 21)
    ema72 = ema(close, 72)

    setup = setup_score(preco, ema21[-1], ema72[-1], close)

    prob = probabilidade(setup)

    ed = edge(setup, prob)

    gain, stop = targets(preco)

    return {
        "Ativo": t,
        "Preço": round(preco,2),
        "Setup": setup_label(setup),
        "Prob": round(prob,2),
        "Edge": round(ed,2),
        "Gain": gain,
        "Stop": stop
    }

# =====================================================
# SCANNER
# =====================================================

st.title("🏦 PRO DESK FINAL ESTÁVEL")

if st.button("ESCANEAR"):

    res = []

    for t in ATIVOS:
        r = analisar(t)
        if r:
            res.append(r)

    df = pd.DataFrame(res)

    df = df.sort_values("Edge", ascending=False)

    df.index = range(1, len(df) + 1)
    df.insert(0, "Rank", df.index)

    st.dataframe(df)
