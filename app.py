import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Dashboard E-commerce", layout="wide")

DATA_PATH = "Ecommerce_Sales.xlsx"


@st.cache_data
def load_data(path):
    df = pd.read_excel(path, parse_dates=["date"])
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    return df


df = load_data(DATA_PATH)

st.title("Dashboard Comercial — E-commerce")

# Filtros
with st.sidebar:
    st.header("Filtros")
    regions = st.multiselect("Região", sorted(df["region"].unique()), default=list(df["region"].unique()))
    categories = st.multiselect("Categoria", sorted(df["category"].unique()), default=list(df["category"].unique()))
    statuses = st.multiselect("Status", sorted(df["status"].unique()), default=list(df["status"].unique()))

mask = df["region"].isin(regions) & df["category"].isin(categories) & df["status"].isin(statuses)
fdf = df[mask]

delivered = fdf[fdf["status"] == "Entregue"]
cancelled = fdf[fdf["status"] == "Cancelado"]

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Receita Entregue", f"R$ {delivered['revenue'].sum():,.2f}")
col2.metric("Pedidos", f"{fdf['order_id'].nunique()}")
col3.metric("Ticket Médio (Entregue)", f"R$ {delivered['revenue'].mean():,.2f}" if len(delivered) else "R$ 0,00")
cancel_rate = len(cancelled) / len(fdf) * 100 if len(fdf) else 0
col4.metric("Taxa de Cancelamento", f"{cancel_rate:.1f}%")

st.divider()

# 1. Receita mensal (linha)
st.subheader("1. Evolução da Receita Mensal")
monthly = fdf.groupby("month")["revenue"].sum().reset_index()
st.plotly_chart(px.line(monthly, x="month", y="revenue", markers=True), use_container_width=True)

c1, c2 = st.columns(2)

# 2. Receita por categoria/produto (top 10)
with c1:
    st.subheader("2. Receita por Categoria")
    cat_rev = fdf.groupby("category")["revenue"].sum().sort_values(ascending=True).reset_index()
    st.plotly_chart(px.bar(cat_rev, x="revenue", y="category", orientation="h"), use_container_width=True)

with c2:
    st.subheader("Top 10 Produtos por Receita")
    prod_rev = fdf.groupby("product")["revenue"].sum().sort_values(ascending=True).tail(10).reset_index()
    st.plotly_chart(px.bar(prod_rev, x="revenue", y="product", orientation="h"), use_container_width=True)

# 3. Receita por região
st.subheader("3. Receita por Região")
region_rev = fdf.groupby("region")["revenue"].sum().sort_values(ascending=False).reset_index()
st.plotly_chart(px.bar(region_rev, x="region", y="revenue"), use_container_width=True)

c3, c4 = st.columns(2)

# 4. Status por categoria (100% stacked)
with c3:
    st.subheader("4. Status do Pedido por Categoria")
    status_cat = fdf.groupby(["category", "status"])["order_id"].count().reset_index(name="count")
    status_cat["pct"] = status_cat.groupby("category")["count"].transform(lambda x: x / x.sum() * 100)
    st.plotly_chart(
        px.bar(status_cat, x="category", y="pct", color="status", barmode="stack"),
        use_container_width=True,
    )

# 5. Receita perdida em cancelamentos (donut)
with c4:
    st.subheader("5. Receita por Status")
    status_rev = fdf.groupby("status")["revenue"].sum().reset_index()
    st.plotly_chart(px.pie(status_rev, names="status", values="revenue", hole=0.5), use_container_width=True)

# 6. Heatmap categoria x região
st.subheader("6. Receita por Categoria x Região (Heatmap)")
heat = fdf.pivot_table(index="region", columns="category", values="revenue", aggfunc="sum", fill_value=0)
st.plotly_chart(px.imshow(heat, text_auto=".0f", aspect="auto"), use_container_width=True)

# 7. Pareto de produtos (cauda longa)
st.subheader("7. Pareto de Produtos")
pareto = fdf.groupby("product")["revenue"].sum().sort_values(ascending=False).reset_index()
pareto["cum_pct"] = pareto["revenue"].cumsum() / pareto["revenue"].sum() * 100
fig_pareto = px.bar(pareto, x="product", y="revenue")
fig_pareto.add_scatter(x=pareto["product"], y=pareto["cum_pct"] * pareto["revenue"].max() / 100,
                       mode="lines+markers", name="% Cumulativo", yaxis="y2")
fig_pareto.update_layout(
    yaxis2=dict(overlaying="y", side="right", title="% Cumulativo", range=[0, 100 * pareto["revenue"].max() / 100]),
)
st.plotly_chart(fig_pareto, use_container_width=True)

# 8. Bubble chart de oportunidades (categoria x região)
st.subheader("8. Oportunidades: Volume x Ticket Médio x Receita")
opp = fdf.groupby(["category", "region"]).agg(
    pedidos=("order_id", "nunique"),
    receita=("revenue", "sum"),
    ticket_medio=("revenue", "mean"),
).reset_index()
st.plotly_chart(
    px.scatter(
        opp, x="pedidos", y="ticket_medio", size="receita", color="category",
        hover_data=["region"], size_max=50,
    ),
    use_container_width=True,
)

st.divider()
st.caption("Dados: Ecommerce_Sales.xlsx")
