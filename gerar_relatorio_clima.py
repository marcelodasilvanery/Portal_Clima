#!/usr/bin/env python3
"""Gera relatório de previsão climática (10 dias) para locais específicos.

Dados contemplados:
- Precipitação diária (mm)
- Velocidade máxima do vento diária (km/h)

APIs utilizadas (Open-Meteo):
- Geocoding API: https://geocoding-api.open-meteo.com/v1/search
- Forecast API: https://api.open-meteo.com/v1/forecast
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urlencode(params)
    request_url = f"{url}?{query}"
    try:
        with urlopen(request_url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"Falha HTTP ({exc.code}) ao consultar {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Falha de rede ao consultar {url}: {exc.reason}") from exc


def geocode_local(local: str, country_code: str | None = None) -> dict[str, Any]:
    params: dict[str, Any] = {"name": local, "count": 1, "language": "pt", "format": "json"}
    if country_code:
        params["countryCode"] = country_code

    data = fetch_json(GEOCODING_URL, params)
    results = data.get("results") or []
    if not results:
        raise ValueError(f"Local não encontrado: {local}")

    return results[0]


def forecast_10_dias(latitude: float, longitude: float, timezone: str = "auto") -> dict[str, Any]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "precipitation_sum,wind_speed_10m_max",
        "forecast_days": 10,
        "timezone": timezone,
        "wind_speed_unit": "kmh",
    }
    return fetch_json(FORECAST_URL, params)


def formatar_tabela_markdown(registros: list[dict[str, Any]]) -> str:
    linhas = [
        "| Data | Precipitação (mm) | Vento máx. (km/h) |",
        "|---|---:|---:|",
    ]
    for item in registros:
        linhas.append(
            f"| {item['data']} | {item['precipitacao_mm']:.1f} | {item['vento_max_kmh']:.1f} |"
        )
    return "\n".join(linhas)


def salvar_csv(caminho: Path, registros: list[dict[str, Any]]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        writer = csv.DictWriter(
            arquivo,
            fieldnames=["local", "data", "precipitacao_mm", "vento_max_kmh"],
        )
        writer.writeheader()
        writer.writerows(registros)


def slug(texto: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in texto).strip("-")


def gerar_relatorio(locais: list[str], country_code: str | None, saida: Path, csv_dir: Path | None) -> None:
    hoje = dt.date.today().isoformat()
    secoes: list[str] = [
        "# Relatório de Previsão Climática (10 dias)",
        "",
        f"Data de geração: **{hoje}**",
        "",
        "Este relatório considera os próximos 10 dias a partir da data de execução.",
        "",
    ]

    registros_globais: list[dict[str, Any]] = []

    for local in locais:
        geo = geocode_local(local, country_code)
        forecast = forecast_10_dias(geo["latitude"], geo["longitude"])

        daily = forecast.get("daily", {})
        datas = daily.get("time", [])
        precipitacoes = daily.get("precipitation_sum", [])
        ventos = daily.get("wind_speed_10m_max", [])

        registros_local: list[dict[str, Any]] = []
        for data, precipitacao, vento in zip(datas, precipitacoes, ventos, strict=False):
            registro = {
                "local": f"{geo['name']}, {geo.get('admin1', geo.get('country', ''))}",
                "data": data,
                "precipitacao_mm": float(precipitacao or 0.0),
                "vento_max_kmh": float(vento or 0.0),
            }
            registros_local.append(registro)
            registros_globais.append(registro)

        cidade_titulo = f"{geo['name']} ({geo.get('admin1', 'N/A')} - {geo.get('country_code', 'N/A')})"
        secoes.extend(
            [
                f"## {cidade_titulo}",
                "",
                f"Coordenadas: `{geo['latitude']:.4f}, {geo['longitude']:.4f}`",
                "",
                formatar_tabela_markdown(registros_local),
                "",
            ]
        )

        if csv_dir:
            arquivo_local = csv_dir / f"forecast_{slug(geo['name'])}.csv"
            salvar_csv(arquivo_local, registros_local)

    if csv_dir:
        salvar_csv(csv_dir / "forecast_todos_os_locais.csv", registros_globais)

    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text("\n".join(secoes), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera relatório climático de 10 dias (precipitação e vento) para locais específicos."
    )
    parser.add_argument(
        "--locais",
        required=True,
        help='Lista de locais separada por vírgula. Ex: "São Paulo,Campinas,Rio de Janeiro"',
    )
    parser.add_argument(
        "--country-code",
        default=None,
        help="Filtra geocodificação pelo código ISO do país (ex.: BR).",
    )
    parser.add_argument(
        "--saida",
        default="relatorio_previsao_climatica.md",
        help="Caminho do arquivo Markdown de saída.",
    )
    parser.add_argument(
        "--csv-dir",
        default="saida_csv",
        help="Pasta para salvar CSVs por local e consolidado. Use string vazia para não gerar CSV.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    locais = [item.strip() for item in args.locais.split(",") if item.strip()]
    if not locais:
        print("Nenhum local válido informado em --locais.", file=sys.stderr)
        return 2

    csv_dir = Path(args.csv_dir) if args.csv_dir else None

    try:
        gerar_relatorio(
            locais=locais,
            country_code=args.country_code,
            saida=Path(args.saida),
            csv_dir=csv_dir,
        )
    except Exception as exc:
        print(f"Erro ao gerar relatório: {exc}", file=sys.stderr)
        return 1

    print(f"Relatório gerado com sucesso em: {args.saida}")
    if csv_dir:
        print(f"CSVs gerados em: {csv_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
