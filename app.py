import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
from datetime import datetime

# ── Paleta Dias+ ──────────────────────────────────────────────────────────────
TEAL_PRIMARY = "#2DC5B4"
TEAL_DEEP    = "#0E7A8C"
TEAL_MEDIUM  = "#5BA8B8"
DARK_BG      = "#0B3040"
DARK_BG2     = "#0D3A4E"
SALMON       = "#C47A77"
AMBER        = "#E8B84B"
WHITE        = "#FFFFFF"
NEUTRAL_700  = "#4A6670"

COR_STATUS = {
    "VENCIDO":      SALMON,
    "PENDENTE":     AMBER,
    "EM ANÁLISE":   TEAL_MEDIUM,
    "REGULARIZADO": TEAL_PRIMARY,
}

ORDEM_STATUS = ["VENCIDO", "PENDENTE", "EM ANÁLISE", "REGULARIZADO"]

# ── Colunas ───────────────────────────────────────────────────────────────────
COL_FILIAL      = "FILIAL"
COL_CATEGORIA   = "CATEGORIA"
COL_ASSUNTO     = "ASSUNTO"
COL_NUM_DOC     = "Nº DOCUMENTO"
COL_EMISSAO     = "DATA DE EMISSÃO/SOLICITAÇÃO"
COL_VENCIMENTO  = "DATA DE VENCIMENTO"
COL_PRAZO_INFRA = "PRAZO (INFRA)"
COL_STATUS      = "STATUS"
COL_RESP        = "RESPONSÁVEL"
COL_OBS         = "OBSERVAÇÕES"

st.set_page_config(
    page_title="Controle de Documentos · Dias+",
    page_icon="➕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;600;700;800;900&display=swap');
  html, body, [class*="css"] {{
    font-family: 'Barlow Condensed', sans-serif !important;
    background-color: {DARK_BG} !important;
    color: {WHITE} !important;
  }}
  .main .block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; }}
  [data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {DARK_BG} 0%, {DARK_BG2} 100%) !important;
    border-right: 1px solid rgba(45,197,180,0.25) !important;
  }}
  [data-testid="stSidebar"] * {{ color: {WHITE} !important; }}
  [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {{
    background-color: {TEAL_DEEP} !important;
  }}
  .hero-header {{
    background: linear-gradient(135deg, {DARK_BG} 0%, {TEAL_DEEP} 100%);
    border-bottom: 3px solid {TEAL_PRIMARY};
    padding: 1.4rem 2rem 1.2rem 2rem;
    border-radius: 0 0 16px 16px;
    margin-bottom: 1.4rem;
  }}
  .hero-header h1 {{
    font-size: 2.2rem; font-weight: 800; text-transform: uppercase;
    letter-spacing: 0.06em; color: {WHITE}; margin: 0 0 .15rem 0;
  }}
  .hero-header .tag {{
    background: {TEAL_PRIMARY}; color: {DARK_BG}; font-weight: 700;
    font-size: .8rem; letter-spacing: .08em; text-transform: uppercase;
    border-radius: 999px; padding: 3px 12px;
  }}
  .hero-header small {{ color: rgba(255,255,255,.55); font-size: .85rem; }}
  [data-testid="metric-container"] {{
    background: rgba(255,255,255,0.07) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 14px !important;
    padding: 1rem 1.2rem !important;
  }}
  [data-testid="metric-container"] label {{
    color: rgba(255,255,255,.6) !important;
    font-size: .8rem !important; letter-spacing: .07em; text-transform: uppercase;
  }}
  [data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size: 2.4rem !important; font-weight: 900 !important; color: {WHITE} !important;
  }}
  .section-title {{
    font-size: 1.05rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .08em; color: {TEAL_PRIMARY};
    border-left: 4px solid {TEAL_PRIMARY};
    padding-left: 10px; margin: 1.4rem 0 .7rem 0;
  }}
  .alert-box {{
    background: rgba(196,122,119,0.15);
    border: 1px solid rgba(196,122,119,0.5);
    border-radius: 10px; padding: .8rem 1.2rem; margin-bottom: .5rem;
  }}
  .alert-box-amber {{
    background: rgba(232,184,75,0.12);
    border: 1px solid rgba(232,184,75,0.4);
    border-radius: 10px; padding: .8rem 1.2rem; margin-bottom: .5rem;
  }}
  [data-testid="stDataFrame"] {{ border-radius: 12px; overflow: hidden; }}
  [data-testid="stDataFrame"] th {{
    background-color: {DARK_BG2} !important;
    color: {TEAL_PRIMARY} !important;
    font-weight: 700 !important; letter-spacing: .06em; text-transform: uppercase;
  }}
  .badge {{
    display: inline-block; border-radius: 6px; padding: 2px 10px;
    font-weight: 700; font-size: .78rem; letter-spacing: .07em; text-transform: uppercase;
  }}
  hr {{ border-color: rgba(45,197,180,0.2) !important; }}
  .stDownloadButton > button {{
    background: {TEAL_PRIMARY} !important; color: {DARK_BG} !important;
    font-weight: 700 !important; border-radius: 8px !important; border: none !important;
  }}
  .stDownloadButton > button:hover {{
    background: {TEAL_DEEP} !important; color: {WHITE} !important;
  }}
  ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
  ::-webkit-scrollbar-track {{ background: {DARK_BG}; }}
  ::-webkit-scrollbar-thumb {{ background: {TEAL_DEEP}; border-radius: 4px; }}
