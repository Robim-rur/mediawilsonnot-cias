# app.py
# Buy Side Terminal MASTER
# Login + Scanner Inteligente + Ativo Específico

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import math
import time
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="Buy Side Terminal MASTER",
    page_icon="🏹",
    layout="wide"
)

SENHA_CORRETA = "LUCRO5"

# =====================================================
# ESTILO
# =====================================================

st.markdown("""
<style>
.main {
    background-color:#0e1117;
}
.stTextInput > div > div > input {
    background:#161b22;
    color:white;
}
.stButton > button {
    width:100%;
    border-radius:8px;
    height:45px;
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

    st.title("🏹 Buy Side Terminal MASTER")
    st.subheader("Área Restrita")

    senha = st.text_input(
        "Digite sua senha:",
        type="password"
    )

    if st.button("🔐 ENTRAR"):

        if senha == SENHA_CORRETA:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha inválida.")

    st.stop()

# =====================================================
# LISTA DE ATIVOS
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

ATIVOS = list(dict.fromkeys(ATIVOS))

# =====================================================
# FUNÇÕES
# =====================================================

def wilson_score(pos, total):
    if total == 0:
        return 0
    z = 1.96
    phat = pos / total
    den = 1 + z**2 / total
    num = phat + z**2/(2*total) - z * math.sqrt(
        (phat*(1-phat)+z**2/(4*total))/total
    )
    return max(0, num / den)

@st.cache_data(ttl=600)
def baixar_dados(ticker):

    try:
        df = yf.download(
            ticker + ".SA",
            period="180d",
            interval="1d",
            progress=False,
            auto_adjust=True
        )

        if df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        cols = ['Open','High','Low','Close','Volume']
        df = df[cols]

        for c in cols:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        df = df.ffill().dropna()

        if len(df) < 80:
            return None

        return df

    except:
        return None

def ema(series, n):
    return series.ewm(span=n, adjust=False).mean()

def calc_obv(close, volume):
    obv = np.zeros(len(close))
    for i in range(1, len(close)):
        if close[i] > close[i-1]:
            obv[i] = obv[i-1] + volume[i]
        elif close[i] < close[i-1]:
            obv[i] = obv[i-1] - volume[i]
        else:
            obv[i] = obv[i-1]
    return obv

def sentimento_score(ticker):
    try:
        obj = yf.Ticker(ticker + ".SA")
        noticias = getattr(obj, "news", [])

        analyzer = SentimentIntensityAnalyzer()

        titulos = []
        for n in noticias[:8]:
            t = n.get("title")
            if t:
                titulos.append(t)

        if len(titulos) == 0:
            return 0

        vals = []
        for t in titulos:
            vals.append(
                analyzer.polarity_scores(t)["compound"]
            )

        return float(np.mean(vals))

    except:
        return 0

def analisar_ativo(ticker):

    df = baixar_dados(ticker)

    if df is None:
        return None

    close = df["Close"].values
    volume = df["Volume"].values
    preco = float(close[-1])

    ema21 = ema(df["Close"], 21).values
    ema72 = ema(df["Close"], 72).values

    obv = calc_obv(close, volume)

    sent = sentimento_score(ticker)

    score = 0

    c1 = preco > ema21[-1] > ema72[-1]
    if c1:
        score += 35

    c2 = obv[-1] > np.mean(obv[-10:])
    if c2:
        score += 25

    c3 = close[-1] > close[-3]
    if c3:
        score += 20

    c4 = sent > 0
    if c4:
        score += 10

    c5 = close[-1] > close[-5]
    if c5:
        score += 10

    positivos = sum([c1,c2,c3,c4,c5])

    wil = wilson_score(positivos, 5) * 100

    prob = (score * 0.65) + (wil * 0.35)

    stop = preco * (1 - 0.035)
    gain = preco * (1 + 0.05)

    if prob >= 85:
        status = "🟢 PREMIUM"
    elif prob >= 75:
        status = "🟢 COMPRA"
    elif prob >= 70:
        status = "🟡 BOA"
    else:
        status = "🔴 FORA"

    return {
        "Ativo": ticker,
        "Preço": round(preco,2),
        "Probabilidade %": round(prob,1),
        "Stop": round(stop,2),
        "Gain": round(gain,2),
        "Status": status,
        "df": df,
        "ema21": ema21,
        "ema72": ema72
    }

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.title("🏹 Menu")

    modo = st.radio(
        "Escolha:",
        ["Scanner Inteligente", "Ativo Específico"]
    )

# =====================================================
# SCANNER
# =====================================================

if modo == "Scanner Inteligente":

    st.title("🏹 Scanner 178+ Ativos")

    if st.button("🚀 ESCANEAR MERCADO"):

        resultados = []

        barra = st.progress(0)

        for i, ativo in enumerate(ATIVOS):

            r = analisar_ativo(ativo)

            if r:
                if r["Probabilidade %"] >= 70:
                    resultados.append(r)

            barra.progress((i+1)/len(ATIVOS))

        if len(resultados) == 0:
            st.warning("Nenhuma oportunidade encontrada.")

        else:

            tabela = pd.DataFrame(resultados)

            tabela = tabela[
                ["Ativo","Preço","Probabilidade %","Stop","Gain","Status"]
            ].sort_values(
                by="Probabilidade %",
                ascending=False
            )

            st.success(
                f"{len(tabela)} oportunidades aprovadas."
            )

            st.dataframe(
                tabela,
                use_container_width=True,
                hide_index=True
            )

# =====================================================
# INDIVIDUAL
# =====================================================

else:

    st.title("🏹 Análise Individual")

    ativo = st.text_input(
        "Digite qualquer ticker:",
        "PETR4"
    ).upper().replace(".SA","")

    if st.button("🔎 ANALISAR"):

        r = analisar_ativo(ativo)

        if r is None:
            st.error("Ativo inválido.")

        else:

            c1,c2,c3,c4 = st.columns(4)

            c1.metric("Preço", f"R$ {r['Preço']}")
            c2.metric("Probabilidade", f"{r['Probabilidade %']}%")
            c3.metric("Stop", f"R$ {r['Stop']}")
            c4.metric("Gain", f"R$ {r['Gain']}")

            st.subheader(r["Status"])

            graf = pd.DataFrame({
                "Preço": r["df"]["Close"],
                "EMA21": r["ema21"],
                "EMA72": r["ema72"]
            }, index=r["df"].index)

            st.line_chart(graf)

# =====================================================
# RODAPÉ
# =====================================================

st.markdown("---")
st.caption(
    f"Buy Side MASTER | {time.strftime('%d/%m/%Y %H:%M:%S')}"
)
