import time
import yfinance as yf
import pandas as pd

TICKERS = {"Petrobras": "PETR4.SA", "Itaú": "ITUB4.SA", "Vale": "VALE3.SA"}
PERIOD = ("2025-01-01", "2025-12-31")


def fetch_data() -> dict[str, pd.DataFrame]:
    """Baixa dados históricos de cada ação via yfinance, com retry em rate limit."""
    data = {}
    for name, ticker in TICKERS.items():
        for attempt in range(5):
            df = yf.download(ticker, start=PERIOD[0], end=PERIOD[1], auto_adjust=True, progress=False)
            if not df.empty:
                break
            wait = 10 * (attempt + 1)
            print(f"Rate limit em {ticker}, aguardando {wait}s... (tentativa {attempt + 1}/5)")
            time.sleep(wait)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index)
        data[name] = df
        time.sleep(3)  # pausa entre tickers para evitar rate limit
    return data


def calc_cumulative_return(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Calcula retorno percentual acumulado desde o primeiro dia disponível."""
    result = {}
    for name, df in data.items():
        close = df["Close"].dropna()
        if close.empty:
            continue
        result[name] = (close / close.iloc[0] - 1) * 100
    return pd.DataFrame(result)


def calc_monthly_volume(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Calcula volume médio diário por mês para cada ação."""
    result = {}
    for name, df in data.items():
        vol = df["Volume"].dropna()
        if vol.empty:
            continue
        monthly = vol.resample("ME").mean()
        monthly.index = monthly.index.to_period("M").astype(str)
        result[name] = monthly
    return pd.DataFrame(result)


def build_summary_table(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Gera tabela de métricas resumidas para cada ação."""
    rows = []
    for name, df in data.items():
        close = df["Close"].dropna()
        if close.empty:
            rows.append({
                "Ação": name,
                "Preço Inicial (R$)": "-",
                "Preço Atual (R$)": "-",
                "Máximo (R$)": "-",
                "Mínimo (R$)": "-",
                "Variação no Ano (%)": "-",
            })
            continue
        preco_inicial = close.iloc[0]
        preco_atual = close.iloc[-1]
        variacao = (preco_atual / preco_inicial - 1) * 100
        rows.append({
            "Ação": name,
            "Preço Inicial (R$)": f"{preco_inicial:.2f}",
            "Preço Atual (R$)": f"{preco_atual:.2f}",
            "Máximo (R$)": f"{close.max():.2f}",
            "Mínimo (R$)": f"{close.min():.2f}",
            "Variação no Ano (%)": f"{variacao:+.2f}%",
        })
    return pd.DataFrame(rows)
