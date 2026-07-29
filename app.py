import streamlit as st
import pandas as pd
import time
import random
import re
from datetime import datetime
import instaloader
import base64

# Configuração da página Streamlit
st.set_page_config(page_title="4Models | IG Scouter", page_icon="🕵️‍♀️", layout="wide")

if 'scraped_leads' not in st.session_state:
    st.session_state['scraped_leads'] = pd.DataFrame()

def generate_hashtags(city, niche):
    """Gera hashtags estratégicas com base na cidade e no nicho para burlar a busca genérica."""
    city_clean = re.sub(r'[^a-zA-Z0-9]', '', city.lower())
    
    niche_mapping = {
        "Infantil/Mães": [f"maternidade{city_clean}", f"maesde{city_clean}", f"kids{city_clean}"],
        "Teen": [f"teen{city_clean}", f"jovens{city_clean}", f"meninasde{city_clean}"],
        "Plus Size": [f"plussize{city_clean}", f"curvy{city_clean}", f"moda{city_clean}"],
        "Comercial/Beleza": [f"modelo{city_clean}", f"beleza{city_clean}", f"look{city_clean}"],
        "Fitness": [f"fitness{city_clean}", f"gym{city_clean}", f"treino{city_clean}"],
        "Estilo Alternativo": [f"alt{city_clean}", f"tatuagem{city_clean}", f"estilo{city_clean}"]
    }
    
    base_tags = niche_mapping.get(niche, [f"modelo{city_clean}", city_clean])
    # Adiciona a cidade pura como fallback
    base_tags.append(city_clean)
    return list(set(base_tags))

def is_eligible(profile, min_followers, max_followers, exclude_keywords):
    """Filtra perfis para garantir que são pessoas reais e qualificadas."""
    if not (min_followers <= profile.followers <= max_followers):
        return False
    
    bio_lower = profile.biography.lower()
    for word in exclude_keywords:
        if word.strip() and word.strip().lower() in bio_lower:
            return False # Exclui lojas, empresas, etc.
            
    return True

def run_scouting(city, niche, min_f, max_f, limit, exclude_kw, use_mock=False):
    """Executa a raspagem de dados reais ou simulados."""
    hashtags = generate_hashtags(city, niche)
    leads = []
    
    if use_mock:
        # Modo de simulação para testes de UI sem bloqueios do Instagram
        st.info("Rodando em MODO SIMULAÇÃO (Mock Data). Os dados abaixo são fictícios.")
        progress_bar = st.progress(0)
        for i in range(limit):
            time.sleep(0.5) # Simula delay de rede
            leads.append({
                "Foto": f"https://placehold.co/100x100/FF69B4/FFFFFF?text=P{i+1}",
                "Nome": f"Candidato Simulado {i+1}",
                "Handle": f"@user_mock_{i+1}",
                "Seguidores": random.randint(min_f, max_f),
                "Bio": f"Amo fotografia 📸 | {city} | Contato via DM! {random.choice(['Estudante', 'Modelo', 'Mãe de 2'])}",
                "Link Bio": "https://wa.me/5511999999999" if random.random() > 0.5 else "N/A",
                "URL Perfil": f"https://instagram.com/user_mock_{i+1}",
                "Nicho": niche
            })
            progress_bar.progress((i + 1) / limit)
        return pd.DataFrame(leads)

    try:
        L = instaloader.Instaloader()
        # Nota: Em produção, usar L.load_session_from_file('seu_user') 
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        profiles_checked = set()
        count = 0
        
        for tag in hashtags:
            if count >= limit: break
            status_text.text(f"Buscando pela hashtag: #{tag}...")
            
            try:
                # Pega posts recentes da hashtag
                post_iterator = instaloader.NodeIterator(
                    L.context, "9b498c08113f1e09617a1703c22b2f32",
                    lambda d: d['data']['hashtag']['edge_hashtag_to_media'],
                    lambda n: instaloader.Post(L.context, n),
                    {'tag_name': tag},
                    f"https://www.instagram.com/explore/tags/{tag}/"
                )
                
                for post in post_iterator:
                    if count >= limit: break
                    
                    owner = post.owner_profile
                    if owner.username in profiles_checked:
                        continue
                        
                    profiles_checked.add(owner.username)
                    
                    # Anti-ban delay: Comportamento humano
                    time.sleep(random.uniform(2.5, 5.5))
                    
                    # Filtros de qualificação
                    if is_eligible(owner, min_f, max_f, exclude_kw):
                        leads.append({
                            "Foto": owner.profile_pic_url,
                            "Nome": owner.full_name,
                            "Handle": f"@{owner.username}",
                            "Seguidores": owner.followers,
                            "Bio": owner.biography.replace('\n', ' '),
                            "Link Bio": owner.external_url or "N/A",
                            "URL Perfil": f"https://instagram.com/{owner.username}",
                            "Nicho": niche
                        })
                        count += 1
                        progress_bar.progress(min(count / limit, 1.0))
                        
            except Exception as e:
                st.warning(f"Erro ao buscar #{tag}: {str(e)}")
                continue

        status_text.text("Busca concluída!")
        return pd.DataFrame(leads)
        
    except Exception as e:
        st.error(f"Erro crítico no scraper: {str(e)}")
        return pd.DataFrame()

