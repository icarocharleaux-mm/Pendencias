import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de Pendências", layout="wide")

@st.cache_data
def carregar_dados():
    # Carrega pulando as 10 primeiras linhas (cabeçalho na 11)
    df = pd.read_excel("pendencias.xlsx", skiprows=10)
    
    # Padroniza os nomes das colunas (minúsculo e sem espaços sobrando)
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Remove linhas totalmente vazias (baseado na coluna filial)
    df = df.dropna(how='all', subset=['filial']) 
    
    return df

try:
    df = carregar_dados()

    # Mapeamos os nomes EXATOS conforme a leitura do Pandas
    col_filial = 'filial'
    col_status = 'status das ações'

    # --- Barra Lateral (Filtros) ---
    st.sidebar.header("Filtros")
    
    filiais = df[col_filial].dropna().unique()
    sel_filiais = st.sidebar.multiselect("Filiais", options=filiais, default=filiais)

    status_lista = df[col_status].dropna().unique()
    sel_status = st.sidebar.multiselect("Status", options=status_lista, default=status_lista)

    # Aplica os filtros no DataFrame
    df_f = df[(df[col_filial].isin(sel_filiais)) & (df[col_status].isin(sel_status))]

    # --- Tela Principal ---
    st.title("📊 Gestão de Pendências - Filiais")
    
    # Métricas Dinâmicas (Cards no topo)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Ações", len(df_f))
    
    # astype(str) garante que não dará erro se houver campos vazios na planilha
    # 'oncluid|oncluíd' busca com ou sem acento
    c2.metric("✅ Concluído", len(df_f[df_f[col_status].astype(str).str.contains('oncluid|oncluíd', case=False, na=False)]))
    c3.metric("🚨 Atrasado", len(df_f[df_f[col_status].astype(str).str.contains('trasado', case=False, na=False)]))
    c4.metric("⚠️ Alerta", len(df_f[df_f[col_status].astype(str).str.contains('lerta', case=False, na=False)]))

    st.markdown("---")
    
    # --- Gráficos ---
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("Pendências por Unidade")
        if not df_f.empty:
            fig_filial = px.bar(df_f[col_filial].value_counts().reset_index(), 
                         x=col_filial, y='count', text_auto=True,
                         labels={col_filial: 'Filial', 'count': 'Quantidade'},
                         color_discrete_sequence=['#004d99'])
            fig_filial.update_layout(xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_filial, use_container_width=True)
        else:
            st.info("Nenhum dado com os filtros atuais.")

    with col_graf2:
        st.subheader("Distribuição do Status")
        if not df_f.empty:
            df_status = df_f[col_status].value_counts().reset_index()
            df_status.columns = ['Status', 'Quantidade']
            fig_status = px.pie(df_status, names='Status', values='Quantidade', hole=0.4)
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("Nenhum dado com os filtros atuais.")

    # --- Tabela detalhada ---
    st.markdown("---")
    st.subheader("📋 Detalhamento das Ações")
    
    # Mostra a tabela filtrada (apenas as colunas mais importantes para a visualização, se quiser)
    # Se quiser mostrar tudo, basta deixar st.dataframe(df_f, hide_index=True)
    st.dataframe(df_f, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro ao processar a planilha: {e}")