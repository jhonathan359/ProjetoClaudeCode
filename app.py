import plotly.graph_objects as go
from dash import Dash, dcc, html, dash_table, Input, Output

from data import (
    fetch_data, calc_cumulative_return, calc_monthly_volume, build_summary_table,
    fetch_top_movers, calc_recommendations, fetch_crypto_data, TICKERS,
)

# --- Cores das ações monitoradas ---
COLORS = {
    "Petrobras": "#009c3b",
    "Itaú": "#0047CC",
    "Vale": "#0077b6",
    "Banco do Brasil": "#ca8a04",
    "WEG": "#0d9488",
    "Ambev": "#7c3aed",
}
TICKER_MAP = {
    "Petrobras": "PETR4", "Itaú": "ITUB4", "Vale": "VALE3",
    "Banco do Brasil": "BBAS3", "WEG": "WEGE3", "Ambev": "ABEV3",
}

# --- Design tokens ---
PAGE_BG   = "#f0f2f5"
CARD_BG   = "#ffffff"
HEADER_BG = "#0d1b3e"
BORDER    = "#e2e8f0"
TEXT_PRIMARY   = "#1a2744"
TEXT_SECONDARY = "#64748b"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

CHART_BASE = dict(
    plot_bgcolor=CARD_BG, paper_bgcolor=CARD_BG,
    font=dict(family=FONT, color=TEXT_PRIMARY, size=12),
    xaxis=dict(gridcolor="#f1f5f9", linecolor=BORDER, showline=True,
               tickfont=dict(size=11, color=TEXT_SECONDARY)),
    yaxis=dict(gridcolor="#f1f5f9", linecolor=BORDER, showline=True,
               tickfont=dict(size=11, color=TEXT_SECONDARY)),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
    hovermode="x unified",
    margin=dict(l=60, r=20, t=10, b=50),
)

# ---------------------------------------------------------------------------
# Carrega dados históricos uma vez na inicialização
# ---------------------------------------------------------------------------
print("Baixando dados históricos... Aguarde.")
data       = fetch_data()
cumulative = calc_cumulative_return(data)
monthly_vol = calc_monthly_volume(data)
summary    = build_summary_table(data)
recs       = calc_recommendations(data)
print("Dados carregados com sucesso.")

# --- Gráfico 1: Preço de Fechamento ---
fig_price = go.Figure()
for name, df in data.items():
    close = df["Close"].dropna() if not df.empty and "Close" in df.columns else None
    if close is None or close.empty:
        continue
    fig_price.add_trace(go.Scatter(
        x=close.index, y=close.values, mode="lines", name=name,
        line=dict(color=COLORS.get(name, "#888"), width=2),
    ))
fig_price.update_layout(**CHART_BASE)

# --- Gráfico 2: Performance Acumulada ---
fig_perf = go.Figure()
for name in cumulative.columns:
    fig_perf.add_trace(go.Scatter(
        x=cumulative.index, y=cumulative[name], mode="lines", name=name,
        line=dict(color=COLORS.get(name, "#888"), width=2),
    ))
fig_perf.add_hline(y=0, line_dash="dash", line_color="#94a3b8", line_width=1)
fig_perf.update_layout(**CHART_BASE, yaxis_ticksuffix="%")

# --- Gráfico 3: Volume Médio Mensal ---
fig_vol = go.Figure()
for name in monthly_vol.columns:
    fig_vol.add_trace(go.Bar(
        x=monthly_vol.index, y=monthly_vol[name], name=name,
        marker_color=COLORS.get(name, "#888"), marker_line_width=0,
    ))
fig_vol.update_layout(**CHART_BASE, barmode="group")


# ---------------------------------------------------------------------------
# Componentes de layout reutilizáveis
# ---------------------------------------------------------------------------
def section_card(title, subtitle, body):
    return html.Div([
        html.Div([
            html.H3(title, style={"margin": "0 0 4px 0", "fontSize": "15px",
                                   "fontWeight": "600", "color": TEXT_PRIMARY}),
            html.P(subtitle, style={"margin": "0", "fontSize": "12px", "color": TEXT_SECONDARY}),
        ], style={"padding": "20px 24px 14px", "borderBottom": f"1px solid {BORDER}"}),
        html.Div(body, style={"padding": "8px"}),
    ], style={"backgroundColor": CARD_BG, "borderRadius": "12px",
              "border": f"1px solid {BORDER}", "boxShadow": "0 1px 4px rgba(0,0,0,0.06)",
              "marginBottom": "24px"})


