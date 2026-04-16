import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import requests
import re

# 1. Configuração da Página
st.set_page_config(page_title="TECADI - Dashboard Logístico", page_icon="📦", layout="wide")

# --- ESTILO TECADI ---
AZUL_TECADI = "#1D569B"
AZUL_ESCURO = "#133A68"
AZUL_CLARO_TECADI = "#009FE3"
VERMELHO_ALERTA = "#D32F2F"
VERDE_SUCESSO = "#2E7D32"
CINZA_FUNDO = "#F8FAFC"

def formatar_br(valor):
    return f"{valor:,.0f}".replace(",", ".")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #FFFFFF; }}
    .dash-header {{ border-left: 10px solid {AZUL_TECADI}; padding-left: 20px; margin-bottom: 20px; }}
    .dash-title {{ color: {AZUL_ESCURO}; font-size: 38px !important; font-weight: 800 !important; }}
    [data-testid="stSidebar"] {{ background: linear-gradient(180deg, {AZUL_ESCURO} 0%, {AZUL_TECADI} 100%); }}
    div[data-testid="stMetric"] {{ background-color: {CINZA_FUNDO} !important; border: 1px solid #E2E8F0 !important; border-radius: 12px !important; }}
    </style>
""", unsafe_allow_html=True)

# Função para forçar download direto do SharePoint
def converter_link_direto(url):
    if "sharepoint.com" in url:
        # Remove parâmetros de visualização e força o download
        base_url = url.split('?')[0]
        return f"{base_url}?download=1"
    return url

@st.cache_data(ttl=300)
def load_data():
    # Links fornecidos
    url_p = "https://tecadi-my.sharepoint.com/:x:/g/personal/anderson_roza_tecadi_com_br/IQBS8GhxPJ3wRYIodpxrwD_5AU15pbYrDvzMKaY1kw161vg"
    url_f = "https://tecadi-my.sharepoint.com/:x:/g/personal/anderson_roza_tecadi_com_br/IQCpXS7IqaNPRpmwTx1-FYuKAWLu5pqlVkA1hpUD-mkCcno"
    
    try:
        # Requisição dos arquivos
        res_p = requests.get(converter_link_direto(url_p), timeout=15)
        res_f = requests.get(converter_link_direto(url_f), timeout=15)
        
        # Leitura dos DataFrames
        df_p = pd.read_excel(io.BytesIO(res_p.content), engine='openpyxl')
        df_f = pd.read_excel(io.BytesIO(res_f.content), engine='openpyxl')
        
        # --- TRATAMENTOS DE DATAS ---
        # Finalizados
        df_f['DT_CRIACAO'] = pd.to_datetime(df_f['Criado em'].astype(str).str.split('-').str[0], dayfirst=True, errors='coerce')
        df_f['DT_FIM'] = pd.to_datetime(df_f['Finalizada em'].astype(str).str.split('-').str[0], dayfirst=True, errors='coerce')
        
        # Pendentes
        df_p['DT_CRIACAO'] = pd.to_datetime(df_p['Criado em'].astype(str).str.split('-').str[0], dayfirst=True, errors='coerce')
        
        # SLA (Baseado na data atual do sistema)
        hoje = pd.to_datetime(datetime.now().date())
        df_f['Dias_Entrega'] = (df_f['DT_FIM'] - df_f['DT_CRIACAO']).dt.days
        df_f['Status_SLA'] = df_f['Dias_Entrega'].apply(lambda x: 'No Prazo' if x <= 2 else 'Fora do Prazo')
        
        df_p['Dias_Aberto'] = (hoje - df_p['DT_CRIACAO']).dt.days
        df_p['Status_SLA'] = df_p['Dias_Aberto'].apply(lambda x: 'Dentro do Prazo' if x <= 2 else 'SLA Estourado')

        return df_p, df_f, None
    except Exception as e:
        return None, None, f"Erro ao acessar SharePoint: {str(e)}"

# Execução da carga
df_p, df_f, erro = load_data()

if erro:
    st.error(f"🚨 {erro}")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://tecadi.com.br/wp-content/uploads/2024/01/LOGO-HORIZONTAL_BRANCA_p.png.webp", width=200)
    st.markdown("---")
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()
    
    # Filtros
    min_d = df_f['DT_FIM'].min().date() if not df_f['DT_FIM'].isnull().all() else datetime.now().date()
    max_d = df_f['DT_FIM'].max().date() if not df_f['DT_FIM'].isnull().all() else datetime.now().date()
    date_range = st.date_input("📅 Período", value=(min_d, max_d))
    
    operadores = ["Todos"] + sorted(df_f['Finalizada por'].dropna().unique().tolist())
    op_filt = st.selectbox("👤 Operador", operadores)

# Filtro de dados
mask = (df_f['DT_FIM'].dt.date >= date_range[0]) & (df_f['DT_FIM'].dt.date <= date_range[1])
if op_filt != "Todos": mask &= (df_f['Finalizada por'] == op_filt)
df_f_filtered = df_f[mask]

# --- DASHBOARD ---
st.markdown('<div class="dash-header"><div class="dash-title">Gestão de Picking & Packing</div></div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Peças Montadas", formatar_br(df_f_filtered['Peças montadas'].sum()))
m2.metric("Linhas Montadas", formatar_br(df_f_filtered['Linhas montadas'].sum()))
m3.metric("Pedidos Concluídos", formatar_br(df_f_filtered['Código'].nunique()))
m4.metric("SLA Médio", f"{df_f_filtered['Dias_Entrega'].mean():.1f} d")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Produtividade", "📋 Pendentes", "⏱️ SLA Global", "📦 SLA Foco Packing"])

with tab1:
    df_evol = df_f_filtered.groupby('DT_FIM').agg({'Peças montadas': 'sum', 'Código': 'nunique'}).reset_index()
    fig = px.line(df_evol, x='DT_FIM', y='Peças montadas', title="Evolução de Peças", markers=True)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.plotly_chart(px.bar(df_p.groupby('Tipo')['Peças solicitadas'].sum().reset_index(), x='Tipo', y='Peças solicitadas', color='Tipo'), use_container_width=True)

with tab3:
    st.plotly_chart(px.pie(df_f_filtered, names='Status_SLA', hole=0.5, color_discrete_map={'No Prazo': VERDE_SUCESSO, 'Fora do Prazo': VERMELHO_ALERTA}), use_container_width=True)

with tab4:
    st.subheader("Análise Detalhada Packing")
    df_pack_p = df_p[df_p['Tipo'] == 'Packing'].copy()
    
    # Formatações solicitadas
    df_pack_p['Tarefa Packing'] = df_pack_p['Código'].astype(str).str.zfill(6)
    df_pack_p['Data Criação'] = df_pack_p['DT_CRIACAO'].dt.strftime('%d/%m/%Y')
    
    def extrair_picking(obs):
        match = re.search(r'Trf\.Picking:(\d+)', str(obs))
        return match.group(1) if match else "N/A"
    
    df_pack_p['Tarefa Picking'] = df_pack_p['Observações'].apply(extrair_picking)
    
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.pie(df_f_filtered[df_f_filtered['Tipo'] == 'Packing'], names='Status_SLA', title="Histórico Packing", hole=0.4), use_container_width=True)
    with c2:
        st.plotly_chart(px.pie(df_pack_p, names='Status_SLA', title="Backlog Packing", hole=0.4), use_container_width=True)
    
    st.dataframe(df_pack_p[['Tarefa Packing', 'Tarefa Picking', 'Status', 'Data Criação', 'Dias_Aberto', 'Peças solicitadas', 'Status_SLA']], use_container_width=True, hide_index=True)
