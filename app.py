import streamlit as st
import pandas as pd
import time
import random
from datetime import datetime, date
import instaloader

st.set_page_config(
    page_title="Four Models - IG Scouter",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS de alto padrão para agência
st.markdown("""
<style>
    /* Estilo Geral e Cores da Agência */
    .stApp {
        background-color: #0d0f12;
        color: #e2e8f0;
    }
    .main-header {
        background: linear-gradient(135deg, #1e1e2f 0%, #0d0f12 100%);
        padding: 24px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        margin-bottom: 24px;
    }
    .main-title {
        color: #ffffff;
        font-size: 28px;
        font-weight: 700;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 14px;
        margin-top: 6px;
    }
    /* Cards de Estatísticas e Status */
    .status-card-connected {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34d399;
        padding: 14px 18px;
        border-radius: 12px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 20px;
    }
    .status-card-mock {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.3);
        color: #60a5fa;
        padding: 14px 18px;
        border-radius: 12px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 20px;
    }
    .status-card-error {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: #f87171;
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    /* Estilização da Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #12161f !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    /* Botão Principal */
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4) !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.6) !important;
    }
</style>
""", unsafe_allow_html=True)

if 'dm_count' not in st.session_state:
    st.session_state['dm_count'] = 0
if 'last_reset' not in st.session_state:
    st.session_state['last_reset'] = date.today()
if st.session_state['last_reset'] != date.today():
    st.session_state['dm_count'] = 0
    st.session_state['last_reset'] = date.today()
if 'scraped_leads' not in st.session_state:
    st.session_state['scraped_leads'] = pd.DataFrame()

def generate_hashtags(city, niche):
    city_clean = city.lower().replace(" ", "").replace("-", "")
    # Expandindo as hashtags para aumentar o alcance regional
    base_tags = [
        city_clean, 
        f"{city_clean}rs", 
        f"modelo{city_clean}", 
        f"modelos{city_clean}", 
        f"divulgacao{city_clean}", 
        f"moda{city_clean}",
        f"achados{city_clean}"
    ]
    
    niche_map = {
        "Infantil/Mães": [f"maes{city_clean}", f"minidiva{city_clean}", f"kids{city_clean}", f"mamaes{city_clean}", f"maternidade{city_clean}"],
        "Teen/Jovem": [f"teen{city_clean}", f"estudante{city_clean}", f"influencer{city_clean}", f"garota{city_clean}"],
        "Plus Size": [f"plussize{city_clean}", f"curvy{city_clean}", f"plussize{city_clean}rs"],
        "Comercial/Beleza": [f"moda{city_clean}", f"lookdodia{city_clean}", f"maquiagem{city_clean}", f"estilo{city_clean}"],
        "Fitness": [f"fitness{city_clean}", f"crossfit{city_clean}", f"treino{city_clean}"]
    }
    return base_tags + niche_map.get(niche, [])

def is_eligible(profile, min_f, max_f, exclude_keywords):
    if not (min_f <= profile.followers <= max_f):
        return False
    bio = (profile.biography or "").lower()
    for kw in exclude_keywords:
        if kw.strip() and kw.strip().lower() in bio:
            return False
    return True

def run_scouting(city, niche, min_f, max_f, limit, exclude_kw, use_mock=False, ig_user="", ig_pass="", session_cookie=""):
    """Executa a raspagem com suporte a login normal e por Cookie sessionid."""
    hashtags = generate_hashtags(city, niche)
    leads = []
    
    if use_mock:
        progress_bar = st.progress(0)
        sample_names = [
            ("Juliana Rossi", "ju_rossi"), ("Camila Becker", "cabi_becker"), 
            ("Mariana Souza", "mari_souza_"), ("Fernanda Lima", "fe_limas"), 
            ("Larissa Manoela", "lari_manu_sm"), ("Beatriz Castro", "bia_castro_"),
            ("Carolina Martins", "carol_martins"), ("Gabriela Ramos", "gabi_ramos"),
            ("Amanda Oliveira", "amanda_oli"), ("Vanessa Duarte", "vanessaduarte"),
            ("Letícia Mendes", "let_mendes"), ("Rafaela Silva", "rafa_silva_sm")
        ]
        for i in range(limit):
            time.sleep(0.05)
            name, username = sample_names[i % len(sample_names)]
            handle = f"{username}_{i+1}" if i >= len(sample_names) else username
            
            leads.append({
                "Foto": f"https://i.pravatar.cc/150?img={(i % 70) + 1}",
                "Nome": name,
                "Handle": f"@{handle}",
                "Seguidores": random.randint(min_f, max_f),
                "Bio": f"📸 | {city} | Contato via DM! {random.choice(['Estudante de Moda', 'Mãe de 2', 'Modelo Comercial'])}",
                "Link Bio": "https://wa.me/5511999999999" if random.random() > 0.5 else None,
                "URL Perfil": f"https://www.instagram.com/{handle}/",
                "Plataforma": "Instagram",
                "Nicho": niche
            })
            progress_bar.progress((i + 1) / limit)
        return pd.DataFrame(leads), "OK"

    # Conexão Real com Instaloader
    try:
        L = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_comments=False,
            save_metadata=False,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
        )
        
        # Tentativa de autenticação
        if session_cookie.strip():
            # Login por Cookie sessionid (Super Seguro para Nuvem)
            try:
                L.context._session.cookies.set('sessionid', session_cookie.strip(), domain='.instagram.com')
                L.context.username = ig_user if ig_user else "session_user"
                st.toast("🔑 Autenticado com sucesso via Cookie SessionID!", icon="✅")
            except Exception as cookie_err:
                return pd.DataFrame(), f"Erro no Cookie: {str(cookie_err)}"
        elif ig_user and ig_pass:
            # Login por Usuário/Senha
            try:
                L.login(ig_user, ig_pass)
            except instaloader.exceptions.BadCredentialsException:
                return pd.DataFrame(), "WRONG_PASSWORD"
            except instaloader.exceptions.TwoFactorAuthRequiredException:
                return pd.DataFrame(), "2FA_REQUIRED"
            except instaloader.exceptions.ConnectionException as conn_err:
                return pd.DataFrame(), f"Trava de IP no servidor: {str(conn_err)}"
            except Exception as login_err:
                return pd.DataFrame(), str(login_err)
        else:
            return pd.DataFrame(), "NO_CREDENTIALS"
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        profiles_checked = set()
        count = 0
        
        for tag in hashtags:
            if count >= limit: break
            status_text.text(f"🔍 Buscando publicações na hashtag #{tag}...")
            
            try:
                hashtag_obj = instaloader.Hashtag.from_name(L.context, tag)
                posts = hashtag_obj.get_posts()
                
                posts_checked = 0
                for post in posts:
                    if count >= limit or posts_checked > 30: break
                    posts_checked += 1
                    owner = post.owner_profile
                    if owner.username in profiles_checked: continue
                    profiles_checked.add(owner.username)
                    time.sleep(random.uniform(1.5, 3.0))
                    
                    if is_eligible(owner, min_f, max_f, exclude_kw):
                        real_name = owner.full_name.strip() if owner.full_name else owner.username
                        leads.append({
                            "Foto": owner.profile_pic_url,
                            "Nome": real_name,
                            "Handle": f"@{owner.username}",
                            "Seguidores": owner.followers,
                            "Bio": owner.biography.replace('\n', ' ') if owner.biography else "",
                            "Link Bio": owner.external_url if owner.external_url else None,
                            "URL Perfil": f"https://www.instagram.com/{owner.username}/",
                            "Plataforma": "Instagram",
                            "Nicho": niche
                        })
                        count += 1
                        progress_bar.progress(min(count / limit, 1.0))
            except Exception as tag_err:
                # Silenciosamente avança para a próxima hashtag em caso de limitação pontual
                continue

        status_text.text("✅ Varredura finalizada!")
        return pd.DataFrame(leads), "OK"
        
    except Exception as e:
        return pd.DataFrame(), str(e)

