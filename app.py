import plotly.graph_objects as go
from dash import Dash, dcc, html, dash_table

from data import fetch_data, calc_cumulative_return, calc_monthly_volume, build_summary_table

# --- Cores das ações ---
COLORS = {"Petrobras": "#009c3b", "Itaú": "#0047CC", "Vale": "#0077b6"}

# --- Design tokens ---
PAGE_BG = "#f0f2f5"
CARD_BG = "#ffffff"
HEADER_BG = "#0d1b3e"
BORDER = "#e2e8f0"
TEXT_PRIMARY = "#1a2744"
TEXT_SECONDARY = "#64748b"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

TICKER_MAP = {"Petrobras": "PETR4", "Itaú": "ITUB4", "Vale": "VALE3"}

CHART_BASE = dict(
    plot_bgcolor=CARD_BG,
    paper_bgcolor=CARD_BG,
    font=dict(family=FONT, color=TEXT_PRIMARY, size=12),
    xaxis=dict(
        gridcolor="#f1f5f9",
        linecolor=BORDER,
        showline=True,
        tickfont=dict(size=11, color=TEXT_SECONDARY),
    ),
    yaxis=dict(
        gridcolor="#f1f5f9",
        linecolor=BORDER,
        showline=True,
        tickfont=dict(size=11, color=TEXT_SECONDARY),
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        bgcolor="rgba(0,0,0,0)",
        font=dict(size=12),
    ),
    hovermode="x unified",
    margin=dict(l=60, r=20, t=10, b=50),
)

print("Baixando dados das ações... Aguarde.")
data = fetch_data()
cumulative = calc_cumulative_return(data)
monthly_vol = calc_monthly_volume(data)
summary = build_summary_table(data)
print("Dados carregados com sucesso.")

# --- Gráfico 1: Preço de Fechamento Ajustado ---
fig_price = go.Figure()
for name, df in data.items():
    close = df["Close"].dropna()
    fig_price.add_trace(go.Scatter(
        x=close.index,
        y=close.values,
        mode="lines",
        name=name,
        line=dict(color=COLORS[name], width=2),
    ))
fig_price.update_layout(**CHART_BASE)

# --- Gráfico 2: Performance Acumulada (%) ---
fig_perf = go.Figure()
for name in cumulative.columns:
    fig_perf.add_trace(go.Scatter(
        x=cumulative.index,
        y=cumulative[name],
        mode="lines",
        name=name,
        line=dict(color=COLORS[name], width=2),
    ))
fig_perf.add_hline(y=0, line_dash="dash", line_color="#94a3b8", line_width=1)
fig_perf.update_layout(**CHART_BASE, yaxis_ticksuffix="%")

# --- Gráfico 3: Volume Médio Diário por Mês ---
fig_vol = go.Figure()
for name in monthly_vol.columns:
    fig_vol.add_trace(go.Bar(
        x=monthly_vol.index,
        y=monthly_vol[name],
        name=name,
        marker_color=COLORS[name],
        marker_line_width=0,
    ))
fig_vol.update_layout(**CHART_BASE, barmode="group")


# --- Componentes de layout ---
def section_card(title, subtitle, body):
    return html.Div([
        html.Div([
            html.H3(title, style={
                "margin": "0 0 4px 0",
                "fontSize": "15px",
                "fontWeight": "600",
                "color": TEXT_PRIMARY,
            }),
            html.P(subtitle, style={
                "margin": "0",
                "fontSize": "12px",
                "color": TEXT_SECONDARY,
            }),
        ], style={"padding": "20px 24px 14px", "borderBottom": f"1px solid {BORDER}"}),
        html.Div(body, style={"padding": "8px"}),
    ], className="card", style={
        "backgroundColor": CARD_BG,
        "borderRadius": "12px",
        "border": f"1px solid {BORDER}",
        "boxShadow": "0 1px 4px rgba(0,0,0,0.06)",
        "marginBottom": "24px",
    })


