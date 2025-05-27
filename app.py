
import streamlit as st
import pandas as pd
import altair as alt
import math
from datetime import timedelta
import re
import numpy as np

st.set_page_config(page_title="Dashboard CDBs", layout="wide")
st.title("📊 CDBs Dashboard")

file_name = "cdbs_processed_27052025.csv"

@st.cache_data
def load_data():
    return pd.read_csv(file_name, parse_dates=["maturity_date"])

df = load_data()

match = re.search(r'_(\d{8})\.csv$', file_name)
if match:
    data_str = match.group(1)
    formatted_date = f"{data_str[0:2]}/{data_str[2:4]}/{data_str[4:]}"
else:
    formatted_date = "Data desconhecida"

st.markdown(f"""
<span style="background-color: #e1f5fe; color: #0277bd; padding: 6px 12px; border-radius: 10px; font-size: 14px;">
📅 Dados atualizados em {formatted_date}
</span>
""", unsafe_allow_html=True)

st.sidebar.header("Filtros")

all_banks = sorted(df['bank'].dropna().unique())
banks_options = all_banks
selected_banks = all_banks

banks_to_exclude = st.sidebar.multiselect("Excluir bancos", all_banks)
filtered_banks = [b for b in selected_banks if b not in banks_to_exclude]

all_indexers = sorted(df['indexer'].dropna().unique())
indexers_options = ["Todos"] + all_indexers
selected_indexers = st.sidebar.multiselect("Indexador", indexers_options, default=["Todos"])
filtered_indexers = all_indexers if "Todos" in selected_indexers or not selected_indexers else selected_indexers

all_ratings = sorted(df['ratingName'].dropna().unique())
ratings_options = ["Todos"] + all_ratings
selected_ratings = st.sidebar.multiselect("Rating", ratings_options, default=["Todos"])
filtered_ratings = all_ratings if "Todos" in selected_ratings or not selected_ratings else selected_ratings

st.sidebar.header("Vencimento")
venc_opcoes = {
    "⏱️ Até 6 meses": (0, 182),
    "📅 De 6 meses a 1 ano": (183, 365),
    "📆 De 1 a 2 anos": (366, 730),
    "📈 Acima de 2 anos": (731, 10000),
}
venc_sel = st.sidebar.selectbox("Selecione o prazo de vencimento:", list(venc_opcoes.keys()))

filtered_df = df[
    df['bank'].isin(filtered_banks) &
    df['indexer'].isin(filtered_indexers) &
    df['ratingName'].isin(filtered_ratings)
].copy()
filtered_df["days_to_maturity"] = (filtered_df["maturity_date"] - pd.Timestamp.today()).dt.days
min_days, max_days = venc_opcoes[venc_sel]
filtered_df = filtered_df[(filtered_df["days_to_maturity"] >= min_days) & (filtered_df["days_to_maturity"] <= max_days)]

st.subheader("🏆 Melhores CDBs do Dia")

def render_card(title, df_tipo):
    if not df_tipo.empty:
        row = df_tipo.loc[df_tipo['minTax'].idxmax()]
        bank = row['bank']
        rate = row['minTax']
        mes_en = row['maturity_date'].strftime('%B')
        meses_pt = {
            'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
            'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
            'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
            'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
        }
        mes_pt = meses_pt.get(mes_en, mes_en)
        venc = f"{mes_pt}/{row['maturity_date'].year}"
        venc = venc.capitalize()
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
        x=alt.X('indexer:N', title='Indexador'),
        y=alt.Y('avg_return:Q', title='Rentabilidade média (% a.a.)', scale=alt.Scale(domain=[0, y_max_rounded])),
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
st.dataframe(df_exibir, hide_index=True)

st.subheader("💰 Simulador de Rendimento")

with st.form("simulador_rendimento_form"):
    valor_aplicado = st.number_input("Valor a ser investido (R$)", min_value=100.0, step=100.0, value=5000.0)
    cdi = st.number_input(
        "CDI anual (%) - Informe a média do CDI dos últimos 12 meses ou a projeção para o período.",
        min_value=0.0,
        value=10.65,
        step=0.01,
        #help="Informe a média do CDI dos últimos 12 meses ou a projeção para o período."
    )

    ipca = st.number_input(
        "IPCA anual (%) - Informe a média do IPCA dos últimos 12 meses ou a expectativa de inflação para o período.",
        min_value=0.0,
        value=4.5,
        step=0.01,
        #help="Informe a média do IPCA dos últimos 12 meses ou a expectativa de inflação para o período."
    )
    simular = st.form_submit_button("Simular")

