import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import math
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="BUY SIDE TERMINAL V4.1 FULL",
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
    st.title("🏹 BUY SIDE TERMINAL V4.1 FULL")

    senha = st.text_input("Senha:", type="password")

    if st.button("ENTRAR"):
        if senha == SENHA:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta")

    st.stop()

# =====================================================
# LISTA COMPLETA (SUA LISTA RESTAURADA)
# =====================================================

ATIVOS = [
"RRRP3","ALOS3","ALPA4","ABEV3","ARZZ3","ASAI3","AZUL4","B3SA3","BBAS3","BBDC3",
"BBDC4","BBSE3","BEEF3","BPAC11","BRAP4","BRFS3","BRKM5","CCRO3","CMIG4","CMIN3",
"COGN3","CPFE3","CPLE6","CRFB3","CSAN3","CSNA3","CYRE3","DXCO3","EGIE3","ELET3",
"ELET6","EMBR3","ENEV3","ENGI11","EQTL3","EZTC3","FLRY3","GGBR4","GOAU4","GOLL4",
"HAPV3","HYPE3","ITSA4","ITUB4","JBSS3","KLBN11","LREN3","LWSA3","MGLU3","MRFG3",
"MRVE3","MULT3","NTCO3","PETR3","PETR4","PRIO3","RADL3","RAIL3","RAIZ4","RENT3",
"RECV3","SANB11","SBSP3","SLCE3","SMTO3","SUZB3","TAEE11","TIMS3","TTEN3","TOTS3",
"TRPL4","UGPA3","USIM5","VALE3","VIVT3","VIVA3","WEGE3","YDUQ3","AURE3","BHIA3",
"CASH3","CVCB3","DIRR3","ENAT3","GMAT3","IFCM3","INTB3","JHSF3","KEPL3","MOVI3",
"ORVR3","PETZ3","PLAS3","POMO4","POSI3","RANI3","RAPT4","STBP3","TEND3","TUPY3",
"BRSR6","CXSE3","AAPL34","AMZO34","GOGL34","MSFT34","TSLA34","META34","NFLX34",
"NVDC34","MELI34","BABA34","DISB34","PYPL34","JNJB34","PGCO34","KOCH34","VISA34",
"WMTB34","NIKE34","ADBE34","AVGO34","CSCO34","COST34","CVSH34","GECO34","GSGI34",
"HDCO34","INTC34","JPMC34","MAEL34","MCDP34","MDLZ34","MRCK34","ORCL34","PEP334",
"PFIZ34","PMIC34","QCOM34","SBUX34","TGTB34","TMOS34","TXN34","UNHH34","UPSB34",
"VZUA34","ABTT34","AMGN34","AXPB34","BAOO34","CATP34","C2OL34","HONB34","BOVA11",
"IVVB11","SMAL11","HASH11","GOLD11","GARE11","HGLG11","XPLG11","VILG11","BRCO11",
"BTLG11","XPML11","VISC11","HSML11","MALL11","KNRI11","JSRE11","PVBI11","HGRE11",
"MXRF11","KNCR11","KNIP11","CPTS11","IRDM11","DIVO11","NDIV11","SPUB11"
]

# =====================================================
# DADOS
# =====================================================

@st.cache_data(ttl=600)
def get_data(t):
    df = yf.download(t + ".SA", period="300d", interval="1d", auto_adjust=True, progress=False)

    if df.empty:
        return None

    df = df.ffill().bfill()
    return df

def ema(s,n):
    return s.ewm(span=n, adjust=False).mean()

def atr(df):
    h,l,c = df["High"],df["Low"],df["Close"]
    tr = pd.concat([h-l, abs(h-c.shift(1)), abs(l-c.shift(1))], axis=1).max(axis=1)
    return tr.rolling(14).mean()

def obv(c,v):
    o = np.zeros(len(c))
    for i in range(1,len(c)):
        if c[i] > c[i-1]:
            o[i] = o[i-1] + v[i]
        elif c[i] < c[i-1]:
            o[i] = o[i-1] - v[i]
        else:
            o[i] = o[i-1]
    return o

def wilson(x,n):
    if n == 0:
        return 0
    z = 1.96
    ph = x/n
    return (ph + z*z/(2*n)) / (1 + z*z/n)

# =====================================================
# MOTOR V4.1 FULL
# =====================================================

def analisar(t):

    df = get_data(t)
    if df is None:
        return None

    close = df["Close"].values
    vol = df["Volume"].values
    price = float(close[-1])

    ema21 = ema(df["Close"],21).values
    ema72 = ema(df["Close"],72).values

    atr_v = float(atr(df).iloc[-1])

    ob = obv(close, vol)

    # =========================
    # SENTIMENTO
    # =========================

    try:
        analyzer = SentimentIntensityAnalyzer()
        news = yf.Ticker(t+".SA").news

        titles = [n["title"] for n in news[:10] if "title" in n]

        if len(titles) > 0:
            sentiment = np.mean([analyzer.polarity_scores(x)["compound"] for x in titles])
        else:
            sentiment = 0
    except:
        sentiment = 0

    # =========================
    # SCORE
    # =========================

    score = 50

    if price > ema21[-1]: score += 10
    if ema21[-1] > ema72[-1]: score += 10
    if ema21[-1] > ema21[-5]: score += 5

    ret5 = ((price/close[-6]) - 1)*100
    if ret5 > 0:
        score += min(ret5*1.5, 8)

    if vol[-1] > np.mean(vol[-20:]):
        score += 7

    if ob[-1] > ob[-5]:
        score += 5

    if sentiment > 0.1:
        score += 5

    dist = ((price/ema21[-1]) - 1)*100
    if dist > 7:
        score -= 8

    score = max(0,min(score,100))

    # =========================
    # PROBABILIDADE
    # =========================

    prob = score * 0.92
    prob = max(1,min(prob,99))

    # =========================
    # STOP / GAIN
    # =========================

    stop_pct = max(2.0, min((atr_v/price)*100*1.25, 6.5))
    gain_pct = min(stop_pct * (prob/60), 12)

    rr = gain_pct / stop_pct

    # =========================
    # EV
    # =========================

    p = prob/100
    ev = (p * gain_pct) - ((1-p) * stop_pct)

    # =========================
    # STATUS
    # =========================

    if ev > 1.5:
        status = "🟢 MUITO FAVORÁVEL"
    elif ev > 0.8:
        status = "🟢 FAVORÁVEL"
    elif ev > 0:
        status = "🟡 NEUTRO POSITIVO"
    else:
        status = "🔴 EV NEGATIVO"

    return {
        "Ativo": t,
        "Preço": round(price,2),
        "Prob %": round(prob,1),
        "Gain %": round(gain_pct,2),
        "Stop %": round(stop_pct,2),
        "RR": round(rr,2),
        "EV": round(ev,2),
        "Sentimento": round(sentiment,2),
        "Status": status
    }

# =====================================================
# SCANNER
# =====================================================

st.title("🏹 V4.1 FULL — UNIVERSO COMPLETO")

if st.button("ESCANEAR MERCADO"):

    res = []

    prog = st.progress(0)

    for i,a in enumerate(ATIVOS):

        r = analisar(a)

        if r and r["Prob %"] >= 65 and r["EV"] > -0.2:
            res.append(r)

        prog.progress((i+1)/len(ATIVOS))

    if len(res) == 0:
        st.warning("Nenhuma oportunidade encontrada.")

    else:

        df = pd.DataFrame(res)
        df = df.sort_values(["EV","Prob %"], ascending=False)

        st.success(f"{len(df)} ativos encontrados")

        st.dataframe(df, use_container_width=True)
