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

# Custom CSS para melhorar a estética do terminal
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .stSuccess { background-color: #052316; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. MOTORES DE CÁLCULO (Estatística e Técnica)
# ==========================================

def wilson_score(positivos, total):
    """Calcula a probabilidade real baseada no Intervalo de Wilson."""
    if total == 0: return 0
    z = 1.96  # 95% Confiança
    phat = positivos / total
    denominador = 1 + z**2/total
    numerador = phat + z**2/(2*total) - z * math.sqrt((phat*(1-phat) + z**2/(4*total))/total)
    return max(0, numerador / denominador)

def calcular_sar_parabolico(df, af=0.02, max_af=0.2):
    """Cálculo manual do SAR para garantir precisão no Momentum."""
    df = df.copy()
    high, low, close = df['High'], df['Low'], df['Close']
    sar = close.copy()
    uptrend = True
    ep = high.iloc[0]
    sar.iloc[0] = low.iloc[0]
    af_current = af
    
    for i in range(1, len(df)):
        sar.iloc[i] = sar.iloc[i-1] + af_current * (ep - sar.iloc[i-1])
        if uptrend:
            if low.iloc[i] < sar.iloc[i]:
                uptrend = False
                sar.iloc[i] = ep
                ep = low.iloc[i]
                af_current = af
            else:
                if high.iloc[i] > ep:
                    ep = high.iloc[i]
                    af_current = min(af_current + af, max_af)
        else:
            if high.iloc[i] > sar.iloc[i]:
                uptrend = True
                sar.iloc[i] = ep
                ep = high.iloc[i]
                af_current = af
            else:
                if low.iloc[i] < ep:
                    ep = low.iloc[i]
                    af_current = min(af_current + af, max_af)
    return sar

# ==========================================
# 3. GERENCIAMENTO DE CACHE E DADOS
# ==========================================

@st.cache_resource(ttl=600)
def obter_ticker_seguro(ticker):
    """Mantém a conexão com o objeto Ticker viva no recurso."""
    return yf.Ticker(ticker)

@st.cache_data(ttl=300)
def buscar_historico_completo(ticker):
    """Baixa e limpa os dados históricos."""
    df = yf.download(ticker, period="100d", interval="1d", progress=False)
    if df.empty: return None
    # Limpeza básica de NaNs que podem quebrar o SAR
    df = df.ffill().dropna()
    return df

# ==========================================
# 4. INTERFACE DO USUÁRIO (UI)
# ==========================================

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2534/2534354.png", width=80)
    st.header("Terminal Buy-Side")
    ticker_raw = st.text_input("Ticker da B3:", "PETR4").upper()
    ticker_sa = ticker_raw if ticker_raw.endswith(".SA") else f"{ticker_raw}.SA"
    
    st.divider()
    st.write("**Parâmetros de Risco:**")
    stop_fixo = st.number_input("Stop Loss Fixo (%)", value=5.0)
    target_fixo = st.number_input("Gain Alvo (%)", value=8.0)
    
    btn_analise = st.button("🚀 EXECUTAR SCANNER", use_container_width=True)

if btn_analise:
    try:
        with st.spinner(f"Processando confluências para {ticker_raw}..."):
            # A. CAPTURA DE DADOS
            ticker_obj = obter_ticker_seguro(ticker_sa)
            hist = buscar_historico_completo(ticker_sa)
            
            if hist is None:
                st.error("Erro: Ativo não encontrado ou sem liquidez.")
            else:
                # B. PROCESSAMENTO TÉCNICO
                preco_atual = hist['Close'].iloc[-1]
                
                # EMA 21
                ema21 = hist['Close'].ewm(span=21, adjust=False).mean()
                
                # OBV (On-Balance Volume)
                obv_list = [0]
                for i in range(1, len(hist)):
                    if hist['Close'].iloc[i] > hist['Close'].iloc[i-1]:
                        obv_list.append(obv_list[-1] + hist['Volume'].iloc[i])
                    elif hist['Close'].iloc[i] < hist['Close'].iloc[i-1]:
                        obv_list.append(obv_list[-1] - hist['Volume'].iloc[i])
                    else:
                        obv_list.append(obv_list[-1])
                hist['OBV'] = obv_list
                
                # SAR
                hist['SAR'] = calcular_sar_parabolico(hist)
                
                # C. ANÁLISE DE SENTIMENTO
                analyzer = SentimentIntensityAnalyzer()
                # Dicionário calibrado para o mercado financeiro
                analyzer.lexicon.update({'lucro': 4.0, 'dividendos': 3.5, 'alta': 2.0, 'ebitda': 2.5, 'recorde': 3.0})
                
                noticias = ticker_obj.news
                titulos = [n['title'] for n in noticias[:12]]
                scores = [analyzer.polarity_scores(t)['compound'] for t in titulos]
                score_sent = sum(scores)/len(scores) if scores else 0
                
                # D. VALIDAÇÃO DOS 4 PILARES (CONFLUÊNCIA)
                c1 = preco_atual > ema21.iloc[-1]
                c2 = hist['OBV'].iloc[-1] > hist['OBV'].iloc[-5]
                c3 = score_sent > 0.12
                c4 = hist['SAR'].iloc[-1] < preco_atual
                
                sinais = sum([c1, c2, c3, c4])
                confianca_wilson = wilson_score(sinais, 4) * 100
                
                # E. OUTPUT DE RESULTADOS
                st.subheader(f"Análise Estratégica: {ticker_raw}")
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Preço Atual", f"R$ {preco_atual:.2f}")
                m2.metric("Score Wilson", f"{confianca_wilson:.1f}%")
                m3.metric("Stop Loss", f"R$ {preco_atual * (1 - stop_fixo/100):.2f}")
                m4.metric("Gain Alvo", f"R$ {preco_atual * (1 + target_fixo/100):.2f}")
                
                st.divider()
                
                col_info, col_chart = st.columns([1, 2])
                
                with col_info:
                    st.write("### ✅ Checklist de Compra")
                    st.write(f"{'🟢' if c1 else '🔴'} **Tendência:** {'Acima' if c1 else 'Abaixo'} da EMA21")
                    st.write(f"{'🟢' if c2 else '🔴'} **Volume:** {'Acumulando' if c2 else 'Distribuindo'} (OBV)")
                    st.write(f"{'🟢' if c3 else '🔴'} **Mídia:** {'Otimista' if c3 else 'Pessimista/Neutra'}")
                    st.write(f"{'🟢' if c4 else '🔴'} **SAR:** {'Sinal de Compra' if c4 else 'Sinal de Venda'}")
                    
                    st.write("---")
                    if confianca_wilson >= 60:
                        st.success("**VEREDITO:** ALTA PROBABILIDADE DE SUCESSO (BUY SIDE)")
                    elif confianca_wilson >= 35:
                        st.warning("**VEREDITO:** AGUARDAR CONFLUÊNCIA DOS INDICADORES")
                    else:
                        st.error("**VEREDITO:** RISCO ESTATÍSTICO ALTO - FIQUE DE FORA")

                with col_chart:
                    st.write("### Gráfico de Médias e SAR")
                    chart_data = pd.DataFrame({
                        'Preço': hist['Close'],
                        'EMA 21': ema21,
                        'SAR': hist['SAR']
                    })
                    st.line_chart(chart_data)

                with st.expander("📄 Ver Manchetes Analisadas pela IA"):
                    for t in titulos:
                        st.write(f"- {t}")

    except Exception as e:
        st.error(f"Erro no processamento do ativo {ticker_raw}. Verifique a conexão.")
        st.exception(e)

# Rodapé de Monitoramento Profissional
st.markdown("---")
st.caption(f"Última atualização do sistema: {time.strftime('%H:%M:%S')} | Modo: Somente Compra (Buy Side) | Fonte: Yahoo Finance")