def calcular_ir_regressivo(dias):
    if dias <= 180:
        return 0.225
    elif dias <= 360:
        return 0.20
    elif dias <= 720:
        return 0.175
    else:
        return 0.15

def render_simulador_card(nome_indexador, melhor, valor_aplicado, cdi, ipca):
    taxa_raw = melhor['minTax']
    indexador = melhor['indexer'].lower()

    if "pós" in indexador:
        taxa = (taxa_raw / 100) * (cdi / 100)
    elif "infla" in indexador:
        taxa = (ipca / 100) + (taxa_raw / 100)
    else:
        taxa = taxa_raw / 100

    dias = melhor['days_to_maturity']
    data_vencimento = melhor['maturity_date'].date()
    data_hoje = pd.Timestamp.today().date()
    dias_uteis = np.busday_count(data_hoje, data_vencimento)
    
    rendimento_bruto = valor_aplicado * ((1 + taxa) ** (dias_uteis / 252 ) - 1)
    aliquota_ir = calcular_ir_regressivo(dias)
    imposto = rendimento_bruto * aliquota_ir
    rendimento_liquido = rendimento_bruto - imposto
    valor_total = valor_aplicado + rendimento_liquido
    vencimento = melhor['maturity_date'].date().strftime('%d/%m/%Y')

##<div style="background-color: #f8f9fa; color: #000000; padding: 20px; border-radius: 10px;
##            border-left: 5px solid #1f77b4; margin-bottom: 10px; height: 200px;">

    st.markdown(f"""
<div style="background-color: #f1f8e9; color: #000000; padding: 20px; border-radius: 10px;
            border-left: 5px solid #1f77b4; margin-bottom: 10px; height: auto;">
    <h4 style="margin-bottom: 5px;">💡 <b>{nome_indexador}</b></h4>
    <p style="margin: 2px 0;"><strong>🏦 Banco:</strong> {melhor['bank']}</p>
    <p style="margin: 2px 0;"><strong>📄 Produto:</strong> {melhor['product']}</p>
    <p style="margin: 2px 0;"><strong>📈 Taxa:</strong> {melhor['minTax']:.2f}% a.a.</p>
    <p style="margin: 2px 0;"><strong>📆 Vencimento:</strong> {vencimento} ({dias} dias)</p>
    <hr style="margin: 10px 0;">
    <p style="margin: 2px 0;"><strong>💵 Rendimento bruto:</strong> R$ {rendimento_bruto:,.2f}</p>
    <p style="margin: 2px 0;"><strong>🧾 IR ({aliquota_ir*100:.1f}%):</strong> R$ {imposto:,.2f}</p>
    <p style="margin: 2px 0;"><strong>💰 Rendimento líquido:</strong> R$ {rendimento_liquido:,.2f}</p>
    <p style="margin: 2px 0;"><strong>📊 Valor final líquido:</strong> <b>R$ {valor_total:,.2f}</b></p>
</div>
""", unsafe_allow_html=True)

if simular:
    st.markdown("### 📊 Resultados da Simulação")
    tipos = [
        ("CDB Pós-fixado", filtered_df[filtered_df['indexer'].str.lower().str.contains("pós")]),
        ("CDB Prefixado", filtered_df[filtered_df['indexer'].str.lower().str.contains("pré")]),
        ("CDB IPCA+", filtered_df[filtered_df['indexer'].str.lower().str.contains("infla")]),
    ]
    col1, col2, col3 = st.columns(3)
    colunas = [col1, col2, col3]
    for i, (nome_indexador, df_tipo) in enumerate(tipos):
        with colunas[i]:
            if not df_tipo.empty:
                melhor = df_tipo.loc[df_tipo['minTax'].idxmax()]
                render_simulador_card(nome_indexador, melhor, valor_aplicado, cdi, ipca)
            else:
                st.warning(f"Nenhum CDB disponível para o tipo {nome_indexador}.")
                
with st.expander("ℹ️ Tabela de Imposto de Renda (IR) regressivo para CDBs"):
    st.markdown("""
    | Dias até o vencimento | Alíquota de IR |
    |------------------------|----------------|
    | Até 180 dias           | 22,5%          |
    | De 181 a 360 dias      | 20,0%          |
    | De 361 a 720 dias      | 17,5%          |
    | Acima de 720 dias      | 15,0%          |

    A alíquota do imposto de renda é aplicada somente sobre o rendimento bruto.
    """)