def kpi_card(row):
    empresa = row["Ação"]
    variacao_str = row["Variação no Ano (%)"]
    is_positive = variacao_str.startswith("+")
    var_color = "#16a34a" if is_positive else "#dc2626"
    var_bg = "#f0fdf4" if is_positive else "#fef2f2"
    ticker = TICKER_MAP.get(empresa, empresa)

    return html.Div([
        html.Div([
            html.Span(ticker, style={
                "fontSize": "11px",
                "fontWeight": "700",
                "color": "#ffffff",
                "backgroundColor": COLORS[empresa],
                "padding": "3px 9px",
                "borderRadius": "5px",
                "letterSpacing": "0.3px",
            }),
            html.Span(variacao_str, style={
                "fontSize": "12px",
                "fontWeight": "600",
                "color": var_color,
                "backgroundColor": var_bg,
                "padding": "3px 9px",
                "borderRadius": "5px",
            }),
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "14px"}),

        html.P(empresa, style={"fontSize": "13px", "color": TEXT_SECONDARY, "margin": "0 0 4px 0", "fontWeight": "400"}),
        html.P(f"R$ {row['Preço Atual (R$)']}", style={
            "fontSize": "28px",
            "fontWeight": "700",
            "color": TEXT_PRIMARY,
            "margin": "0 0 16px 0",
            "letterSpacing": "-0.5px",
        }),

        html.Div([
            html.Div([
                html.Span("Abertura", style={"fontSize": "10px", "color": TEXT_SECONDARY, "display": "block", "marginBottom": "2px", "textTransform": "uppercase", "letterSpacing": "0.4px"}),
                html.Span(f"R$ {row['Preço Inicial (R$)']}", style={"fontSize": "13px", "fontWeight": "500", "color": TEXT_PRIMARY}),
            ]),
            html.Div([
                html.Span("Máximo", style={"fontSize": "10px", "color": TEXT_SECONDARY, "display": "block", "marginBottom": "2px", "textTransform": "uppercase", "letterSpacing": "0.4px"}),
                html.Span(f"R$ {row['Máximo (R$)']}", style={"fontSize": "13px", "fontWeight": "500", "color": "#16a34a"}),
            ]),
            html.Div([
                html.Span("Mínimo", style={"fontSize": "10px", "color": TEXT_SECONDARY, "display": "block", "marginBottom": "2px", "textTransform": "uppercase", "letterSpacing": "0.4px"}),
                html.Span(f"R$ {row['Mínimo (R$)']}", style={"fontSize": "13px", "fontWeight": "500", "color": "#dc2626"}),
            ]),
        ], style={"display": "flex", "justifyContent": "space-between", "paddingTop": "14px", "borderTop": f"1px solid {BORDER}"}),
    ], className="kpi-card", style={
        "backgroundColor": CARD_BG,
        "borderRadius": "12px",
        "border": f"1px solid {BORDER}",
        "boxShadow": "0 1px 4px rgba(0,0,0,0.06)",
        "padding": "20px",
        "flex": "1",
        "minWidth": "220px",
        "transition": "all 0.2s ease",
    })


# --- App Dash ---
app = Dash(__name__)
app.title = "Dashboard de Ações B3 — 2025"

kpi_cards = [kpi_card(row) for row in summary.to_dict("records")]

