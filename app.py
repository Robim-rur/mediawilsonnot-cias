# =====================================================
# BUY SIDE TERMINAL V6 TURBO
# EDGE INSTITUCIONAL V2
# Código completo pronto para colar
# =====================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="BUY SIDE TERMINAL V6 EDGE V2",
    page_icon="🏹",
    layout="wide"
)

SENHA = "LUCRO5"

# =====================================================
# VISUAL
# =====================================================

st.markdown("""
<style>
.main {background:#0e1117;}
.stTextInput input{
    background:#161b22 !important;
    color:white !important;
}
.stButton button{
    width:100%;
    height:44px;
    border-radius:10px;
}
.stMetric{
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

    st.title("🏹 BUY SIDE TERMINAL V6")
    senha = st.text_input("Senha:", type="password")

    if st.button("🔐 Entrar"):
        if senha.strip().upper() == SENHA:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")

    st.stop()

# =====================================================
# UNIVERSO
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
"RECV3","ENAT3","ORVR3","AURE3","ENEV3","UGPA3","CMIG4",

"BOVA11","IVVB11","SMAL11","HASH11","GOLD11","DIVO11","NDIV11",

"HGLG11","XPLG11","VISC11","MXRF11","KNRI11","KNCR11","KNIP11",
"CPTS11","IRDM11","TRXF11","TGAR11","HGRU11","ALZR11","IEEX11",
"UTLL11",

"AAPL34","AMZO34","GOGL34","MSFT34","TSLA34","META34","NFLX34",
"NVDC34","MELI34","BABA34","DISB34","PYPL34","JNJB34","VISA34",
"WMTB34","NIKE34","ADBE34","CSCO34","INTC34","JPMC34","ORCL34",
"QCOM34","SBUX34","TXN34","ABTT34","AMGN34","AXPB34","BERK34",

"C2OL34"
]

# =====================================================
# FUNÇÕES BASE
# =====================================================

def arr1d(x):
    x = np.array(x, dtype=float).reshape(-1)
    x = x[~np.isnan(x)]
    return x

@st.cache_data(ttl=1800)
def baixar_dados(ticker):

    try:
        df = yf.download(
            ticker + ".SA",
            period="420d",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False
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

        if len(df) < 120:
            return None

        return df

    except:
        return None

def ema(s, n):
    return pd.Series(s).ewm(span=n, adjust=False).mean().values

def prob_logistica(score):
    return 100 / (1 + np.exp(-(score - 50)/9))

# =====================================================
# EDGE INSTITUCIONAL V2
# =====================================================

def analisar(ticker):

    df = baixar_dados(ticker)

    if df is None:
        return None

    close = arr1d(df["Close"].values)

    if len(close) < 120:
        return None

    preco = close[-1]

    e21 = ema(close,21)
    e72 = ema(close,72)

    # ---------------------------------
    # tendência
    # ---------------------------------

    trend = 0

    if preco > e21[-1]:
        trend += 1

    if e21[-1] > e72[-1]:
        trend += 1

    slope = e21[-1] - e21[-6]

    if slope > 0:
        trend += 1

    trend_score = trend / 3 * 100

    # ---------------------------------
    # momentum
    # ---------------------------------

    r5 = ((preco / close[-6]) - 1) * 100
    r20 = ((preco / close[-21]) - 1) * 100

    mom = max(0, min((r5 * 6 + r20 * 2), 100))

    # ---------------------------------
    # volatilidade ajustada
    # ---------------------------------

    ret = np.diff(close[-31:]) / close[-31:-1]
    vol = np.std(ret) * 100

    vol_score = max(0, 100 - vol * 8)

    # ---------------------------------
    # drawdown
    # ---------------------------------

    topo60 = np.max(close[-60:])
    dd = ((preco / topo60) - 1) * 100

    dd_score = max(0, 100 + dd * 4)

    # ---------------------------------
    # distensão (anti esticado)
    # ---------------------------------

    dist = ((preco / e21[-1]) - 1) * 100

    stretch = max(0, 100 - abs(dist) * 10)

    # ---------------------------------
    # EDGE INSTITUCIONAL
    # ---------------------------------

    edge = (
        trend_score * 0.30 +
        mom * 0.25 +
        vol_score * 0.15 +
        dd_score * 0.15 +
        stretch * 0.15
    )

    edge = max(1, min(edge, 100))

    # ---------------------------------
    # PROBABILIDADE REALISTA
    # ---------------------------------

    prob = prob_logistica(edge)

    # ---------------------------------
    # setup texto
    # ---------------------------------

    if edge >= 82:
        setup = "🏆 ELITE"
    elif edge >= 68:
        setup = "🟢 FORTE"
    elif edge >= 55:
        setup = "🟡 MÉDIO"
    else:
        setup = "🔴 FRACO"

    # ---------------------------------
    # gain stop fixo
    # ---------------------------------

    gain = preco * 1.06
    stop = preco * 0.96

    score_final = edge * 0.60 + prob * 0.40

    return {
        "Ativo": ticker,
        "Preço": round(preco,2),
        "Setup": setup,
        "Probabilidade": round(prob,2),
        "Edge": round(edge,2),
        "ScoreFinal": round(score_final,2),
        "Gain": round(gain,2),
        "Stop": round(stop,2),
        "df": df,
        "EMA21": e21,
        "EMA72": e72
    }

# =====================================================
# MENU
# =====================================================

with st.sidebar:

    st.title("🏹 MENU")

    modo = st.radio(
        "Escolha:",
        ["Scanner Mercado","Ativo Específico"]
    )

# =====================================================
# SCANNER
# =====================================================

if modo == "Scanner Mercado":

    st.title("🏹 EDGE INSTITUCIONAL V2")

    if st.button("🚀 ESCANEAR"):

        barra = st.progress(0)
        resultados = []

        total = len(ATIVOS)

        with ThreadPoolExecutor(max_workers=8) as executor:

            futures = {
                executor.submit(analisar, t): t
                for t in ATIVOS
            }

            feitos = 0

            for future in as_completed(futures):

                r = future.result()

                if r:
                    resultados.append(r)

                feitos += 1
                barra.progress(feitos/total)

        if len(resultados) == 0:
            st.warning("Sem resultados.")
        else:

            tabela = pd.DataFrame(resultados)

            tabela = tabela.sort_values(
                "ScoreFinal",
                ascending=False
            ).reset_index(drop=True)

            tabela.index += 1
            tabela.insert(0,"Rank",tabela.index)

            st.success(f"{len(tabela)} ativos analisados.")

            st.dataframe(
                tabela[
                    [
                        "Rank","Ativo","Setup","Preço",
                        "Probabilidade","Edge",
                        "ScoreFinal","Gain","Stop"
                    ]
                ],
                use_container_width=True
            )

# =====================================================
# INDIVIDUAL
# =====================================================

else:

    st.title("🏹 Análise Individual")

    ticker = st.text_input(
        "Ticker:",
        "PETR4"
    ).upper().replace(".SA","")

    if st.button("🔎 ANALISAR"):

        r = analisar(ticker)

        if r is None:
            st.error("Ativo inválido.")
        else:

            c1,c2,c3,c4 = st.columns(4)

            c1.metric("Preço", f"R$ {r['Preço']}")
            c2.metric("Prob", f"{r['Probabilidade']}%")
            c3.metric("Gain", f"R$ {r['Gain']}")
            c4.metric("Stop", f"R$ {r['Stop']}")

            st.subheader(r["Setup"])

            graf = pd.DataFrame({
                "Preço": r["df"]["Close"],
                "EMA21": r["EMA21"],
                "EMA72": r["EMA72"]
            }, index=r["df"].index)

            st.line_chart(graf, use_container_width=True)

# =====================================================
# RODAPÉ
# =====================================================

st.markdown("---")
st.caption(
    f"BUY SIDE TERMINAL V6 EDGE V2 | {time.strftime('%d/%m/%Y %H:%M:%S')}"
)
