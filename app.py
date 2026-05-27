import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
from datetime import datetime

# ── Paleta Dias+ ──────────────────────────────────────────────────────────────
TEAL_PRIMARY  = "#2DC5B4"
TEAL_DEEP     = "#0E7A8C"
TEAL_MEDIUM   = "#5BA8B8"
DARK_BG       = "#0B3040"
DARK_BG2      = "#0D3A4E"
SALMON        = "#C47A77"
YELLOW_ALERT  = "#E8B84B"
WHITE         = "#FFFFFF"
NEUTRAL_700   = "#4A6670"
NEUTRAL_300   = "#D8E1E5"

COR_STATUS = {
    "ATRASADO":  SALMON,
    "ALERTA":    YELLOW_ALERT,
    "PENDENTE":  TEAL_MEDIUM,
    "CONCLUÍDO": TEAL_PRIMARY,
}

st.set_page_config(
    page_title="Pendências Regulatórias · Dias+",
    page_icon="➕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS Dias+ ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;600;700;800;900&display=swap');

  /* fundo e tipografia base */
  html, body, [class*="css"] {{
    font-family: 'Barlow Condensed', sans-serif !important;
    background-color: {DARK_BG} !important;
    color: {WHITE} !important;
  }}
  .main .block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; }}

  /* sidebar */
  [data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {DARK_BG} 0%, {DARK_BG2} 100%) !important;
    border-right: 1px solid rgba(45,197,180,0.25) !important;
  }}
  [data-testid="stSidebar"] * {{ color: {WHITE} !important; }}
  [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {{
    background-color: {TEAL_DEEP} !important;
  }}

  /* cabeçalho hero */
  .hero-header {{
    background: linear-gradient(135deg, {DARK_BG} 0%, {TEAL_DEEP} 100%);
    border-bottom: 3px solid {TEAL_PRIMARY};
    padding: 1.4rem 2rem 1.2rem 2rem;
    border-radius: 0 0 16px 16px;
    margin-bottom: 1.4rem;
  }}
  .hero-header h1 {{
    font-size: 2.2rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: {WHITE};
    margin: 0 0 .15rem 0;
  }}
  .hero-header span.tag {{
    background: {TEAL_PRIMARY};
    color: {DARK_BG};
    font-weight: 700;
    font-size: .8rem;
    letter-spacing: .08em;
    text-transform: uppercase;
    border-radius: 999px;
    padding: 3px 12px;
  }}
  .hero-header small {{ color: rgba(255,255,255,.55); font-size: .85rem; }}

  /* cards KPI */
  [data-testid="metric-container"] {{
    background: rgba(255,255,255,0.07) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 14px !important;
    padding: 1rem 1.2rem !important;
  }}
  [data-testid="metric-container"] label {{
    color: rgba(255,255,255,.6) !important;
    font-size: .8rem !important;
    letter-spacing: .07em;
    text-transform: uppercase;
  }}
  [data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size: 2.4rem !important;
    font-weight: 900 !important;
    color: {WHITE} !important;
  }}

  /* subtítulos de seção */
  .section-title {{
    font-size: 1.05rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: {TEAL_PRIMARY};
    border-left: 4px solid {TEAL_PRIMARY};
    padding-left: 10px;
    margin: 1.4rem 0 .7rem 0;
  }}

  /* tabela */
  [data-testid="stDataFrame"] {{ border-radius: 12px; overflow: hidden; }}
  [data-testid="stDataFrame"] th {{
    background-color: {DARK_BG2} !important;
    color: {TEAL_PRIMARY} !important;
    font-weight: 700 !important;
    letter-spacing: .06em;
    text-transform: uppercase;
  }}

  /* divider */
  hr {{ border-color: rgba(45,197,180,0.2) !important; }}

  /* botão de export */
  .stDownloadButton > button {{
    background: {TEAL_PRIMARY} !important;
    color: {DARK_BG} !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    border: none !important;
  }}
  .stDownloadButton > button:hover {{
    background: {TEAL_DEEP} !important;
    color: {WHITE} !important;
  }}

  /* scrollbar */
  ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
  ::-webkit-scrollbar-track {{ background: {DARK_BG}; }}
  ::-webkit-scrollbar-thumb {{ background: {TEAL_DEEP}; border-radius: 4px; }}
