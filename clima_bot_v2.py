# -*- coding: utf-8 -*-

import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import os
import sys
import telegram
import asyncio
import pytz

# --- CONFIGURAÇÃO (Chaves do ambiente) ---
API_KEY = os.environ.get("WEATHER_API_KEY")
LOCALIZACAO = os.environ.get("LOCATION")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
# -----------------------------------------


def pegar_dados_clima(api_key, localizacao):
    if not api_key or not localizacao:
        print("❌ Variáveis de ambiente não encontradas.")
        sys.exit(1)

    url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={localizacao}&days=10&aqi=no&alerts=no"
    print(f"Buscando dados para: {localizacao}")

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro API: {e}")
        return None


def criar_grafico(dados):
    if not dados:
        return None

    print("Criando gráfico profissional...")

    dias = []
    for dia in dados['forecast']['forecastday']:
        data_obj = datetime.datetime.strptime(dia['date'], '%Y-%m-%d')
        dias.append({
            "Data": data_obj,
            "Probabilidade": dia['day']['daily_chance_of_rain'],
            "Precipitacao": dia['day']['totalprecip_mm']
        })

    df = pd.DataFrame(dias)

    # ===== Métricas =====
    media_precip = df['Precipitacao'].mean()
    volume_total = df['Precipitacao'].sum()
    prob_media = df['Probabilidade'].mean()
    dia_maior = df.loc[df['Precipitacao'].idxmax()]

    # ===== Layout =====
    fig = plt.figure(figsize=(14,6))
    gs = fig.add_gridspec(1, 5)

    ax = fig.add_subplot(gs[0, :4])
    ax_info = fig.add_subplot(gs[0, 4])

    cidade = dados["location"]["name"]
    fig.suptitle(f"{cidade} - Previsão 10 dias", fontsize=16, weight='bold')

    # Barras de chuva
    bars = ax.bar(df['Data'], df['Precipitacao'])

    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.2,
                    f"{h:.1f}", ha='center', fontsize=8)

    ax.set_ylabel("Precipitação (mm)")
    ax.grid(True, linestyle='--', alpha=0.4)

    # Linha probabilidade
    ax2 = ax.twinx()
    ax2.plot(df['Data'], df['Probabilidade'], marker='o', linestyle='--')

    for x, y in zip(df['Data'], df['Probabilidade']):
        ax2.text(x, y + 2, f"{int(y)}%", ha='center', fontsize=8)

    ax2.set_ylabel("Probabilidade (%)")
    ax2.set_ylim(0, 100)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))

    # ===== Painel lateral =====
    ax_info.axis('off')

    info_text = (
        f"Média diária\n{media_precip:.2f} mm\n\n"
        f"Volume total\n{volume_total:.1f} mm\n\n"
        f"Prob. média\n{prob_media:.0f}%\n\n"
        f"Maior volume\n"
        f"{dia_maior['Precipitacao']:.1f} mm\n"
        f"{dia_maior['Data'].strftime('%d/%m')}"
    )

    ax_info.text(0.05, 0.9, info_text, fontsize=11, va='top')

    plt.tight_layout()
    nome_arquivo = "grafico_clima.png"
    plt.savefig(nome_arquivo, dpi=150)
    plt.close()

    return nome_arquivo


async def enviar_telegram(token, chat_id, mensagem, caminho_imagem):
    if not token or not chat_id:
        print("Token ou Chat ID não encontrado.")
        return

    try:
        bot = telegram.Bot(token=token)
        with open(caminho_imagem, 'rb') as photo:
            await bot.send_photo(chat_id=chat_id, photo=photo, caption=mensagem)
        print("Mensagem enviada!")
    except Exception as e:
        print(f"Erro Telegram: {e}")


# ===== EXECUÇÃO =====
if __name__ == "__main__":

    dados = pegar_dados_clima(API_KEY, LOCALIZACAO)

    if dados:
        grafico = criar_grafico(dados)

        if grafico:
            cidade = dados['location']['name']

            agora_utc = datetime.datetime.now(pytz.utc)
            brasil = pytz.timezone('America/Sao_Paulo')
            agora_br = agora_utc.astimezone(brasil)

            mensagem = (
                f"📊 Previsão para {cidade}\n"
                f"Atualizado: {agora_br.strftime('%d/%m/%Y %H:%M')}"
            )

            asyncio.run(
                enviar_telegram(
                    TELEGRAM_BOT_TOKEN,
                    TELEGRAM_CHAT_ID,
                    mensagem,
                    grafico
                )
            )