</style>
""", unsafe_allow_html=True)

# ── Carregamento ──────────────────────────────────────────────────────────────
URL_PLANILHA  = "https://docs.google.com/spreadsheets/d/1dWty5R8y9H8CI1gCrSVJbHJFM3tR2LVbhfj0rxA_JN8/edit?usp=sharing"
ARQUIVO_LOCAL = "Pendencias.xlsx"

HOJE = pd.Timestamp(datetime.now().date())


def _url_download(url: str) -> str:
    """Converte URL de compartilhamento do Google Sheets para download direto."""
    import re
    if "docs.google.com/spreadsheets" in url:
        m = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url)
        if m:
            return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=xlsx"
    return url


def _processar_excel(conteudo_bytes):
    xls = pd.ExcelFile(io.BytesIO(conteudo_bytes))

    # ── Lê TODAS as abas e concatena ────────────────────────────────────────
    ABAS_IGNORAR = {"_TIPOS", "_tipos", "TIPOS_DOC"}
    df_list = []
    for aba in xls.sheet_names:
        if aba in ABAS_IGNORAR:
            continue
        try:
            df_temp = pd.read_excel(xls, sheet_name=aba)
            df_temp.columns = [str(c).strip().upper() for c in df_temp.columns]
            df_temp = df_temp.dropna(how="all")
            if not df_temp.empty and COL_FILIAL in df_temp.columns:
                df_list.append(df_temp)
        except Exception:
            continue

    if not df_list:
        return pd.DataFrame()

    df = pd.concat(df_list, ignore_index=True)

    # ── Preenche vazios para não sumirem nos filtros ─────────────────────────
    for col, fill in [(COL_FILIAL, "NÃO INFORMADO"), (COL_CATEGORIA, "NÃO INFORMADO"),
                      (COL_ASSUNTO, "NÃO INFORMADO"), (COL_RESP, "SEM RESPONSÁVEL")]:
        if col in df.columns:
            df[col] = df[col].fillna(fill).astype(str).str.strip()

    # ── Datas com dayfirst=True (padrão BR DD/MM/YYYY) ───────────────────────
    for col in [COL_EMISSAO, COL_VENCIMENTO, COL_PRAZO_INFRA]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

    # ── Normaliza STATUS ─────────────────────────────────────────────────────
    if COL_STATUS in df.columns:
        df[COL_STATUS] = (
            df[COL_STATUS]
            .astype(str).str.strip().str.upper()
            .replace({
                "EM ANALISE":  "EM ANÁLISE",
                "ANALISE":     "EM ANÁLISE",
                "CONCLUIDO":   "REGULARIZADO",
                "CONCLUÍDO":   "REGULARIZADO",
                "NAN":         "PENDENTE",
            })
        )
        df.loc[~df[COL_STATUS].isin(COR_STATUS), COL_STATUS] = "PENDENTE"
    else:
        df[COL_STATUS] = "PENDENTE"

    # ── Prazo efetivo: INFRA usa PRAZO (INFRA), demais usam DATA DE VENCIMENTO
    df["_PRAZO"] = df[COL_VENCIMENTO] if COL_VENCIMENTO in df.columns else pd.NaT
    if COL_PRAZO_INFRA in df.columns and COL_CATEGORIA in df.columns:
        mask_infra = (
            df[COL_CATEGORIA].str.upper().str.contains("INFRA", na=False) &
            df[COL_PRAZO_INFRA].notna()
        )
        df.loc[mask_infra, "_PRAZO"] = df.loc[mask_infra, COL_PRAZO_INFRA]

    # ── Auto-calcula VENCIDO pelo prazo efetivo ──────────────────────────────
    mask_vencido = (
        df["_PRAZO"].notna() &
        (df["_PRAZO"] < HOJE) &
        (df[COL_STATUS] != "REGULARIZADO")
    )
    df.loc[mask_vencido, COL_STATUS] = "VENCIDO"
    df["DIAS_VENC"] = (df["_PRAZO"] - HOJE).dt.days
    df = df.drop(columns=["_PRAZO"])

    return df


@st.cache_data(ttl=120)
def _carregar_online(url):
    url_dl = _url_download(url)
    r = requests.get(url_dl, headers={"User-Agent": "Mozilla/5.0"}, timeout=30, allow_redirects=True)
    r.raise_for_status()
    return r.content


def _carregar_local():
    """Leitura direta do disco — sem cache, sempre atualizado."""
    import os
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), ARQUIVO_LOCAL)
    if os.path.exists(caminho):
        with open(caminho, "rb") as f:
            return f.read()
    return None


# ── Sidebar: upload + botões ──────────────────────────────────────────────────
with st.sidebar:
    upload = st.file_uploader("Substituir arquivo manualmente", type=["xlsx"],
                               help="Use se o OneDrive estiver indisponível.")
    st.markdown("---")

df_raw     = pd.DataFrame()
ts_carga   = None
fonte_dados = ""

# Prioridade 1: upload manual
if upload is not None:
    try:
        df_raw = _processar_excel(upload.read())
        ts_carga = datetime.now()
        fonte_dados = f"upload manual · {upload.name}"
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")

# Prioridade 2: Google Sheets (fonte principal)
if df_raw.empty and URL_PLANILHA != "COLE_AQUI_A_URL_DO_GOOGLE_SHEETS":
    try:
        conteudo_gs = _carregar_online(URL_PLANILHA)
        df_raw = _processar_excel(conteudo_gs)
        ts_carga = datetime.now()
        fonte_dados = "Google Sheets (online)"
    except Exception as e:
        st.error(f"❌ Erro ao carregar Google Sheets: {e}")
        st.stop()

# Prioridade 3: arquivo local (fallback offline)
if df_raw.empty:
    conteudo = _carregar_local()
    if conteudo:
        try:
            df_raw = _processar_excel(conteudo)
            ts_carga = datetime.now()
            fonte_dados = f"arquivo local · {ARQUIVO_LOCAL}"
        except Exception as e:
            st.error(f"Erro ao ler arquivo local: {e}")

# ── Hero header ───────────────────────────────────────────────────────────────
ts_str = ts_carga.strftime("%d/%m/%Y  %H:%M") if ts_carga else "—"
st.markdown(f"""
<div class="hero-header">
  <h1>Controle de Documentos <span class="tag">Filiais</span></h1>
  <small>Última atualização: {ts_str} &nbsp;·&nbsp; diaslog.com.br</small>