</style>
""", unsafe_allow_html=True)

# ── Carregamento de dados ──────────────────────────────────────────────────────
URL_PADRAO    = "https://1drv.ms/x/c/6b2fcbf5f5526df1/IQDUu6abClz1TaxKoOFMsGzRAZ9EeqagjmL0UE7-KNygSWc?e=Roqh7k&download=1"
ARQUIVO_LOCAL = "pendencias.xlsx"

def _processar_excel(conteudo_bytes):
    df = pd.read_excel(io.BytesIO(conteudo_bytes), skiprows=10)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.dropna(how="all")
    for col in ["DATA", "QUANDO", "DATA CONCLUSÃO"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    if "STATUS DAS AÇÕES" in df.columns:
        df["STATUS DAS AÇÕES"] = df["STATUS DAS AÇÕES"].astype(str).str.strip().str.upper()
    if "PRIORIDADE" in df.columns:
        df["PRIORIDADE"] = df["PRIORIDADE"].astype(str).str.strip().str.upper()
    return df

@st.cache_data(ttl=300)          # recarrega a cada 5 min automaticamente
def carregar_online(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    r = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
    r.raise_for_status()
    return r.content

@st.cache_data
def carregar_local():
    import os
    if os.path.exists(ARQUIVO_LOCAL):
        with open(ARQUIVO_LOCAL, "rb") as f:
            return f.read()
    return None

# --- Sidebar: upload de emergência + recarregar ---
with st.sidebar:
    arquivo_upload = st.file_uploader(
        "Substituir arquivo manualmente",
        type=["xlsx"],
        help="Use apenas se o OneDrive estiver indisponível.",
    )
    st.markdown("---")

# --- Carregamento automático com fallbacks ---
df_raw     = pd.DataFrame()
ts_carga   = None
fonte_dados = ""

if arquivo_upload is not None:
    # Prioridade 1: upload manual na sidebar
    try:
        df_raw = _processar_excel(arquivo_upload.read())
        ts_carga = datetime.now()
        fonte_dados = f"upload manual · {arquivo_upload.name}"
    except Exception as e:
        st.error(f"Erro ao ler arquivo enviado: {e}")

if df_raw.empty:
    # Prioridade 2: OneDrive (URL fixa, cache 5 min)
    try:
        conteudo = carregar_online(URL_PADRAO)
        df_raw = _processar_excel(conteudo)
        ts_carga = datetime.now()
        fonte_dados = "OneDrive (atualização automática)"
    except Exception as e:
        st.sidebar.warning(f"OneDrive indisponível: {e}")

if df_raw.empty:
    # Prioridade 3: arquivo local como último recurso
    conteudo_local = carregar_local()
    if conteudo_local:
        try:
            df_raw = _processar_excel(conteudo_local)
            ts_carga = datetime.now()
            fonte_dados = f"arquivo local ({ARQUIVO_LOCAL})"
        except Exception as e:
            st.error(f"Erro ao ler arquivo local: {e}")

# ── Hero header ───────────────────────────────────────────────────────────────
ts_str = ts_carga.strftime("%d/%m/%Y  %H:%M") if ts_carga else "—"
st.markdown(f"""
<div class="hero-header">
  <h1>Pendências Regulatórias <span class="tag">Filiais</span></h1>
  <small>Última atualização: {ts_str} &nbsp;·&nbsp; diaslog.com.br</small>
