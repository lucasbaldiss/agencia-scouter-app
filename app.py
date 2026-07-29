import streamlit as st
import pandas as pd
import time
import random
import re
from datetime import datetime
import instaloader
import urllib.parse

# Configuração da página Streamlit
st.set_page_config(page_title="4Models | Multi-Scouter Hub", page_icon="🕵️‍♀️", layout="wide")

# Inicialização de variáveis de sessão
if 'scraped_leads' not in st.session_state:
    st.session_state['scraped_leads'] = pd.DataFrame()
if 'dm_counter' not in st.session_state:
    st.session_state['dm_counter'] = 0

def generate_hashtags(city, niche):
    """Gera hashtags estratégicas com base na cidade e no nicho para otimizar o scouting."""
    city_clean = re.sub(r'[^a-zA-Z0-9]', '', city.lower())
    
    niche_mapping = {
        "Infantil/Mães": [f"maternidade{city_clean}", f"maesde{city_clean}", f"kids{city_clean}", f"minidiva{city_clean}"],
        "Teen": [f"teen{city_clean}", f"jovens{city_clean}", f"meninasde{city_clean}", f"estiloteen{city_clean}"],
        "Plus Size": [f"plussize{city_clean}", f"curvy{city_clean}", f"modaplussize{city_clean}"],
        "Comercial/Beleza": [f"modelo{city_clean}", f"beleza{city_clean}", f"look{city_clean}", f"modafeminina{city_clean}"],
        "Fitness": [f"fitness{city_clean}", f"gym{city_clean}", f"treino{city_clean}"],
        "Estilo Alternativo": [f"alt{city_clean}", f"tatuagem{city_clean}", f"estilo{city_clean}"]
    }
    
    base_tags = niche_mapping.get(niche, [f"modelo{city_clean}", city_clean])
    base_tags.append(city_clean)
    return list(set(base_tags))

def is_eligible(profile, min_followers, max_followers, exclude_keywords):
    """Filtra perfis para garantir que são pessoas reais e qualificadas."""
    if not (min_followers <= profile.followers <= max_followers):
        return False
    
    bio_lower = profile.biography.lower() if profile.biography else ""
    for word in exclude_keywords:
        if word.strip() and word.strip().lower() in bio_lower:
            return False # Exclui lojas, empresas, etc.
            
    return True

def run_scouting(city, niche, min_f, max_f, limit, exclude_kw, use_mock=False, ig_user="", ig_pass=""):
    """Executa a raspagem de dados reais ou simulados do Instagram."""
    hashtags = generate_hashtags(city, niche)
    leads = []
    
    if use_mock:
        st.info("💡 Modo Simulação Ativo: Dados fictícios gerados para demonstração de interface.")
        progress_bar = st.progress(0)
        for i in range(limit):
            time.sleep(0.1) # Simulação rápida
            leads.append({
                "Foto": f"https://placehold.co/100x100/3A86FF/FFFFFF?text=P{i+1}",
                "Nome": f"Candidato Simulado {i+1}",
                "Handle": f"@user_mock_{i+1}",
                "Seguidores": random.randint(min_f, max_f),
                "Bio": f"Amo fotografia 📸 | {city} | Contato via DM! {random.choice(['Estudante', 'Modelo', 'Mãe de 2'])}",
                "Link Bio": "https://wa.me/5511999999999" if random.random() > 0.5 else "N/A",
                "URL Perfil": f"https://instagram.com/user_mock_{i+1}",
                "Plataforma": "Instagram",
                "Nicho": niche
            })
            progress_bar.progress((i + 1) / limit)
        return pd.DataFrame(leads)

    # Conexão Real com Instaloader
    try:
        L = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_comments=False,
            save_metadata=False
        )
        
        # Realiza Login se credenciais forem fornecidas
        if ig_user and ig_pass:
            try:
                L.login(ig_user, ig_pass)
                st.sidebar.success(f"Autenticado como: @{ig_user}")
            except Exception as login_err:
                st.error(f"⚠️ Erro ao fazer login no Instagram com @{ig_user}: {str(login_err)}")
                st.warning("Recomendação: Verifique se a conta não exige confirmação de SMS/Email no app oficial ou use o Modo Simulação.")
                return pd.DataFrame()
        else:
            st.warning("⚠️ Você está tentando buscar sem login. Servidores em nuvem (como Streamlit Cloud) são bloqueados pelo Instagram se não houver login. Insira uma conta de suporte na barra lateral.")
        
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
                
                for post in posts:
                    if count >= limit: break
                    
                    owner = post.owner_profile
                    if owner.username in profiles_checked:
                        continue
                        
                    profiles_checked.add(owner.username)
                    
                    # Delay anti-ban entre requisições
                    time.sleep(random.uniform(2.0, 4.0))
                    
                    if is_eligible(owner, min_f, max_f, exclude_kw):
                        leads.append({
                            "Foto": owner.profile_pic_url,
                            "Nome": owner.full_name or owner.username,
                            "Handle": f"@{owner.username}",
                            "Seguidores": owner.followers,
                            "Bio": owner.biography.replace('\n', ' ') if owner.biography else "",
                            "Link Bio": owner.external_url or "N/A",
                            "URL Perfil": f"https://instagram.com/{owner.username}",
                            "Plataforma": "Instagram",
                            "Nicho": niche
                        })
                        count += 1
                        progress_bar.progress(min(count / limit, 1.0))
                        
            except Exception as tag_err:
                st.caption(f"Aviso na hashtag #{tag}: {str(tag_err)}")
                continue

        status_text.text("✅ Busca concluída!")
        return pd.DataFrame(leads)
        
    except Exception as e:
        st.error(f"Erro no Scraper: {str(e)}")
        return pd.DataFrame()