def kpi_card(row):
    empresa = row["Ação"]
    variacao_str = row["Variação no Período (%)"]
    is_pos = isinstance(variacao_str, str) and variacao_str.startswith("+")
    var_color = "#16a34a" if is_pos else "#dc2626"
    var_bg    = "#f0fdf4" if is_pos else "#fef2f2"
    ticker    = TICKER_MAP.get(empresa, empresa)
    cor       = COLORS.get(empresa, "#64748b")

    return html.Div([
        html.Div([
            html.Span(ticker, style={"fontSize": "11px", "fontWeight": "700", "color": "#fff",
                                     "backgroundColor": cor, "padding": "3px 9px",
                                     "borderRadius": "5px"}),
            html.Span(variacao_str, style={"fontSize": "12px", "fontWeight": "600",
                                           "color": var_color, "backgroundColor": var_bg,
                                           "padding": "3px 9px", "borderRadius": "5px"}),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "center", "marginBottom": "14px"}),
        html.P(empresa, style={"fontSize": "13px", "color": TEXT_SECONDARY,
                                "margin": "0 0 4px 0"}),
        html.P(f"R$ {row['Preço Atual (R$)']}", style={"fontSize": "28px", "fontWeight": "700",
                                                        "color": TEXT_PRIMARY, "margin": "0 0 16px 0",
                                                        "letterSpacing": "-0.5px"}),
        html.Div([
            html.Div([html.Span("Abertura", style={"fontSize": "10px", "color": TEXT_SECONDARY,
                                                    "display": "block", "marginBottom": "2px",
                                                    "textTransform": "uppercase"}),
                      html.Span(f"R$ {row['Preço Inicial (R$)']}", style={"fontSize": "13px",
                                                                            "fontWeight": "500"})]),
            html.Div([html.Span("Máximo", style={"fontSize": "10px", "color": TEXT_SECONDARY,
                                                  "display": "block", "marginBottom": "2px",
                                                  "textTransform": "uppercase"}),
                      html.Span(f"R$ {row['Máximo (R$)']}", style={"fontSize": "13px",
                                                                     "fontWeight": "500",
                                                                     "color": "#16a34a"})]),
            html.Div([html.Span("Mínimo", style={"fontSize": "10px", "color": TEXT_SECONDARY,
                                                  "display": "block", "marginBottom": "2px",
                                                  "textTransform": "uppercase"}),
                      html.Span(f"R$ {row['Mínimo (R$)']}", style={"fontSize": "13px",
                                                                     "fontWeight": "500",
                                                                     "color": "#dc2626"})]),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "paddingTop": "14px", "borderTop": f"1px solid {BORDER}"}),
    ], style={"backgroundColor": CARD_BG, "borderRadius": "12px",
              "border": f"1px solid {BORDER}", "boxShadow": "0 1px 4px rgba(0,0,0,0.06)",
              "padding": "20px", "flex": "1", "minWidth": "220px"})


