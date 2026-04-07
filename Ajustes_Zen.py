import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# 1. Configuração da Página
st.set_page_config(page_title="TECADI - Acuracidade ZEN", page_icon="🎯", layout="wide")

# ---------------------------------------------------------
# 2. ESTILO VISUAL TECADI (CSS Customizado)
# ---------------------------------------------------------
AZUL_ESCURO, AZUL_TECADI, VERMELHO_FALTA, VERDE_SOBRA = "#133A68", "#1D569B", "#D32F2F", "#2E7D32"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #FFFFFF; }}
    .dash-header {{ border-left: 10px solid {AZUL_TECADI}; padding-left: 20px; margin-bottom: 20px; }}
    .dash-title {{ color: {AZUL_ESCURO}; font-size: 38px !important; font-weight: 800 !important; }}
    
    [data-testid="stSidebar"] {{ 
        background: linear-gradient(180deg, {AZUL_ESCURO} 0%, {AZUL_TECADI} 100%); 
    }}
    
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{ 
        color: white !important; 
    }}

    [data-testid="stSidebar"] .stMultiSelect span[data-baseweb="tag"] {{
        background-color: white !important;
        color: {AZUL_ESCURO} !important;
    }}
    
    [data-testid="stSidebar"] svg {{ fill: white !important; }}

    [data-testid="stMetric"] {{ 
        background-color: #F8FAFC !important; 
        border-radius: 12px !important; 
        border: 1px solid #E2E8F0 !important; 
        padding: 15px; 
    }}
    [data-testid="stMetricValue"] > div {{ color: {AZUL_ESCURO} !important; font-weight: 800 !important; }}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. MOTOR DE DADOS
# ---------------------------------------------------------
@st.cache_data
def load_data():
    f_kardex, f_custos = "Kardex (30).xlsx", "CMP.xlsx"
    if not os.path.exists(f_kardex): return None, f"Arquivo '{f_kardex}' não encontrado."
    
    try:
        df_raw = pd.read_excel(f_kardex, engine='openpyxl')
        df_c = pd.read_excel(f_custos, engine='openpyxl').drop_duplicates(subset=['PRODUTO'], keep='first') if os.path.exists(f_custos) else pd.DataFrame(columns=['PRODUTO', 'CUSTO_MEDIO_POND'])

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
            'Qtd_Sinal': 'sum',
            'Usuario': 'first'
        }).reset_index()

        df_ajustes = df_net[df_net['Qtd_Sinal'] != 0].copy()
        df_final = pd.merge(df_ajustes, df_c[['PRODUTO', 'CUSTO_MEDIO_POND']], left_on='Produto', right_on='PRODUTO', how='left')
        
        df_final['Custo_Unit'] = pd.to_numeric(df_final['CUSTO_MEDIO_POND'], errors='coerce').fillna(0)
        df_final['Valor (R$)'] = df_final['Qtd_Sinal'] * df_final['Custo_Unit']
        df_final['Mes_Ano_Sort'] = df_final['Data_Dia'].dt.to_period('M')
        df_final['Mes_Ano'] = df_final['Data_Dia'].dt.strftime('%m/%Y')
        
        return df_final, None
    except Exception as e: return None, str(e)

df, erro = load_data()

if erro:
    st.error(f"❌ Erro ao processar: {erro}")
