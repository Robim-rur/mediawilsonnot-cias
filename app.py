import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import math
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Wilson Buy-Side Score", layout="wide")

# O Cache é vital para evitar o Rate Limit (Bloqueio)
@st.cache_data(ttl=600) # Mantém os dados por 10 minutos
def buscar_dados_seguro(ticker_b3):
    # Deixamos o yfinance gerenciar a sessão interna
    ticker_obj = yf.Ticker(ticker_b3)
    hist = ticker_obj.history(period="60d")
    return ticker_obj, hist

def wilson_score(positivos, total, confidence=0.95):
    if total == 0: return 0
    z = 1.96 
    phat = positivos / total
    denominador = 1 + z**2/total
    numerador = phat + z**2/(2*total) - z * math.sqrt((phat*(1-phat) + z**2/(4*total))/total)
    return max(0, numerador / denominador)

def calcular_sar_parabolico(df):
    high, low, close = df['High'], df['Low'], df['Close']
    sar = close.copy()
    uptrend = True
    ep = high.iloc[0]
    sar.iloc[0] = low.iloc[0]
    af = 0.02
    for i in range(1, len(df)):
        sar.iloc[i] = sar.iloc[i-1] + af * (ep - sar.iloc[i-1])
        if uptrend:
            if low.iloc[i] < sar.iloc[i]:
                uptrend = False
                sar.iloc[i] = ep
                ep = low.iloc[i]
                af = 0.02
            else:
                if high.iloc[i] > ep:
                    ep = high.iloc[i]
                    af = min(af + 0.02, 0.2)
        else:
            if high.iloc[i] > sar.iloc[i]:
                uptrend = True
                sar.iloc[i] = ep
                ep = high.iloc[i]
                af = 0.02
            else:
                if low.iloc[i] < ep:
                    ep = low.iloc[i]
                    af = min(af + 0.02, 0.2)
    return sar

# --- INTERFACE ---
st.title("🏹 Buy-Side Intelligence: Wilson Confidence")

ticker = st.sidebar.text_input("Ticker B3", "PETR4").upper()
if ticker and not ticker.endswith(".SA"): ticker += ".SA"

if st.sidebar.button("EXECUTAR ANÁLISE PROFISSIONAL"):
    try:
        with st.spinner("Buscando dados no Yahoo Finance..."):
            # Chamada otimizada
            acao, hist = buscar_dados_seguro(ticker)
            
            if hist.empty:
                st.warning("O Yahoo retornou um DataFrame vazio. Tente outro ticker ou aguarde alguns instantes.")
            else:
                # 1. Indicadores Técnicos
                ema21 = hist['Close'].ewm(span=21, adjust=False).mean()
                sar = calcular_sar_parabolico(hist)
                
                # OBV
                obv = [0]
                for i in range(1, len(hist)):
                    if hist['Close'].iloc[i] > hist['Close'].iloc[i-1]:
                        obv.append(obv[-1] + hist['Volume'].iloc[i])
                    elif hist['Close'].iloc[i] < hist['Close'].iloc[i-1]:
                        obv.append(obv[-1] - hist['Volume'].iloc[i])
                    else: obv.append(obv[-1])
                hist['OBV'] = obv

                # 2. Sentimento
                analyzer = SentimentIntensityAnalyzer()
                analyzer.lexicon.update({'lucro': 4, 'alta': 2, 'dividendos': 3, 'ebitda': 2, 'recorde': 3})
                news = acao.news
                titulos = [n['title'] for n in news[:15]]
                sent_scores = [analyzer.polarity_scores(t)['compound'] for t in titulos]
                avg_sent = sum(sent_scores)/len(sent_scores) if sent_scores else 0

                # 3. Wilson Score
                sinais = 0
                total_testes = 4
                
                cond_ema = hist['Close'].iloc[-1] > ema21.iloc[-1]
                cond_obv = hist['OBV'].iloc[-1] > hist['OBV'].iloc[-5]
                cond_sent = avg_sent > 0.10
                cond_sar = sar.iloc[-1] < hist['Close'].iloc[-1]

                if cond_ema: sinais += 1
                if cond_obv: sinais += 1
                if cond_sent: sinais += 1
                if cond_sar: sinais += 1

                prob_wilson = wilson_score(sinais, total_testes) * 100

                # --- DISPLAY ---
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.metric("Confiança de Wilson", f"{prob_wilson:.1f}%")
                    if prob_wilson > 60: st.success("SINAL DE COMPRA FORTE")
                    elif prob_wilson > 30: st.warning("SINAL MODERADO")
                    else: st.error("RISCO ALTO / FORA")
                
                with c2:
                    st.write("**Checklist de Confluência:**")
                    st.write(f"{'✅' if cond_ema else '❌'} EMA21 (Tendência)")
                    st.write(f"{'✅' if cond_obv else '❌'} OBV (Volume)")
                    st.write(f"{'✅' if cond_sent else '❌'} Sentimento (Notícias)")
                    st.write(f"{'✅' if cond_sar else '❌'} SAR (Suporte)")

                st.line_chart(hist['Close'])

    except Exception as e:
        st.error(f"Ocorreu um erro na requisição: {e}")
        st.info("Dica: Verifique se 'curl_cffi' está instalado no seu ambiente.")