app.layout = html.Div(
    style={"fontFamily": FONT, "backgroundColor": PAGE_BG, "minHeight": "100vh"},
    children=[

        # Header
        html.Div([
            html.Div([
                html.Div([
                    html.H1("Dashboard B3", style={
                        "margin": "0",
                        "fontSize": "22px",
                        "fontWeight": "700",
                        "color": "#ffffff",
                        "letterSpacing": "-0.3px",
                    }),
                    html.P("Petrobras (PETR4) · Itaú (ITUB4) · Vale (VALE3) · 2025", style={
                        "margin": "4px 0 0",
                        "fontSize": "13px",
                        "color": "rgba(255,255,255,0.55)",
                    }),
                ]),
                html.Span("B3 — Bolsa do Brasil", style={
                    "fontSize": "12px",
                    "fontWeight": "500",
                    "color": "rgba(255,255,255,0.75)",
                    "backgroundColor": "rgba(255,255,255,0.10)",
                    "padding": "6px 14px",
                    "borderRadius": "20px",
                    "border": "1px solid rgba(255,255,255,0.15)",
                }),
            ], style={
                "maxWidth": "1200px",
                "margin": "0 auto",
                "padding": "22px 32px",
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
            }),
        ], style={"backgroundColor": HEADER_BG, "borderBottom": "1px solid rgba(255,255,255,0.07)"}),

        # Conteúdo principal
        html.Div([

            # KPI Cards
            html.Div(kpi_cards, style={
                "display": "flex",
                "gap": "20px",
                "marginBottom": "24px",
                "flexWrap": "wrap",
            }),

            # Gráfico 1
            section_card(
                "Preço de Fechamento Ajustado",
                "Evolução do preço de fechamento (R$) ao longo de 2025",
                dcc.Graph(figure=fig_price, config={"displayModeBar": False}),
            ),

            # Gráfico 2
            section_card(
                "Performance Acumulada",
                "Retorno percentual acumulado desde 01/01/2025",
                dcc.Graph(figure=fig_perf, config={"displayModeBar": False}),
            ),

            # Gráfico 3
            section_card(
                "Volume Médio Diário",
                "Volume médio de negociações por mês em 2025",
                dcc.Graph(figure=fig_vol, config={"displayModeBar": False}),
            ),

            # Tabela resumo
            html.Div([
                html.Div([
                    html.H3("Resumo das Ações", style={
                        "margin": "0 0 4px 0",
                        "fontSize": "15px",
                        "fontWeight": "600",
                        "color": TEXT_PRIMARY,
                    }),
                    html.P("Métricas consolidadas do período", style={
                        "margin": "0",
                        "fontSize": "12px",
                        "color": TEXT_SECONDARY,
                    }),
                ], style={"padding": "20px 24px 14px", "borderBottom": f"1px solid {BORDER}"}),

                dash_table.DataTable(
                    data=summary.to_dict("records"),
                    columns=[{"name": col, "id": col} for col in summary.columns],
                    style_table={"overflowX": "auto"},
                    style_header={
                        "backgroundColor": "#f8fafc",
                        "color": TEXT_SECONDARY,
                        "fontWeight": "600",
                        "textAlign": "center",
                        "fontSize": "11px",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.5px",
                        "border": "none",
                        "borderBottom": f"2px solid {BORDER}",
                        "padding": "14px 16px",
                        "fontFamily": FONT,
                    },
                    style_cell={
                        "textAlign": "center",
                        "padding": "14px 16px",
                        "fontSize": "14px",
                        "fontFamily": FONT,
                        "color": TEXT_PRIMARY,
                        "border": "none",
                        "borderBottom": f"1px solid {BORDER}",
                    },
                    style_data_conditional=[
                        {"if": {"row_index": "odd"}, "backgroundColor": "#f8fafc"},
                    ],
                    style_as_list_view=True,
                ),
            ], className="card", style={
                "backgroundColor": CARD_BG,
                "borderRadius": "12px",
                "border": f"1px solid {BORDER}",
                "boxShadow": "0 1px 4px rgba(0,0,0,0.06)",
                "marginBottom": "24px",
                "overflow": "hidden",
            }),

            # Footer
            html.Div([
                html.P("Dados obtidos via Yahoo Finance · yfinance", style={
                    "margin": "0",
                    "fontSize": "12px",
                    "color": TEXT_SECONDARY,
                }),
                html.P("Dashboard B3 2025 · Desenvolvido com Dash + Plotly", style={
                    "margin": "0",
                    "fontSize": "12px",
                    "color": TEXT_SECONDARY,
                }),
            ], style={
                "display": "flex",
                "justifyContent": "space-between",
                "padding": "16px 0",
                "borderTop": f"1px solid {BORDER}",
            }),

        ], style={"maxWidth": "1200px", "margin": "0 auto", "padding": "32px"}),

    ]
)

if __name__ == "__main__":
    app.run(debug=False)
