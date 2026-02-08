# -*- coding: utf-8 -*-

# Importando as bibliotecas necessárias
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import pywhatkit
import time
import os

# --- CONFIGURAÇÃO INICIAL (PREENCHA APENAS AQUI!) ---
# Cole a NOVA chave que você criou e ESPEROU 1 hora
API_KEY = "9d98fe48f5fcc78ba571c4989654c386" 

# Coordenadas da sua cidade (exemplo para São Paulo)
LAT = -20,626  
LON = -49.649

# Número de telefone com DDI e DDD (ex: +5511999998888)
NUMERO_WHATSAPP = "+5517997927252" 
# --- FIM DA CONFIGURAÇÃO ---


def pegar_dados_clima(api_key, lat, lon):
    """Faz a requisição para a API do OpenWeatherMap e retorna os dados."""
    # Monta a URL da API
    url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=current,minutely,hourly,alerts&appid={api_key}&units=metric&lang=pt_br"
    
    print(f"Conectando à API com a chave: {api_key[:10]}...") # Mostra só o começo da chave por segurança
    
    try:
        response = requests.get(url)
        # Força um erro se o status não for 200 (OK)
        response.raise_for_status() 
        print("✅ Dados recebidos da API com sucesso!")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        # Pega a mensagem de erro exata da API
        error_message = response.json().get('message', 'Nenhuma mensagem de erro.')
        print(f"❌ Erro HTTP da API: {http_err} - Detalhes: {error_message}")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado ao buscar dados: {e}")
    return None

def criar_grafico(dados):
    """Processa os dados e cria o gráfico, salvando como imagem."""
    if not dados or 'daily' not in dados:
        print("❌ Dados inválidos para criar o gráfico.")
        return None

    print("📊 Processando dados e criando o gráfico...")
    dias = []
    for dia in dados['daily']:
        data_obj = datetime.datetime.fromtimestamp(dia['dt'])
        dias.append({
            "Data": data_obj,
            "Probabilidade de Chuva (%)": dia.get('pop', 0) * 100,
            "Precipitação (mm)": dia.get('rain', {}).get('24h', 0),
            "Vento (km/h)": dia['wind_speed'] * 3.6
        })
    
    df = pd.DataFrame(dias)

    fig, axs = plt.subplots(3, 1, figsize=(12, 12), sharex=True)
    fig.suptitle('Previsão Climática Próximos 10 Dias', fontsize=20, weight='bold')

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
    # Verifica se o arquivo de imagem realmente existe antes de tentar enviar
    if not os.path.exists(caminho_imagem):
        print(f"❌ ERRO: O arquivo de imagem '{caminho_imagem}' não foi encontrado. Envio cancelado.")
        return

    try:
        print("📱 Enviando mensagem para o WhatsApp...")
        print("ATENÇÃO: Seu navegador irá abrir. Mantenha-o aberto e não mexa no mouse/teclado.")
        pywhatkit.sendwhats_image(
            receiver_number=numero,
            image_path=caminho_imagem,
            caption=mensagem,
            wait_time=20, # Aumentei para 20 segundos para dar mais tempo de carregar
            close_time=5
        )
        print("✅ Mensagem enviada com sucesso!")
    except Exception as e:
        print(f"❌ Ocorreu um erro ao enviar a mensagem: {e}")

# --- FLUXO PRINCIPAL ---
if __name__ == "__main__":
    print("="*50)
    print("     INICIANDO O ROBÔ DE CLIMA v2.0")
    print("="*50)
    
    # 1. Pegar os dados
    dados_climaticos = pegar_dados_clima(API_KEY, LAT, LON)
    
    if dados_climaticos:
        # 2. Criar o gráfico
        caminho_do_grafico = criar_grafico(dados_climaticos)
        
        if caminho_do_grafico:
            # 3. Enviar pelo WhatsApp
            mensagem = f"📊 Previsão do tempo para os próximos 10 dias. \n\nAtualizado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
            enviar_whatsapp(NUMERO_WHATSAPP, mensagem, caminho_do_grafico)

    print("="*50)
    print("     PROCESSO FINALIZADO")
    print("="*50)
