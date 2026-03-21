# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Setup
```bash
# Criar e ativar o ambiente virtual
python -m venv .venv
source .venv/Scripts/activate  # Windows (bash)

# Instalar dependências
pip install -r requirements.txt
```

### Executar o app
```bash
python app.py
# Acesse em http://127.0.0.1:8050
```

## Arquitetura

O projeto é um dashboard web estático construído com **Dash + Plotly**, composto por apenas dois módulos:

- **`data.py`** — camada de dados: faz download via `yfinance`, e expõe quatro funções puras (`fetch_data`, `calc_cumulative_return`, `calc_monthly_volume`, `build_summary_table`). Toda lógica de cálculo fica aqui.
- **`app.py`** — camada de apresentação: importa as funções de `data.py`, constrói as figuras Plotly e monta o layout Dash. Não há callbacks interativos; os gráficos são gerados uma única vez na inicialização.

### Fluxo de dados
```
yfinance API → fetch_data() → dict[str, DataFrame]
                                  ├─ calc_cumulative_return() → DataFrame
                                  ├─ calc_monthly_volume()    → DataFrame
                                  └─ build_summary_table()    → DataFrame
                                                    ↓
                                             app.py (Dash layout)
```

### Ações monitoradas
As três ações B3 estão definidas em `data.py:5` (`TICKERS`) e o período em `data.py:6` (`PERIOD`). Para adicionar novas ações, também é necessário incluir a cor correspondente em `app.py:6` (`COLORS`).