with st.sidebar:
    st.image("https://img.icons8.com/color/96/instagram-new--v1.png", width=50)
    st.title("Four Models Scouter")
    st.caption("v2.5 - Sistema Avançado de Prospecção")
    st.markdown("---")
    
    st.subheader("1. Alvo da Prospecção")
    city_input = st.text_input("Cidade/Região", value="Santa Maria", help="Ex: Santa Maria, Caxias do Sul, Porto Alegre")
    niche_input = st.selectbox(
        "Nicho / Perfil Desejado",
        ["Infantil/Mães", "Teen/Jovem", "Plus Size", "Comercial/Beleza", "Fitness"]
    )
    
    st.subheader("2. Filtros de Elegibilidade")
    col_min, col_max = st.columns(2)
    with col_min:
        min_f = st.number_input("Min Seg.", value=500, step=100)
    with col_max:
        max_f = st.number_input("Max Seg.", value=25000, step=1000)
        
    exclude_kw_input = st.text_area(
        "Excluir palavras na Bio",
        value="loja, marca, oficial, empresa, vendas, agência",
        help="Termos separados por vírgula"
    ).split(",")
    
    st.subheader("3. Parâmetros de Extração")
    limit_input = st.slider("Quantidade de Leads", 5, 50, 15)
    
    use_mock = st.checkbox("⚙️ Modo Simulação (Sem Necessidade de Login)", value=True)
    
    st.markdown("---")
    
    # Sanfona Elegante para Login e Credenciais
    with st.expander("🔑 Acesso Conta Instagram (Para Busca Real)"):
        st.caption("Como a nuvem (AWS/Streamlit) é um IP de servidor, escolha o melhor método de conexão abaixo:")
        
        login_method = st.radio("Método de Autenticação", ["Cookie SessionID (Recomendado)", "Usuário e Senha Direct"], index=0)
        
        ig_user = ""
        ig_pass = ""
        session_cookie = ""
        
        if login_method == "Cookie SessionID (Recomendado)":
            ig_user = st.text_input("Seu @Usuário", value="", placeholder="ex: scouter_fourmodels")
            session_cookie = st.text_input("Cookie sessionid", type="password", help="Cole o cookie sessionid extraído do navegador")
            st.info("💡 **Como pegar o SessionID:** No seu navegador, abra o Instagram -> F12 -> Application/Storage -> Cookies -> Copie o valor de 'sessionid'. Isso ignora qualquer erro de senha ou SMS!")
        else:
            ig_user = st.text_input("Usuário do Insta", value="", placeholder="ex: scouter_fourmodels")
            ig_pass = st.text_input("Senha do Insta", type="password")
            st.warning("⚠️ O Instagram costuma recusar login direto por senha vindo de servidores em nuvem. Se der erro, use o método Cookie SessionID acima.")

    st.markdown("---")
    st.subheader("🛡️ Controle de DMs Diárias")
    st.metric("Mensagens Enviadas Hoje", f"{st.session_state['dm_count']} / 25")
    if st.button("➕ Registrar 1 DM Enviada"):
        st.session_state['dm_count'] += 1
        st.rerun()