st.sidebar.title("🕵️‍♀️ 4Models Scouter Hub")
st.sidebar.markdown("---")

st.sidebar.header("1. Alvo de Busca")
city_input = st.sidebar.text_input("Cidade/Região", value="Santa Maria")
niche_input = st.sidebar.selectbox("Nicho/Perfil", 
    ["Infantil/Mães", "Teen", "Plus Size", "Comercial/Beleza", "Fitness", "Estilo Alternativo"])

st.sidebar.header("2. Qualificação")
col1, col2 = st.sidebar.columns(2)
with col1:
    min_followers = st.number_input("Min Seguidores", min_value=0, value=500, step=100)
with col2:
    max_followers = st.number_input("Max Seguidores", min_value=0, value=20000, step=500)

exclude_words = st.sidebar.text_area("Palavras a Excluir na Bio (separadas por vírgula)", 
    value="loja, marca, ofc, oficial, roupas, unhas, lash, designer, empresa, vendas, loja virtual, atacado")

st.sidebar.header("3. Configuração de Extração")
scrape_limit = st.sidebar.slider("Limite de Leads por Busca", 5, 50, 15)

is_mock = st.sidebar.checkbox("Usar Modo Simulação (Anti-Ban)", value=True, 
    help="Mantenha ativo para testar a interface sem risco. Desmarque para buscar perfis reais.")

# Expander para credenciais de acesso seguro do Instagram
with st.sidebar.expander("🔑 Credenciais Instagram (Para busca real na Nuvem)"):
    st.caption("Use uma conta de suporte/secundária (nunca a oficial da agência).")
    ig_user_input = st.text_input("Usuário do Instagram", value="")
    ig_pass_input = st.text_input("Senha do Instagram", type="password", value="")

st.sidebar.markdown("---")
st.sidebar.header("🛡️ Radar Anti-Ban e Limites Diários")
st.sidebar.metric("DMs Enviadas Hoje (Sessão)", f"{st.session_state['dm_counter']} / 25 DMs")

if st.sidebar.button("➕ Registrar DM Enviada"):
    st.session_state['dm_counter'] += 1
    st.rerun()

if st.session_state['dm_counter'] >= 25:
    st.sidebar.error("🚨 ALERTA DE SEGURANÇA: Limite diário recomendado atingido (25 DMs). Pause os disparos por 24 horas para evitar bloqueio da conta!")
elif st.session_state['dm_counter'] >= 18:
    st.sidebar.warning("⚠️ Atenção: Você está próximo do teto seguro diário do Meta/Instagram.")

st.title("Painel de Prospecção Ativa Multiplataforma")
st.markdown("Identifique talentos regionais no Instagram, TikTok e Facebook, qualifique os perfis e gere abordagens personalizadas.")

tab_ig, tab_tiktok, tab_fb = st.tabs(["📸 Instagram Scouter", "🎵 TikTok Scouter", "👥 Facebook Groups"])

