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
    layout="wide"
)

st.markdown("""
    <style>
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

def calcular_sar_parabolico(df):
    # Usando .values para evitar erros de Series Ambiguous
    high = df['High'].astype(float).values
    low = df['Low'].astype(float).values
    close = df['Close'].astype(float).values
    
    sar = np.copy(close)
    uptrend = True
    ep = high[0]
    sar[0] = low[0]
    af, max_af = 0.02, 0.2
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
# 3. GERENCIAMENTO DE DADOS (BLINDADO)
# ==========================================

@st.cache_resource(ttl=600)
def obter_ticker_seguro(ticker):
    return yf.Ticker(ticker)

@st.cache_data(ttl=300)
def buscar_historico_completo(ticker):
    df = yf.download(ticker, period="100d", interval="1d", progress=False, auto_adjust=True)
    if df.empty: return None
    # Achata MultiIndex se existir
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    return df.ffill().dropna()

# ==========================================
# 4. INTERFACE E LÓGICA PRINCIPAL
# ==========================================

with st.sidebar:
    st.header("🏹 Terminal Buy-Side")
    ticker_input = st.text_input("Ticker B3:", "PETR4").upper()
    ticker_sa = ticker_input if ticker_input.endswith(".SA") else f"{ticker_input}.SA"
    btn_analise = st.button("🚀 EXECUTAR SCANNER", use_container_width=True)

if btn_analise:
    try:
        with st.spinner(f"Analisando {ticker_input}..."):
            ticker_obj = obter_ticker_seguro(ticker_sa)
            hist = buscar_historico_completo(ticker_sa)
            
            if hist is None:
                st.error("Erro: Dados do Yahoo indisponíveis para este ativo.")
            else:
                # Dados Numéricos
                precos = hist['Close'].astype(float).values
                preco_atual = float(precos[-1])
                ema21 = hist['Close'].ewm(span=21, adjust=False).mean().values
                sar_values = calcular_sar_parabolico(hist)
                
                # OBV
                volumes = hist['Volume'].astype(float).values
                obv = np.zeros(len(precos))
                for i in range(1, len(precos)):
                    if precos[i] > precos[i-1]: obv[i] = obv[i-1] + volumes[i]
                    elif precos[i] < precos[i-1]: obv[i] = obv[i-1] - volumes[i]
                    else: obv[i] = obv[i-1]

                # --- CORREÇÃO DO ERRO DE TITLE (NOTÍCIAS) ---
                analyzer = SentimentIntensityAnalyzer()
                analyzer.lexicon.update({'lucro': 4.0, 'dividendos': 3.5, 'alta': 2.0})
                
                score_sent = 0
                titulos_encontrados = []
                
                try:
                    raw_news = ticker_obj.news
                    if raw_news and len(raw_news) > 0:
                        for item in raw_news:
                            # Verifica se 'title' existe no dicionário da notícia
                            t = item.get('title', '')
                            if t:
                                titulos_encontrados.append(t)
                        
                        if titulos_encontrados:
                            scores = [analyzer.polarity_scores(t)['compound'] for t in titulos_encontrados]
                            score_sent = sum(scores) / len(scores)
                except:
                    score_sent = 0 # Falha silenciosa: assume neutro se a API de notícias falhar

                # --- VALIDAÇÃO DOS 4 PILARES ---
                c1 = bool(preco_atual > ema21[-1])
                c2 = bool(obv[-1] > obv[-5])
                c3 = bool(score_sent > 0.10)
                c4 = bool(sar_values[-1] < preco_atual)
                
                sinais = sum([c1, c2, c3, c4])
                confianca = wilson_score(sinais, 4) * 100
                
                # --- OUTPUT ---
                st.subheader(f"Análise: {ticker_input}")
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Preço Atual", f"R$ {preco_atual:.2f}")
                m2.metric("Confiança Wilson", f"{confianca:.1f}%")
                m3.metric("Sentimento", f"{score_sent:.2f}")
                
                col_info, col_chart = st.columns([1, 2])
                with col_info:
                    st.write("### ✅ Checklist")
                    st.write(f"{'🟢' if c1 else '🔴'} EMA21")
                    st.write(f"{'🟢' if c2 else '🔴'} OBV")
                    st.write(f"{'🟢' if c3 else '🔴'} Notícias")
                    st.write(f"{'🟢' if c4 else '🔴'} SAR")
                    
                    if confianca >= 60: st.success("SINAL DE COMPRA")
                    else: st.warning("AGUARDAR CONFLUÊNCIA")

                with col_chart:
                    st.line_chart(pd.DataFrame({'Preço': precos, 'EMA21': ema21, 'SAR': sar_values}, index=hist.index))

                with st.expander("Ver Manchetes"):
                    if titulos_encontrados:
                        for t in titulos_encontrados: st.write(f"- {t}")
                    else:
                        st.write("Nenhuma notícia recente encontrada para este ativo.")

    except Exception as e:
        st.error(f"Erro no processamento.")
        st.write(f"Detalhes: {e}")

st.caption(f"Terminal Buy Side Pro | {time.strftime('%H:%M:%S')}")
