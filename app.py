# app.py
# BUY SIDE TERMINAL V3 ELITE
# Login + Scanner + Ichimoku + Anti-Esticado + Score Real + EDGE METRICS

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
    page_title="BUY SIDE TERMINAL V3 ELITE",
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

    st.title("🏹 BUY SIDE TERMINAL V3 ELITE")
    st.subheader("Área Restrita")

    senha_input = st.text_input("Digite a senha:", type="password")

    if st.button("🔐 ENTRAR"):
        if senha_input == SENHA:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")

    st.stop()

# =====================================================
# LISTA DE ATIVOS
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

ATIVOS = list(dict.fromkeys(ATIVOS))

# =====================================================
# FUNÇÕES
# =====================================================

@st.cache_data(ttl=900)
def baixar_dados(ticker):

    df = yf.download(
        ticker + ".SA",
        period="260d",
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

    df = df.ffill().dropna()

    return df


def ema(series, n):
    return series.ewm(span=n, adjust=False).mean()


def wilson_score(pos, total):
    if total == 0:
        return 0

    z = 1.96
    phat = pos / total
    den = 1 + z**2/total
    num = phat + z**2/(2*total) - z * math.sqrt(
        (phat*(1-phat)+z**2/(4*total))/total
    )
    return max(0, num/den)


# =====================================================
# CORE ANALYSIS
# =====================================================

def analisar_ativo(ticker):

    df = baixar_dados(ticker)

    if df is None:
        return None

    close = df["Close"].values.astype(float)
    high = df["High"].values.astype(float)
    volume = df["Volume"].values.astype(float)

    preco = float(close[-1])

    ema21 = ema(df["Close"], 21).values
    ema72 = ema(df["Close"], 72).values

    score = 0

    if preco > ema21[-1]:
        score += 12

    if ema21[-1] > ema72[-1]:
        score += 12

    slope = ema21[-1] - ema21[-5]
    if slope > 0:
        score += 10

    ret5 = ((preco / close[-6]) - 1) * 100
    ret10 = ((preco / close[-11]) - 1) * 100

    if ret5 > 0:
        score += min(ret5 * 2, 10)

    if ret10 > 0:
        score += min(ret10, 8)

    media_vol = np.mean(volume[-20:])

    if volume[-1] > media_vol:
        score += 10

    # ==========================
    # WILSON
    # ==========================

    checks = [
        preco > ema21[-1],
        ema21[-1] > ema72[-1],
        ret5 > 0,
        volume[-1] > media_vol,
        close[-1] > close[-3]
    ]

    positivos = sum(checks)
    wil = wilson_score(positivos, len(checks)) * 100

    prob = (score * 0.62) + (wil * 0.38)
    prob = max(1, min(prob, 99))

    stop = preco * 0.965

    # =====================================================
    # 🔥 EDGE METRICS (ADICIONADO SEM MEXER NO RESTO)
    # =====================================================

    atr = np.std(close[-14:])
    resistencia = np.max(high[-20:])

    gain_pot = atr * (wil / 100) * 2.2
    gain_pct = (gain_pot / preco) * 100

    stop_dist = (preco - stop) / preco * 100
    rr = gain_pct / stop_dist if stop_dist != 0 else 0

    dias = gain_pot / (atr / 14) if atr != 0 else 0

    dist_res = (resistencia - preco) / preco * 100

    gain_dist = abs(resistencia - preco)
    stop_dist_abs = abs(preco - stop)

    prob_gain_first = (
        gain_dist / (gain_dist + stop_dist_abs)
    ) * 100 if (gain_dist + stop_dist_abs) != 0 else 0

    prob_gain_first = prob_gain_first * (wil / 100)

    # =====================================================
    # STATUS
    # =====================================================

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

        "Gain Potencial %": round(gain_pct,2),
        "RR": round(rr,2),
        "Dias": round(dias,1),
        "Distância Resistência %": round(dist_res,2),
        "Prob Gain Antes Stop %": round(prob_gain_first,1),

        "Stop": round(stop,2),
        "Status": status
    }

# =====================================================
# SCANNER
# =====================================================

st.title("🏹 Scanner V3 ELITE + EDGE METRICS")

if st.button("🚀 ESCANEAR"):

    resultados = []
    barra = st.progress(0)

    for i, ativo in enumerate(ATIVOS):

        r = analisar_ativo(ativo)

        if r:

            # ✔ FILTRO ATUALIZADO
            if r["Probabilidade %"] >= 70 and r["Prob Gain Antes Stop %"] >= 60:
                resultados.append(r)

        barra.progress((i+1)/len(ATIVOS))

    if resultados:

        df = pd.DataFrame(resultados)

        df = df.sort_values("Probabilidade %", ascending=False)

        st.success(f"{len(df)} oportunidades encontradas")

        st.dataframe(df, use_container_width=True)

    else:
        st.warning("Nenhum ativo qualificado hoje.")