with tab_ig:
    st.subheader("Buscador de Talentos no Instagram")
    
    if is_mock:
        st.warning("⚠️ MODO SIMULAÇÃO ATIVO. Desmarque 'Usar Modo Simulação' na barra lateral e informe uma conta de suporte para coletar dados reais.")
    else:
        st.info("🟢 MODO REAL ATIVO. Buscando perfis ao vivo via hashtags e geolocalização.")

    if st.button("🚀 Iniciar Scouting no Instagram", key="btn_ig", use_container_width=True):
        with st.spinner('Mapeando perfis locais... Isso pode levar alguns instantes.'):
            exclude_list = [w.strip() for w in exclude_words.split(',')]
            df = run_scouting(
                city_input, niche_input, min_followers, max_followers, 
                scrape_limit, exclude_list, is_mock, ig_user_input, ig_pass_input
            )
            
            if not df.empty:
                st.session_state['scraped_leads'] = df
                st.success(f"Sucesso! Encontramos {len(df)} leads qualificados para {city_input}.")
            else:
                st.warning("Nenhum perfil encontrado. Tente ajustar a contagem de seguidores ou as credenciais de login.")

    if not st.session_state['scraped_leads'].empty:
        df = st.session_state['scraped_leads']
        
        st.markdown("### Leads Encontrados")
        display_df = df.drop(columns=['Foto'], errors='ignore')
        st.dataframe(display_df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Lista de Leads (CSV/Excel)",
            data=csv,
            file_name=f'leads_ig_{niche_input}_{city_input.replace(" ", "")}_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )
        
        st.markdown("---")
        st.markdown("### 💬 Gerador de Abordagem Personalizada")
        
        selected_lead = st.selectbox("Selecione o Lead para Abordar:", df['Nome'].tolist() + df['Handle'].tolist())
        
        lead_data = df[(df['Nome'] == selected_lead) | (df['Handle'] == selected_lead)].iloc[0]
        first_name = str(lead_data['Nome']).split()[0] if lead_data['Nome'] else lead_data['Handle']
        
        templates = {
            "Infantil/Mães": f"Oi {first_name}, tudo bem? Vi o seu perfil e o charme do seu pequeno(a)! Somos da equipe de scouting da agência 4Models. Estamos selecionando novos rostos infantis na região de {city_input} para marcas parceiras. Gostaria de te passar mais detalhes de como funciona?",
            "Teen": f"Oie {first_name}, tudo bem? Nossa equipe de scouting curtiu muito o teu estilo e fotos aqui no Insta! A 4Models está buscando novos talentos teen na região de {city_input}. Topa conversar com a gente no Whats para entender como funciona uma seletiva?",
            "Plus Size": f"Olá {first_name}! Tudo bem? Acompanhamos teu perfil e amamos a tua beleza e presença! A 4Models está expandindo o casting Plus Size em {city_input} e adoraríamos te apresentar uma oportunidade. Posso te enviar as informações?",
            "Geral": f"Oie {first_name}, tudo bem? O scouting da 4Models amou a tua energia e perfil aqui no Insta! Estamos com uma seletiva aberta para novos talentos na região de {city_input}. Queremos muito te conhecer, podemos bater um papo?"
        }
        
        copy_text = templates.get(niche_input, templates["Geral"])
        
        colA, colB = st.columns([1, 2])
        with colA:
            if str(lead_data['Foto']).startswith('http'):
                st.image(lead_data['Foto'], width=140)
            st.markdown(f"**Handle:** {lead_data['Handle']}")
            st.markdown(f"**Bio:** {lead_data['Bio']}")
            st.markdown(f"[🔗 Abrir Perfil no Instagram]({lead_data['URL Perfil']})")
                 
        with colB:
            st.text_area("Copy Sugerida (Pronta para copiar e colar na DM):", value=copy_text, height=140)
            st.info("💡 **Dica de Ouro:** Curta 2 fotos do candidato e faça 1 comentário genuíno ANTES de enviar a DM. Isso garante que sua mensagem vá para a caixa principal e previne queda em 'Solicitações Ocultas'.")

with tab_tiktok:
    st.subheader("🎵 TikTok Scouting Radar")
    st.markdown("Devido às restrições do TikTok, o método mais eficaz e seguro é o direcionamento de busca otimizada por palavras-chave e hashtags regionais.")
    
    tk_city = city_input.lower().replace(" ", "")
    tk_query = f"modelo {city_input}"
    
    tt_url = f"https://www.tiktok.com/search?q={urllib.parse.quote(tk_query)}"
    tt_tag_url = f"https://www.tiktok.com/tag/modelo{tk_city}"
    
    st.markdown(f"""
    #### Links Diretos de Scouting para {city_input}:
    - 🔍 [Abrir Busca TikTok por Criadores em {city_input}]({tt_url})
    - 🏷️ [Explorar Hashtag #modelo{tk_city} no TikTok]({tt_tag_url})
    """)
    
    st.markdown("#### Copy Especial para Abordagem TikTok:")
    st.code(f"Oie! Vi teus vídeos no TikTok e a nossa equipe de scouting da 4Models achou teu conteúdo incrível! Estamos selecionando novos rostos em {city_input}. Dá uma olhada no nosso Insta e me chama se quiser participar!", language="text")

with tab_fb:
    st.subheader("👥 Facebook Groups & Comunidades")
    st.markdown("O Facebook é uma excelente fonte de captação para o nicho **Infantil/Mães** e **Comercial** através dos Grupos da Cidade.")
    
    fb_query_maes = f"mães {city_input}"
    fb_query_modelos = f"modelos {city_input}"
    
    fb_url_maes = f"https://www.facebook.com/groups/search/groups/?q={urllib.parse.quote(fb_query_maes)}"
    fb_url_modelos = f"https://www.facebook.com/groups/search/groups/?q={urllib.parse.quote(fb_query_modelos)}"
    
    st.markdown(f"""
    #### Atalhos de Grupos em {city_input}:
    - 👩‍👧‍👦 [Buscar Grupos de Mães em {city_input}]({fb_url_maes})
    - 📸 [Buscar Grupos de Modelos e Divulgação em {city_input}]({fb_url_modelos})
    """)
    
    st.info("💡 **Estratégia de Captação no Facebook:** Entre nos grupos de Mães da cidade e publique posts informativos ou de convite para seletivas presenciais com link direto para o WhatsApp do Scouter.")
