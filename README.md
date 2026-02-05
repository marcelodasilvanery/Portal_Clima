# Relatório de previsão climática (10 dias)

Este projeto entrega um fluxo pronto para gerar relatório de previsão climática para locais específicos, contemplando:

- **Precipitação diária (mm)**
- **Velocidade máxima do vento diária (km/h)**
- Janela de **10 dias a partir da data atual**

## Caminho recomendado

1. Informar os locais desejados.
2. Geocodificar os nomes para latitude/longitude.
3. Consultar previsão diária de 10 dias.
4. Gerar relatório em Markdown + CSV consolidado e por local.

A automação completa desse fluxo está no script `gerar_relatorio_clima.py`.

## APIs consultadas

### 1) Geocodificação (nome do local -> coordenadas)
- Endpoint: `https://geocoding-api.open-meteo.com/v1/search`
- Uso no projeto: converte o nome da cidade em latitude/longitude.

### 2) Previsão do tempo (diária)
- Endpoint: `https://api.open-meteo.com/v1/forecast`
- Parâmetros usados:
  - `daily=precipitation_sum,wind_speed_10m_max`
  - `forecast_days=10`
  - `wind_speed_unit=kmh`
  - `timezone=auto`

> API escolhida: **Open-Meteo** (sem necessidade de chave para este cenário).

## Modelo de relatório visualizado

Formato principal: **Markdown** com seções por local e tabela diária.

Exemplo de tabela:

| Data | Precipitação (mm) | Vento máx. (km/h) |
|---|---:|---:|
| 2026-02-05 | 5.2 | 21.3 |
| 2026-02-06 | 0.0 | 18.9 |

Além do Markdown, também são gerados:
- CSV por local (`saida_csv/forecast_<cidade>.csv`)
- CSV consolidado (`saida_csv/forecast_todos_os_locais.csv`)

## Como executar (pronto para uso)

```bash
python3 gerar_relatorio_clima.py \
  --locais "São Paulo,Campinas,Rio de Janeiro" \
  --country-code BR \
  --saida relatorio_previsao_climatica.md \
  --csv-dir saida_csv
```

Saídas esperadas:
- `relatorio_previsao_climatica.md`
- `saida_csv/forecast_sao-paulo.csv` (e demais locais)
- `saida_csv/forecast_todos_os_locais.csv`

## Observações

- Para reduzir ambiguidades em nomes de cidade, use `--country-code` (ex.: `BR`).
- Se quiser desativar CSV, use `--csv-dir ""`.
