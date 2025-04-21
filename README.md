
# 📊 Dashboard CDBs

Dashboard interativo para visualização e comparação de CDBs com base em vencimento, indexador e rentabilidade.  
Desenvolvido com Python e Streamlit.

## 🔍 Funcionalidades

- Filtro por banco, indexador e vencimento
- Destaque dos melhores CDBs do dia (pós-fixado, prefixado e IPCA+)
- Tabela organizada com vencimento e rentabilidade
- Gráfico com rentabilidade média por tipo de indexador

## 🚀 Como executar localmente

1. Clone este repositório:
```bash
git clone https://github.com/seu-usuario/dashboard-cdbs.git
cd dashboard-cdbs
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute o app:
```bash
streamlit run app.py
```

## 🌐 Deploy com Streamlit Cloud

Você pode publicar gratuitamente criando um repositório público no GitHub  
e conectando com sua conta no [Streamlit Cloud](https://streamlit.io/cloud).

## 📁 Estrutura esperada

- `app.py` → aplicação principal
- `cdbs_processed.csv` → base de dados com CDBs atualizada
- `requirements.txt` → dependências

## 🛡️ Licença

Este projeto é open-source e está disponível sob a licença MIT.
