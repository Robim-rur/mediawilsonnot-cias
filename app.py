# app.py
# BUY SIDE TERMINAL V3 ELITE
# Login + Scanner + Ichimoku + Anti-Esticado + Score Real
# Arquivo completo pronto para colar

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

    try:
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

        for c in cols:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        df = df.ffill().dropna()

        if len(df) < 120:
            return None

        return df

    except:
        return None


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


def ichimoku(df):

    high9 = df["High"].rolling(9).max()
    low9 = df["Low"].rolling(9).min()
    tenkan = (high9 + low9) / 2

    high26 = df["High"].rolling(26).max()
    low26 = df["Low"].rolling(26).min()
    kijun = (high26 + low26) / 2

    span_a = ((tenkan + kijun) / 2).shift(26)

    high52 = df["High"].rolling(52).max()
    low52 = df["Low"].rolling(52).min()
    span_b = ((high52 + low52) / 2).shift(26)

    return tenkan, kijun, span_a, span_b


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

    tenkan, kijun, span_a, span_b = ichimoku(df)

    score = 0

    # ==================================
    # TENDÊNCIA
    # ==================================

    if preco > ema21[-1]:
        score += 12

    if ema21[-1] > ema72[-1]:
        score += 12

    slope = ema21[-1] - ema21[-5]
    if slope > 0:
        score += 10

    # ==================================
    # MOMENTUM
    # ==================================

    ret5 = ((preco / close[-6]) - 1) * 100
    ret10 = ((preco / close[-11]) - 1) * 100

    if ret5 > 0:
        score += min(ret5 * 2, 10)

    if ret10 > 0:
        score += min(ret10, 8)

    # ==================================
    # ANTI ESTICADO
    # ==================================

    dist_ema = ((preco / ema21[-1]) - 1) * 100

    if dist_ema > 8:
        score -= 18
    elif dist_ema > 6:
        score -= 10
    elif dist_ema > 4:
        score -= 5

    # ==================================
    # VOLUME / FLUXO
    # ==================================

    media_vol = np.mean(volume[-20:])

    if volume[-1] > media_vol:
        score += 10

    if obv[-1] > np.mean(obv[-10:]):
        score += 10

    # ==================================
    # ICHIMOKU
    # ==================================

    sa = float(span_a.iloc[-1]) if pd.notna(span_a.iloc[-1]) else np.nan
    sb = float(span_b.iloc[-1]) if pd.notna(span_b.iloc[-1]) else np.nan
    tk = float(tenkan.iloc[-1]) if pd.notna(tenkan.iloc[-1]) else np.nan
    kj = float(kijun.iloc[-1]) if pd.notna(kijun.iloc[-1]) else np.nan

    if not np.isnan(sa) and not np.isnan(sb):

        topo = max(sa, sb)
        base = min(sa, sb)

        if preco > topo:
            score += 14

        if tk > kj:
            score += 8

        if sa > sb:
            score += 8

        # se muito longe da nuvem = esticado
        dist_nuvem = ((preco / topo) - 1) * 100

        if dist_nuvem > 8:
            score -= 10

    # ==================================
    # VOLATILIDADE
    # ==================================

    vol = pd.Series(close).pct_change().dropna().tail(20).std() * 100

    if vol > 4:
        score -= min((vol - 4) * 2, 10)

    # ==================================
    # WILSON
    # ==================================

    checks = [
        preco > ema21[-1],
        ema21[-1] > ema72[-1],
        ret5 > 0,
        volume[-1] > media_vol,
        obv[-1] > obv[-5],
        tk > kj if not np.isnan(tk) else False,
        preco > sa if not np.isnan(sa) else False
    ]

    positivos = sum(checks)

    wil = wilson_score(positivos, len(checks)) * 100

    prob = (score * 0.62) + (wil * 0.38)
    prob = max(1, min(prob, 99))

    stop = preco * 0.965
    gain = preco * 1.05

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

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.title("🏹 MENU")

    modo = st.radio(
        "Escolha:",
        ["Scanner Inteligente", "Ativo Específico"]
    )

# =====================================================
# SCANNER
# =====================================================

if modo == "Scanner Inteligente":

    st.title("🏹 Scanner Inteligente V3 ELITE")

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
            st.warning("Nenhum ativo acima de 70% hoje.")

        else:

            tabela = pd.DataFrame(resultados)

            tabela = tabela[
                ["Ativo","Preço","Probabilidade %","Stop","Gain","Status"]
            ]

            tabela = tabela.sort_values(
                by="Probabilidade %",
                ascending=False
            )

            st.success(f"{len(tabela)} oportunidades encontradas.")

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

# =====================================================
# RODAPÉ
# =====================================================

st.markdown("---")
st.caption(
    f"BUY SIDE TERMINAL V3 ELITE | {time.strftime('%d/%m/%Y %H:%M:%S')}"
)
