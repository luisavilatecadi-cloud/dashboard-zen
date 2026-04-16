import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import re
import requests
import io

# 1. Configuração da Página
st.set_page_config(page_title="TECADI - Dashboard Logístico", page_icon="📦", layout="wide")

# ---------------------------------------------------------
# 2. ESTILO E CORES PADRÃO TECADI
# ---------------------------------------------------------
AZUL_ESCURO = "#133A68"
AZUL_TECADI = "#1D569B"
AZUL_CLARO_TECADI = "#009FE3"
VERMELHO_ALERTA = "#D32F2F"
VERDE_SUCESSO = "#2E7D32"
CINZA_FUNDO = "#F8FAFC"

def formatar_br(valor):
    return f"{valor:,.0f}".replace(",", ".")

# Função para converter link do SharePoint em download direto
def link_download_direto(url):
    if "?e=" in url:
        return url.replace("?e=", "&download=1&e=")
    return url + "&download=1"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #FFFFFF; }}
    .dash-header {{ border-left: 10px solid {AZUL_TECADI}; padding-left: 20px; margin-bottom: 20px; }}
    .dash-title {{ color: {AZUL_ESCURO}; font-size: 38px !important; font-weight: 800 !important; }}
    [data-testid="stSidebar"] {{ background: linear-gradient(180deg, {AZUL_ESCURO} 0%, {AZUL_TECADI} 100%); }}
    .sidebar-label {{ color: white !important; font-weight: 700 !important; margin-top: 20px; display: block; }}
    div[data-testid="stMetric"] {{ background-color: {CINZA_FUNDO} !important; border: 1px solid #E2E8F0 !important; border-radius: 12px !important; }}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. MOTOR DE DADOS (CORRIGIDO)
# ---------------------------------------------------------
@st.cache_data(ttl=1)
def load_data():
    url_p = link_download_direto("https://tecadi-my.sharepoint.com/:x:/g/personal/anderson_roza_tecadi_com_br/IQBS8GhxPJ3wRYIodpxrwD_5AU15pbYrDvzMKaY1kw161vg?e=BPvvkp")
    url_f = link_download_direto("https://tecadi-my.sharepoint.com/:x:/g/personal/anderson_roza_tecadi_com_br/IQCpXS7IqaNPRpmwTx1-FYuKAWLu5pqlVkA1hpUD-mkCcno?e=c94Til")
    
    try:
        # Baixando os arquivos via requests para evitar erro de formato
        res_p = requests.get(url_p)
        res_f = requests.get(url_f)
        
        # Lendo os bytes com o engine openpyxl explicitamente
        df_p = pd.read_excel(io.BytesIO(res_p.content), engine='openpyxl')
        df_f = pd.read_excel(io.BytesIO(res_f.content), engine='openpyxl')
        
        # Tratamento de Datas - Finalizados
        df_f['DT_CRIACAO'] = pd.to_datetime(df_f['Criado em'].astype(str).str.split('-').str[0], dayfirst=True, errors='coerce')
        df_f['DT_FIM'] = pd.to_datetime(df_f['Finalizada em'].astype(str).str.split('-').str[0], dayfirst=True, errors='coerce')
        
        # Tratamento de Datas - Pendentes
        df_p['DT_CRIACAO'] = pd.to_datetime(df_p['Criado em'].astype(str).str.split('-').str[0], dayfirst=True, errors='coerce')
        
        # Cálculo de SLA (Usando data atual)
        hoje = pd.to_datetime(datetime.now().date())
        
        df_f['Dias_Entrega'] = (df_f['DT_FIM'] - df_f['DT_CRIACAO']).dt.days
        df_f['Status_SLA'] = df_f['Dias_Entrega'].apply(lambda x: 'No Prazo' if x <= 2 else 'Fora do Prazo')
        
        df_p['Dias_Aberto'] = (hoje - df_p['DT_CRIACAO']).dt.days
        df_p['Status_SLA'] = df_p['Dias_Aberto'].apply(lambda x: 'Dentro do Prazo' if x <= 2 else 'SLA Estourado')

        return df_p, df_f, None
    except Exception as e:
        return None, None, f"Erro ao carregar dados: {str(e)}"

df_p, df_f, erro = load_data()

if erro:
    st.error(erro)
    st.stop()

# --- Restante do código (Sidebar e Abas) permanece o mesmo ---
# (Inserir aqui o código das abas enviado anteriormente)

with st.sidebar:
    st.image("https://tecadi.com.br/wp-content/uploads/2024/01/LOGO-HORIZONTAL_BRANCA_p.png.webp", width=200)
    st.markdown("---")
    if st.button("🔄 Forçar Atualização"):
        st.cache_data.clear()
        st.rerun()
    
    # Filtro de Data
    min_d = df_f['DT_FIM'].min().date() if not df_f['DT_FIM'].isnull().all() else datetime.now().date()
    max_d = df_f['DT_FIM'].max().date() if not df_f['DT_FIM'].isnull().all() else datetime.now().date()
    date_range = st.date_input("📅 Período de Finalização", value=(min_d, max_d))
    operadores = ["Todos"] + sorted(df_f['Finalizada por'].dropna().unique().tolist())
    op_filt = st.selectbox("👤 Operador", operadores)

mask = (df_f['DT_FIM'].dt.date >= date_range[0]) & (df_f['DT_FIM'].dt.date <= date_range[1])
if op_filt != "Todos": mask &= (df_f['Finalizada por'] == op_filt)
df_f_filtered = df_f[mask]

st.markdown('<div class="dash-header"><div class="dash-title">Gestão de Picking & Packing</div></div>', unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Peças Montadas", formatar_br(df_f_filtered['Peças montadas'].sum()))
m2.metric("Linhas Montadas", formatar_br(df_f_filtered['Linhas montadas'].sum()))
m3.metric("Pedidos Concluídos", formatar_br(df_f_filtered['Código'].nunique()))
m4.metric("SLA Médio (Dias)", f"{df_f_filtered['Dias_Entrega'].mean():.1f} d")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Produtividade", "📋 Pendentes Gerais", "⏱️ SLA Global D+2", "📦 SLA Foco Packing"])

with tab1:
    df_evol = df_f_filtered.groupby('DT_FIM').agg({'Peças montadas': 'sum', 'Linhas montadas': 'sum', 'Código': 'nunique'}).reset_index().rename(columns={'Código': 'Pedidos'})
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_evol['DT_FIM'], y=df_evol['Peças montadas'], name='Peças', mode='lines+markers+text', text=df_evol['Peças montadas'], textposition="top center", line=dict(color=AZUL_CLARO_TECADI, width=4)))
    fig.add_trace(go.Bar(x=df_evol['DT_FIM'], y=df_evol['Linhas montadas'], name='Linhas', text=df_evol['Linhas montadas'], textposition='auto', marker_color=AZUL_TECADI, opacity=0.6))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    df_p_summary = df_p.groupby('Tipo').agg({'Peças solicitadas': 'sum', 'Linhas totais': 'sum', 'Código': 'nunique'}).reset_index().rename(columns={'Código': 'Pedidos'})
    c_p1, c_p2, c_p3 = st.columns(3)
    c_p1.plotly_chart(px.bar(df_p_summary, x='Tipo', y='Peças solicitadas', title="Peças Pendentes", color='Tipo', color_discrete_map={'Picking': AZUL_ESCURO, 'Packing': AZUL_CLARO_TECADI}), use_container_width=True)
    c_p2.plotly_chart(px.bar(df_p_summary, x='Tipo', y='Linhas totais', title="Linhas Pendentes", color='Tipo', color_discrete_map={'Picking': AZUL_ESCURO, 'Packing': AZUL_CLARO_TECADI}), use_container_width=True)
    c_p3.plotly_chart(px.bar(df_p_summary, x='Tipo', y='Pedidos', title="Pedidos Pendentes", color='Tipo', color_discrete_map={'Picking': AZUL_ESCURO, 'Packing': AZUL_CLARO_TECADI}), use_container_width=True)

with tab3:
    st.subheader("Performance de Entrega Global (Meta: D+2)")
    sla_counts = df_f_filtered['Status_SLA'].value_counts().reset_index()
    st.plotly_chart(px.pie(sla_counts, values='count', names='Status_SLA', hole=0.5, color='Status_SLA', color_discrete_map={'No Prazo': VERDE_SUCESSO, 'Fora do Prazo': VERMELHO_ALERTA}), use_container_width=True)

with tab4:
    st.subheader("Análise Detalhada SLA Packing (D+2)")
    df_pack_p = df_p[df_p['Tipo'] == 'Packing'].copy()
    df_pack_p['Tarefa Packing'] = df_pack_p['Código'].astype(str).str.zfill(6)
    df_pack_p['Data Criação'] = df_pack_p['DT_CRIACAO'].dt.strftime('%d/%m/%Y')
    def extrair_picking(obs):
        match = re.search(r'Trf\.Picking:(\d+)', str(obs))
        return match.group(1) if match else "N/A"
    df_pack_p['Tarefa Picking'] = df_pack_p['Observações'].apply(extrair_picking)
    c1, c2 = st.columns(2)
    with c1:
        fig_f = px.pie(df_f_filtered[df_f_filtered['Tipo'] == 'Packing'], names='Status_SLA', hole=0.4, title="Histórico Packing (Finalizados)", color_discrete_map={'No Prazo': VERDE_SUCESSO, 'Fora do Prazo': VERMELHO_ALERTA})
        st.plotly_chart(fig_f, use_container_width=True)
    with c2:
        fig_p = px.pie(df_pack_p, names='Status_SLA', hole=0.4, title="Situação Atual (Pendentes)", color_discrete_map={'Dentro do Prazo': AZUL_CLARO_TECADI, 'SLA Estourado': VERMELHO_ALERTA})
        st.plotly_chart(fig_p, use_container_width=True)
    st.markdown("#### 🚨 Tabela de Prioridades: Packing Pendente")
    df_tabela = df_pack_p[['Tarefa Packing', 'Tarefa Picking', 'Status', 'Data Criação', 'Dias_Aberto', 'Peças solicitadas', 'Status_SLA']].sort_values('Dias_Aberto', ascending=False)
    st.dataframe(df_tabela, use_container_width=True, hide_index=True)
