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
    page_title="Buy Side Terminal PRO",
    page_icon="🏹",
    layout="wide"
)

# =====================================================
# ESTILO
# =====================================================

st.markdown("""
<style>
.main {background-color:#0e1117;}
.stMetric {
    background:#161b22;
    padding:14px;
    border-radius:10px;
    border:1px solid #30363d;
}
div[data-testid="stDataFrame"] {
    border:1px solid #30363d;
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# UNIVERSO TOP 30
# =====================================================

ATIVOS = [
    "PETR4","VALE3","BBAS3","ITUB4","BBDC4","ABEV3",
    "WEGE3","RENT3","SUZB3","PRIO3","RADL3","LREN3",
    "JBSS3","GGBR4","CSNA3","CMIG4","ELET3","TAEE11",
    "B3SA3","EGIE3","VIVT3","MULT3","TIMS3","RAIL3",
    "BOVA11","SMAL11","IVVB11","DIVO11","XFIX11","HASH11"
]

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
    tk = ticker + ".SA"

    df = yf.download(
        tk,
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

def calc_dmi(df, n=14):
    high = df['High']
    low = df['Low']
    close = df['Close']

    plus_dm = high.diff()
    minus_dm = low.diff() * -1

    plus_dm = np.where(
        (plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0
    )
    minus_dm = np.where(
        (minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0
    )

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(n).mean()

    plus_di = 100 * (pd.Series(plus_dm).rolling(n).mean() / atr)
    minus_di = 100 * (pd.Series(minus_dm).rolling(n).mean() / atr)

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(n).mean()

    return plus_di.values, minus_di.values, adx.values

def sentimento_score(ticker):
    try:
        obj = yf.Ticker(ticker + ".SA")
        noticias = getattr(obj, "news", [])

        analyzer = SentimentIntensityAnalyzer()

        titulos = []

        for n in noticias[:10]:
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

    close = df['Close'].values
    volume = df['Volume'].values
    preco = float(close[-1])

    ema21 = ema(df['Close'], 21).values
    ema72 = ema(df['Close'], 72).values

    obv = calc_obv(close, volume)

    plus_di, minus_di, adx = calc_dmi(df)

    sent = sentimento_score(ticker)

    # ===================================
    # SCORE CONSERVADOR
    # ===================================

    score = 0

    c1 = preco > ema21[-1] > ema72[-1]
    if c1:
        score += 30

    c2 = adx[-1] > 20 if not np.isnan(adx[-1]) else False
    if c2:
        score += 18

    c3 = plus_di[-1] > minus_di[-1] if not np.isnan(plus_di[-1]) else False
    if c3:
        score += 15

    c4 = obv[-1] > np.mean(obv[-10:])
    if c4:
        score += 15

    c5 = sent > 0
    if c5:
        score += 7

    c6 = close[-1] > close[-3]
    if c6:
        score += 15

    positivos = sum([c1,c2,c3,c4,c5,c6])

    wil = wilson_score(positivos, 6) * 100

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

    st.title("🏹 Buy Side PRO")

    modo = st.radio(
        "Modo:",
        ["Scanner Inteligente", "Ativo Específico"]
    )

# =====================================================
# SCANNER
# =====================================================

if modo == "Scanner Inteligente":

    st.title("🏹 Scanner Inteligente Top 30")
    st.caption("Mostra apenas ativos com maior chance de êxito.")

    if st.button("🚀 ESCANEAR MERCADO", use_container_width=True):

        resultados = []

        barra = st.progress(0)

        for i, ativo in enumerate(ATIVOS):

            r = analisar_ativo(ativo)

            if r:
                # MOSTRAR SOMENTE APROVADOS
                if r["Probabilidade %"] >= 70:
                    resultados.append(r)

            barra.progress((i+1)/len(ATIVOS))

        if len(resultados) == 0:
            st.warning("Nenhuma oportunidade forte encontrada hoje.")

        else:
            tabela = pd.DataFrame(resultados)

            tabela = tabela[
                [
                    "Ativo",
                    "Preço",
                    "Probabilidade %",
                    "Stop",
                    "Gain",
                    "Status"
                ]
            ].sort_values(
                by="Probabilidade %",
                ascending=False
            )

            st.success(
                f"{len(tabela)} oportunidades encontradas."
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
        "Digite qualquer ticker da B3:",
        "PETR4"
    ).upper().replace(".SA","")

    if st.button("🔎 ANALISAR", use_container_width=True):

        r = analisar_ativo(ativo)

        if r is None:
            st.error("Ativo inválido ou sem dados.")

        else:

            c1,c2,c3,c4 = st.columns(4)

            c1.metric("Preço", f"R$ {r['Preço']}")
            c2.metric("Probabilidade", f"{r['Probabilidade %']}%")
            c3.metric("Stop", f"R$ {r['Stop']}")
            c4.metric("Gain", f"R$ {r['Gain']}")

            st.subheader(r["Status"])

            plot = pd.DataFrame({
                "Preço": r["df"]["Close"],
                "EMA21": r["ema21"],
                "EMA72": r["ema72"]
            }, index=r["df"].index)

            st.line_chart(plot)

# =====================================================
# RODAPÉ
# =====================================================

st.markdown("---")
st.caption(
    f"Atualizado em {time.strftime('%d/%m/%Y %H:%M:%S')} | Perfil Segurança"
)