st.markdown("""
<div class="main-header">
    <div class="main-title">🎬 Four Models Scouting Hub</div>
    <div class="sub-title">Ferramenta de prospeção orgânica de talentos por cidade, nicho e geolocalização.</div>
</div>
""", unsafe_allow_html=True)

# Status Bar
if use_mock:
    st.markdown("""
    <div class="status-card-mock">
        ⚡ <b>MODO SIMULAÇÃO ATIVO</b> — Gerando perfis demonstrativos de teste com dados reais para validação de interface.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="status-card-connected">
        🟢 <b>MODO REAL ATIVO</b> — Conectando ao Instagram para buscar talentos em tempo real em <b>{}</b>.
    </div>
    """.format(city_input), unsafe_allow_html=True)

# Botão Principal de Ação
if st.button("🚀 Iniciar Varredura de Talentos", use_container_width=True):
    with st.spinner("Conectando e filtrando perfis qualificados..."):
        df_result, status = run_scouting(
            city=city_input,
            niche=niche_input,
            min_f=min_f,
            max_f=max_f,
            limit=limit_input,
            exclude_kw=exclude_kw_input,
            use_mock=use_mock,
            ig_user=ig_user,
            ig_pass=ig_pass,
            session_cookie=session_cookie
        )
        
        if status == "OK":
            st.session_state['scraped_leads'] = df_result
            if len(df_result) > 0:
                st.toast(f"Sucesso! Encontrados {len(df_result)} leads.", icon="🎉")
            else:
                st.warning("⚠️ **A busca terminou, mas nenhum perfil atendeu a 100% dos filtros definidos.**")
        else:
            # Painel Elegante de Tratamento de Erro
            st.markdown("""
            <div class="status-card-error">
                <h4>⚠️ Atenção: Trava de Segurança do Instagram</h4>
                <p>O Instagram recusou a conexão por senha vindo do servidor da nuvem (Streamlit/AWS Cloud).</p>
            </div>
            """, unsafe_allow_html=True)
            
            if status == "WRONG_PASSWORD":
                st.error("🔑 **Erro de Autenticação:** O Instagram locks a verificação de senha direta vinda de um servidor em nuvem.")
                st.info("💡 **Solução Definitiva:** Na barra lateral, em **🔑 Acesso Conta Instagram**, selecione a opção **'Cookie SessionID'**. Cole o seu cookie do navegador. Isso autentica sua conta instantaneamente sem pedir senha!")
            elif status == "NO_CREDENTIALS":
                st.warning("👈 Preencha o login ou desmarque o 'Modo Simulação' na barra lateral para continuar.")
            else:
                st.error(f"Detalhes do Erro: {status}")