def rec_card(rec: dict):
    sinal = rec["sinal"]
    cor   = rec["cor"]
    cor_bg = {"COMPRA": "#f0fdf4", "VENDA": "#fef2f2", "NEUTRO": "#fffbeb"}.get(sinal, "#f8fafc")
    ticker = TICKER_MAP.get(rec["name"], rec["name"])
    color  = COLORS.get(rec["name"], "#64748b")
    ma50_str = f"R$ {rec['ma50']:.2f}" if rec["ma50"] is not None else "N/D"

    return html.Div([
        html.Div([
            html.Span(ticker, style={"fontSize": "11px", "fontWeight": "700", "color": "#fff",
                                     "backgroundColor": color, "padding": "3px 9px",
                                     "borderRadius": "5px"}),
            html.Span(sinal, style={"fontSize": "12px", "fontWeight": "700", "color": cor,
                                    "backgroundColor": cor_bg, "padding": "3px 10px",
                                    "borderRadius": "5px", "border": f"1px solid {cor}"}),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "center", "marginBottom": "10px"}),
        html.P(rec["name"], style={"fontSize": "13px", "color": TEXT_SECONDARY, "margin": "0 0 2px 0"}),
        html.P(f"R$ {rec['preco']:.2f}", style={"fontSize": "22px", "fontWeight": "700",
                                                 "color": TEXT_PRIMARY, "margin": "0 0 12px 0"}),
        html.Div([
            html.Div([html.Span("RSI (14)", style={"fontSize": "10px", "color": TEXT_SECONDARY,
                                                    "display": "block", "textTransform": "uppercase"}),
                      html.Span(f"{rec['rsi']:.1f}", style={
                          "fontSize": "13px", "fontWeight": "600",
                          "color": "#16a34a" if rec["rsi"] < 40 else ("#dc2626" if rec["rsi"] > 65 else TEXT_PRIMARY),
                      })]),
            html.Div([html.Span("MA20", style={"fontSize": "10px", "color": TEXT_SECONDARY,
                                                "display": "block", "textTransform": "uppercase"}),
                      html.Span(f"R$ {rec['ma20']:.2f}", style={"fontSize": "13px", "fontWeight": "600",
                                                                  "color": TEXT_PRIMARY})]),
            html.Div([html.Span("Moment. 5d", style={"fontSize": "10px", "color": TEXT_SECONDARY,
                                                      "display": "block", "textTransform": "uppercase"}),
                      html.Span(f"{rec['momentum']:+.1f}%", style={
                          "fontSize": "13px", "fontWeight": "600",
                          "color": "#16a34a" if rec["momentum"] > 0 else "#dc2626",
                      })]),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "paddingTop": "12px", "borderTop": f"1px solid {BORDER}"}),
    ], style={"backgroundColor": CARD_BG, "borderRadius": "12px",
              "border": f"1px solid {BORDER}", "boxShadow": "0 1px 4px rgba(0,0,0,0.06)",
              "padding": "18px", "flex": "1", "minWidth": "200px"})


# ---------------------------------------------------------------------------
# Builders de conteúdo dinâmico (chamados nos callbacks)
# ---------------------------------------------------------------------------
def build_movers_content(df):
    if df.empty:
        return html.P("Sem dados no momento.", style={"color": TEXT_SECONDARY, "padding": "16px"})

    top5    = df.head(5)
    bottom5 = df.tail(5).iloc[::-1]
    combined = pd.concat([top5, bottom5]).drop_duplicates()

    colors = ["#16a34a" if v >= 0 else "#dc2626" for v in combined["Variação (%)"]]
    labels = [f"{row['Ticker']} ({row['Variação (%)']:+.2f}%)" for _, row in combined.iterrows()]

    fig = go.Figure(go.Bar(
        x=combined["Variação (%)"],
        y=labels,
        orientation="h",
        marker_color=colors,
        marker_line_width=0,
        text=[f"{v:+.2f}%" for v in combined["Variação (%)"]],
        textposition="outside",
    ))
    fig.update_layout(
        **{**CHART_BASE, "margin": dict(l=120, r=60, t=10, b=30)},
        height=320,
        yaxis=dict(tickfont=dict(size=12), gridcolor="#f1f5f9", linecolor=BORDER, showline=False),
        xaxis=dict(ticksuffix="%", gridcolor="#f1f5f9", linecolor=BORDER, showline=True,
                   tickfont=dict(size=11, color=TEXT_SECONDARY)),
    )
    fig.add_vline(x=0, line_color="#94a3b8", line_width=1)

    return dcc.Graph(figure=fig, config={"displayModeBar": False})