</div>
""", unsafe_allow_html=True)

if df_raw.empty:
    st.warning("Aguardando dados da planilha...")
    st.stop()

# ── Colunas disponíveis ────────────────────────────────────────────────────────
COL_FILIAL    = "FILIAL"
COL_STATUS    = "STATUS DAS AÇÕES"
COL_PRIORIDADE = "PRIORIDADE"
COL_RESP      = "RESPONSÁVEL (STAKEHOLDER)"
COL_ASSUNTO   = "ASSUNTO (WHAT)"
COL_ACAO      = "AÇÕES (HOW)"
COL_QUANDO    = "QUANDO"
COL_CONCLUSAO = "DATA CONCLUSÃO"
COL_FOLLOWUP  = "FOLLOW UP"

# Normaliza nome do responsável se vier diferente
if COL_RESP not in df_raw.columns:
    resp_cols = [c for c in df_raw.columns if "RESPONS" in c]
    COL_RESP = resp_cols[0] if resp_cols else None

# ── Sidebar filtros ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<h3 style='color:{TEAL_PRIMARY};text-transform:uppercase;letter-spacing:.1em;'>Filtros</h3>", unsafe_allow_html=True)

    filiais = sorted(df_raw[COL_FILIAL].dropna().unique())
    sel_filiais = st.multiselect("Filial", options=filiais, default=filiais)

    status_opts = sorted(df_raw[COL_STATUS].dropna().unique())
    sel_status = st.multiselect("Status", options=status_opts, default=status_opts)

    prio_opts = sorted(df_raw[COL_PRIORIDADE].dropna().unique())
    sel_prio = st.multiselect("Prioridade", options=prio_opts, default=prio_opts)

    if COL_RESP:
        resp_opts = sorted(df_raw[COL_RESP].dropna().unique())
        sel_resp = st.multiselect("Responsável", options=resp_opts, default=resp_opts)
    else:
        sel_resp = []

    st.markdown("---")
    if st.button("🔄 Recarregar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if fonte_dados:
        st.caption(f"📡 {fonte_dados}")
    if ts_carga:
        st.caption(f"🕐 {ts_carga.strftime('%d/%m/%Y %H:%M')}")

# ── Filtragem ─────────────────────────────────────────────────────────────────
mask = (
    df_raw[COL_FILIAL].isin(sel_filiais) &
    df_raw[COL_STATUS].isin(sel_status) &
    df_raw[COL_PRIORIDADE].isin(sel_prio)
)
if COL_RESP and sel_resp:
    mask &= df_raw[COL_RESP].isin(sel_resp)

df = df_raw[mask].copy()

# ── Cálculo de atraso ─────────────────────────────────────────────────────────
hoje = pd.Timestamp(datetime.now().date())
if COL_CONCLUSAO in df.columns:
    df["DIAS ATRASO"] = df.apply(
        lambda r: max(0, (hoje - r[COL_CONCLUSAO]).days)
        if r[COL_STATUS] == "ATRASADO" and pd.notna(r[COL_CONCLUSAO]) else None,
        axis=1
    )

# ── KPIs ──────────────────────────────────────────────────────────────────────
total       = len(df)
concluidos  = (df[COL_STATUS] == "CONCLUÍDO").sum()
atrasados   = (df[COL_STATUS] == "ATRASADO").sum()
alertas     = (df[COL_STATUS] == "ALERTA").sum()
pendentes   = (df[COL_STATUS] == "PENDENTE").sum()
prio_alta   = (df[COL_PRIORIDADE] == "ALTO").sum()
pct_ok      = f"{100*concluidos/total:.0f}%" if total else "—"

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total de Ações", total)
c2.metric("Concluído", concluidos, delta=pct_ok)
c3.metric("Atrasado", int(atrasados))
c4.metric("Alerta", int(alertas))
c5.metric("Pendente", int(pendentes))
c6.metric("Prioridade Alta", int(prio_alta))

st.markdown("<hr>", unsafe_allow_html=True)

# ── Gráficos ───────────────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Barlow Condensed", color=WHITE),
    margin=dict(t=30, b=10, l=10, r=10),
    xaxis=dict(gridcolor="rgba(255,255,255,0.08)", linecolor="rgba(255,255,255,0.15)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.08)", linecolor="rgba(255,255,255,0.15)"),
)

st.markdown("<div class='section-title'>Visão por Filial e Status</div>", unsafe_allow_html=True)
col_g1, col_g2 = st.columns([3, 2])

with col_g1:
    # Barras empilhadas: Status por Filial
    df_cross = (
        df.groupby([COL_FILIAL, COL_STATUS])
        .size()
        .reset_index(name="QTD")
    )
    ordem_status = ["ATRASADO", "ALERTA", "PENDENTE", "CONCLUÍDO"]
    cores_map = {s: COR_STATUS.get(s, TEAL_MEDIUM) for s in ordem_status}
    fig_stack = px.bar(
        df_cross, x=COL_FILIAL, y="QTD", color=COL_STATUS,
        text_auto=True,
        color_discrete_map=cores_map,
        category_orders={COL_STATUS: ordem_status},
        labels={COL_FILIAL: "", "QTD": "Ações"},
        title="Ações por Filial",
    )
    fig_stack.update_traces(marker_line_width=0)
    fig_stack.update_layout(**PLOTLY_LAYOUT, barmode="stack",
                             legend=dict(orientation="h", y=-0.15))
    st.plotly_chart(fig_stack, use_container_width=True)

with col_g2:
    # Donut de status
    df_st = df[COL_STATUS].value_counts().reset_index()
    df_st.columns = ["Status", "QTD"]
    fig_donut = px.pie(
        df_st, names="Status", values="QTD",
        hole=0.55,
        color="Status",
        color_discrete_map=COR_STATUS,
        title="Distribuição de Status",
    )
    fig_donut.update_traces(textfont_color=WHITE, marker=dict(line=dict(color=DARK_BG, width=2)))
    fig_donut.update_layout(**PLOTLY_LAYOUT, showlegend=True,
                             legend=dict(orientation="h", y=-0.1))
    st.plotly_chart(fig_donut, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

col_g3, col_g4 = st.columns(2)

with col_g3:
    st.markdown("<div class='section-title'>Pendências por Prioridade</div>", unsafe_allow_html=True)
    df_prio = df[COL_PRIORIDADE].value_counts().reset_index()
    df_prio.columns = ["Prioridade", "QTD"]
    cores_prio = {"ALTO": SALMON, "MÉDIO": YELLOW_ALERT, "BAIXO": TEAL_MEDIUM}
    fig_prio = px.bar(
        df_prio, x="Prioridade", y="QTD", text_auto=True,
        color="Prioridade", color_discrete_map=cores_prio,
    )
    fig_prio.update_traces(marker_line_width=0)
    fig_prio.update_layout(**PLOTLY_LAYOUT, showlegend=False, xaxis_title=None, yaxis_title=None)
    st.plotly_chart(fig_prio, use_container_width=True)

with col_g4:
    if COL_RESP:
        st.markdown("<div class='section-title'>Pendências por Responsável</div>", unsafe_allow_html=True)
        df_resp = (
            df[df[COL_STATUS] != "CONCLUÍDO"][COL_RESP]
            .value_counts()
            .reset_index()
        )
        df_resp.columns = ["Responsável", "QTD"]
        fig_resp = px.bar(
            df_resp, x="QTD", y="Responsável", orientation="h",
            text_auto=True, color_discrete_sequence=[TEAL_MEDIUM],
        )
        fig_resp.update_traces(marker_line_width=0)
        layout_resp = {**PLOTLY_LAYOUT,
                       "showlegend": False,
                       "xaxis_title": None,
                       "yaxis_title": None,
                       "yaxis": {**PLOTLY_LAYOUT.get("yaxis", {}),
                                 "autorange": "reversed"}}
        fig_resp.update_layout(**layout_resp)
        st.plotly_chart(fig_resp, use_container_width=True)

# ── Tabela detalhada ──────────────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Detalhamento das Ações</div>", unsafe_allow_html=True)

# Colunas para exibição (sem dados pessoais — LGPD)
cols_exibir = [c for c in [
    COL_FILIAL, COL_ASSUNTO, COL_ACAO, COL_RESP,
    COL_PRIORIDADE, COL_QUANDO, COL_CONCLUSAO, COL_STATUS,
    "DIAS ATRASO", COL_FOLLOWUP,
] if c and c in df.columns]

df_exibir = df[cols_exibir].copy()

# Rótulos de coluna mais legíveis
RENAME = {
    COL_FILIAL:    "Filial",
    COL_ASSUNTO:   "Assunto",
    COL_ACAO:      "Ação",
    COL_RESP:      "Responsável",
    COL_PRIORIDADE:"Prioridade",
    COL_QUANDO:    "Prazo Previsto",
    COL_CONCLUSAO: "Data Conclusão",
    COL_STATUS:    "Status",
    "DIAS ATRASO": "Dias em Atraso",
    COL_FOLLOWUP:  "Follow Up",
}
df_exibir = df_exibir.rename(columns={k: v for k, v in RENAME.items() if k in df_exibir.columns})

# Colorização de linhas por status
def colorir_linha(row):
    s = str(row.get("Status", "")).upper()
    if s == "ATRASADO":
        return ["background-color: rgba(196,122,119,0.22);"] * len(row)
    elif s == "ALERTA":
        return ["background-color: rgba(232,184,75,0.18);"] * len(row)
    elif s == "CONCLUÍDO":
        return ["background-color: rgba(45,197,180,0.13);"] * len(row)
    return [""] * len(row)

styled = df_exibir.style.apply(colorir_linha, axis=1)

# Altura dinâmica: mostra todas as linhas sem scroll interno excessivo
altura_tabela = min(600, max(300, 38 + len(df_exibir) * 35))
st.dataframe(styled, use_container_width=True, hide_index=True, height=altura_tabela)

# ── Export ────────────────────────────────────────────────────────────────────
buffer = io.BytesIO()
df_exibir.to_excel(buffer, index=False, engine="openpyxl")
buffer.seek(0)
nome_arquivo = f"pendencias_filtrado_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
st.download_button(
    label="⬇  Exportar tabela filtrada (.xlsx)",
    data=buffer,
    file_name=nome_arquivo,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# ── Rodapé ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='text-align:center;margin-top:2rem;color:{NEUTRAL_700};font-size:.8rem;letter-spacing:.06em;'>
  DIAS+ · diaslog.com.br · Pendências Regulatórias
</div>
""", unsafe_allow_html=True)
