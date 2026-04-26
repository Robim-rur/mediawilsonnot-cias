import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import math
import time
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Buy-Side Wilson Score Pro", layout="wide")

# --- FUNÇÕES MATEMÁTICAS E ESTATÍSTICAS ---

def wilson_score(positivos, total, confidence=0.95):
    """Calcula a probabilidade de sucesso usando o limite inferior de Wilson."""
    if total == 0: return 0
    z = 1.96  # Nível de confiança de 95%
    phat = positivos / total
    denominador = 1 + z**2/total
    numerador = phat + z**2/(2*total) - z * math.sqrt((phat*(1-phat) + z**2/(4*total))/total)
    return max(0, numerador / denominador)

def calcular_sar_parabolico(df, af=0.02, max_af=0.2):
    """Implementação manual do SAR Parabólico para evitar dependências extras."""
    df = df.copy()
    high = df['High']
    low = df['Low']
    close = df['Close']
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

@st.cache_data(ttl=600)
def obter_dados_yahoo(ticker_b3):
    """Busca dados com lógica de repetição para evitar erros de Rate Limit."""
    max_tentativas = 3
    for i in range(max_tentativas):
        try:
            # Forçamos o ticker correto
            if not ticker_b3.endswith(".SA"):
                ticker_b3 += ".SA"
            
            ativo = yf.Ticker(ticker_b3)
            # O yfinance v0.2.40+ lida melhor com curl_cffi internamente
            hist = ativo.history(period="100d")
            
            if not hist.empty:
                return ativo, hist
            time.sleep(1) # Pequena pausa entre tentativas
        except Exception as e:
            if i == max_tentativas - 1:
                raise e
            time.sleep(2)
    return None, None

# --- INTERFACE PRINCIPAL ---

st.title("🏹 Analista Buy-Side: Confluência de Wilson")
st.markdown("""
Este aplicativo cruza dados técnicos e sentimentais para gerar uma probabilidade estatística de alta.
**Pilares:** Tendência (EMA21), Volume (OBV), Momentum (SAR) e Notícias (VADER).
""")

# Sidebar
st.sidebar.header("Configurações do Scanner")
ticker_input = st.sidebar.text_input("Digite o Ticker (B3):", "PETR4").upper()
dias_obv = st.sidebar.slider("Janela de Volume (Dias):", 3, 10, 5)

if st.sidebar.button("GERAR ANÁLISE COMPLETA"):
    try:
        with st.spinner(f"Analisando {ticker_input}..."):
            # 1. Coleta de Dados
            acao, hist = obter_dados_yahoo(ticker_input)
            
            if hist is None or hist.empty:
                st.error("Não foi possível obter dados. O Yahoo Finance pode estar bloqueando a conexão.")
            else:
                # 2. Cálculos Técnicos
                # EMA 21
                ema21 = hist['Close'].ewm(span=21, adjust=False).mean()
                
                # OBV (On-Balance Volume)
                obv_values = [0]
                for i in range(1, len(hist)):
                    if hist['Close'].iloc[i] > hist['Close'].iloc[i-1]:
                        obv_values.append(obv_values[-1] + hist['Volume'].iloc[i])
                    elif hist['Close'].iloc[i] < hist['Close'].iloc[i-1]:
                        obv_values.append(obv_values[-1] - hist['Volume'].iloc[i])
                    else:
                        obv_values.append(obv_values[-1])
                hist['OBV'] = obv_values
                
                # SAR Parabólico
                hist['SAR'] = calcular_sar_parabolico(hist)
                
                # 3. Análise de Sentimento (NLP)
                analyzer = SentimentIntensityAnalyzer()
                # Personalização para o "Financês"
                analyzer.lexicon.update({'lucro': 4.0, 'dividendos': 3.5, 'recorde': 3.0, 'alta': 2.0, 'ebitda': 2.5})
                
                news = acao.news
                titulos = [n['title'] for n in news[:12]]
                sent_scores = [analyzer.polarity_scores(t)['compound'] for t in titulos]
                media_sentimento = sum(sent_scores) / len(sent_scores) if sent_scores else 0
                
                # 4. Cálculo da Probabilidade de Wilson
                sinais_positivos = 0
                total_testes = 4
                
                # Condição 1: Preço acima da EMA21
                cond_ema = hist['Close'].iloc[-1] > ema21.iloc[-1]
                # Condição 2: OBV subindo na janela escolhida
                cond_obv = hist['OBV'].iloc[-1] > hist['OBV'].iloc[-(dias_obv + 1)]
                # Condição 3: Sentimento positivo
                cond_sent = media_sentimento > 0.10
                # Condição 4: SAR Parabólico abaixo do preço (Sinal de Compra)
                cond_sar = hist['SAR'].iloc[-1] < hist['Close'].iloc[-1]
                
                if cond_ema: sinais_positivos += 1
                if cond_obv: sinais_positivos += 1
                if cond_sent: sinais_positivos += 1
                if cond_sar: sinais_positivos += 1
                
                prob_wilson = wilson_score(sinais_positivos, total_testes) * 100
                
                # --- EXIBIÇÃO DOS RESULTADOS ---
                st.divider()
                col_score, col_check = st.columns([1, 2])
                
                with col_score:
                    st.metric("Score de Confiança (Wilson)", f"{prob_wilson:.1f}%")
                    if prob_wilson >= 60:
                        st.success("🎯 ALTA ASSERTIVIDADE: COMPRA")
                    elif prob_wilson >= 35:
                        st.warning("⚖️ CONFLUÊNCIA MÉDIA: AGUARDAR")
                    else:
                        st.error("⚠️ BAIXA ASSERTIVIDADE: FORA")
                    
                    st.write(f"Preço Atual: **R$ {hist['Close'].iloc[-1]:.2f}**")
                    st.write(f"Sentimento Médio: **{media_sentimento:.2f}**")
                
                with col_check:
                    st.subheader("Checklist Buy-Side")
                    st.write(f"{'✅' if cond_ema else '❌'} Tendência de Alta (Preço > EMA21)")
                    st.write(f"{'✅' if cond_obv else '❌'} Pressão de Volume (OBV em Alta)")
                    st.write(f"{'✅' if cond_sent else '❌'} Clima do Mercado (Sentimento)")
                    st.write(f"{'✅' if cond_sar else '❌'} Momentum SAR (Suporte Ativo)")

                # Gráfico
                st.subheader("Gráfico de Preço e Indicadores")
                df_grafico = pd.DataFrame({
                    'Preço': hist['Close'],
                    'EMA 21': ema21,
                    'SAR': hist['SAR']
                })
                st.line_chart(df_grafico)
                
                # Exibição de Notícias
                with st.expander("Ver manchetes analisadas"):
                    for t in titulos:
                        st.write(f"- {t}")

    except Exception as e:
        st.error(f"Erro crítico no sistema: {e}")
        st.info("Dica: Verifique se o arquivo requirements.txt inclui 'yfinance', 'vaderSentiment' e 'pandas'.")

st.markdown("---")
st.caption("Aviso: Este app é uma ferramenta de apoio. Decisões financeiras envolvem risco. Mantenha seu Stop Loss fixo.")