def build_crypto_content(df):
    if df.empty:
        return html.P("Sem dados cripto no momento.", style={"color": TEXT_SECONDARY, "padding": "16px"})

    # Gráfico barras 24h
    bar_df = df.sort_values("Var. 24h (%)", ascending=False).head(15)
    bar_colors = ["#16a34a" if v >= 0 else "#dc2626" for v in bar_df["Var. 24h (%)"]]
    fig_crypto = go.Figure(go.Bar(
        x=bar_df["Símbolo"],
        y=bar_df["Var. 24h (%)"],
        marker_color=bar_colors,
        marker_line_width=0,
        text=[f"{v:+.1f}%" for v in bar_df["Var. 24h (%)"]],
        textposition="outside",
    ))
    fig_crypto.update_layout(
        **{**CHART_BASE, "margin": dict(l=40, r=20, t=10, b=50)},
        height=260,
        yaxis_ticksuffix="%",
    )
    fig_crypto.add_hline(y=0, line_dash="dash", line_color="#94a3b8", line_width=1)

    # Formata preço
    def fmt_price(p):
        if p >= 1:
            return f"R$ {p:,.2f}"
        return f"R$ {p:.6f}"

    df_display = df.copy()
    df_display["Preço (BRL)"] = df_display["Preço (BRL)"].apply(fmt_price)
    df_display["Var. 24h (%)"] = df_display["Var. 24h (%)"].apply(lambda v: f"{v:+.2f}%")
    df_display["Var. 7d (%)"]  = df_display["Var. 7d (%)"].apply(lambda v: f"{v:+.2f}%")

    signal_colors = [
        {"if": {"filter_query": '{Sinal} = "COMPRA"', "column_id": "Sinal"},
         "color": "#16a34a", "fontWeight": "700"},
        {"if": {"filter_query": '{Sinal} = "VENDA"', "column_id": "Sinal"},
         "color": "#dc2626", "fontWeight": "700"},
        {"if": {"filter_query": '{Sinal} = "NEUTRO"', "column_id": "Sinal"},
         "color": "#d97706", "fontWeight": "700"},
    ]

    table = dash_table.DataTable(
        data=df_display.to_dict("records"),
        columns=[{"name": c, "id": c} for c in df_display.columns],
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": "#f8fafc", "color": TEXT_SECONDARY, "fontWeight": "600",
                       "textAlign": "center", "fontSize": "11px", "textTransform": "uppercase",
                       "letterSpacing": "0.5px", "border": "none",
                       "borderBottom": f"2px solid {BORDER}", "padding": "14px 16px",
                       "fontFamily": FONT},
        style_cell={"textAlign": "center", "padding": "12px 16px", "fontSize": "13px",
                     "fontFamily": FONT, "color": TEXT_PRIMARY, "border": "none",
                     "borderBottom": f"1px solid {BORDER}"},
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#f8fafc"},
            *signal_colors,
        ],
        style_as_list_view=True,
    )

    return html.Div([
        dcc.Graph(figure=fig_crypto, config={"displayModeBar": False}),
        html.Div(style={"height": "16px"}),
        table,
    ])


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
app = Dash(__name__)
app.title = "Dashboard B3 + Cripto"

TAB_STYLE = {
    "fontFamily": FONT, "fontSize": "14px", "fontWeight": "500",
    "color": TEXT_SECONDARY, "padding": "12px 24px",
    "borderBottom": f"2px solid {BORDER}", "backgroundColor": PAGE_BG,
}
TAB_SELECTED_STYLE = {
    **TAB_STYLE, "color": TEXT_PRIMARY, "fontWeight": "700",
    "borderBottom": f"2px solid #0047CC", "backgroundColor": CARD_BG,
}

kpi_cards = [kpi_card(row) for row in summary.to_dict("records")]
rec_cards  = [rec_card(r) for r in recs]

