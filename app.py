# =====================================================
# BUY SIDE TERMINAL V5 ELITE FINAL
# Scanner + Busca Individual + Gráfico + Ranking
# Código completo pronto para colar
# =====================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="BUY SIDE TERMINAL V5 ELITE FINAL",
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
    border-radius:10px;
    height:44px;
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

    st.title("🏹 BUY SIDE TERMINAL V5 ELITE FINAL")
    st.subheader("Área Restrita")

    senha = st.text_input("Digite a senha:", type="password")

    if st.button("🔐 ENTRAR"):
        if senha == SENHA:
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

def safe(x):
    x = np.array(x, dtype=float).reshape(-1)
    x = x[~np.isnan(x)]
    return x if len(x) > 30 else None

@st.cache_data(ttl=900)
def baixar_dados(ticker):

    try:
        df = yf.download(
            ticker + ".SA",
            period="320d",
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

def ema(series, n):
    return pd.Series(series).ewm(span=n, adjust=False).mean().values

def setup_score(preco, e21, e72, close):

    score = 0

    if preco > e21:
        score += 35

    if e21 > e72:
        score += 35

    ret5 = (preco / close[-6]) - 1

    if ret5 > 0:
        score += min(ret5 * 80, 20)

    dist = (preco / e21) - 1

    if dist > 0.08:
        score -= 20
    elif dist > 0.05:
        score -= 10

    return max(0, min(score, 100))

def probabilidade(score):
    return (1 / (1 + np.exp(-0.08 * (score - 50)))) * 100

def setup_label(score):

    if score < 40:
        return "🔴 FRACO"
    elif score < 60:
        return "🟡 NEUTRO"
    elif score < 80:
        return "🟢 FORTE"
    else:
        return "🏆 ELITE"

def gain_stop(preco):
    gain = preco * 1.06
    stop = preco * 0.96
    return round(gain,2), round(stop,2)

def analisar_ativo(ticker):

    df = baixar_dados(ticker)

    if df is None:
        return None

    close = safe(df["Close"])

    if close is None:
        return None

    preco = close[-1]

    e21 = ema(close, 21)
    e72 = ema(close, 72)

    score = setup_score(preco, e21[-1], e72[-1], close)

    prob = probabilidade(score)

    gain, stop = gain_stop(preco)

    return {
        "Ativo": ticker,
        "Preço": round(preco,2),
        "SetupScore": score,
        "Setup": setup_label(score),
        "Prob": round(prob,2),
        "Gain": gain,
        "Stop": stop,
        "df": df,
        "EMA21": e21,
        "EMA72": e72
    }

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.title("🏹 MENU")

    modo = st.radio(
        "Escolha:",
        ["Scanner Mercado", "Ativo Específico"]
    )

# =====================================================
# SCANNER MERCADO
# =====================================================

if modo == "Scanner Mercado":

    st.title("🏹 Scanner Mercado V5 Elite")

    if st.button("🚀 ESCANEAR MERCADO"):

        resultados = []

        barra = st.progress(0)

        total = len(ATIVOS)

        for i, ativo in enumerate(ATIVOS):

            r = analisar_ativo(ativo)

            if r:
                resultados.append(r)

            barra.progress((i+1)/total)

        if len(resultados) == 0:
            st.warning("Nenhum resultado encontrado.")

        else:

            tabela = pd.DataFrame(resultados)

            # EDGE PERCENTIL
            tabela["Edge"] = tabela["SetupScore"].rank(pct=True) * 100

            # SCORE FINAL
            tabela["ScoreFinal"] = (
                tabela["Edge"] * 0.7 +
                tabela["Prob"] * 0.3
            )

            tabela = tabela.sort_values(
                "ScoreFinal",
                ascending=False
            ).reset_index(drop=True)

            tabela.index += 1
            tabela.insert(0, "Rank", tabela.index)

            st.success(f"{len(tabela)} ativos analisados.")

            st.dataframe(
                tabela[
                    [
                        "Rank",
                        "Ativo",
                        "Setup",
                        "Preço",
                        "Prob",
                        "Edge",
                        "ScoreFinal",
                        "Gain",
                        "Stop"
                    ]
                ],
                use_container_width=True
            )

# =====================================================
# ATIVO ESPECÍFICO
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
            c2.metric("Probabilidade", f"{r['Prob']}%")
            c3.metric("Gain", f"R$ {r['Gain']}")
            c4.metric("Stop", f"R$ {r['Stop']}")

            st.subheader(r["Setup"])

            # semáforo
            if r["Prob"] >= 75:
                st.success("🟢 Comprar / Forte")
            elif r["Prob"] >= 60:
                st.warning("🟡 Observar")
            else:
                st.error("🔴 Evitar")

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
    f"BUY SIDE TERMINAL V5 ELITE FINAL | {time.strftime('%d/%m/%Y %H:%M:%S')}"
)
