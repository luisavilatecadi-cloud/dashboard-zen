import streamlit as st

# 1. Configuração da Página
st.set_page_config(
    page_title="TECADI - Hub Acuracidade",
    page_icon="🏢",
    layout="wide"
)

# 2. Estilização Estilo "Netflix Corporativo"
st.markdown("""
    <style>
    .stApp {
        background-color: #050C16;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    .logo-container { padding: 20px 0; }

    .hero-title {
        color: #009FE3; 
        font-size: 50px;
        font-weight: 700;
        margin-bottom: 0px;
        letter-spacing: -1px;
    }
    
    .hero-subtitle {
        color: white;
        font-size: 18px;
        font-weight: 500;
        margin-bottom: 40px;
        text-transform: uppercase;
        letter-spacing: 2px;
        opacity: 0.8;
    }

    .category-title {
        color: #FFFFFF;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 20px;
        border-left: 4px solid #009FE3;
        padding-left: 15px;
    }

    .netflix-card {
        background-color: #0B1E33;
        border-radius: 8px;
        padding: 0px;
        transition: transform 0.4s ease, border-color 0.4s ease;
        border: 1px solid #1D569B;
        overflow: hidden;
        height: 240px;
        display: flex;
        flex-direction: column;
        position: relative; 
    }

    /* Target _blank evita o loop de redirecionamento do Streamlit Cloud */
    .full-card-link {
        position: absolute;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        text-decoration: none;
        z-index: 10;
    }

    .netflix-card:hover {
        transform: scale(1.05);
        border-color: #009FE3;
        box-shadow: 0 10px 20px rgba(0, 159, 227, 0.3);
    }

    .card-banner {
        height: 100px;
        background: linear-gradient(135deg, #133A68 0%, #1D569B 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 45px;
    }

    .card-content {
        padding: 20px;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .card-title-text {
        color: white;
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .card-desc {
        color: #A0AEC0;
        font-size: 14px;
        line-height: 1.4;
    }

    .footer {
        margin-top: 80px;
        padding: 30px;
        border-top: 1px solid #1D569B;
        color: #4A5568;
        font-size: 12px;
        text-align: left;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Header Principal
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
st.image("https://tecadi.com.br/wp-content/uploads/2024/01/LOGO-HORIZONTAL_BRANCA_p.png.webp", width=180)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<h1 class="hero-title">Hub Acuracidade</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Gestão ZEN • Inteligência de Dados</p>', unsafe_allow_html=True)

# 4. Grid de Dashboards
st.markdown('<p class="category-title">Dashboards Disponíveis</p>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
        <div class="netflix-card">
            <a href="https://acuracidade-zen-cortes-de-pedido.streamlit.app/" target="_blank" class="full-card-link"></a>
            <div class="card-banner">✂️</div>
            <div class="card-content">
                <div class="card-title-text">Cortes de Pedido</div>
                <div class="card-desc">Análise crítica de rupturas e perdas financeiras operacionais.</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="netflix-card">
            <a href="https://acuracidade-zen-ajuste-de-inventario.streamlit.app/" target="_blank" class="full-card-link"></a>
            <div class="card-banner">🎯</div>
            <div class="card-content">
                <div class="card-title-text">Acuracidade de Estoque</div>
                <div class="card-desc">Balanço de inventário, sobras, faltas e ajustes sistêmicos.</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="netflix-card">
            <a href="https://acuracidade-zen-pulos.streamlit.app/" target="_blank" class="full-card-link"></a>
            <div class="card-banner">📊</div>
            <div class="card-content">
                <div class="card-title-text">Análise de Pulos</div>
                <div class="card-desc">Monitoramento de produtividade e recorrência de endereços (Pulos Reais).</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# 5. Rodapé
st.markdown("""
    <div class="footer">
        <b>SETOR DE ACURACIDADE - TECADI LOGÍSTICA</b><br>
        Monitoramento de performance interna e integridade de estoque.
    </div>
""", unsafe_allow_html=True)