</div>
""", unsafe_allow_html=True)

if df_raw.empty:
    st.warning("Aguardando dados. Faça upload da planilha ou configure o link do OneDrive.")
    st.stop()

# ── Sidebar: filtros ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<h3 style='color:{TEAL_PRIMARY};text-transform:uppercase;letter-spacing:.1em;'>Filtros</h3>",
                unsafe_allow_html=True)

    filiais = sorted(df_raw[COL_FILIAL].dropna().unique())
    sel_filiais = st.multiselect("Filial", filiais, default=filiais)

    if COL_CATEGORIA in df_raw.columns:
        cats = sorted(df_raw[COL_CATEGORIA].dropna().unique())
        sel_cats = st.multiselect("Categoria", cats, default=cats)
    else:
        sel_cats = []

    assuntos = sorted(df_raw[COL_ASSUNTO].dropna().unique()) if COL_ASSUNTO in df_raw.columns else []
    sel_assuntos = st.multiselect("Assunto", assuntos, default=assuntos)

    status_opts = [s for s in ORDEM_STATUS if s in df_raw[COL_STATUS].unique()]
    sel_status = st.multiselect("Status", status_opts, default=status_opts)

    if COL_RESP in df_raw.columns:
        resp_opts = sorted(df_raw[COL_RESP].dropna().unique())
        sel_resp = st.multiselect("Responsável", resp_opts, default=resp_opts)
    else:
        sel_resp = []

    # Filtro rápido: vencimento nos próximos N dias
    st.markdown("---")
    dias_alerta = st.slider("Alerta de vencimento (dias)", 7, 90, 30, step=7)

    st.markdown("---")
    if st.button("Recarregar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if fonte_dados:
        st.caption(f"Fonte: {fonte_dados}")
    if ts_carga:
        st.caption(f"{ts_carga.strftime('%d/%m/%Y %H:%M')}")

# ── Filtragem ─────────────────────────────────────────────────────────────────
mask = df_raw[COL_FILIAL].isin(sel_filiais) & df_raw[COL_STATUS].isin(sel_status)
if sel_cats and COL_CATEGORIA in df_raw.columns:
    mask &= df_raw[COL_CATEGORIA].isin(sel_cats)
if sel_assuntos and COL_ASSUNTO in df_raw.columns:
    mask &= df_raw[COL_ASSUNTO].isin(sel_assuntos)
if sel_resp and COL_RESP in df_raw.columns:
    mask &= df_raw[COL_RESP].isin(sel_resp)

df = df_raw[mask].copy()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total       = len(df)
regulariz   = (df[COL_STATUS] == "REGULARIZADO").sum()
em_analise  = (df[COL_STATUS] == "EM ANÁLISE").sum()
pendentes   = (df[COL_STATUS] == "PENDENTE").sum()
vencidos    = (df[COL_STATUS] == "VENCIDO").sum()
pct_ok      = f"{100*regulariz/total:.0f}%" if total else "—"

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total de Documentos", total)
c2.metric("Regularizados", int(regulariz), delta=pct_ok)
c3.metric("Em Análise", int(em_analise))
c4.metric("Pendentes", int(pendentes))
c5.metric("Vencidos", int(vencidos))

# Vencendo nos próximos N dias (não vencidos ainda, não regularizados)
if "DIAS_VENC" in df.columns:
    proximos = df[(df["DIAS_VENC"] >= 0) & (df["DIAS_VENC"] <= dias_alerta) & (df[COL_STATUS] != "REGULARIZADO")]
    c6.metric(f"Vencem em {dias_alerta}d", len(proximos))

st.markdown("<hr>", unsafe_allow_html=True)

# ── Base de layout dos gráficos ───────────────────────────────────────────────
LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Barlow Condensed", color=WHITE),
    margin=dict(t=36, b=10, l=10, r=10),
    xaxis=dict(gridcolor="rgba(255,255,255,0.07)", linecolor="rgba(255,255,255,0.12)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.07)", linecolor="rgba(255,255,255,0.12)"),
)

STATUS_PEND = ["VENCIDO", "PENDENTE", "EM ANÁLISE"]

# ── Seção 1: Ranking de Pendências por Filial ─────────────────────────────────
st.markdown("<div class='section-title'>Ranking de Pendências por Filial</div>", unsafe_allow_html=True)
col_g1, col_g2 = st.columns([3, 2])

with col_g1:
    df_rank = (
        df[df[COL_STATUS].isin(STATUS_PEND)]
        .groupby([COL_FILIAL, COL_STATUS]).size().reset_index(name="QTD")
    )
    ordem_filiais = (
        df_rank.groupby(COL_FILIAL)["QTD"].sum()
        .sort_values(ascending=True).index.tolist()
    )
    fig_rank = px.bar(
        df_rank, x="QTD", y=COL_FILIAL, color=COL_STATUS, orientation="h",
        text_auto=True, color_discrete_map=COR_STATUS,
        category_orders={COL_FILIAL: ordem_filiais, COL_STATUS: STATUS_PEND},
        labels={COL_FILIAL: "", "QTD": "Pendências"},
        title="Ranking de Pendências por Filial",
    )
    fig_rank.update_traces(marker_line_width=0)
    fig_rank.update_layout(**LAYOUT, barmode="stack",
                            legend=dict(orientation="h", y=-0.08, title_text=""),
                            height=max(350, len(ordem_filiais) * 28))
    st.plotly_chart(fig_rank, use_container_width=True)

with col_g2:
    df_st = df[COL_STATUS].value_counts().reindex(ORDEM_STATUS).dropna().reset_index()
    df_st.columns = ["Status", "QTD"]
    fig_donut = px.pie(
        df_st, names="Status", values="QTD",
        hole=0.55, color="Status",
        color_discrete_map=COR_STATUS,
        title="Distribuição de Status",
    )
    fig_donut.update_traces(textfont_color=WHITE,
                            marker=dict(line=dict(color=DARK_BG, width=2)))
    fig_donut.update_layout(**LAYOUT, showlegend=True,
                             legend=dict(orientation="h", y=-0.12, title_text=""))
    st.plotly_chart(fig_donut, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Seção 2: Análise por Categoria e Assunto ──────────────────────────────────
st.markdown("<div class='section-title'>Análise por Categoria</div>", unsafe_allow_html=True)
col_g3, col_g4 = st.columns(2)

with col_g3:
    if COL_CATEGORIA in df.columns:
        df_cat = (
            df[df[COL_STATUS].isin(STATUS_PEND)]
            .groupby([COL_CATEGORIA, COL_STATUS]).size().reset_index(name="QTD")
        )
        fig_cat = px.bar(
            df_cat, x=COL_CATEGORIA, y="QTD", color=COL_STATUS,
            text_auto=True, color_discrete_map=COR_STATUS,
            category_orders={COL_STATUS: STATUS_PEND},
            labels={COL_CATEGORIA: "", "QTD": "Pendências"},
            title="Pendências por Categoria",
        )
        fig_cat.update_traces(marker_line_width=0)
        fig_cat.update_layout(**LAYOUT, barmode="group",
                               legend=dict(orientation="h", y=-0.15, title_text=""))
        st.plotly_chart(fig_cat, use_container_width=True)

with col_g4:
    if COL_ASSUNTO in df.columns:
        df_ass = (
            df[df[COL_STATUS].isin(STATUS_PEND)]
            .groupby(COL_ASSUNTO).size().reset_index(name="QTD")
            .sort_values("QTD", ascending=True).tail(12)
        )
        fig_ass = px.bar(
            df_ass, x="QTD", y=COL_ASSUNTO, orientation="h",
            text_auto=True, color_discrete_sequence=[SALMON],
            title="Assuntos com mais pendências (Top 12)",
        )
        fig_ass.update_traces(marker_line_width=0)
        fig_ass.update_layout(**LAYOUT, showlegend=False,
                               xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_ass, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Seção 3: % Regularizado por Filial ───────────────────────────────────────
st.markdown("<div class='section-title'>Cobertura de Regularização por Filial</div>", unsafe_allow_html=True)
df_tot_f = df.groupby(COL_FILIAL).size().reset_index(name="TOTAL")
df_reg_f = df[df[COL_STATUS] == "REGULARIZADO"].groupby(COL_FILIAL).size().reset_index(name="REG")
df_cob_f = df_tot_f.merge(df_reg_f, on=COL_FILIAL, how="left").fillna(0)
df_cob_f["PCT"] = (df_cob_f["REG"] / df_cob_f["TOTAL"] * 100).round(1)
df_cob_f = df_cob_f.sort_values("PCT", ascending=True)
fig_pct = px.bar(
    df_cob_f, x="PCT", y=COL_FILIAL, orientation="h",
    text_auto=True, color_discrete_sequence=[TEAL_MEDIUM],
    title="% Documentos Regularizados por Filial",
)
fig_pct.update_traces(marker_line_width=0, texttemplate="%{x:.0f}%", textposition="outside")
layout_pct = {**LAYOUT, "xaxis": {**LAYOUT["xaxis"], "range": [0, 110]}}
fig_pct.update_layout(**layout_pct, showlegend=False, xaxis_title=None, yaxis_title=None,
                       height=max(350, len(df_cob_f) * 28))
st.plotly_chart(fig_pct, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Seção 3: Alertas de Vencimento ───────────────────────────────────────────
st.markdown("<div class='section-title'>Alertas de Vencimento</div>", unsafe_allow_html=True)

if "DIAS_VENC" in df.columns:
    df_alerta = df[
        (df["DIAS_VENC"] >= 0) &
        (df["DIAS_VENC"] <= dias_alerta) &
        (df[COL_STATUS] != "REGULARIZADO")
    ].sort_values("DIAS_VENC")

    df_vencidos_tab = df[df[COL_STATUS] == "VENCIDO"].copy()

    ca, cb = st.columns(2)

    with ca:
        st.markdown(f"**Vencendo nos próximos {dias_alerta} dias** — {len(df_alerta)} documento(s)")
        if not df_alerta.empty:
            cols_al = [c for c in [COL_FILIAL, COL_ASSUNTO, COL_VENCIMENTO, "DIAS_VENC", COL_STATUS, COL_RESP] if c in df_alerta.columns]
            df_al_show = df_alerta[cols_al].rename(columns={
                COL_FILIAL: "Filial", COL_ASSUNTO: "Tipo de Documento",
                COL_VENCIMENTO: "Vence em", "DIAS_VENC": "Dias",
                COL_STATUS: "Status", COL_RESP: "Responsável",
            })
            st.dataframe(df_al_show, use_container_width=True, hide_index=True, height=280)
        else:
            st.success(f"Nenhum documento vencendo nos próximos {dias_alerta} dias.")

    with cb:
        st.markdown(f"**Documentos Vencidos** — {len(df_vencidos_tab)} documento(s)")
        if not df_vencidos_tab.empty:
            cols_venc = [c for c in [COL_FILIAL, COL_ASSUNTO, COL_VENCIMENTO, "DIAS_VENC", COL_RESP] if c in df_vencidos_tab.columns]
            df_venc_show = df_vencidos_tab[cols_venc].sort_values("DIAS_VENC").rename(columns={
                COL_FILIAL: "Filial", COL_ASSUNTO: "Tipo de Documento",
                COL_VENCIMENTO: "Venceu em", "DIAS_VENC": "Dias (negativo)",
                COL_RESP: "Responsável",
            })
            st.dataframe(df_venc_show, use_container_width=True, hide_index=True, height=280)
        else:
            st.success("Nenhum documento vencido.")
else:
    st.info("Coluna 'DATA DE VENCIMENTO' não encontrada na planilha.")

st.markdown("<hr>", unsafe_allow_html=True)

# ── Seção 4: Tabela Detalhada ─────────────────────────────────────────────────
st.markdown("<div class='section-title'>Detalhamento Completo</div>", unsafe_allow_html=True)

COLS_TABELA = [c for c in [
    COL_FILIAL, COL_ASSUNTO, COL_NUM_DOC,
    COL_EMISSAO, COL_VENCIMENTO, "DIAS_VENC",
    COL_STATUS, COL_RESP, COL_OBS,
] if c and c in df.columns]

df_tab = df[COLS_TABELA].copy()
df_tab = df_tab.rename(columns={
    COL_FILIAL:     "Filial",
    COL_ASSUNTO:   "Tipo de Documento",
    COL_NUM_DOC:    "Nº Documento",
    COL_EMISSAO:    "Emissão",
    COL_VENCIMENTO: "Vencimento",
    "DIAS_VENC":    "Dias p/ Vencer",
    COL_STATUS:     "Status",
    COL_RESP:       "Responsável",
    COL_OBS:        "Observações",
})

def _colorir(row):
    s = str(row.get("Status", "")).upper()
    mapa = {
        "VENCIDO":      "background-color: rgba(196,122,119,0.22);",
        "PENDENTE":     "background-color: rgba(232,184,75,0.18);",
        "EM ANÁLISE":   "background-color: rgba(91,168,184,0.15);",
        "REGULARIZADO": "background-color: rgba(45,197,180,0.12);",
    }
    return [mapa.get(s, "")] * len(row)

styled = df_tab.style.apply(_colorir, axis=1)
altura = min(700, max(300, 40 + len(df_tab) * 35))
st.dataframe(styled, use_container_width=True, hide_index=True, height=altura)

# ── Export ────────────────────────────────────────────────────────────────────
buf = io.BytesIO()
df_tab.to_excel(buf, index=False, engine="openpyxl")
buf.seek(0)
st.download_button(
    label="Exportar tabela filtrada (.xlsx)",
    data=buf,
    file_name=f"documentos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# ── Rodapé ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='text-align:center;margin-top:2rem;color:{NEUTRAL_700};font-size:.8rem;letter-spacing:.06em;'>
  DIAS+ · diaslog.com.br · Controle de Documentos
</div>
""", unsafe_allow_html=True)
