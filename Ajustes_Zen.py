import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import requests

# 1. Configuração da Página
st.set_page_config(page_title="TECADI - Acuracidade ZEN", page_icon="🎯", layout="wide")

# ---------------------------------------------------------
# 2. ESTILO VISUAL E TRADUÇÃO
# ---------------------------------------------------------
AZUL_ESCURO, AZUL_TECADI, VERMELHO_FALTA, VERDE_SOBRA = "#133A68", "#1D569B", "#D32F2F", "#2E7D32"

MESES_MAP = {
    'January': 'Jan', 'February': 'Fev', 'March': 'Mar', 'April': 'Abr',
    'May': 'Mai', 'June': 'Jun', 'July': 'Jul', 'August': 'Ago',
    'September': 'Set', 'October': 'Out', 'November': 'Nov', 'December': 'Dez'
}

st.markdown(f"""
    <style>
    .stApp {{ background-color: #FFFFFF; }}
    .dash-header {{ border-left: 10px solid {AZUL_TECADI}; padding-left: 20px; margin-bottom: 20px; }}
    .dash-title {{ color: {AZUL_ESCURO}; font-size: 38px !important; font-weight: 800 !important; }}
    
    /* ESTILIZAÇÃO DA SIDEBAR */
    [data-testid="stSidebar"] {{ 
        background: linear-gradient(180deg, {AZUL_ESCURO} 0%, {AZUL_TECADI} 100%); 
        min-width: 300px !important;
    }}
    
    /* Logo centralizado na Sidebar */
    .sidebar-logo-container {{
        text-align: center;
        padding: 20px 0px;
        margin-bottom: 10px;
    }}

    /* Textos dos Filtros em Negrito e Branco */
    [data-testid="stSidebar"] label p {{
        color: white !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    /* Ajuste de cor de títulos secundários na sidebar */
    [data-testid="stSidebar"] .stMarkdown h3 {{
        color: #FFFFFF !important;
        border-bottom: 1px solid rgba(255,255,255,0.2);
        padding-bottom: 10px;
    }}

    div[data-testid="stMetric"] {{
        border-radius: 10px !important;
        padding: 15px !important;
        border: 1px solid #E2E8F0 !important;
        transition: transform 0.2s ease;
    }}
    div[data-testid="stMetric"]:hover {{ 
        transform: translateY(-5px); 
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
    }}
    
    [data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stMetric"] {{ background-color: #F0FDF4 !important; border-left: 5px solid {VERDE_SOBRA} !important; }}
    [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stMetric"] {{ background-color: #FEF2F2 !important; border-left: 5px solid {VERMELHO_FALTA} !important; }}
    [data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stMetric"] {{ background-color: #F8FAFC !important; border-left: 5px solid {AZUL_TECADI} !important; }}
    [data-testid="stHorizontalBlock"] > div:nth-child(4) [data-testid="stMetric"] {{ background-color: #F0FDF4 !important; border-left: 5px solid {VERDE_SOBRA} !important; }}
    [data-testid="stHorizontalBlock"] > div:nth-child(5) [data-testid="stMetric"] {{ background-color: #FEF2F2 !important; border-left: 5px solid {VERMELHO_FALTA} !important; }}
    
    [data-testid="stMetricValue"] > div {{ font-size: 26px !important; font-weight: 800 !important; color: {AZUL_ESCURO} !important; }}
    [data-testid="stMetricLabel"] p {{ font-size: 13px !important; color: #475569 !important; font-weight: 600 !important; }}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. MOTOR DE DADOS
# ---------------------------------------------------------

@st.cache_data(ttl=3600)
def load_data():
    url_cmp = "https://tecadi-my.sharepoint.com/:x:/g/personal/luis_avila_tecadi_com_br/IQBpY04fnUXVQanV1HmDAdMsARKUwfgvQAXZZYf0rWhv2t0?download=1"
    url_kardex = "https://tecadi-my.sharepoint.com/:x:/g/personal/luis_avila_tecadi_com_br/IQD-_9KS9a3XQKv8SYwEidTUASpjTiD5xu0SKD5sj0nFqro?download=1"
    
    try:
        resp_k = requests.get(url_kardex)
        df_raw = pd.read_excel(BytesIO(resp_k.content), engine='openpyxl')
        resp_c = requests.get(url_cmp)
        df_c = pd.read_excel(BytesIO(resp_c.content), engine='openpyxl').drop_duplicates(subset=['PRODUTO'], keep='first')

        if 'Observacao' in df_raw.columns:
            df_raw = df_raw[~df_raw['Observacao'].fillna('').str.lower().str.contains('excluir')]
            df_raw = df_raw[df_raw['Observacao'].fillna('').str.lower().str.contains('inv')]

        df_raw['Data_Completa'] = pd.to_datetime(df_raw['Data'], dayfirst=True)
        df_raw['Data_Dia'] = df_raw['Data_Completa'].dt.normalize()
        df_raw['Somente_Data'] = df_raw['Data_Completa'].dt.strftime('%d/%m/%Y')
        
        df_raw['Qtd_Sinal'] = df_raw.apply(
            lambda x: x['Quantidade'] if str(x['Tipo Mov']).upper() == 'ENTRADA' else -x['Quantidade'], axis=1
        )

        df_net = df_raw.groupby(['Somente_Data', 'Data_Dia', 'Produto', 'Localizacao']).agg({
            'Qtd_Sinal': 'sum', 'Usuario': 'first'
        }).reset_index()

        df_ajustes = df_net[df_net['Qtd_Sinal'] != 0].copy()
        df_final = pd.merge(df_ajustes, df_c[['PRODUTO', 'CUSTO_MEDIO_POND']], left_on='Produto', right_on='PRODUTO', how='left')
        
        df_final['Custo_Unit'] = pd.to_numeric(df_final['CUSTO_MEDIO_POND'], errors='coerce').fillna(0)
        df_final['Valor (R$)'] = df_final['Qtd_Sinal'] * df_final['Custo_Unit']
        df_final['Mes_Ano_Sort'] = df_final['Data_Dia'].dt.to_period('M')
        df_final['Mes_Nome_EN'] = df_final['Data_Dia'].dt.strftime('%B')
        df_final['Mes_Ano'] = df_final['Mes_Nome_EN'].map(MESES_MAP) + df_final['Data_Dia'].dt.strftime('/%Y')
        
        return df_final, None
    except Exception as e: 
        return None, f"Erro ao acessar SharePoint: {str(e)}"

df, erro = load_data()

if erro:
    st.error(f"❌ {erro}")
elif df is not None:
    # --- CONTEÚDO DA SIDEBAR ---
    with st.sidebar:
        # Logo da Empresa (Uso do st.image para melhor compatibilidade)
        st.image("https://tecadi.com.br/wp-content/uploads/2024/01/LOGO-HORIZONTAL_BRANCA_p.png.webp", width=200)
        
        st.markdown("### ⚙️ PAINEL DE FILTROS")
        
        meses_disponiveis = df.sort_values('Mes_Ano_Sort', ascending=False)['Mes_Ano'].unique()
        mes_filt = st.multiselect("📅 PERÍODO (MÊS/ANO)", options=meses_disponiveis)
        
        prod_global_filt = st.multiselect("📦 PRODUTO ESPECÍFICO", options=sorted(df['Produto'].unique()))
        
        st.markdown("---")
        
        # Texto de ajuda com cor forçada para branco via HTML/CSS inline
        st.markdown("""
            <div style="color: white; opacity: 0.8; font-size: 0.85rem; font-style: italic;">
                💡 Use os filtros acima para atualizar todos os indicadores do dashboard.
            </div>
        """, unsafe_allow_html=True)

    # Lógica de Filtros
    df_f = df.copy()
    if mes_filt: df_f = df_f[df_f['Mes_Ano'].isin(mes_filt)]
    if prod_global_filt: df_f = df_f[df_f['Produto'].isin(prod_global_filt)]

    st.markdown('<div class="dash-header"><div class="dash-title">Balanço de Inventário ZEN</div></div>', unsafe_allow_html=True)
    
    aba_resumo, aba_faltas, aba_sobras, aba_logs = st.tabs([
        "📊 Visão Geral", "📉 Faltas Ativas", "📈 Sobras Ativas", "🔍 Consulta de Logs"
    ])

    # --- ABA 1: VISÃO GERAL ---
    with aba_resumo:
        v_sobra_total = df_f[df_f['Qtd_Sinal'] > 0]['Valor (R$)'].sum()
        v_falta_total = df_f[df_f['Qtd_Sinal'] < 0]['Valor (R$)'].sum()
        total_liq = v_sobra_total + v_falta_total

        df_ativos = df_f.groupby(['Produto', 'Localizacao']).agg({'Qtd_Sinal': 'sum', 'Custo_Unit': 'mean'}).reset_index()
        df_ativos['Valor_Ativo'] = df_ativos['Qtd_Sinal'] * df_ativos['Custo_Unit']
        v_sobra_ativa = df_ativos[df_ativos['Qtd_Sinal'] > 0]['Valor_Ativo'].sum()
        v_falta_ativa = df_ativos[df_ativos['Qtd_Sinal'] < 0]['Valor_Ativo'].sum()

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Sobras (Período)", f"R$ {v_sobra_total:,.0f}")
        c2.metric("Faltas (Período)", f"R$ {abs(v_falta_total):,.0f}")
        c3.metric("Saldo Líquido", f"R$ {total_liq:,.0f}")
        c4.metric("Sobra Ativa (Estoque)", f"R$ {v_sobra_ativa:,.0f}")
        c5.metric("Falta Ativa (Estoque)", f"R$ -{abs(v_falta_ativa):,.0f}")

        st.divider()
        st.subheader("📈 Histórico de Impacto Acumulado")
        df_hist = df_f.groupby('Data_Dia')['Valor (R$)'].sum().reset_index().sort_values('Data_Dia')
        df_hist['Acumulado'] = df_hist['Valor (R$)'].cumsum()
        
        cor_hist = VERDE_SOBRA if total_liq >= 0 else VERMELHO_FALTA
        fill_hist = "rgba(46, 125, 50, 0.1)" if total_liq >= 0 else "rgba(211, 47, 47, 0.1)"

        fig_evolucao = go.Figure()
        fig_evolucao.add_trace(go.Scatter(
            x=df_hist['Data_Dia'], y=df_hist['Acumulado'], mode='lines+markers+text',
            line=dict(color=cor_hist, width=3), fill='tozeroy', fillcolor=fill_hist,
            text=[f"R$ {v/1000:.1f}k" if i % 5 == 0 else "" for i, v in enumerate(df_hist['Acumulado'])],
            textposition="top center"
        ))
        fig_evolucao.add_hline(y=0, line_dash="dash", line_color="#333", opacity=0.5)
        fig_evolucao.update_layout(xaxis_title="Data", yaxis_title="Acumulado (R$)", plot_bgcolor='white')
        st.plotly_chart(fig_evolucao, use_container_width=True)

        st.divider()
        st.subheader("📅 Impacto Financeiro por Dia (Ajustes Brutos)")
        df_dia = df_f.groupby('Data_Dia')['Valor (R$)'].sum().reset_index()
        df_dia['Cor'] = df_dia['Valor (R$)'].apply(lambda x: VERDE_SOBRA if x >= 0 else VERMELHO_FALTA)
        
        fig_diario = go.Figure()
        fig_diario.add_trace(go.Bar(x=df_dia['Data_Dia'], y=df_dia['Valor (R$)'], marker_color=df_dia['Cor'], text=df_dia['Valor (R$)'].apply(lambda x: f"R$ {x/1000:.1f}k"), textposition='auto'))
        fig_diario.update_layout(xaxis_title="Data", yaxis_title="Valor (R$)", plot_bgcolor='white', height=400)
        st.plotly_chart(fig_diario, use_container_width=True)

    # --- ABA 2: FALTAS ATIVAS ---
    with aba_faltas:
        df_resumo_ativo = df_f.groupby('Produto').agg({'Qtd_Sinal': 'sum', 'Custo_Unit': 'mean', 'Valor (R$)': 'sum'}).reset_index()
        df_faltas = df_resumo_ativo[df_resumo_ativo['Qtd_Sinal'] < 0].copy()
        
        st.subheader("Maiores Impactos de Falta (Top 10)")
        c1, c2 = st.columns(2)
        with c1:
            top_f_fin = df_faltas.sort_values('Valor (R$)', ascending=True).head(10)
            fig_f1 = px.bar(top_f_fin, x='Valor (R$)', y='Produto', orientation='h', title="Por Valor (R$)", text_auto='.2s', color_discrete_sequence=[VERMELHO_FALTA])
            fig_f1.update_layout(yaxis={'categoryorder':'total descending'}, showlegend=False, height=450)
            st.plotly_chart(fig_f1, use_container_width=True)
        with c2:
            top_f_qtd = df_faltas.sort_values('Qtd_Sinal', ascending=True).head(10)
            fig_f2 = px.bar(top_f_qtd, x='Qtd_Sinal', y='Produto', orientation='h', title="Por Quantidade (PÇ)", text_auto='.0f', color_discrete_sequence=[VERMELHO_FALTA])
            fig_f2.update_layout(yaxis={'categoryorder':'total descending'}, showlegend=False, height=450)
            st.plotly_chart(fig_f2, use_container_width=True)
        
        st.markdown("### 📋 Listagem Completa de Faltas")
        f_prod_faltas = st.multiselect("Filtrar Produto (Tabela):", options=sorted(df_faltas['Produto'].unique()), key="filter_faltas")
        df_faltas_view = df_faltas[df_faltas['Produto'].isin(f_prod_faltas)] if f_prod_faltas else df_faltas
        
        st.dataframe(
            df_faltas_view.sort_values('Valor (R$)', ascending=True), 
            use_container_width=True, hide_index=True, 
            column_config={
                "Qtd_Sinal": st.column_config.NumberColumn("Quantidade", format="%d"),
                "Custo_Unit": st.column_config.NumberColumn("Custo Unit.", format="R$ %.2f"), 
                "Valor (R$)": st.column_config.NumberColumn("Valor Total", format="R$ %,.2f")
            }
        )

    # --- ABA 3: SOBRAS ATIVAS ---
    with aba_sobras:
        df_resumo_ativo = df_f.groupby('Produto').agg({'Qtd_Sinal': 'sum', 'Custo_Unit': 'mean', 'Valor (R$)': 'sum'}).reset_index()
        df_sobras = df_resumo_ativo[df_resumo_ativo['Qtd_Sinal'] > 0].copy()
        
        st.subheader("Maiores Impactos de Sobra (Top 10)")
        c3, c4 = st.columns(2)
        with c3:
            top_s_fin = df_sobras.sort_values('Valor (R$)', ascending=False).head(10)
            fig_s1 = px.bar(top_s_fin, x='Valor (R$)', y='Produto', orientation='h', title="Por Valor (R$)", text_auto='.2s', color_discrete_sequence=[VERDE_SOBRA])
            fig_s1.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, height=450)
            st.plotly_chart(fig_s1, use_container_width=True)
        with c4:
            top_s_qtd = df_sobras.sort_values('Qtd_Sinal', ascending=False).head(10)
            fig_s2 = px.bar(top_s_qtd, x='Qtd_Sinal', y='Produto', orientation='h', title="Por Quantidade (PÇ)", text_auto='.0f', color_discrete_sequence=[VERDE_SOBRA])
            fig_s2.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, height=450)
            st.plotly_chart(fig_s2, use_container_width=True)
        
        st.markdown("### 📋 Listagem Completa de Sobras")
        f_prod_sobras = st.multiselect("Filtrar Produto (Tabela):", options=sorted(df_sobras['Produto'].unique()), key="filter_sobras")
        df_sobras_view = df_sobras[df_sobras['Produto'].isin(f_prod_sobras)] if f_prod_sobras else df_sobras

        st.dataframe(
            df_sobras_view.sort_values('Valor (R$)', ascending=False), 
            use_container_width=True, hide_index=True,
            column_config={
                "Qtd_Sinal": st.column_config.NumberColumn("Quantidade", format="%d"),
                "Custo_Unit": st.column_config.NumberColumn("Custo Unit.", format="R$ %.2f"), 
                "Valor (R$)": st.column_config.NumberColumn("Valor Total", format="R$ %,.2f")
            }
        )

    # --- ABA 4: LOGS ---
    with aba_logs:
        st.subheader("📋 Detalhamento de Movimentações")
        cl1, cl2, cl3 = st.columns(3)
        with cl1: f_data_log = st.multiselect("Filtrar Data:", options=sorted(df_f['Somente_Data'].unique()))
        with cl2: f_loc_log = st.multiselect("Filtrar Localização:", options=sorted(df_f['Localizacao'].unique()))
        with cl3: f_prod_log = st.multiselect("Filtrar Produto:", options=sorted(df_f['Produto'].unique()))

        df_display = df_f[['Somente_Data', 'Localizacao', 'Produto', 'Qtd_Sinal', 'Custo_Unit', 'Valor (R$)', 'Usuario']].copy()
        
        if f_data_log: df_display = df_display[df_display['Somente_Data'].isin(f_data_log)]
        if f_loc_log: df_display = df_display[df_display['Localizacao'].isin(f_loc_log)]
        if f_prod_log: df_display = df_display[df_display['Produto'].isin(f_prod_log)]

        df_display.columns = ['Data', 'Localização', 'Produto', 'Qtd', 'Custo Unit.', 'Valor Total', 'Usuário']
        st.dataframe(
            df_display.sort_values('Data', ascending=False), 
            use_container_width=True, hide_index=True,
            column_config={
                "Valor Total": st.column_config.NumberColumn("Valor Total", format="R$ %,.2f"),
                "Custo Unit.": st.column_config.NumberColumn("Custo Unit.", format="R$ %.2f")
            }
        )
