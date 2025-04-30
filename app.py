
import streamlit as st
import pandas as pd
import altair as alt
import math
from datetime import timedelta
import re

st.set_page_config(page_title="Dashboard CDBs", layout="wide")
st.title("📊 CDBs Dashboard")

# Nome do arquivo de dados
file_name = "cdbs_processed_30042025.csv"

@st.cache_data
def load_data():
    return pd.read_csv(file_name, parse_dates=["maturity_date"])

df = load_data()

# Extrair data do nome do arquivo
match = re.search(r'_(\d{8})\.csv$', file_name)
if match:
    data_str = match.group(1)
    formatted_date = f"{data_str[0:2]}/{data_str[2:4]}/{data_str[4:]}"
else:
    formatted_date = "Data desconhecida"

# Badge estilizada
st.markdown(f"""
<span style="background-color: #e1f5fe; color: #0277bd; padding: 6px 12px; border-radius: 10px; font-size: 14px;">
📅 Dados atualizados em {formatted_date}
</span>
""", unsafe_allow_html=True)

# Sidebar - Filtros
st.sidebar.header("Filtros")

all_banks = sorted(df['bank'].dropna().unique())
banks_options = ["Todos"] + all_banks
selected_banks = st.sidebar.multiselect("Banco", banks_options, default=["Todos"])
filtered_banks = all_banks if "Todos" in selected_banks or not selected_banks else selected_banks

all_indexers = sorted(df['indexer'].dropna().unique())
indexers_options = ["Todos"] + all_indexers
selected_indexers = st.sidebar.multiselect("Indexador", indexers_options, default=["Todos"])
filtered_indexers = all_indexers if "Todos" in selected_indexers or not selected_indexers else selected_indexers

# Novo Filtro - Rating
all_ratings = sorted(df['ratingName'].dropna().unique())
ratings_options = ["Todos"] + all_ratings
selected_ratings = st.sidebar.multiselect("Rating", ratings_options, default=["Todos"])
filtered_ratings = all_ratings if "Todos" in selected_ratings or not selected_ratings else selected_ratings

# Filtro por vencimento
st.sidebar.header("Vencimento")
venc_opcoes = {
    "⏱️ Até 6 meses": (0, 182),
    "📅 De 6 meses a 1 ano": (183, 365),
    "📆 De 1 a 2 anos": (366, 730),
    "📈 Acima de 2 anos": (731, 10000),
}
venc_sel = st.sidebar.selectbox("Selecione o prazo de vencimento:", list(venc_opcoes.keys()))

# Aplicar filtros
filtered_df = df[
    df['bank'].isin(filtered_banks) &
    df['indexer'].isin(filtered_indexers) &
    df['ratingName'].isin(filtered_ratings)
].copy()
filtered_df["days_to_maturity"] = (filtered_df["maturity_date"] - pd.Timestamp.today()).dt.days
min_days, max_days = venc_opcoes[venc_sel]
filtered_df = filtered_df[(filtered_df["days_to_maturity"] >= min_days) & (filtered_df["days_to_maturity"] <= max_days)]

# Cards
st.subheader("🏆 Melhores CDBs do Dia")

def render_card(title, df_tipo):
    if not df_tipo.empty:
        row = df_tipo.loc[df_tipo['minTax'].idxmax()]
        bank = row['bank']
        rate = row['minTax']
        venc = row['maturity_date'].strftime('%B/%Y')
        st.markdown(f"""
<div style="background-color: #f8f9fa; color: #000000; padding: 20px; border-radius: 10px;
            border-left: 5px solid #1f77b4; margin-bottom: 10px; height: 200px;">
    <h4 style="margin-bottom: 5px;">📌 <b>{title}</b></h4>
    <p style="margin: 2px 0;"><strong>🏦 Banco:</strong> {bank}</p>
    <p style="margin: 2px 0;"><strong>📈 Taxa:</strong> <span style="color:#1f77b4;">{rate:.2f}% a.a.</span></p>
    <p style="margin: 2px 0;"><strong>📅 Vencimento:</strong> {venc}</p>
</div>
        """, unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    render_card("CDB Pós-fixado", filtered_df[filtered_df['indexer'].str.lower().str.contains("pós")])
with col2:
    render_card("CDB Prefixado", filtered_df[filtered_df['indexer'].str.lower().str.contains("pré")])
with col3:
    render_card("CDB IPCA+", filtered_df[filtered_df['indexer'].str.lower().str.contains("infla")])

# Gráfico
st.subheader("📈 Rentabilidade média por Indexador")

media_rent_df = (
    filtered_df.groupby('indexer', as_index=False)['minTax']
    .mean()
    .rename(columns={'minTax': 'avg_return'})
)

if not media_rent_df.empty:
    y_max_raw = media_rent_df['avg_return'].max()
    y_max_rounded = math.ceil((y_max_raw + 5) / 5) * 5

    chart = alt.Chart(media_rent_df).mark_bar().encode(
        x='indexer:N',
        y=alt.Y('avg_return:Q', scale=alt.Scale(domain=[0, y_max_rounded])),
        tooltip=['indexer', 'avg_return']
    ).properties(width=600, height=400).interactive()

    text = alt.Chart(media_rent_df).mark_text(
        align='center', baseline='bottom', dy=-2
    ).encode(
        x='indexer',
        y='avg_return',
        text=alt.Text('avg_return:Q', format=".2f")
    )

    st.altair_chart(chart + text, use_container_width=True)
else:
    st.info("Nenhum dado disponível para exibir o gráfico.")

# Tabela
st.subheader("📋 Tabela de CDBs")

cols_ordenadas = [
    'bank', 'maturity_date', 'product', 'indexer',
    'ratingName', 'riskScore', 'minTax', 'puMinValue', 'quantityAvailable'
]
nomes_colunas = {
    'bank': 'Banco',
    'maturity_date': 'Vencimento',
    'product': 'Produto',
    'indexer': 'Indexador',
    'ratingName': 'Rating',
    'riskScore': 'Risco',
    'minTax': 'Rentabilidade (% a.a.)',
    'puMinValue': 'Aplicação mínima (R$)',
    'quantityAvailable': 'Quantidade disponível'
}

df_exibir = filtered_df[cols_ordenadas].rename(columns=nomes_colunas)
df_exibir['Vencimento'] = df_exibir['Vencimento'].dt.strftime('%d/%m/%Y')
st.dataframe(df_exibir)
