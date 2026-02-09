import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import datetime

# --- CONFIGURAÇÕES ---
API_KEY = os.getenv('WEATHER_API_KEY')
LOCATION = "Tanabi, SP"
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# --- FUNÇÕES ---

def obter_dados_clima():
    """Busca os dados da API de clima para os próximos 10 dias."""
    if not API_KEY:
        print("Erro: Variável de ambiente (WEATHER_API_KEY) não configurada.")
        return None

    url = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={LOCATION}&days=10&aqi=no&alerts=no"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar dados da API: {e}")
        return None

def formatar_mensagem(dados):
    """Formata a mensagem de texto de forma compacta para não exceder o limite do Telegram."""
    local = dados['location']['name']
    # O título da mensagem também foi atualizado para manter consistência
    mensagem = f"🌤️ *Previsão {local} - Próximos 10 dias*\n\n"
    
    for dia in dados['forecast']['forecastday']:
        data = datetime.strptime(dia['date'], '%Y-%m-%d').strftime('%d/%m')
        temp_max = dia['day']['maxtemp_c']
        temp_min = dia['day']['mintemp_c']
        # A API já retorna a condição em português para cidades no Brasil
        condicao = dia['day']['condition']['text'] 
        chuva_prob = dia['day']['daily_chance_of_rain']
        vento_max = dia['day']['maxwind_kph']
        
        mensagem += (
            f"*{data}*: {condicao}\n"
            f"🌡️ {temp_min:.0f}° / {temp_max:.0f}° | "
            f"💧 {chuva_prob}% | "
            f"💨 {vento_max:.0f}km/h\n\n"
        )
    return mensagem

def criar_graficos(dados):
    """Cria e salva os três gráficos com valores e título atualizado."""
    dias = dados['forecast']['forecastday']
    datas = [datetime.strptime(d['date'], '%Y-%m-%d') for d in dias]
    prob_chuva = [d['day']['daily_chance_of_rain'] for d in dias]
    temp_media = [d['day']['avgtemp_c'] for d in dias]
    temp_min = [d['day']['mintemp_c'] for d in dias]
    temp_max = [d['day']['maxtemp_c'] for d in dias]
    vento_max = [d['day']['maxwind_kph'] for d in dias]

    # Aumentei um pouco a altura para acomodar os valores
    fig, axs = plt.subplots(3, 1, figsize=(14, 20)) 
    
    # --- MUDANÇA 1: TÍTULO ATUALIZADO ---
    fig.suptitle('Previsão Tanabi - SP - Próximos 10 dias', fontsize=22, fontweight='bold')

    # --- GRÁFICO 1: PROBABILIDADE DE CHUVA ---
    axs[0].bar(datas, prob_chuva, color='skyblue', edgecolor='gray')
    axs[0].set_title('Probabilidade de Chuva (%)', fontsize=14)
    axs[0].set_ylabel('Probabilidade (%)')
    axs[0].set_ylim(0, 100)
    axs[0].grid(axis='y', linestyle='--', alpha=0.7)
    axs[0].xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    
    # --- MUDANÇA 2: ADICIONAR VALORES NO GRÁFICO DE CHUVA ---
    for i, (data, valor) in enumerate(zip(datas, prob_chuva)):
        axs[0].text(data, valor + 2, f'{valor}%', ha='center', va='bottom', fontsize=10)

    # --- GRÁFICO 2: TEMPERATURA ---
    axs[1].plot(datas, temp_max, marker='o', linestyle='-', label='Máxima (°C)', color='red')
    axs[1].plot(datas, temp_media, marker='s', linestyle='--', label='Média (°C)', color='orange')
    axs[1].plot(datas, temp_min, marker='^', linestyle='-', label='Mínima (°C)', color='blue')
    axs[1].set_title('Temperatura (°C)', fontsize=14)
    axs[1].set_ylabel('Temperatura (°C)')
    axs[1].legend()
    axs[1].grid(True, linestyle='--', alpha=0.7)
    axs[1].xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))

    # --- MUDANÇA 3: ADICIONAR VALORES NOS GRÁFICOS DE TEMPERATURA ---
    for i, (data, valor) in enumerate(zip(datas, temp_max)):
        axs[1].text(data, valor + 0.5, f'{valor:.0f}°', ha='center', va='bottom', fontsize=9, color='red')
    for i, (data, valor) in enumerate(zip(datas, temp_media)):
        axs[1].text(data, valor - 0.5, f'{valor:.0f}°', ha='center', va='top', fontsize=9, color='orange')
    for i, (data, valor) in enumerate(zip(datas, temp_min)):
        axs[1].text(data, valor - 0.5, f'{valor:.0f}°', ha='center', va='top', fontsize=9, color='blue')

    # --- GRÁFICO 3: VENTO ---
    axs[2].plot(datas, vento_max, marker='o', linestyle='-', color='green', label='Vel. Máxima')
    axs[2].set_title('Velocidade Máxima do Vento (km/h)', fontsize=14)
    axs[2].set_ylabel('Velocidade (km/h)')
    axs[2].set_xlabel('Data')
    axs[2].legend()
    axs[2].grid(True, linestyle='--', alpha=0.7)
    axs[2].xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))

    # --- MUDANÇA 4: ADICIONAR VALORES NO GRÁFICO DE VENTO ---
    for i, (data, valor) in enumerate(zip(datas, vento_max)):
        axs[2].text(data, valor + 1, f'{valor:.0f}', ha='center', va='bottom', fontsize=10, color='green')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    plt.savefig('grafico_clima.png')
    plt.close()
    print("Gráficos gerados com sucesso.")


def enviar_telegram(mensagem, caminho_imagem):
    """Envia a mensagem de texto e a imagem para o Telegram, com melhor tratamento de erro."""
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

            if response.status_code != 200:
                error_data = response.json()
                error_description = error_data.get('description', 'Erro desconhecido')
                print(f"Erro ao enviar para o Telegram: {response.status_code} - {error_description}")
            else:
                print("Mensagem e imagem enviadas com sucesso para o Telegram.")

    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão ao enviar para o Telegram: {e}")
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