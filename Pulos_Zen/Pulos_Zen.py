import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from io import BytesIO

# 1. Configuração da Página
st.set_page_config(page_title="TECADI - Análise de Pulos", page_icon="🦘", layout="wide")

# ---------------------------------------------------------
# 2. ESTILO E CORES PADRÃO TECADI
# ---------------------------------------------------------
AZUL_ESCURO = "#133A68"
AZUL_TECADI = "#1D569B"
AZUL_CLARO_TECADI = "#009FE3"
CINZA_FUNDO = "#F8FAFC"

def formatar_br(valor):
    return f"{valor:,.0f}".replace(",", ".")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #FFFFFF; }}
    .dash-header {{ border-left: 10px solid {AZUL_TECADI}; padding-left: 20px; margin-bottom: 20px; }}
    .dash-title {{ color: {AZUL_ESCURO}; font-size: 38px !important; font-weight: 800 !important; }}
    
    /* Sidebar Gradiente */
    [data-testid="stSidebar"] {{ background: linear-gradient(180deg, {AZUL_ESCURO} 0%, {AZUL_TECADI} 100%); }}
    .sidebar-label {{ color: white !important; font-size: 1.1rem !important; font-weight: 700 !important; margin-top: 20px; margin-bottom: 10px; display: block; }}

    /* Cards Métricas */
    div[data-testid="stMetric"] {{
        background-color: {CINZA_FUNDO} !important;
        border: 1px solid #E2E8F0 !important;
        padding: 15px !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }}
    div[data-testid="stMetric"]:hover {{
        transform: translateY(-5px) !important;
        border-color: {AZUL_CLARO_TECADI} !important;
    }}
    div[data-testid="stMetric"] label p {{ color: {AZUL_ESCURO} !important; font-size: 16px !important; font-weight: 600 !important; }}
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{ color: {AZUL_TECADI} !important; font-size: 28px !important; font-weight: 800 !important; }}

    /* Estilização do Slider */
    div[data-baseweb="tooltip"] {{ display: none !important; visibility: hidden !important; }}
    div[data-baseweb="slider"] > div > div {{ background: rgba(255, 255, 255, 0.2) !important; }}
    div[data-baseweb="slider"] > div > div > div {{ background: #FFFFFF !important; }}
    div[role="slider"] {{ background-color: {AZUL_CLARO_TECADI} !important; border: 2px solid white !important; }}
    div[data-baseweb="slider"] div {{ color: white !important; font-weight: 600 !important; }}
    
    [data-testid="stSidebar"] * {{ outline: none !important; border: none !important; box-shadow: none !important; }}
    [data-testid="stSidebar"] label p {{ color: white !important; }}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. MOTOR DE DADOS (OneDrive + Pulos Reais)
# ---------------------------------------------------------
# Link do OneDrive ajustado para download direto
URL_DATA = "https://tecadi-my.sharepoint.com/:x:/g/personal/luis_avila_tecadi_com_br/IQBdA_Yt563JR4yERPu4o5NwAc0XmKnxbR6NrGQehUHQ35k?download=1"

@st.cache_data(ttl=3600)
def load_and_process_data(url):
    try:
        response = requests.get(url)
        df = pd.read_excel(BytesIO(response.content))
        
        # 1. Ajuste de Data e Hora
        df['Data'] = pd.to_datetime(df['Data'])
        df['Timestamp'] = pd.to_datetime(df['Data'].dt.strftime('%Y-%m-%d') + ' ' + df['Hora'].astype(str))
        
        # 2. Ordenação para cálculo de janela
        df = df.sort_values(by=['Usuario', 'Endereco', 'Timestamp'])
        
        # 3. Regra de Negócio: Agrupar por Endereço em janelas de 5 minutos
        # Consideramos o mesmo pulo se: mesmo Operador + mesmo Endereço + diferença < 5 min
        df['Diff_Minutos'] = df.groupby(['Usuario', 'Endereco'])['Timestamp'].diff().dt.total_seconds() / 60
        df['Novo_Pulo'] = (df['Diff_Minutos'].isna()) | (df['Diff_Minutos'] > 5)
        
        # 4. Criar DataFrame de Pulos Reais (1 linha por pulo)
        df_pulos = df[df['Novo_Pulo'] == True].copy()
        df_pulos['Hora_Full'] = df_pulos['Timestamp'].dt.hour
        
        return df_pulos, None
    except Exception as e:
        return None, str(e)

df_f_base, erro = load_and_process_data(URL_DATA)

if df_f_base is not None:
    # --- SIDEBAR ---
    with st.sidebar:
        st.image("https://tecadi.com.br/wp-content/uploads/2024/01/LOGO-HORIZONTAL_BRANCA_p.png.webp", width=200)
        st.markdown("---")
        
        st.markdown('<span class="sidebar-label">📅 INTERVALO DE TEMPO</span>', unsafe_allow_html=True)
        min_d, max_d = df_f_base['Data'].min().date(), df_f_base['Data'].max().date()
        date_range = st.slider("Período", min_value=min_d, max_value=max_d, value=(min_d, max_d), format="DD/MM/YYYY", label_visibility="collapsed")
        
        st.markdown('<span class="sidebar-label">👤 FILTRO GLOBAL: OPERADOR</span>', unsafe_allow_html=True)
        user_filt = st.multiselect("Filtrar Usuário", options=sorted(df_f_base['Usuario'].unique()), label_visibility="collapsed")

    # Filtro Global do Dashboard
    df_f = df_f_base[(df_f_base['Data'].dt.date >= date_range[0]) & (df_f_base['Data'].dt.date <= date_range[1])]
    if user_filt:
        df_f = df_f[df_f['Usuario'].isin(user_filt)]

    # --- TÍTULO ---
    st.markdown('<div class="dash-header"><div class="dash-title">Análise de Produtividade ZEN (Pulos Reais)</div></div>', unsafe_allow_html=True)

    # --- MÉTRICAS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de Pulos Reais", formatar_br(len(df_f)))
    m2.metric("Operadores Ativos", formatar_br(df_f['Usuario'].nunique()))
    m3.metric("Endereços Visitados", formatar_br(df_f['Endereco'].nunique()))
    dias_ativos = max(1, df_f['Data'].nunique())
    m4.metric("Média Pulos / Dia", formatar_br(len(df_f) / dias_ativos))

    st.divider()

    # --- GRÁFICOS PRINCIPAIS ---
    c_dir, c_esq = st.columns([2, 1])
    with c_dir:
        st.subheader("📈 Evolução de Movimentações (Pulos)")
        df_evol = df_f.groupby(df_f['Data'].dt.date).size().reset_index(name='Pulos')
        fig_evol = px.line(df_evol, x='Data', y='Pulos', color_discrete_sequence=[AZUL_TECADI], text='Pulos')
        fig_evol.update_traces(textposition="top center", mode='lines+markers+text')
        fig_evol.update_layout(plot_bgcolor='rgba(0,0,0,0)', xaxis_title=None, yaxis_title="Qtd Pulos")
        st.plotly_chart(fig_evol, use_container_width=True)

    with c_esq:
        st.subheader("🏆 Ranking Operadores")
        top_u = df_f['Usuario'].value_counts().head(10).reset_index()
        top_u.columns = ['Usuario', 'Pulos']
        fig_u = px.bar(top_u, x='Pulos', y='Usuario', orientation='h', color_discrete_sequence=[AZUL_ESCURO], text='Pulos')
        fig_u.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_u, use_container_width=True)

    # --- INDICADORES DE RECORRÊNCIA ---
    st.divider()
    col_prod, col_end = st.columns(2)
    with col_prod:
        st.subheader("📦 Pulos por Produto (Top 15)")
        df_rec_p = df_f['Produto'].value_counts().head(15).reset_index()
        df_rec_p.columns = ['Produto', 'Qtd']
        fig_p = px.bar(df_rec_p, x='Qtd', y='Produto', orientation='h', color_discrete_sequence=[AZUL_CLARO_TECADI], text='Qtd')
        fig_p.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_p, use_container_width=True)

    with col_end:
        st.subheader("📍 Pulos por Endereço (Top 15)")
        df_rec_e = df_f['Endereco'].value_counts().head(15).reset_index()
        df_rec_e.columns = ['Endereco', 'Qtd']
        fig_e = px.bar(df_rec_e, x='Qtd', y='Endereco', orientation='h', color_discrete_sequence=["#FF7F0E"], text='Qtd')
        fig_e.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_e, use_container_width=True)

    st.divider()

    # --- TABELA COM FILTROS ESPECÍFICOS ---
    st.subheader("🔍 Detalhamento e Filtros da Tabela")
    
    # Painel de filtros da tabela
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        t_user = st.multiselect("Filtrar Usuário", options=sorted(df_f['Usuario'].unique()), key="filter_user")
    with f2:
        t_prod = st.text_input("Filtrar Produto (SKU)", key="filter_prod")
    with f3:
        t_end = st.text_input("Filtrar Endereço", key="filter_end")
    with f4:
        datas_disponiveis = sorted(df_f['Data'].dt.date.unique(), reverse=True)
        t_data = st.multiselect("Filtrar Data", options=datas_disponiveis, key="filter_date")

    # Lógica de filtragem da tabela
    df_tab = df_f.copy()
    if t_user:
        df_tab = df_tab[df_tab['Usuario'].isin(t_user)]
    if t_prod:
        df_tab = df_tab[df_tab['Produto'].astype(str).str.contains(t_prod, case=False)]
    if t_end:
        df_tab = df_tab[df_tab['Endereco'].astype(str).str.contains(t_end, case=False)]
    if t_data:
        df_tab = df_tab[df_tab['Data'].dt.date.isin(t_data)]

    st.dataframe(
        df_tab[['Data', 'Hora', 'Usuario', 'Endereco', 'Produto']],
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY")
        }
    )

else:
    st.error("❌ Não foi possível carregar os dados do OneDrive.")
    if erro: st.info(f"Erro técnico: {erro}")
