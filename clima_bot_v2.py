# -*- coding: utf-8 -*-

# Importando as bibliotecas necessárias
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import os
import sys
import telegram
import asyncio

# --- CONFIGURAÇÃO (Chaves lidas do ambiente) ---
API_KEY = os.environ.get("WEATHER_API_KEY")
LOCALIZACAO = os.environ.get("LOCATION")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
# --- FIM DA CONFIGURAÇÃO ---


def pegar_dados_clima(api_key, localizacao):
    """Faz a requisição para a API do WeatherAPI.com e retorna os dados."""
    if not api_key or not localizacao:
        print("❌ ERRO: Variáveis de ambiente (WEATHER_API_KEY ou LOCATION) não encontradas.")
        sys.exit(1)
    url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={localizacao}&days=10&aqi=no&alerts=no"
    print(f"Conectando à API do WeatherAPI.com para: {localizacao}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        print("✅ Dados recebidos da API com sucesso!")
        return response.json()
    except Exception as e:
        print(f"❌ Erro ao buscar dados da API: {e}")
        return None

def criar_grafico(dados):
    """Processa os dados do WeatherAPI e cria o gráfico com melhorias."""
    if not dados or 'forecast' not in dados or 'forecastday' not in dados['forecast']:
        print("❌ Dados inválidos para criar o gráfico.")
        return None

    print("📊 Processando dados e criando o gráfico com a maquiagem...")
    dias = []
    for dia in dados['forecast']['forecastday']:
        data_obj = datetime.datetime.strptime(dia['date'], '%Y-%m-%d')
        dias.append({
            "Data": data_obj,
            "Probabilidade de Chuva (%)": dia['day']['daily_chance_of_rain'],
            "Precipitação (mm)": dia['day']['totalprecip_mm'],
            "Vento (km/h)": dia['day']['maxwind_kph']
        })
    
    df = pd.DataFrame(dias)

    fig, axs = plt.subplots(3, 1, figsize=(12, 12), sharex=True)
    fig.suptitle(f'Previsão para {dados["location"]["name"]}', fontsize=20, weight='bold')

    # --- Gráfico 1: Probabilidade de Chuva (com valores) ---
    axs[0].plot(df['Data'], df['Probabilidade de Chuva (%)'], marker='o', linestyle='-', color='royalblue', label='Prob. Chuva')
    axs[0].set_ylabel('Probabilidade de Chuva (%)')
    axs[0].grid(True, linestyle='--', alpha=0.6)
    axs[0].set_ylim(0, 105)
    
    # Adiciona os valores em cima de cada ponto
    for i, row in df.iterrows():
        axs[0].text(row['Data'], row['Probabilidade de Chuva (%)'] + 2, f"{int(row['Probabilidade de Chuva (%)'])}%", 
                     ha='center', va='bottom', fontsize=9, color='darkblue')

    # --- Gráfico 2: Precipitação ---
    axs[1].bar(df['Data'], df['Precipitação (mm)'], color='skyblue', label='Precipitação')
    axs[1].set_ylabel('Precipitação (mm)')
    axs[1].grid(True, linestyle='--', alpha=0.6)

    # --- Gráfico 3: Vento ---
    axs[2].plot(df['Data'], df['Vento (km/h)'], marker='s', linestyle='-', color='green', label='Vel. Vento')
    axs[2].set_ylabel('Vento (km/h)')
    axs[2].set_xlabel('Data')
    axs[2].grid(True, linestyle='--', alpha=0.6)

    # --- Formatação do Eixo X para TODOS os gráficos ---
    fig.autofmt_xdate() # Ajusta o ângulo das datas para não se sobreporem
    date_format = mdates.DateFormatter('%d/%m')
    
    for ax in axs:
        ax.xaxis.set_major_formatter(date_format)
        ax.set_xlabel('Data') # Adiciona o rótulo "Data" em todos os gráficos
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    nome_arquivo = "grafico_clima.png"
    plt.savefig(nome_arquivo)
    print(f"✅ Gráfico salvo como '{nome_arquivo}'")
    plt.close()
    return nome_arquivo

async def enviar_telegram(token, chat_id, mensagem, caminho_imagem):
    """Usa a biblioteca python-telegram-bot para enviar a imagem."""
    if not token or not chat_id:
        print("❌ ERRO: Variáveis de ambiente (TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID) não encontradas.")
        return
    try:
        print("📱 Enviando mensagem para o Telegram...")
        bot = telegram.Bot(token=token)
        with open(caminho_imagem, 'rb') as photo_file:
            await bot.send_photo(chat_id=chat_id, photo=photo_file, caption=mensagem)
        print("✅ Mensagem enviada com sucesso!")
    except Exception as e:
        print(f"❌ Ocorreu um erro ao enviar a mensagem: {e}")

# --- FLUXO PRINCIPAL ---
if __name__ == "__main__":
    print("="*50)
    print("  INICIANDO O ROBÔ DE CLIMA (Telegram)")
    print("="*50)
    dados_climaticos = pegar_dados_clima(API_KEY, LOCALIZACAO)
    if dados_climaticos:
        caminho_do_grafico = criar_grafico(dados_climaticos)
        if caminho_do_grafico:
            cidade = dados_climaticos['location']['name']
            mensagem = f"📊 Previsão para {cidade} - Próximos 10 dias.\n\nAtualizado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
            asyncio.run(enviar_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, mensagem, caminho_do_grafico))
    print("="*50)
    print("     PROCESSO FINALIZADO")
    print("="*50)