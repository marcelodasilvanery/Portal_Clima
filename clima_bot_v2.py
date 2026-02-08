# -*- coding: utf-8 -*-

# Importando as bibliotecas necessárias
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import pywhatkit
import os
import sys

# --- CONFIGURAÇÃO (Chaves serão lidas do ambiente de forma segura) ---
# Elas são configuradas nos "Secrets" do GitHub Actions
API_KEY = os.environ.get("WEATHER_API_KEY")
LOCALIZACAO = os.environ.get("LOCATION")
NUMERO_WHATSAPP = os.environ.get("PHONE_NUMBER")
# --- FIM DA CONFIGURAÇÃO ---


def pegar_dados_clima(api_key, localizacao):
    """Faz a requisição para a API do WeatherAPI.com e retorna os dados."""
    if not api_key or not localizacao:
        print("❌ ERRO: Variáveis de ambiente (API_KEY ou LOCALIZACAO) não encontradas.")
        sys.exit(1) # Encerra o script com erro

    url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={localizacao}&days=10&aqi=no&alerts=no"
    
    print(f"Conectando à API do WeatherAPI.com para a localização: {localizacao}")
    
    try:
        response = requests.get(url)
        response.raise_for_status() 
        print("✅ Dados recebidos da API com sucesso!")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"❌ Erro HTTP da API: {http_err}")
        try:
            error_details = response.json().get('error', {}).get('message', 'Nenhuma mensagem de erro.')
            print(f"   Detalhes: {error_details}")
        except:
            pass
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado ao buscar dados: {e}")
    return None

def criar_grafico(dados):
    """Processa os dados do WeatherAPI e cria o gráfico."""
    if not dados or 'forecast' not in dados or 'forecastday' not in dados['forecast']:
        print("❌ Dados inválidos para criar o gráfico.")
        return None

    print("📊 Processando dados e criando o gráfico...")
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
    fig.suptitle(f'Previsão Climática para {dados["location"]["name"]}', fontsize=20, weight='bold')

    axs[0].plot(df['Data'], df['Probabilidade de Chuva (%)'], marker='o', linestyle='-', color='royalblue')
    axs[0].set_ylabel('Probabilidade de Chuva (%)')
    axs[0].grid(True, linestyle='--', alpha=0.6)
    axs[0].set_ylim(0, 100)

    axs[1].bar(df['Data'], df['Precipitação (mm)'], color='skyblue')
    axs[1].set_ylabel('Precipitação (mm)')
    axs[1].grid(True, linestyle='--', alpha=0.6)

    axs[2].plot(df['Data'], df['Vento (km/h)'], marker='s', linestyle='-', color='green')
    axs[2].set_ylabel('Vento (km/h)')
    axs[2].set_xlabel('Data')
    axs[2].grid(True, linestyle='--', alpha=0.6)

    fig.autofmt_xdate()
    axs[2].xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    nome_arquivo = "grafico_clima.png"
    plt.savefig(nome_arquivo)
    print(f"✅ Gráfico salvo como '{nome_arquivo}'")
    plt.close()
    return nome_arquivo

def enviar_whatsapp(numero, mensagem, caminho_imagem):
    """Usa a biblioteca pywhatkit para enviar a imagem pelo WhatsApp."""
    if not numero:
        print("❌ ERRO: Variável de ambiente (PHONE_NUMBER) não encontrada.")
        return
        
    if not os.path.exists(caminho_imagem):
        print(f"❌ ERRO: O arquivo de imagem '{caminho_imagem}' não foi encontrado. Envio cancelado.")
        return

    try:
        print("📱 Enviando mensagem para o WhatsApp...")
        print("ATENÇÃO: O navegador virtual irá abrir. Não é necessário fazer nada.")
        pywhatkit.sendwhats_image(
            phone_no=numero,
            image_path=caminho_imagem,
            caption=mensagem,
            wait_time=25, # Aumentado para garantir carregamento
            close_time=5
        )
        print("✅ Mensagem enviada com sucesso!")
    except Exception as e:
        print(f"❌ Ocorreu um erro ao enviar a mensagem: {e}")

# --- FLUXO PRINCIPAL ---
if __name__ == "__main__":
    print("="*50)
    print("  INICIANDO O ROBÔ DE CLIMA (GitHub Actions)")
    print("="*50)
    
    # 1. Pegar os dados
    dados_climaticos = pegar_dados_clima(API_KEY, LOCALIZACAO)
    
    if dados_climaticos:
        # 2. Criar o gráfico
        caminho_do_grafico = criar_grafico(dados_climaticos)
        
        if caminho_do_grafico:
            # 3. Enviar pelo WhatsApp
            cidade = dados_climaticos['location']['name']
            mensagem = f"📊 Previsão do tempo para os próximos 10 dias em {cidade}. \n\nAtualizado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
            enviar_whatsapp(NUMERO_WHATSAPP, mensagem, caminho_do_grafico)

    print("="*50)
    print("     PROCESSO FINALIZADO")
    print("="*50)