from yahooquery import Ticker
import pandas as pd

TICKERS = {
    "Petrobras": "PETR4.SA",
    "Itaú": "ITUB4.SA",
    "Vale": "VALE3.SA",
    "Banco do Brasil": "BBAS3.SA",
    "WEG": "WEGE3.SA",
    "Ambev": "ABEV3.SA",
}
PERIOD = ("2025-01-01", "2025-12-31")


def fetch_data() -> dict[str, pd.DataFrame]:
    """Baixa dados históricos de cada ação via yahooquery."""
    tickers_str = " ".join(TICKERS.values())
    try:
        raw = Ticker(tickers_str).history(start=PERIOD[0], end=PERIOD[1])
    except Exception as e:
        print(f"Erro ao baixar dados: {e}")
        return {name: pd.DataFrame() for name in TICKERS}
    data = {}
    for name, ticker in TICKERS.items():
        try:
            df = raw.loc[ticker].copy()
            df.index = pd.to_datetime(df.index)
            df = df.rename(columns={
                "close": "Close", "open": "Open",
                "high": "High", "low": "Low", "volume": "Volume",
            })
            df = df.sort_index()
        except Exception as e:
            print(f"Erro ao processar {ticker}: {e}")
            df = pd.DataFrame()
        data[name] = df
    return data


def calc_cumulative_return(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Calcula retorno percentual acumulado desde o primeiro dia disponível."""
    result = {}
    for name, df in data.items():
        if df.empty or "Close" not in df.columns:
            continue
        close = df["Close"].dropna()
        if close.empty:
            continue
        result[name] = (close / close.iloc[0] - 1) * 100
    return pd.DataFrame(result)


def calc_monthly_volume(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Calcula volume médio diário por mês para cada ação."""
    result = {}
    for name, df in data.items():
        if df.empty or "Volume" not in df.columns:
            continue
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
        if df.empty or "Close" not in df.columns:
            rows.append({
                "Ação": name,
                "Preço Inicial (R$)": "-",
                "Preço Atual (R$)": "-",
                "Máximo (R$)": "-",
                "Mínimo (R$)": "-",
                "Variação no Período (%)": "-",
            })
            continue
        close = df["Close"].dropna()
        if close.empty:
            rows.append({
                "Ação": name,
                "Preço Inicial (R$)": "-",
                "Preço Atual (R$)": "-",
                "Máximo (R$)": "-",
                "Mínimo (R$)": "-",
                "Variação no Período (%)": "-",
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
            "Variação no Período (%)": f"{variacao:+.2f}%",
        })
    return pd.DataFrame(rows)
