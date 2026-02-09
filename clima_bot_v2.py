import os
import requests
import matplotlib.pyplot as plt
import pandas as pd

# --- CONFIGURAÇÃO DAS CHAVES DE API ---
# Todas as chaves são lidas de variáveis de ambiente para maior segurança.

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
LOCATION = os.getenv("LOCATION")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- FUNÇÕES PRINCIPAIS ---

def get_weather_data():
    """Busca os dados de previsão do tempo na API WeatherAPI.com."""
    if not all([WEATHER_API_KEY, LOCATION]):
        print("Erro: WEATHER_API_KEY ou LOCATION não foram encontrados nas variáveis de ambiente.")
        return None, None

    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={LOCATION}&days=1&aqi=no&alerts=no"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lança um erro para respostas HTTP ruins
        data = response.json()
        local = data['location']['name']
        forecast_hours = data['forecast']['forecastday'][0]['hour']
        return local, forecast_hours
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar dados da API de clima: {e}")
        return None, None
    except KeyError:
        print("Erro: A resposta da API de clima não tem o formato esperado. Verifique a chave e a localização.")
        return None, None

def create_graph(forecast_hours, local):
    """Cria o gráfico da previsão do tempo e o salva como um arquivo PNG."""
    if not forecast_hours:
        print("Não há dados para criar o gráfico.")
        return None

    df = pd.DataFrame(forecast_hours)
    df['time'] = pd.to_datetime(df['time'])
    df['temp_c'] = df['temp_c'].astype(float)

    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(12, 6))
    plt.plot(df['time'], df['temp_c'], marker='o', linestyle='-', color='b', label='Temperatura (°C)')
    plt.title(f'Previsão do Tempo para {local.title()}')
    plt.xlabel('Hora')
    plt.ylabel('Temperatura (°C)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend()

    image_path = 'previsao.png'
    plt.savefig(image_path)
    plt.close()
    print(f"Gráfico salvo como '{image_path}'")
    return image_path

def send_to_telegram(image_path, local):
    """Envia o gráfico e o texto para o Telegram."""
    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, image_path]):
        print("Erro: Faltam configurações para o Telegram.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    caption = f"Previsão do Tempo para {local.title()}.\n\nFonte: WeatherAPI.com"

    try:
        with open(image_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
        print("Mensagem enviada com sucesso para o Telegram!")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar para o Telegram: {e}")

# --- BLOCO PRINCIPAL DE EXECUÇÃO ---
if __name__ == "__main__":
    print("Iniciando o robô de clima...")

    local, forecast_hours = get_weather_data()

    if local and forecast_hours:
        image_path = create_graph(forecast_hours, local)
        
        if image_path:
            # Envia para o Telegram
            send_to_telegram(image_path, local)

    print("Robô de clima finalizado.")