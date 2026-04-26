# app.py
# BUY SIDE TERMINAL MASTER V2
# Login + Scanner 178 Ativos + Ativo Específico
# Probabilidade Real Corrigida

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import math
import time

# ==========================================================
# CONFIG
# ==========================================================

st.set_page_config(
    page_title="Buy Side Terminal MASTER V2",
    page_icon="🏹",
    layout="wide"
)

SENHA_CORRETA = "LUCRO5"

# ==========================================================
# ESTILO
# ==========================================================

st.markdown("""
<style>
.main {background:#0e1117;}
.stTextInput input {
    background:#161b22 !important;
    color:white !important;
}
.stButton button {
    width:100%;
    height:45px;
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

# ==========================================================
# LOGIN
# ==========================================================

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    st.title("🏹 Buy Side Terminal MASTER")
    st.subheader("Área Restrita")

    senha = st.text_input("Digite sua senha:", type="password")

    if st.button("🔐 ENTRAR"):
        if senha == SENHA_CORRETA:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")

    st.stop()

# ==========================================================
# LISTA DE ATIVOS
# ==========================================================

ATIVOS = [
"PETR4","VALE3","BBAS3","ITUB4","BBDC4","WEGE3","PRIO3","RENT3",
"ELET3","ELET6","CPLE6","CMIG4","TAEE11","EGIE3","VIVT3","TIMS3",
"ABEV3","RADL3","SUZB3","GGBR4","GOAU4","USIM5","CSNA3","RAIL3",
"SBSP3","EQTL3","HYPE3","MULT3","LREN3","ARZZ3","TOTS3","EMBR3",
"JBSS3","BEEF3","MRFG3","BRFS3","SLCE3","SMTO3","B3SA3","BBSE3",
"BPAC11","SANB11","ITSA4","BRSR6","CXSE3","POMO4","STBP3","TUPY3",
"LEVE3","DIRR3","CYRE3","EZTC3","JHSF3","KEPL3","POSI3","MOVI3",
"PETZ3","COGN3","YDUQ3","MGLU3","NTCO3","AZUL4","GOLL4","CVCB3",
"RRRP3","RECV3","ENAT3","ORVR3","AURE3","GMAT3","ENEV3","UGPA3",

"BOVA11","SMAL11","IVVB11","HASH11","GOLD11","DIVO11","NDIV11",

"HGLG11","XPLG11","VISC11","MXRF11","KNRI11","KNCR11","KNIP11",
"CPTS11","IRDM11","TRXF11","TGAR11","HGRU11","RBRR11","ALZR11",

"AAPL34","AMZO34","GOGL34","MSFT34","TSLA34","META34","NFLX34",
"NVDC34","MELI34","BABA34","DISB34","PYPL34","JNJB34","VISA34",
"WMTB34","NIKE34","ADBE34","CSCO34","INTC34","JPMC34","ORCL34",
"QCOM34","SBUX34","TXN34","ABTT34","AMGN34","AXPB34","BERK34",

"C2OL34"
]

ATIVOS = list(dict.fromkeys(ATIVOS))

# ==========================================================
# FUNÇÕES
# ==========================================================

@st.cache_data(ttl=900)
def baixar_dados(ticker):
    try:
        df = yf.download(
            ticker + ".SA",
            period="180d",
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        if df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        cols = ["Open","High","Low","Close","Volume"]
        df = df[cols].copy()

        for c in cols:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        df = df.ffill().dropna()

        if len(df) < 80:
            return None

        return df

    except:
        return None


def ema(series, p):
    return series.ewm(span=p, adjust=False).mean()


def wilson_score(pos, total):
    if total == 0:
        return 0

    z = 1.96
    phat = pos / total

    den = 1 + z**2 / total
    num = phat + z**2/(2*total) - z * math.sqrt(
        (phat*(1-phat) + z**2/(4*total))/total
    )

    return max(0, num / den)


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


def analisar_ativo(ticker):

    df = baixar_dados(ticker)

    if df is None:
        return None

    close = df["Close"].values.astype(float)
    volume = df["Volume"].values.astype(float)

    preco = float(close[-1])

    ema21 = ema(df["Close"], 21).values
    ema72 = ema(df["Close"], 72).values

    obv = calc_obv(close, volume)

    # ===============================
    # SCORE REAL
    # ===============================

    score = 0

    # Tendência
    dist21 = ((preco / ema21[-1]) - 1) * 100
    dist72 = ((preco / ema72[-1]) - 1) * 100

    score += max(0, min(dist21 * 4, 18))
    score += max(0, min(dist72 * 2, 12))

    # Momentum
    ret5 = ((preco / close[-6]) - 1) * 100
    ret10 = ((preco / close[-11]) - 1) * 100

    score += max(0, min(ret5 * 3, 15))
    score += max(0, min(ret10 * 1.5, 10))

    # OBV
    media_obv = np.mean(obv[-10:])
    if obv[-1] > media_obv:
        score += 12

    # Volume
    vol_media = np.mean(volume[-20:])
    if volume[-1] > vol_media:
        score += 10

    # Volatilidade
    retornos = pd.Series(close).pct_change().dropna()
    vol = retornos[-20:].std() * 100

    if vol > 4:
        score -= min((vol - 4) * 2, 10)

    # ===============================
    # WILSON
    # ===============================

    c1 = preco > ema21[-1]
    c2 = ema21[-1] > ema72[-1]
    c3 = ret5 > 0
    c4 = ret10 > 0
    c5 = obv[-1] > obv[-5]
    c6 = volume[-1] > vol_media

    positivos = sum([c1,c2,c3,c4,c5,c6])

    wil = wilson_score(positivos, 6) * 100

    # Final
    prob = (score * 0.62) + (wil * 0.38)
    prob = max(1, min(prob, 99))

    # Stops
    stop = preco * 0.965
    gain = preco * 1.05

    # Status
    if prob >= 85:
        status = "🟢 PREMIUM"
    elif prob >= 78:
        status = "🟢 FORTE"
    elif prob >= 72:
        status = "🟡 BOA"
    elif prob >= 70:
        status = "🟠 OPERÁVEL"
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

# ==========================================================
# MENU
# ==========================================================

with st.sidebar:

    st.title("🏹 MENU")

    modo = st.radio(
        "Escolha:",
        ["Scanner Inteligente", "Ativo Específico"]
    )

# ==========================================================
# SCANNER
# ==========================================================

if modo == "Scanner Inteligente":

    st.title("🏹 Scanner Inteligente")

    if st.button("🚀 ESCANEAR MERCADO"):

        resultados = []
        barra = st.progress(0)

        total = len(ATIVOS)

        for i, ativo in enumerate(ATIVOS):

            r = analisar_ativo(ativo)

            if r:
                if r["Probabilidade %"] >= 70:
                    resultados.append(r)

            barra.progress((i+1)/total)

        if len(resultados) == 0:
            st.warning("Nenhuma oportunidade encontrada.")

        else:

            tabela = pd.DataFrame(resultados)

            tabela = tabela[
                ["Ativo","Preço","Probabilidade %","Stop","Gain","Status"]
            ]

            tabela = tabela.sort_values(
                by="Probabilidade %",
                ascending=False
            )

            st.success(f"{len(tabela)} ativos aprovados.")

            st.dataframe(
                tabela,
                use_container_width=True,
                hide_index=True
            )

# ==========================================================
# INDIVIDUAL
# ==========================================================

else:

    st.title("🏹 Ativo Específico")

    ticker = st.text_input(
        "Digite o ticker:",
        "PETR4"
    ).upper().replace(".SA","")

    if st.button("🔎 ANALISAR"):

        r = analisar_ativo(ticker)

        if r is None:
            st.error("Ativo inválido ou sem dados.")
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

# ==========================================================
# RODAPÉ
# ==========================================================

st.markdown("---")
st.caption(
    f"Buy Side MASTER V2 | {time.strftime('%d/%m/%Y %H:%M:%S')}"
)
