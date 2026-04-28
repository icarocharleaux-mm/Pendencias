import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io

st.set_page_config(page_title="Dashboard Online - Filiais", layout="wide")

@st.cache_data
def carregar_dados_online():
    # URL original do SharePoint
    url_sharepoint = "https://diaslog-my.sharepoint.com/:x:/g/personal/icaro_nascimento_mmdeliverytransportes_com_br/IQAsd1mwKCDrSpWC-4kACmmnAYDjJXVif9cFArG3rRXBD44?download=1"
    
    # Cabeçalhos para simular um navegador real
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    try:
        # Fazendo a requisição simulando o navegador
        response = requests.get(url_sharepoint, headers=headers)
        response.raise_for_status() # Verifica se houve erro de conexão
        
        # Transforma o conteúdo baixado em um fluxo de dados que o Pandas entende
        conteudo_arquivo = io.BytesIO(response.content)
        
        # Carrega pulando as 10 primeiras linhas (cabeçalho na 11)
        df = pd.read_excel(conteudo_arquivo, skiprows=10)
        
        # Padroniza nomes das colunas
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Remove linhas totalmente vazias (baseado na coluna filial)
        df = df.dropna(how='all', subset=['filial']) 
        
        return df
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha online: {e}")
        return pd.DataFrame()

# Chamada da função
df = carregar_dados_online()

if not df.empty:
    # Mapeamos os nomes conforme detectado anteriormente
    col_filial = 'filial'
    col_status = 'status das ações'

    # --- Barra Lateral (Filtros) ---
    st.sidebar.header("Filtros")
    
    filiais = df[col_filial].dropna().unique()
    sel_filiais = st.sidebar.multiselect("Filiais", options=filiais, default=filiais)

    status_lista = df[col_status].dropna().unique()
    sel_status = st.sidebar.multiselect("Status", options=status_lista, default=status_lista)

    # Aplica os filtros
    df_f = df[(df[col_filial].isin(sel_filiais)) & (df[col_status].isin(sel_status))]

    # --- Interface Principal ---
    st.title("📊 Gestão de Pendências Online - Filiais")
    
    # Cards de Indicadores
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Ações", len(df_f))
    
    # Lógica de contagem por status (com busca flexível de texto)
    c2.metric("✅ Concluído", len(df_f[df_f[col_status].astype(str).str.contains('oncluid|oncluíd', case=False, na=False)]))
    c3.metric("🚨 Atrasado", len(df_f[df_f[col_status].astype(str).str.contains('trasado', case=False, na=False)]))
    c4.metric("⚠️ Alerta", len(df_f[df_f[col_status].astype(str).str.contains('lerta', case=False, na=False)]))

    st.markdown("---")
    
    # Gráficos
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("Pendências por Unidade")
        fig_filial = px.bar(df_f[col_filial].value_counts().reset_index(), 
                            x=col_filial, y='count', text_auto=True,
                            labels={col_filial: 'Filial', 'count': 'Quantidade'},
                            color_discrete_sequence=['#004d99'])
        st.plotly_chart(fig_filial, use_container_width=True)

    with col_graf2:
        st.subheader("Distribuição do Status")
        df_status_counts = df_f[col_status].value_counts().reset_index()
        df_status_counts.columns = ['Status', 'Quantidade']
        fig_status = px.pie(df_status_counts, names='Status', values='Quantidade', hole=0.4)
        st.plotly_chart(fig_status, use_container_width=True)

    # Tabela detalhada
    st.markdown("---")
    st.subheader("📋 Detalhamento das Ações")
    st.dataframe(df_f, use_container_width=True, hide_index=True)
else:
    st.warning("Aguardando carregamento dos dados da planilha...")
