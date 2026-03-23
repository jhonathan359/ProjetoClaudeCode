from yahooquery import Ticker
from datetime import date, timedelta
import pandas as pd
import requests

TICKERS = {
    "Petrobras": "PETR4.SA",
    "Itaú": "ITUB4.SA",
    "Vale": "VALE3.SA",
    "Banco do Brasil": "BBAS3.SA",
    "WEG": "WEGE3.SA",
    "Ambev": "ABEV3.SA",
}

MOVERS_TICKERS = {
    **TICKERS,
    "Bradesco": "BBDC4.SA",
    "Eletrobras": "ELET3.SA",
    "B3 S.A.": "B3SA3.SA",
    "Suzano": "SUZB3.SA",
    "Localiza": "RENT3.SA",
    "Embraer": "EMBR3.SA",
    "BTG Pactual": "BPAC11.SA",
    "Itaúsa": "ITSA4.SA",
}

_today = date.today()
PERIOD = (
    (_today - timedelta(days=365)).strftime("%Y-%m-%d"),
    _today.strftime("%Y-%m-%d"),
)


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
    rows = []
    for name, df in data.items():
        base = {"Ação": name, "Preço Inicial (R$)": "-", "Preço Atual (R$)": "-",
                "Máximo (R$)": "-", "Mínimo (R$)": "-", "Variação no Período (%)": "-"}
        if df.empty or "Close" not in df.columns:
            rows.append(base)
            continue
        close = df["Close"].dropna()
        if close.empty:
            rows.append(base)
            continue
        variacao = (close.iloc[-1] / close.iloc[0] - 1) * 100
        rows.append({
            "Ação": name,
            "Preço Inicial (R$)": f"{close.iloc[0]:.2f}",
            "Preço Atual (R$)": f"{close.iloc[-1]:.2f}",
            "Máximo (R$)": f"{close.max():.2f}",
            "Mínimo (R$)": f"{close.min():.2f}",
            "Variação no Período (%)": f"{variacao:+.2f}%",
        })
    return pd.DataFrame(rows)


def fetch_top_movers() -> pd.DataFrame:
    """Busca variação do dia em tempo real para um conjunto de ações B3."""
    tickers_str = " ".join(MOVERS_TICKERS.values())
    try:
        prices = Ticker(tickers_str).price
    except Exception as e:
        print(f"Erro ao buscar top movers: {e}")
        return pd.DataFrame()
    rows = []
    for name, ticker in MOVERS_TICKERS.items():
        q = prices.get(ticker, {})
        if not isinstance(q, dict):
            continue
        change_pct = (q.get("regularMarketChangePercent") or 0) * 100
        price = q.get("regularMarketPrice") or 0
        rows.append({
            "Ação": name,
            "Ticker": ticker.replace(".SA", ""),
            "Preço (R$)": round(price, 2),
            "Variação (%)": round(change_pct, 2),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("Variação (%)", ascending=False).reset_index(drop=True)


def calc_recommendations(data: dict[str, pd.DataFrame]) -> list[dict]:
    """Calcula RSI(14), médias móveis e gera sinal de compra/venda."""
    rows = []
    for name, df in data.items():
        if df.empty or "Close" not in df.columns:
            continue
        close = df["Close"].dropna()
        if len(close) < 20:
            continue

        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rsi = (100 - (100 / (1 + gain / loss))).iloc[-1]

        current = close.iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else None
        momentum = (current / close.iloc[-6] - 1) * 100 if len(close) >= 6 else 0

        score = 0
        if rsi < 30:      score += 2
        elif rsi < 45:    score += 1
        elif rsi > 70:    score -= 2
        elif rsi > 55:    score -= 1
        if current > ma20:                    score += 1
        if ma50 is not None and ma20 > ma50:  score += 1
        if momentum > 2:   score += 1
        elif momentum < -2: score -= 1

        if score >= 3:
            sinal, cor = "COMPRA", "#16a34a"
        elif score <= -2:
            sinal, cor = "VENDA", "#dc2626"
        else:
            sinal, cor = "NEUTRO", "#d97706"

        rows.append({
            "name": name,
            "rsi": rsi,
            "ma20": ma20,
            "ma50": ma50,
            "momentum": momentum,
            "preco": current,
            "sinal": sinal,
            "cor": cor,
        })
    return rows


def fetch_crypto_data() -> pd.DataFrame:
    """Busca top 20 criptomoedas via CoinGecko com sinal de compra/venda."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "brl",
        "order": "market_cap_desc",
        "per_page": 20,
        "page": 1,
        "price_change_percentage": "24h,7d",
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        rows = []
        for c in r.json():
            ch24 = c.get("price_change_percentage_24h") or 0
            ch7d = c.get("price_change_percentage_7d_in_currency") or 0

            score = 0
            if ch24 > 5:    score += 2
            elif ch24 > 2:  score += 1
            elif ch24 < -5: score -= 2
            elif ch24 < -2: score -= 1
            if ch7d > 10:   score += 1
            elif ch7d < -10: score -= 1

            sinal = "COMPRA" if score >= 2 else ("VENDA" if score <= -2 else "NEUTRO")
            rows.append({
                "Nome": c["name"],
                "Símbolo": c["symbol"].upper(),
                "Preço (BRL)": c["current_price"],
                "Var. 24h (%)": round(ch24, 2),
                "Var. 7d (%)": round(ch7d, 2),
                "Sinal": sinal,
            })
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"Erro ao buscar crypto: {e}")
        return pd.DataFrame()
