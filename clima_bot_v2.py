import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import datetime

# --- CONFIGURAÇÕES ---
# A chave da API ainda vem do ambiente (seguro)
API_KEY = os.getenv('WEATHER_API_KEY')
# A localização agora é fixa no código
LOCATION = "Tanabi, SP" 
# O token e chat_id ainda vêm do ambiente (seguro)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# --- FUNÇÕES ---

def obter_dados_clima():
    """Busca os dados da API de clima para os próximos 10 dias."""
    if not API_KEY:
        print("Erro: Variável de ambiente (WEATHER_API_KEY) não configurada.")
        return None

    # Mudança: o parâmetro 'days' agora é 10
    url = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={LOCATION}&days=10&aqi=no&alerts=no"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lança um erro para respostas HTTP ruins (4xx ou 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar dados da API: {e}")
        return None

def formatar_mensagem(dados):
    """Formata a mensagem de texto com a previsão para os próximos dias."""
    local = dados['location']['name']
    mensagem = f"🌤️ *Previsão do Tempo para {local} (Próximos 10 dias)*\n\n"
    
    for dia in dados['forecast']['forecastday']:
        data = datetime.strptime(dia['date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        temp_max = dia['day']['maxtemp_c']
        temp_min = dia['day']['mintemp_c']
        condicao = dia['day']['condition']['text']
        chuva_prob = dia['day']['daily_chance_of_rain']
        vento_max = dia['day']['maxwind_kph']
        
        mensagem += (
            f"📅 *{data}*\n"
            f"   Condição: {condicao}\n"
            f"   Temp: {temp_min:.1f}°C / {temp_max:.1f}°C\n"
            f"   Chuva: {chuva_prob}% | Vento: {vento_max:.1f} km/h\n\n"
        )
    return mensagem

def criar_graficos(dados):
    """Cria e salva os três gráficos solicitados em um único arquivo."""
    # Extração dos dados diários
    dias = dados['forecast']['forecastday']
    datas = [datetime.strptime(d['date'], '%Y-%m-%d') for d in dias]
    prob_chuva = [d['day']['daily_chance_of_rain'] for d in dias]
    temp_media = [d['day']['avgtemp_c'] for d in dias]
    temp_min = [d['day']['mintemp_c'] for d in dias]
    temp_max = [d['day']['maxtemp_c'] for d in dias]
    vento_max = [d['day']['maxwind_kph'] for d in dias]

    # --- Criação dos 3 Gráficos ---
    # Aumentei um pouco a altura para acomodar 10 dias sem ficar muito apertado
    fig, axs = plt.subplots(3, 1, figsize=(14, 18)) 
    fig.suptitle('Previsão do Tempo - Próximos 10 Dias', fontsize=20, fontweight='bold')

    # Gráfico 1: Probabilidade de Chuva
    axs[0].bar(datas, prob_chuva, color='skyblue', edgecolor='gray')
    axs[0].set_title('Probabilidade de Chuva (%)', fontsize=14)
    axs[0].set_ylabel('Probabilidade (%)')
    axs[0].set_ylim(0, 100)
    axs[0].grid(axis='y', linestyle='--', alpha=0.7)
    axs[0].xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    
    # Gráfico 2: Temperatura (Média, Mínima, Máxima)
    axs[1].plot(datas, temp_max, marker='o', linestyle='-', label='Máxima (°C)', color='red')
    axs[1].plot(datas, temp_media, marker='s', linestyle='--', label='Média (°C)', color='orange')
    axs[1].plot(datas, temp_min, marker='^', linestyle='-', label='Mínima (°C)', color='blue')
    axs[1].set_title('Temperatura (°C)', fontsize=14)
    axs[1].set_ylabel('Temperatura (°C)')
    axs[1].legend()
    axs[1].grid(True, linestyle='--', alpha=0.7)
    axs[1].xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))

    # Gráfico 3: Velocidade Máxima do Vento
    axs[2].plot(datas, vento_max, marker='o', linestyle='-', color='green', label='Vel. Máxima')
    axs[2].set_title('Velocidade Máxima do Vento (km/h)', fontsize=14)
    axs[2].set_ylabel('Velocidade (km/h)')
    axs[2].set_xlabel('Data')
    axs[2].legend()
    axs[2].grid(True, linestyle='--', alpha=0.7)
    axs[2].xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))

    # Ajuste final para não sobrepor elementos
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # Salvar o gráfico
    plt.savefig('grafico_clima.png')
    plt.close()
    print("Gráficos gerados com sucesso.")


def enviar_telegram(mensagem, caminho_imagem):
    """Envia a mensagem de texto e a imagem para o Telegram."""
    if not all([BOT_TOKEN, CHAT_ID]):
        print("Erro: Variáveis de ambiente (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) não configuradas.")
        return

    url_envio = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    
    try:
        with open(caminho_imagem, 'rb') as foto:
            payload = {
                'chat_id': CHAT_ID,
                'caption': mensagem,
                'parse_mode': 'Markdown'
            }
            files = {'photo': foto}
            response = requests.post(url_envio, data=payload, files=files)
            response.raise_for_status()
        print("Mensagem e imagem enviadas com sucesso para o Telegram.")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar para o Telegram: {e}")
    except FileNotFoundError:
        print(f"Erro: Arquivo de imagem '{caminho_imagem}' não encontrado.")


# --- EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    dados_clima = obter_dados_clima()
    
    if dados_clima:
        print("Dados obtidos. Gerando gráficos...")
        criar_graficos(dados_clima)
        
        print("Formatando mensagem...")
        mensagem_texto = formatar_mensagem(dados_clima)
        
        print("Enviando para o Telegram...")
        enviar_telegram(mensagem_texto, 'grafico_clima.png')
    else:
        print("Não foi possível obter os dados do clima. A execução foi cancelada.")