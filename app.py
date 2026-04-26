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
    page_title="BUY SIDE TERMINAL V3.2 ELITE",
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
    st.title("🏹 BUY SIDE TERMINAL V3.2")
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
    "BOVA11","IVVB11","SMAL11","HASH11","GOLD11",
    "HGLG11","XPLG11","VISC11","MXRF11","KNRI11",
    "AAPL34","AMZO34","GOGL34","MSFT34","TSLA34",
    "META34","NFLX34","NVDC34","MELI34","BABA34",
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


def atr(df, periodo=14):

    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    return tr.rolling(periodo).mean()


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

    atr_val = float(atr(df).iloc[-1])

    score = 0

    if preco > ema21[-1]:
        score += 15

    if ema21[-1] > ema72[-1]:
        score += 15

    if ema21[-1] > ema21[-5]:
        score += 10

    ret5 = ((preco / close[-6]) - 1) * 100

    if ret5 > 0:
        score += min(ret5 * 2, 10)

    dist = ((preco / ema21[-1]) - 1) * 100

    if dist > 8:
        score -= 15
    elif dist > 6:
        score -= 8

    media_vol = np.mean(volume[-20:])

    if volume[-1] > media_vol:
        score += 10

    if obv[-1] > obv[-5]:
        score += 10

    checks = [
        preco > ema21[-1],
        ema21[-1] > ema72[-1],
        ret5 > 0,
        volume[-1] > media_vol,
        obv[-1] > obv[-5]
    ]

    wil = wilson_score(sum(checks), len(checks)) * 100

    prob = (score * 0.60) + (wil * 0.40)
    prob = max(1, min(prob, 99))

    # Stop Inteligente
    stop_pct = max(2.0, min((atr_val / preco) * 100 * 1.4, 6.0))
    stop_r = preco * (1 - stop_pct / 100)

    # Gain Potencial
    gain_pct = max(2.0, min(stop_pct * (prob / 60), 12.0))
    gain_r = preco * (1 + gain_pct / 100)

    # RR
    rr = gain_pct / stop_pct

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
        "Gain %": round(gain_pct,2),
        "Gain R$": round(gain_r,2),
        "Stop %": round(stop_pct,2),
        "Stop R$": round(stop_r,2),
        "RR": round(rr,2),
        "Status": status,
        "df": df,
        "ema21": ema21,
        "ema72": ema72
    }

# =====================================================
# MENU
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

    st.title("🏹 Scanner Inteligente V3.2")

    if st.button("🚀 ESCANEAR MERCADO"):

        resultados = []
        barra = st.progress(0)

        total = len(ATIVOS)

        for i, ativo in enumerate(ATIVOS):

            r = analisar_ativo(ativo)

            if r:
                if r["Probabilidade %"] >= 70 and r["RR"] >= 1.0:
                    resultados.append(r)

            barra.progress((i+1)/total)

        if len(resultados) == 0:
            st.warning("Nenhum ativo operável hoje.")

        else:

            tabela = pd.DataFrame(resultados)

            tabela = tabela[
                [
                    "Ativo","Preço","Probabilidade %",
                    "Gain %","Gain R$",
                    "Stop %","Stop R$",
                    "RR","Status"
                ]
            ]

            tabela = tabela.sort_values(
                by=["Probabilidade %","RR"],
                ascending=False
            )

            st.success(f"{len(tabela)} ativos operáveis encontrados.")

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
            c3.metric("Gain", f"{r['Gain %']}%")
            c4.metric("RR", f"{r['RR']}")

            c5,c6 = st.columns(2)

            c5.metric("Stop", f"{r['Stop %']}%")
            c6.metric("Status", r["Status"])

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
    f"BUY SIDE TERMINAL V3.2 ELITE | {time.strftime('%d/%m/%Y %H:%M:%S')}"
)