app.layout = html.Div(
    style={"fontFamily": FONT, "backgroundColor": PAGE_BG, "minHeight": "100vh"},
    children=[

        # Header
        html.Div([
            html.Div([
                html.Div([
                    html.H1("Dashboard B3 + Cripto", style={"margin": "0", "fontSize": "22px",
                                                              "fontWeight": "700", "color": "#fff",
                                                              "letterSpacing": "-0.3px"}),
                    html.P("PETR4 · ITUB4 · VALE3 · BBAS3 · WEGE3 · ABEV3 + Criptomoedas",
                           style={"margin": "4px 0 0", "fontSize": "13px",
                                  "color": "rgba(255,255,255,0.55)"}),
                ]),
                html.Span("B3 — Bolsa do Brasil", style={
                    "fontSize": "12px", "fontWeight": "500", "color": "rgba(255,255,255,0.75)",
                    "backgroundColor": "rgba(255,255,255,0.10)", "padding": "6px 14px",
                    "borderRadius": "20px", "border": "1px solid rgba(255,255,255,0.15)",
                }),
            ], style={"maxWidth": "1200px", "margin": "0 auto", "padding": "22px 32px",
                      "display": "flex", "justifyContent": "space-between", "alignItems": "center"}),
        ], style={"backgroundColor": HEADER_BG, "borderBottom": "1px solid rgba(255,255,255,0.07)"}),

        # Tabs
        dcc.Tabs(id="tabs", value="acoes", children=[

            # ── Tab 1: Ações B3 ──────────────────────────────────────────────
            dcc.Tab(label="Ações B3", value="acoes",
                    style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE,
                    children=[html.Div([

                        # KPI Cards
                        html.Div(kpi_cards, style={"display": "flex", "gap": "20px",
                                                    "marginBottom": "24px", "flexWrap": "wrap"}),

                        # Top Movers (tempo real)
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.H3("Top Movers — Tempo Real", style={
                                        "margin": "0 0 4px 0", "fontSize": "15px",
                                        "fontWeight": "600", "color": TEXT_PRIMARY}),
                                    html.P("Maiores altas e baixas do dia · Atualiza a cada 60s",
                                           style={"margin": "0", "fontSize": "12px",
                                                  "color": TEXT_SECONDARY}),
                                ]),
                                html.Span("● AO VIVO", style={
                                    "fontSize": "11px", "fontWeight": "700", "color": "#16a34a",
                                    "backgroundColor": "#f0fdf4", "padding": "4px 10px",
                                    "borderRadius": "20px", "border": "1px solid #bbf7d0",
                                }),
                            ], style={"display": "flex", "justifyContent": "space-between",
                                      "alignItems": "center",
                                      "padding": "20px 24px 14px",
                                      "borderBottom": f"1px solid {BORDER}"}),
                            html.Div(id="top-movers-content", style={"padding": "8px"}),
                        ], style={"backgroundColor": CARD_BG, "borderRadius": "12px",
                                  "border": f"1px solid {BORDER}",
                                  "boxShadow": "0 1px 4px rgba(0,0,0,0.06)",
                                  "marginBottom": "24px"}),

                        # Recomendações
                        html.Div([
                            html.Div([
                                html.H3("Recomendações", style={"margin": "0 0 4px 0",
                                                                  "fontSize": "15px",
                                                                  "fontWeight": "600",
                                                                  "color": TEXT_PRIMARY}),
                                html.P("Baseado em RSI(14), médias móveis e momentum. Não é consultoria financeira.",
                                       style={"margin": "0", "fontSize": "12px", "color": TEXT_SECONDARY}),
                            ], style={"padding": "20px 24px 14px", "borderBottom": f"1px solid {BORDER}"}),
                            html.Div(rec_cards, style={"display": "flex", "gap": "16px",
                                                        "flexWrap": "wrap", "padding": "16px"}),
                        ], style={"backgroundColor": CARD_BG, "borderRadius": "12px",
                                  "border": f"1px solid {BORDER}",
                                  "boxShadow": "0 1px 4px rgba(0,0,0,0.06)",
                                  "marginBottom": "24px"}),

                        # Gráficos históricos
                        section_card("Preço de Fechamento Ajustado",
                                     "Evolução do preço de fechamento (R$) nos últimos 12 meses",
                                     dcc.Graph(figure=fig_price, config={"displayModeBar": False})),
                        section_card("Performance Acumulada",
                                     "Retorno percentual acumulado nos últimos 12 meses",
                                     dcc.Graph(figure=fig_perf, config={"displayModeBar": False})),
                        section_card("Volume Médio Diário",
                                     "Volume médio de negociações por mês nos últimos 12 meses",
                                     dcc.Graph(figure=fig_vol, config={"displayModeBar": False})),

                        # Tabela resumo
                        html.Div([
                            html.Div([
                                html.H3("Resumo das Ações", style={"margin": "0 0 4px 0",
                                                                     "fontSize": "15px",
                                                                     "fontWeight": "600",
                                                                     "color": TEXT_PRIMARY}),
                                html.P("Métricas consolidadas do período", style={
                                    "margin": "0", "fontSize": "12px", "color": TEXT_SECONDARY}),
                            ], style={"padding": "20px 24px 14px", "borderBottom": f"1px solid {BORDER}"}),
                            dash_table.DataTable(
                                data=summary.to_dict("records"),
                                columns=[{"name": c, "id": c} for c in summary.columns],
                                style_table={"overflowX": "auto"},
                                style_header={"backgroundColor": "#f8fafc", "color": TEXT_SECONDARY,
                                               "fontWeight": "600", "textAlign": "center",
                                               "fontSize": "11px", "textTransform": "uppercase",
                                               "letterSpacing": "0.5px", "border": "none",
                                               "borderBottom": f"2px solid {BORDER}",
                                               "padding": "14px 16px", "fontFamily": FONT},
                                style_cell={"textAlign": "center", "padding": "14px 16px",
                                             "fontSize": "14px", "fontFamily": FONT,
                                             "color": TEXT_PRIMARY, "border": "none",
                                             "borderBottom": f"1px solid {BORDER}"},
                                style_data_conditional=[
                                    {"if": {"row_index": "odd"}, "backgroundColor": "#f8fafc"},
                                ],
                                style_as_list_view=True,
                            ),
                        ], style={"backgroundColor": CARD_BG, "borderRadius": "12px",
                                  "border": f"1px solid {BORDER}",
                                  "boxShadow": "0 1px 4px rgba(0,0,0,0.06)",
                                  "marginBottom": "24px", "overflow": "hidden"}),

                        # Footer
                        html.Div([
                            html.P("Dados via Yahoo Finance · yahooquery",
                                   style={"margin": "0", "fontSize": "12px", "color": TEXT_SECONDARY}),
                            html.P("Dashboard B3 · Dash + Plotly",
                                   style={"margin": "0", "fontSize": "12px", "color": TEXT_SECONDARY}),
                        ], style={"display": "flex", "justifyContent": "space-between",
                                  "padding": "16px 0", "borderTop": f"1px solid {BORDER}"}),

                    ], style={"maxWidth": "1200px", "margin": "0 auto", "padding": "32px"})]),

            # ── Tab 2: Criptomoedas ─────────────────────────────────────────
            dcc.Tab(label="Criptomoedas", value="cripto",
                    style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE,
                    children=[html.Div([

                        html.Div([
                            html.Div([
                                html.Div([
                                    html.H3("Mercado Cripto — Tempo Real", style={
                                        "margin": "0 0 4px 0", "fontSize": "15px",
                                        "fontWeight": "600", "color": TEXT_PRIMARY}),
                                    html.P("Top 20 por market cap · Sinais por momentum 24h e 7d · Atualiza a cada 5min",
                                           style={"margin": "0", "fontSize": "12px",
                                                  "color": TEXT_SECONDARY}),
                                ]),
                                html.Span("● AO VIVO", style={
                                    "fontSize": "11px", "fontWeight": "700", "color": "#16a34a",
                                    "backgroundColor": "#f0fdf4", "padding": "4px 10px",
                                    "borderRadius": "20px", "border": "1px solid #bbf7d0",
                                }),
                            ], style={"display": "flex", "justifyContent": "space-between",
                                      "alignItems": "center",
                                      "padding": "20px 24px 14px",
                                      "borderBottom": f"1px solid {BORDER}"}),
                            html.Div(id="crypto-content", style={"padding": "8px"}),
                        ], style={"backgroundColor": CARD_BG, "borderRadius": "12px",
                                  "border": f"1px solid {BORDER}",
                                  "boxShadow": "0 1px 4px rgba(0,0,0,0.06)",
                                  "marginBottom": "24px"}),

                        html.Div([
                            html.P("⚠ As recomendações são baseadas em momentum de curto prazo e não constituem "
                                   "consultoria de investimento. Criptomoedas são ativos de alto risco.",
                                   style={"margin": "0", "fontSize": "12px", "color": "#92400e",
                                          "backgroundColor": "#fffbeb", "padding": "12px 16px",
                                          "borderRadius": "8px", "border": "1px solid #fde68a"}),
                        ], style={"marginBottom": "24px"}),

                        html.Div([
                            html.P("Dados via CoinGecko API · coingecko.com",
                                   style={"margin": "0", "fontSize": "12px", "color": TEXT_SECONDARY}),
                            html.P("Dashboard B3 + Cripto · Dash + Plotly",
                                   style={"margin": "0", "fontSize": "12px", "color": TEXT_SECONDARY}),
                        ], style={"display": "flex", "justifyContent": "space-between",
                                  "padding": "16px 0", "borderTop": f"1px solid {BORDER}"}),

                    ], style={"maxWidth": "1200px", "margin": "0 auto", "padding": "32px"})]),

        ], style={"backgroundColor": PAGE_BG}),

        # Intervalos de atualização
        dcc.Interval(id="interval-movers", interval=60_000,  n_intervals=0),
        dcc.Interval(id="interval-crypto", interval=300_000, n_intervals=0),
    ]
)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------
@app.callback(Output("top-movers-content", "children"),
              Input("interval-movers", "n_intervals"))
def update_movers(_n):
    return build_movers_content(fetch_top_movers())


@app.callback(Output("crypto-content", "children"),
              Input("interval-crypto", "n_intervals"))
def update_crypto(_n):
    return build_crypto_content(fetch_crypto_data())


if __name__ == "__main__":
    app.run(debug=False)