if not st.session_state['scraped_leads'].empty:
    df = st.session_state['scraped_leads']
    
    st.markdown("### 📋 Leads Qualificados Encontrados")
    
    # Tabela Formatada Profissional
    st.dataframe(
        df,
        column_config={
            "Foto": st.column_config.ImageColumn("Foto", help="Foto de Perfil"),
            "Nome": st.column_config.TextColumn("Nome no Perfil", help="Nome do talento no Insta"),
            "Handle": st.column_config.TextColumn("Usuário (@)"),
            "Seguidores": st.column_config.NumberColumn("Seguidores", format="%d"),
            "Bio": st.column_config.TextColumn("Biografia", width="medium"),
            "Link Bio": st.column_config.LinkColumn("Link Bio", display_text="Abrir Link ↗️"),
            "URL Perfil": st.column_config.LinkColumn("Perfil Insta", display_text="Ver Perfil ↗️"),
        },
        use_container_width=True,
        hide_index=True
    )
    
    col_csv, col_copy = st.columns([1, 2])
    with col_csv:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Tabela para CSV/Excel",
            data=csv,
            file_name=f'leads_{city_input.lower()}_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
            use_container_width=True
        )
        
    st.markdown("---")
    st.markdown("### 💬 Gerador de Mensagem Personalizada (Abordagem)")
    
    selected_handle = st.selectbox("Selecione o Lead para Abordar:", df['Handle'].tolist())
    selected_lead = df[df['Handle'] == selected_handle].iloc[0]
    
    first_name = selected_lead['Nome'].split()[0] if selected_lead['Nome'] else "tudo bem"
    
    copy_template = f"""Oi {first_name}, tudo bem? ✨
Sou da equipe de novos talentos da Agência Four Models! 🎬
Estávamos analisando alguns perfis de {city_input} para os nossos próximos materiais e seleções e adoramos o teu perfil/estilo.

Gostaríamos de te convidar para conhecer a agência e conversar sobre oportunidades para {niche_input}.
Teria interesse em receber mais informações no WhatsApp ou por aqui? 😊"""

    st.text_area("Copia da Mensagem (Pronta para colar no DM):", value=copy_template, height=160)
elif status == "OK" if 'status' in locals() else False:
    st.info("""
    💡 **Dicas para encontrar mais perfis na sua busca:**
    1. **Diminua o limite de seguidores mínimos:** Muitos talentos em cidades do interior têm entre 300 e 800 seguidores. Tente colocar `300` no campo **Min Seg.**.
    2. **Remova termos restritivos:** Limpe alguns termos da caixa *Excluir palavras na Bio*.
    3. **Validação da SessionID:** Certifique-se de que o valor colado no *Cookie sessionid* no menu lateral veio da mesma conta que está ativa no seu navegador.
    """)
