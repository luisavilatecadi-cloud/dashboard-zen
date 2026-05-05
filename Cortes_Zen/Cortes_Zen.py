import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import requests
from datetime import datetime

# 1. Configuração da Página
st.set_page_config(page_title="TECADI - Cortes ZEN", page_icon="✂️", layout="wide")

# ---------------------------------------------------------
# 2. ESTILO E CORES PADRÃO TECADI
# ---------------------------------------------------------
AZUL_ESCURO = "#133A68"
AZUL_TECADI = "#1D569B"
AZUL_CLARO_TECADI = "#009FE3"
VERMELHO_CORTE = "#D32F2F"
CINZA_FUNDO = "#F8FAFC"

# Função para formatação milhar brasileira sem decimais
def formatar_br(valor):
    return f"{valor:,.0f}".replace(",", ".")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #FFFFFF; }}
    .dash-header {{ border-left: 10px solid {AZUL_TECADI}; padding-left: 20px; margin-bottom: 20px; }}
    .dash-title {{ color: {AZUL_ESCURO}; font-size: 38px !important; font-weight: 800 !important; }}
    
    /* Sidebar Gradiente */
    [data-testid="stSidebar"] {{ background: linear-gradient(180deg, {AZUL_ESCURO} 0%, {AZUL_TECADI} 100%); }}
    
    /* Títulos da Sidebar */
    .sidebar-label {{
        color: white !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        margin-top: 20px;
        margin-bottom: 10px;
        display: block;
    }}

    /* --- ESTILIZAÇÃO DOS CARDS (FÍSICO, HOVER, COR) --- */
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
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }}
    div[data-testid="stMetric"] label p {{
        color: {AZUL_ESCURO} !important;
        font-size: 16px !important;
        font-weight: 600 !important;
    }}
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
        color: {AZUL_TECADI} !important;
        font-size: 28px !important;
        font-weight: 800 !important;
    }}

    /* --- REMOVENDO ELEMENTOS INDESEJADOS DO SLIDER --- */
    div[data-baseweb="tooltip"] {{ display: none !important; visibility: hidden !important; }}
    div[data-baseweb="slider"] {{ background-color: transparent !important; }}
    div[data-baseweb="slider"] > div > div {{ background: rgba(255, 255, 255, 0.2) !important; }}
    div[data-baseweb="slider"] > div > div > div {{ background: #FFFFFF !important; }}
    div[role="slider"] {{ background-color: {AZUL_CLARO_TECADI} !important; border: 2px solid white !important; box-shadow: none !important; }}
    div[data-baseweb="slider"] div {{ color: white !important; font-weight: 600 !important; }}

    [data-testid="stSidebar"] * {{ outline: none !important; border: none !important; box-shadow: none !important; }}
    [data-testid="stSidebar"] label p {{ color: white !important; }}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. MOTOR DE DADOS
# ---------------------------------------------------------

@st.cache_data(ttl=60)
def load_data():
    url_cmp = "https://tecadi-my.sharepoint.com/:x:/g/personal/luis_avila_tecadi_com_br/IQBpY04fnUXVQanV1HmDAdMsARKUwfgvQAXZZYf0rWhv2t0?download=1"
    url_cortes = "https://tecadi-my.sharepoint.com/:x:/g/personal/luis_avila_tecadi_com_br/IQDLjMQfLyv9S4OOTJtwcU1tAVwF1nq8EGvzlOjKejbdn-o?download=1"
    
    try:
        resp_c = requests.get(url_cmp)
        df_c = pd.read_excel(BytesIO(resp_c.content), engine='openpyxl').drop_duplicates(subset=['PRODUTO'], keep='first')
        
        resp_k = requests.get(url_cortes)
        df_cortes = pd.read_excel(BytesIO(resp_k.content), engine='openpyxl')
        
        df_cortes['Pedido Cliente'] = df_cortes['Pedido Cliente'].ffill()
        df_cortes['DT_FIM_PACKING'] = df_cortes['DT_FIM_PACKING'].ffill()
        df_cortes['DATA_PROCESSADA'] = pd.to_datetime(df_cortes['DT_FIM_PACKING'], errors='coerce')
        df_cortes = df_cortes.dropna(subset=['DATA_PROCESSADA'])
        
        df_cortes = df_cortes.rename(columns={
            'Cod. Produto': 'COD_PRODUTO',
            'Qtd Solicitada': 'QTD_SOLICITADA',
            'Qtd Packing': 'QTD_PACKING',
            'Qtd Corte': 'QTD_CORTE'
        })

        df_final = pd.merge(df_cortes, df_c[['PRODUTO', 'CUSTO_MEDIO_POND']], 
                            left_on='COD_PRODUTO', right_on='PRODUTO', how='left')
        
        df_final['Custo_Unit'] = pd.to_numeric(df_final['CUSTO_MEDIO_POND'], errors='coerce').fillna(0)
        df_final['Valor_Corte'] = df_final['QTD_CORTE'] * df_final['Custo_Unit']
        
        return df_final, None
    except Exception as e:
        return None, str(e)

df, erro = load_data()

if df is not None:
    # --- SIDEBAR COM FILTROS ---
    with st.sidebar:
        st.image("https://tecadi.com.br/wp-content/uploads/2024/01/LOGO-HORIZONTAL_BRANCA_p.png.webp", width=200)
        st.markdown("---")
        
        st.markdown('<span class="sidebar-label">📅 INTERVALO DE TEMPO</span>', unsafe_allow_html=True)
        min_date = df['DATA_PROCESSADA'].min().date()
        max_date = df['DATA_PROCESSADA'].max().date()
        
        date_range = st.slider(
            "Selecione o período",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="DD/MM/YYYY",
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown('<span class="sidebar-label">📦 FILTRAR POR PRODUTO</span>', unsafe_allow_html=True)
        lista_skus = sorted(df['COD_PRODUTO'].unique())
        sku_filt = st.multiselect("Pesquise ou selecione os SKUs", options=lista_skus, label_visibility="collapsed")
        
        df_f = df.copy()
        df_f = df_f[(df_f['DATA_PROCESSADA'].dt.date >= date_range[0]) & 
                    (df_f['DATA_PROCESSADA'].dt.date <= date_range[1])]
        if sku_filt:
            df_f = df_f[df_f['COD_PRODUTO'].isin(sku_filt)]

        st.markdown("---")
        st.markdown("""
            <div style="color: white; opacity: 0.8; font-size: 0.85rem; font-style: italic;">
                💡 Use os filtros acima para atualizar todos os indicadores do dashboard.
            </div>
        """, unsafe_allow_html=True)

    # --- TÍTULO ---
    st.markdown('<div class="dash-header"><div class="dash-title">Análise de Cortes ZEN</div></div>', unsafe_allow_html=True)

    # --- MÉTRICAS (COM FORMATAÇÃO BR E SEM DECIMAIS) ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Volume de Peças", f"{formatar_br(df_f['QTD_CORTE'].sum())} PÇ")
    c2.metric("Valor Total (R$)", f"R$ {formatar_br(df_f['Valor_Corte'].sum())}")
    c3.metric("Total de Pedidos", f"{formatar_br(df_f['Pedido Cliente'].nunique())}")
    c4.metric("Produtos Distintos", f"{formatar_br(df_f['COD_PRODUTO'].nunique())}")

    st.divider()

    # --- ABAS ANALÍTICAS ---
    tab_rs, tab_pc, tab_sku,tab_ped = st.tabs(["💰 Análise Financeira (R$)", "📦 Análise Quantitativa (PÇ)", "🆔 SKU (Diversidade)", "🚚 Análise de Pedidos"])

# ABA R$
    with tab_rs:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Evolução Diária do Prejuízo")
            df_v = df_f.groupby('DATA_PROCESSADA')['Valor_Corte'].sum().reset_index().sort_values('DATA_PROCESSADA')
            
            # --- CRIAÇÃO DO GRÁFICO COM RÓTULOS #K ---
            fig_evol_v = go.Figure()
            fig_evol_v.add_trace(go.Scatter(
                x=df_v['DATA_PROCESSADA'], 
                y=df_v['Valor_Corte'],
                mode='lines+markers+text', # Ativa linha, pontos e texto
                name='Prejuízo',
                line=dict(color=AZUL_TECADI, width=3),
                marker=dict(size=8),
                # Formata o texto: Divide por 1000 e adiciona o 'k'
                text=[f"{v/1000:.1f}k" if v > 0 else "" for v in df_v['Valor_Corte']],
                textposition="top center",
                textfont=dict(size=10, color=AZUL_ESCURO)
            ))

            fig_evol_v.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Data",
                yaxis_title="R$",
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#EEE')
            )
            st.plotly_chart(fig_evol_v, use_container_width=True)
        
        with col2:
            st.subheader("Top 10 SKUs (R$)")
            top_v = df_f.groupby('COD_PRODUTO')['Valor_Corte'].sum().nlargest(10).reset_index()
            fig_top_v = px.bar(top_v, x='Valor_Corte', y='COD_PRODUTO', orientation='h', 
                               color_discrete_sequence=[AZUL_ESCURO], text_auto='.2s')
            fig_top_v.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_top_v, use_container_width=True)

   # ABA PÇ
    with tab_pc:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Evolução Diária de Peças")
            df_q = df_f.groupby('DATA_PROCESSADA')['QTD_CORTE'].sum().reset_index().sort_values('DATA_PROCESSADA')
            
            # --- CRIAÇÃO DO GRÁFICO DE PEÇAS COM RÓTULOS #K ---
            fig_evol_q = go.Figure()
            fig_evol_q.add_trace(go.Scatter(
                x=df_q['DATA_PROCESSADA'], 
                y=df_q['QTD_CORTE'],
                mode='lines+markers+text', # Linha, pontos e rótulos
                name='Peças Cortadas',
                line=dict(color=AZUL_TECADI, width=3),
                marker=dict(size=8),
                # Formata o texto: Se for acima de 1000, mostra #.#k, senão mostra o valor cheio
                text=[f"{v/1000:.1f}k" if v >= 1000 else f"{v:.0f}" for v in df_q['QTD_CORTE']],
                textposition="top center",
                textfont=dict(size=10, color=AZUL_ESCURO)
            ))

            fig_evol_q.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Data",
                yaxis_title="Quantidade (PÇ)",
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#EEE')
            )
            st.plotly_chart(fig_evol_q, use_container_width=True)
            
            st.subheader("Evolução Consolidada (Acumulado PÇ)")
            df_q_sorted = df_q.sort_values('DATA_PROCESSADA')
            df_q_sorted['Pecas_Acumuladas'] = df_q_sorted['QTD_CORTE'].cumsum()
            fig_q_acum = px.area(df_q_sorted, x='DATA_PROCESSADA', y='Pecas_Acumuladas', color_discrete_sequence=[AZUL_CLARO_TECADI])
            fig_q_acum.update_layout(plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Data", yaxis_title="PÇ Acumuladas")
            st.plotly_chart(fig_q_acum, use_container_width=True)
        
        with col2:
            st.subheader("Top 10 SKUs (PÇ)")
            top_q = df_f.groupby('COD_PRODUTO')['QTD_CORTE'].sum().nlargest(10).reset_index()
            fig_top_q = px.bar(top_q, x='QTD_CORTE', y='COD_PRODUTO', orientation='h', 
                               color_discrete_sequence=[AZUL_ESCURO], text_auto='.0f')
            fig_top_q.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_top_q, use_container_width=True)
    # ABA SKU (Quantidade de Códigos Únicos)
    with tab_sku:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Evolução Diária de Diversidade (SKUs)")
            # Agrupamento por data contando valores únicos de COD_PRODUTO
            df_sku_evol = df_f.groupby('DATA_PROCESSADA')['COD_PRODUTO'].nunique().reset_index().sort_values('DATA_PROCESSADA')
            df_sku_evol.columns = ['DATA_PROCESSADA', 'QTD_SKU_UNICO']
            
            # --- CRIAÇÃO DO GRÁFICO DE SKUs ---
            fig_evol_sku = go.Figure()
            fig_evol_sku.add_trace(go.Scatter(
                x=df_sku_evol['DATA_PROCESSADA'], 
                y=df_sku_evol['QTD_SKU_UNICO'],
                mode='lines+markers+text',
                name='SKUs Únicos',
                line=dict(color=AZUL_TECADI, width=3),
                marker=dict(size=8),
                text=[f"{v:.0f}" for v in df_sku_evol['QTD_SKU_UNICO']],
                textposition="top center",
                textfont=dict(size=10, color=AZUL_ESCURO)
            ))

            fig_evol_sku.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Data",
                yaxis_title="Qtd de SKUs Distintos",
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#EEE')
            )
            st.plotly_chart(fig_evol_sku, use_container_width=True)
            
            # Gráfico de barras por dia para facilitar a leitura da "largura" do corte
            st.subheader("Concentração de SKUs por Dia")
            fig_bar_sku = px.bar(df_sku_evol, x='DATA_PROCESSADA', y='QTD_SKU_UNICO', 
                                 color_discrete_sequence=[AZUL_CLARO_TECADI])
            fig_bar_sku.update_layout(plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Data", yaxis_title="SKUs")
            st.plotly_chart(fig_bar_sku, use_container_width=True)
        
        with col2:
            st.subheader("Top 10 Datas com mais Variedade")
            # Seleciona os 10 dias com mais SKUs
            top_datas_sku = df_sku_evol.nlargest(10, 'QTD_SKU_UNICO').copy()
            
            # Formata a data para String (remove a hora e inverte para formato BR)
            top_datas_sku['DATA_STR'] = top_datas_sku['DATA_PROCESSADA'].dt.strftime('%d/%m/%Y')
            
            fig_top_datas = px.bar(
                top_datas_sku, 
                x='QTD_SKU_UNICO', 
                y='DATA_STR', # Usamos a nova coluna formatada
                orientation='h',
                color_discrete_sequence=[AZUL_ESCURO], 
                text_auto=True
            )
            
            fig_top_datas.update_layout(
                yaxis={'categoryorder':'total ascending'}, # Ordena pelo valor
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Qtd SKUs",
                yaxis_title=None,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            st.plotly_chart(fig_top_datas, use_container_width=True)
    # ABA PEDIDOS (Quantidade de Pedidos Únicos)
    with tab_ped:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Evolução Diária de Pedidos com Corte")
            # Agrupamento por data contando Pedidos únicos
            df_ped_evol = df_f.groupby('DATA_PROCESSADA')['Pedido Cliente'].nunique().reset_index().sort_values('DATA_PROCESSADA')
            df_ped_evol.columns = ['DATA_PROCESSADA', 'QTD_PED_UNICO']
            
            # --- GRÁFICO DE EVOLUÇÃO ---
            fig_evol_ped = go.Figure()
            fig_evol_ped.add_trace(go.Scatter(
                x=df_ped_evol['DATA_PROCESSADA'], 
                y=df_ped_evol['QTD_PED_UNICO'],
                mode='lines+markers+text',
                name='Pedidos',
                line=dict(color=AZUL_TECADI, width=3),
                marker=dict(size=8),
                text=[f"{v:.0f}" for v in df_ped_evol['QTD_PED_UNICO']],
                textposition="top center",
                textfont=dict(size=10, color=AZUL_ESCURO)
            ))

            fig_evol_ped.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Data",
                yaxis_title="Qtd de Pedidos Únicos",
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#EEE')
            )
            st.plotly_chart(fig_evol_ped, use_container_width=True)
            
            # Gráfico de Área para Volume Acumulado de Pedidos no período
            st.subheader("Pedidos Afetados (Acumulado no Período)")
            df_ped_evol['PED_ACUM'] = df_ped_evol['QTD_PED_UNICO'].cumsum()
            fig_ped_acum = px.area(df_ped_evol, x='DATA_PROCESSADA', y='PED_ACUM', 
                                   color_discrete_sequence=[AZUL_CLARO_TECADI])
            fig_ped_acum.update_layout(plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Data", yaxis_title="Pedidos Acumulados")
            st.plotly_chart(fig_ped_acum, use_container_width=True)
        
        with col2:
            st.subheader("Top 10 Datas (Volume de Pedidos)")
            top_datas_ped = df_ped_evol.nlargest(10, 'QTD_PED_UNICO').copy()
            
            # Formatação de data sem horas para o eixo Y
            top_datas_ped['DATA_STR'] = top_datas_ped['DATA_PROCESSADA'].dt.strftime('%d/%m/%Y')
            
            fig_top_ped = px.bar(
                top_datas_ped, 
                x='QTD_PED_UNICO', 
                y='DATA_STR',
                orientation='h',
                color_discrete_sequence=[AZUL_ESCURO], 
                text_auto=True
            )
            
            fig_top_ped.update_layout(
                yaxis={'categoryorder':'total ascending'},
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Nº de Pedidos",
                yaxis_title=None
            )
            st.plotly_chart(fig_top_ped, use_container_width=True)
    st.divider()
    
    

    # --- RECORRÊNCIA ---
    st.subheader("🔄 Frequência de Cortes por SKU")
    df_rec = df_f.groupby('COD_PRODUTO').size().reset_index(name='Vezes Cortado').sort_values('Vezes Cortado', ascending=False)
    col_r1, col_r2 = st.columns([2, 1])
    with col_r1:
        fig_rec = px.bar(df_rec.head(15), x='COD_PRODUTO', y='Vezes Cortado', 
                         color_discrete_sequence=[AZUL_TECADI], text_auto=True)
        fig_rec.update_layout(plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_rec, use_container_width=True)
    with col_r2:
        st.write("Frequência Detalhada")
        st.dataframe(df_rec, use_container_width=True, hide_index=True)

    st.divider()

    # --- TABELA DE DADOS ---
    st.subheader("🔍 Detalhamento dos Itens")
    
    tf1, tf2, tf3 = st.columns(3)
    with tf1:
        search_ped = st.text_input("🔍 Filtrar por Pedido")
    with tf2:
        search_sku = st.text_input("📦 Filtrar por Código Produto")
    with tf3:
        unique_dates_f = sorted(df_f['DATA_PROCESSADA'].dt.date.unique(), reverse=True)
        search_date = st.multiselect("📅 Filtrar por Data", options=unique_dates_f)

    df_tab = df_f.copy()
    if search_ped:
        df_tab = df_tab[df_tab['Pedido Cliente'].astype(str).str.contains(search_ped, case=False)]
    if search_sku:
        df_tab = df_tab[df_tab['COD_PRODUTO'].astype(str).str.contains(search_sku, case=False)]
    if search_date:
        df_tab = df_tab[df_tab['DATA_PROCESSADA'].dt.date.isin(search_date)]

    df_tab_view = df_tab.rename(columns={
        'DATA_PROCESSADA': 'Data Packing',
        'Pedido Cliente': 'Pedido',
        'COD_PRODUTO': 'Cod. Produto',
        'QTD_SOLICITADA': 'Qtd Solicitada',
        'QTD_PACKING': 'Qtd Atendida',
        'QTD_CORTE': 'Qtd Corte',
        'Valor_Corte': 'Valor Corte (R$)'
    })

    st.dataframe(
        df_tab_view[['Data Packing', 'Pedido', 'Cod. Produto', 'Qtd Solicitada', 'Qtd Atendida', 'Qtd Corte', 'Valor Corte (R$)']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Data Packing": st.column_config.DateColumn("Data Packing", format="DD/MM/YYYY"),
            "Valor Corte (R$)": st.column_config.NumberColumn("Valor Corte (R$)", format="R$ %.0f"), # Sem decimais
            "Qtd Solicitada": st.column_config.NumberColumn(format="%.0f"),
            "Qtd Atendida": st.column_config.NumberColumn(format="%.0f"),
            "Qtd Corte": st.column_config.NumberColumn(format="%.0f")
        }
    )
