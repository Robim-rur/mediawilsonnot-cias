import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import math
import time
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ==========================================
# 1. CONFIGURAÇÕES E ESTILO
# ==========================================
st.set_page_config(
    page_title="Buy-Side Terminal | Wilson Score",
    page_icon="🏹",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. MOTORES DE CÁLCULO
# ==========================================

def wilson_score(positivos, total):
    if total == 0: return 0
    z = 1.96 
    phat = positivos / total
    denominador = 1 + z**2/total
    numerador = phat + z**2/(2*total) - z * math.sqrt((phat*(1-phat) + z**2/(4*total))/total)
    return max(0, numerador / denominador)

def calcular_sar_parabolico(df, af=0.02, max_af=0.2):
    # Garantir que os dados são arrays simples para evitar erro de Series Ambiguous
    high = df['High'].values
    low = df['Low'].values
    close = df['Close'].values
    
    sar = np.copy(close)
    uptrend = True
    ep = high[0]
    sar[0] = low[0]
    af_current = af
    
    for i in range(1, len(close)):
        sar[i] = sar[i-1] + af_current * (ep - sar[i-1])
        if uptrend:
            if low[i] < sar[i]:
                uptrend = False
                sar[i] = ep
                ep = low[i]
                af_current = af
            else:
                if high[i] > ep:
                    ep = high[i]
                    af_current = min(af_current + af, max_af)
        else:
            if high[i] > sar[i]:
                uptrend = True
                sar[i] = ep
                ep = high[i]
                af_current = af
            else:
                if low[i] < ep:
                    ep = low[i]
                    af_current = min(af_current + af, max_af)
    return sar

# ==========================================
# 3. GERENCIAMENTO DE CACHE
# ==========================================

@st.cache_resource(ttl=600)
def obter_ticker_seguro(ticker):
    return yf.Ticker(ticker)

@st.cache_data(ttl=300)
def buscar_historico_completo(ticker):
    # Auto_adjust=True ajuda a evitar colunas duplicadas
    df = yf.download(ticker, period="100d", interval="1d", progress=False, auto_adjust=True)
    if df.empty: return None
    # Forçar os nomes das colunas para evitar conflitos de MultiIndex
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    df = df.ffill().dropna()
    return df

# ==========================================
# 4. INTERFACE E LÓGICA PRINCIPAL
# ==========================================

with st.sidebar:
    st.header("🏹 Terminal Buy-Side")
    ticker_raw = st.text_input("Ticker B3:", "PETR4").upper()
    ticker_sa = ticker_raw if ticker_raw.endswith(".SA") else f"{ticker_raw}.SA"
    
    st.divider()
    stop_fixo = st.number_input("Stop Loss Fixo (%)", value=5.0)
    target_fixo = st.number_input("Gain Alvo (%)", value=8.0)
    
    btn_analise = st.button("🚀 EXECUTAR SCANNER", use_container_width=True)

if btn_analise:
    try:
        with st.spinner(f"Analisando confluências para {ticker_raw}..."):
            ticker_obj = obter_ticker_seguro(ticker_sa)
            hist = buscar_historico_completo(ticker_sa)
            
            if hist is None:
                st.error("Erro: Ativo não encontrado ou sem liquidez.")
            else:
                # Extração de valores puros para evitar erros de Series/Ambiguous
                precos = hist['Close'].astype(float).values
                volumes = hist['Volume'].astype(float).values
                preco_atual = float(precos[-1])
                
                # EMA 21
                ema21 = hist['Close'].ewm(span=21, adjust=False).mean().values
                
                # OBV (Cálculo Otimizado com Numpy para evitar erro iloc)
                obv_values = np.zeros(len(precos))
                for i in range(1, len(precos)):
                    if precos[i] > precos[i-1]:
                        obv_values[i] = obv_values[i-1] + volumes[i]
                    elif precos[i] < precos[i-1]:
                        obv_values[i] = obv_values[i-1] - volumes[i]
                    else:
                        obv_values[i] = obv_values[i-1]
                
                # SAR
                sar_values = calcular_sar_parabolico(hist)
                
                # Sentimento
                analyzer = SentimentIntensityAnalyzer()
                analyzer.lexicon.update({'lucro': 4.0, 'dividendos': 3.5, 'alta': 2.0, 'ebitda': 2.5})
                
                noticias = ticker_obj.news
                titulos = [n['title'] for n in noticias[:12]]
                scores = [analyzer.polarity_scores(t)['compound'] for t in titulos]
                score_sent = sum(scores)/len(scores) if scores else 0
                
                # VALIDAÇÃO DOS 4 PILARES
                c1 = bool(preco_atual > ema21[-1])
                c2 = bool(obv_values[-1] > obv_values[-5])
                c3 = bool(score_sent > 0.12)
                c4 = bool(sar_values[-1] < preco_atual)
                
                sinais = sum([c1, c2, c3, c4])
                confianca_wilson = wilson_score(sinais, 4) * 100
                
                # OUTPUT
                st.subheader(f"Resultado da Análise: {ticker_raw}")
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Preço Atual", f"R$ {preco_atual:.2f}")
                m2.metric("Score Wilson", f"{confianca_wilson:.1f}%")
                m3.metric("Stop Loss", f"R$ {preco_atual * (1 - stop_fixo/100):.2f}")
                m4.metric("Gain Alvo", f"R$ {preco_atual * (1 + target_fixo/100):.2f}")
                
                st.divider()
                
                col_info, col_chart = st.columns([1, 2])
                with col_info:
                    st.write("### ✅ Checklist de Compra")
                    st.write(f"{'🟢' if c1 else '🔴'} Tendência (EMA21)")
                    st.write(f"{'🟢' if c2 else '🔴'} Volume (OBV)")
                    st.write(f"{'🟢' if c3 else '🔴'} Mídia (Sentimento)")
                    st.write(f"{'🟢' if c4 else '🔴'} SAR (Momentum)")
                    
                    if confianca_wilson >= 60:
                        st.success("**SINAL DE COMPRA CONFIRMADO**")
                    else:
                        st.warning("**AGUARDAR CONFLUÊNCIA**")

                with col_chart:
                    df_plot = pd.DataFrame({
                        'Preço': precos,
                        'EMA 21': ema21,
                        'SAR': sar_values
                    }, index=hist.index)
                    st.line_chart(df_plot)

    except Exception as e:
        st.error(f"Erro no processamento do ativo {ticker_raw}.")
        st.write(f"Detalhe técnico: {e}")

st.markdown("---")
st.caption(f"Terminal Buy Side Pro | {time.strftime('%d/%m/%Y %H:%M:%S')}")
