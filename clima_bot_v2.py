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