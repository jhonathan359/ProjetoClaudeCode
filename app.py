import plotly.graph_objects as go
from dash import Dash, dcc, html, dash_table

from data import fetch_data, calc_cumulative_return, calc_monthly_volume, build_summary_table

COLORS = {"Petrobras": "#009c3b", "Itaú": "#003399", "Vale": "#003f72"}

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
fig_price.update_layout(
    title="Preço de Fechamento Ajustado — 2025",
    xaxis_title="Data",
    yaxis_title="Preço (R$)",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    plot_bgcolor="#f9f9f9",
    paper_bgcolor="#ffffff",
)

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
fig_perf.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
fig_perf.update_layout(
    title="Performance Acumulada em 2025 (%)",
    xaxis_title="Data",
    yaxis_title="Retorno Acumulado (%)",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    plot_bgcolor="#f9f9f9",
    paper_bgcolor="#ffffff",
)

# --- Gráfico 3: Volume Médio Diário por Mês ---
fig_vol = go.Figure()
for name in monthly_vol.columns:
    fig_vol.add_trace(go.Bar(
        x=monthly_vol.index,
        y=monthly_vol[name],
        name=name,
        marker_color=COLORS[name],
    ))
fig_vol.update_layout(
    title="Volume Médio Diário por Mês — 2025",
    xaxis_title="Mês",
    yaxis_title="Volume Médio",
    barmode="group",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    plot_bgcolor="#f9f9f9",
    paper_bgcolor="#ffffff",
)

# --- App Dash ---
app = Dash(__name__)
app.title = "Dashboard de Ações B3 — 2025"

app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "maxWidth": "1200px", "margin": "0 auto", "padding": "20px"},
    children=[
        html.H1("Dashboard de Cotações — B3 2025", style={"textAlign": "center", "color": "#333"}),
        html.P(
            "Análise comparativa de Petrobras (PETR4), Itaú (ITUB4) e Vale (VALE3) ao longo de 2025.",
            style={"textAlign": "center", "color": "#666", "marginBottom": "30px"},
        ),

        dcc.Graph(figure=fig_price, style={"marginBottom": "30px"}),
        dcc.Graph(figure=fig_perf, style={"marginBottom": "30px"}),
        dcc.Graph(figure=fig_vol, style={"marginBottom": "30px"}),

        html.H2("Resumo das Ações", style={"color": "#333"}),
        dash_table.DataTable(
            data=summary.to_dict("records"),
            columns=[{"name": col, "id": col} for col in summary.columns],
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "#003399",
                "color": "white",
                "fontWeight": "bold",
                "textAlign": "center",
            },
            style_cell={
                "textAlign": "center",
                "padding": "10px",
                "fontSize": "14px",
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#f2f2f2"},
            ],
        ),
    ],
)

if __name__ == "__main__":
    app.run(debug=False)