elif df is not None:
    # --- SIDEBAR ---
    st.sidebar.markdown("### ⚙️ Filtros Gerais")
    meses_disponiveis = df.sort_values('Mes_Ano_Sort', ascending=False)['Mes_Ano'].unique()
    mes_filt = st.sidebar.multiselect("📅 Mês/Ano", options=meses_disponiveis)
    prod_global_filt = st.sidebar.multiselect("📦 Produto (Global)", options=sorted(df['Produto'].unique()))

    df_f = df.copy()
    if mes_filt: df_f = df_f[df_f['Mes_Ano'].isin(mes_filt)]
    if prod_global_filt: df_f = df_f[df_f['Produto'].isin(prod_global_filt)]

    st.markdown('<div class="dash-header"><div class="dash-title">Balanço de Inventário ZEN</div></div>', unsafe_allow_html=True)
    aba_resumo, aba_rankings, aba_logs = st.tabs(["📊 Visão Geral", "🏆 Top Rankings", "🔍 Consulta de Logs"])

    # --- ABA 1: VISÃO GERAL ---
    with aba_resumo:
        v_sobra = df_f[df_f['Qtd_Sinal'] > 0]['Valor (R$)'].sum()
        v_falta = df_f[df_f['Qtd_Sinal'] < 0]['Valor (R$)'].sum()
        total_liq = v_sobra + v_falta
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Sobras Financeiras", f"R$ {v_sobra:,.2f}")
        m2.metric("Faltas Financeiras", f"R$ {abs(v_falta):,.2f}")
        m3.metric("Resultado Líquido", f"R$ {total_liq:,.2f}")

        # Gráfico 1: Acumulado (REVERTIDO PARA CORES ORIGINAIS DINÂMICAS)
        st.subheader("📈 Histórico de Impacto Acumulado")
        df_hist = df_f.groupby('Data_Dia')['Valor (R$)'].sum().reset_index().sort_values('Data_Dia')
        df_hist['Acumulado'] = df_hist['Valor (R$)'].cumsum()
        
        cor_linha_din = VERDE_SOBRA if total_liq >= 0 else VERMELHO_FALTA
        cor_fill_din = "rgba(46, 125, 50, 0.2)" if total_liq >= 0 else "rgba(211, 47, 47, 0.2)"

        fig_evolucao = go.Figure()
        fig_evolucao.add_trace(go.Scatter(
            x=df_hist['Data_Dia'], y=df_hist['Acumulado'],
            mode='lines+markers', line=dict(color=cor_linha_din, width=4),
            fill='tozeroy', fillcolor=cor_fill_din, name='Saldo Acumulado'
        ))
        fig_evolucao.add_hline(y=0, line_dash="dash", line_color="#333")
        fig_evolucao.update_layout(xaxis_title="Data", yaxis_title="Acumulado (R$)", hovermode="x unified")
        st.plotly_chart(fig_evolucao, use_container_width=True)

        # Gráfico 2: Resumo Financeiro Mensal (Ajuste Azul Tecadi + Fonte)
        st.subheader("🗓️ Resumo Financeiro por Mês")
        df_mensal = df_f.groupby(['Mes_Ano_Sort', 'Mes_Ano'])['Valor (R$)'].sum().reset_index().sort_values('Mes_Ano_Sort')
        
        fig_mensal = px.bar(
            df_mensal, x='Mes_Ano', y='Valor (R$)',
            text_auto='.2s',
            color_discrete_sequence=[AZUL_TECADI]
        )
        fig_mensal.update_layout(
            xaxis_title="Mês/Ano", yaxis_title="Saldo Mensal (R$)",
            font=dict(size=14),
            showlegend=False
        )
        st.plotly_chart(fig_mensal, use_container_width=True)

   # --- ABA 2: RANKINGS ---
    with aba_rankings:
        st.markdown("### 🚨 Rankings de Impacto de Inventário")
        
        df_resumo = df_f.groupby('Produto').agg({'Qtd_Sinal': 'sum', 'Valor (R$)': 'sum'}).reset_index()
        
        # Função para estilizar os gráficos conforme solicitado
        def style_ranking_charts(fig):
            fig.update_traces(
                textposition='inside', 
                textfont=dict(
                    color="white", 
                    size=14,          # Fonte ajustada (um pouco menor que a anterior)
                    family="Arial"    # Fonte padrão limpa
                ),
                insidetextanchor='middle'
            )
            fig.update_layout(
                showlegend=False,
                height=550,           # Altura para manter barras com boa espessura
                margin=dict(l=20, r=20, t=50, b=20),
                yaxis={'categoryorder':'total ascending'}
            )
            return fig

        # Seção de Faltas
        st.subheader("📉 Top 15 Faltas")
        c1, c2 = st.columns(2)
        with c1:
            top_f_fin = df_resumo.sort_values('Valor (R$)', ascending=True).head(15)
            fig1 = px.bar(top_f_fin, x='Valor (R$)', y='Produto', orientation='h', 
                          title="Financeiro (R$)", text_auto='.2s',
                          color_discrete_sequence=[AZUL_TECADI])
            st.plotly_chart(style_ranking_charts(fig1), use_container_width=True)
            
        with c2:
            top_f_qtd = df_resumo.sort_values('Qtd_Sinal', ascending=True).head(15)
            fig2 = px.bar(top_f_qtd, x='Qtd_Sinal', y='Produto', orientation='h', 
                          title="Quantidade (PÇ)", text_auto='.0f',
                          color_discrete_sequence=[AZUL_TECADI])
            st.plotly_chart(style_ranking_charts(fig2), use_container_width=True)

        st.divider()

        # Seção de Sobras
        st.subheader("📈 Top 15 Sobras")
        c3, c4 = st.columns(2)
        with c3:
            top_s_fin = df_resumo.sort_values('Valor (R$)', ascending=False).head(15)
            fig3 = px.bar(top_s_fin, x='Valor (R$)', y='Produto', orientation='h', 
                          title="Financeiro (R$)", text_auto='.2s',
                          color_discrete_sequence=[AZUL_TECADI])
            st.plotly_chart(style_ranking_charts(fig3), use_container_width=True)
            
        with c4:
            top_s_qtd = df_resumo.sort_values('Qtd_Sinal', ascending=False).head(15)
            fig4 = px.bar(top_s_qtd, x='Qtd_Sinal', y='Produto', orientation='h', 
                          title="Quantidade (PÇ)", text_auto='.0f',
                          color_discrete_sequence=[AZUL_TECADI])
            st.plotly_chart(style_ranking_charts(fig4), use_container_width=True)
    # --- ABA 3: LOGS ---
    with aba_logs:
        st.subheader("📋 Detalhamento de Movimentações")
        c1, c2, c3 = st.columns(3)
        with c1: log_local = st.multiselect("📍 Localização", options=sorted(df_f['Localizacao'].unique()))
        with c2: log_prod = st.multiselect("📦 Produto", options=sorted(df_f['Produto'].unique()))
        with c3: log_data = st.date_input("📅 Intervalo", value=(df_f['Data_Dia'].min(), df_f['Data_Dia'].max()))

        df_l = df_f.copy()
        if log_local: df_l = df_l[df_l['Localizacao'].isin(log_local)]
        if log_prod: df_l = df_l[df_l['Produto'].isin(log_prod)]
        if isinstance(log_data, tuple) and len(log_data) == 2:
            df_l = df_l[(df_l['Data_Dia'].dt.date >= log_data[0]) & (df_l['Data_Dia'].dt.date <= log_data[1])]
            
        # Formatação para exibição (REMOVIDO HORA)
        df_display = df_l.copy()
        df_display = df_display[['Somente_Data', 'Localizacao', 'Produto', 'Qtd_Sinal', 'Custo_Unit', 'Valor (R$)', 'Usuario']]
        df_display.columns = ['Data', 'Localização', 'Produto', 'Qtd', 'Custo Unit.', 'Valor Total', 'Usuário']

        st.dataframe(
            df_display.sort_values('Data', ascending=False),
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Custo Unit.": st.column_config.NumberColumn("Custo Unit.", format="R$ %.2f"),
                "Valor Total": st.column_config.NumberColumn("Valor Total", format="R$ %.2f"),
                "Qtd": st.column_config.NumberColumn("Qtd", format="%d")
            }
        )