st.sidebar.title("🕵️‍♀️ 4Models Scouter")
st.sidebar.markdown("---")

st.sidebar.header("1. Alvo de Busca")
city_input = st.sidebar.text_input("Cidade/Região", value="Santa Maria")
niche_input = st.sidebar.selectbox("Nicho/Perfil", 
    ["Infantil/Mães", "Teen", "Plus Size", "Comercial/Beleza", "Fitness", "Estilo Alternativo"])

st.sidebar.header("2. Qualificação")
col1, col2 = st.sidebar.columns(2)
with col1:
    min_followers = st.number_input("Min Seguidores", min_value=0, value=800, step=100)
with col2:
    max_followers = st.number_input("Max Seguidores", min_value=0, value=15000, step=500)

exclude_words = st.sidebar.text_area("Palavras a Excluir na Bio (separadas por vírgula)", 
    value="loja, marca, ofc, oficial, roupas, unhas, lash, designer, empresa, vendas")

st.sidebar.header("3. Configuração de Extração")
scrape_limit = st.sidebar.slider("Limite de Leads (Segurança)", 5, 50, 15)
is_mock = st.sidebar.checkbox("Usar Modo Simulação (Anti-Ban)", value=True, 
    help="Ative para testar a interface sem logar no Instagram.")

st.title("Painel de Prospecção Ativa")
st.markdown("Busque talentos locais no Instagram através de geolocalização por nicho, qualifique os leads e gere abordagens personalizadas.")

if st.sidebar.button("🚀 Iniciar Scouting", use_container_width=True):
    with st.spinner('Mapeando perfis... isso pode levar alguns minutos (respeitando limites do Instagram).'):
        exclude_list = [w.strip() for w in exclude_words.split(',')]
        df = run_scouting(city_input, niche_input, min_followers, max_followers, scrape_limit, exclude_list, is_mock)
        
        if not df.empty:
            st.session_state['scraped_leads'] = df
            st.success(f"Sucesso! Encontramos {len(df)} leads qualificados em {city_input}.")
        else:
            st.warning("Nenhum perfil encontrado com esses critérios. Tente alterar os limites de seguidores ou cidade.")

if not st.session_state['scraped_leads'].empty:
    df = st.session_state['scraped_leads']
    
    st.markdown("### Leads Encontrados")
    # Exibe tabela (sem a coluna da URL da imagem para não quebrar a UI padrão, mostramos como link)
    display_df = df.drop(columns=['Foto'])
    st.dataframe(display_df, use_container_width=True)
    
    # Exportar CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Exportar Lista para CSV (Excel)",
        data=csv,
        file_name=f'leads_{niche_input}_{city_input.replace(" ", "")}_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv',
    )
    
    st.markdown("---")
    st.markdown("### 💬 Gerador de Abordagem (Copywriter)")
    st.markdown("Selecione um lead abaixo para gerar a mensagem de DM/WhatsApp formatada.")
    
    selected_lead = st.selectbox("Selecione o Lead:", df['Nome'].tolist() + df['Handle'].tolist())
    
    # Encontra os dados do lead selecionado
    lead_data = df[(df['Nome'] == selected_lead) | (df['Handle'] == selected_lead)].iloc[0]
    first_name = str(lead_data['Nome']).split()[0] if lead_data['Nome'] else lead_data['Handle']
    
    # Templates baseados no Nicho
    templates = {
        "Infantil/Mães": f"Oi {first_name}, tudo bem? Vi o seu perfil e as fotos do seu pequeno(a)! Somos da agência 4Models, estamos organizando uma seletiva presencial em {city_input} e adoraríamos avaliar o perfil para campanhas infantis. Podemos te explicar como funciona?",
        "Geral": f"Oie {first_name}, tudo bem? Nossa equipe de scouting amou o seu estilo e presença aqui no Insta! Somos a 4Models e estamos buscando novos rostos em {city_input} para campanhas locais e nacionais. Topa participar de uma seletiva presencial nossa?"
    }
    
    copy_text = templates["Infantil/Mães"] if niche_input == "Infantil/Mães" else templates["Geral"]
    
    colA, colB = st.columns([1, 2])
    with colA:
        if str(lead_data['Foto']).startswith('http'):
            st.image(lead_data['Foto'], width=150, caption=lead_data['Handle'])
        st.markdown(f"**Bio:** {lead_data['Bio']}")
        st.markdown(f"[🔗 Abrir Perfil no Instagram]({lead_data['URL Perfil']})")
        if lead_data['Link Bio'] != "N/A":
             st.markdown(f"**Link na Bio:** {lead_data['Link Bio']}")
             
    with colB:
        st.text_area("Copy sugerida (Pronta para copiar e colar na DM):", value=copy_text, height=150)
        st.info("💡 Dica de Growth: Sempre interaja (curta 2 fotos e comente em 1) antes de enviar a DM. Isso aumenta a taxa de resposta em 40% e previne cair na caixa de 'Solicitações Ocultas'.")
