import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import streamlit as st
import httpx

st.set_page_config(page_title='AI Learning Coach', page_icon='🎓', layout='wide')

st.markdown('''
<style>
/* ── Temel renkler ──────────────────────────────────────────────────────────
   Arka plan  : #0e0b1e  (derin mor-siyah)
   Kart/panel : #16122a  (koyu mor)
   Kenar      : #2d2060  (orta mor)
   Vurgu 1    : #7c3aed  (canlı mor — primary)
   Vurgu 2    : #06b6d4  (cyan — accent)
   Metin      : #f0eeff  (kırık beyaz)
   İkincil    : #a89ec9  (soluk lavanta)
*/

.stApp { background-color: #0e0b1e !important; }

/* Sidebar */
section[data-testid='stSidebar'] {
    background: linear-gradient(180deg, #0a0818 0%, #130f28 100%) !important;
    border-right: 1px solid #2d2060 !important;
}
section[data-testid='stSidebar'] * { color: #f0eeff !important; }

/* Butonlar */
.stButton>button {
    background: linear-gradient(135deg, #5b21b6, #7c3aed) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px;
    transition: all 0.2s ease;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #7c3aed, #06b6d4) !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(124,58,237,0.4);
}

/* Input alanları */
.stTextInput>div>div>input,
.stTextArea>div>div>textarea {
    background: #16122a !important;
    border: 1px solid #2d2060 !important;
    color: #f0eeff !important;
    border-radius: 8px !important;
}
.stTextInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 2px rgba(124,58,237,0.25) !important;
}
.stSelectbox>div>div {
    background: #16122a !important;
    border: 1px solid #2d2060 !important;
    color: #f0eeff !important;
    border-radius: 8px !important;
}

/* Chat */
.stChatInput>div { background: #16122a !important; border-top: 1px solid #2d2060 !important; }
.stChatInput textarea { background: #16122a !important; border: 1px solid #2d2060 !important; color: #f0eeff !important; }
[data-testid='stChatMessage'] {
    background: #16122a !important;
    border: 1px solid #2d2060 !important;
    border-radius: 14px !important;
    margin: 6px 0 !important;
}
[data-testid='stChatMessage'] * { color: #f0eeff !important; }

/* Expander */
[data-testid='stExpander'] {
    background: #16122a !important;
    border: 1px solid #2d2060 !important;
    border-radius: 10px !important;
}
.streamlit-expanderHeader { background: #16122a !important; color: #f0eeff !important; }
.streamlit-expanderContent { background: #16122a !important; }

/* Tabs */
.stTabs [data-baseweb='tab-list'] {
    background: #16122a !important;
    border-bottom: 1px solid #2d2060 !important;
    border-radius: 10px 10px 0 0;
    gap: 4px;
}
.stTabs [data-baseweb='tab'] {
    color: #a89ec9 !important;
    background: transparent !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 8px 16px !important;
}
.stTabs [aria-selected='true'] {
    color: #06b6d4 !important;
    border-bottom: 2px solid #06b6d4 !important;
    background: rgba(6,182,212,0.08) !important;
}

/* Metrikler */
[data-testid='metric-container'] {
    background: #16122a !important;
    border: 1px solid #2d2060 !important;
    border-radius: 12px !important;
    padding: 12px !important;
}
[data-testid='stMetricValue'] { color: #06b6d4 !important; font-weight: 700 !important; }
[data-testid='stMetricLabel'] { color: #a89ec9 !important; }
[data-testid='stMetricDelta'] { color: #34d399 !important; }

/* Progress bar */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #7c3aed, #06b6d4) !important;
    border-radius: 4px !important;
}
[data-testid='stProgressBar'] > div {
    background: #2d2060 !important;
    border-radius: 4px !important;
}

/* Alert kutuları */
[data-testid='stAlert'] { border-radius: 10px !important; }
.stInfo  { background: #0d1a2e !important; border: 1px solid #1e3a5f !important; border-radius: 10px !important; }
.stSuccess { background: #0d2a1e !important; border: 1px solid #1a5c3a !important; border-radius: 10px !important; }
.stWarning { background: #2a1e0d !important; border: 1px solid #5c3a1a !important; border-radius: 10px !important; }
.stError   { background: #2a0d0d !important; border: 1px solid #5c1a1a !important; border-radius: 10px !important; }

/* Form */
[data-testid='stForm'] {
    background: #16122a !important;
    border: 1px solid #2d2060 !important;
    border-radius: 12px !important;
    padding: 20px !important;
}
[data-testid='stFormSubmitButton']>button {
    background: linear-gradient(135deg, #5b21b6, #7c3aed) !important;
    color: white !important;
    width: 100% !important;
    border-radius: 10px !important;
}

/* Divider */
hr { border-color: #2d2060 !important; }

/* Slider */
[data-testid='stSlider'] > div > div > div { background: #7c3aed !important; }

/* Genel metin */
h1, h2, h3, h4, h5, h6 { color: #f0eeff !important; }
p, label { color: #f0eeff !important; }
.stMarkdown p { color: #f0eeff !important; }
.stCaption, [data-testid='stCaptionContainer'], small { color: #a89ec9 !important; }
* { color: #f0eeff; }
</style>
''', unsafe_allow_html=True)

PAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_pages')

_PAGE_MAP = {
    'coaching_chat.py': ('💬', 'AI Koc ile Sohbet'),
    'dashboard.py': ('📊', 'Gösterge Paneli'),
    'learning_plan.py': ('📚', 'Ogrenme Plani'),
    'progress_view.py': ('📈', 'Ilerleme'),
}

with st.sidebar:
    st.markdown('## 🎓 AI Learning Coach')
    st.markdown('---')
    api_url = st.text_input('🔗 Backend URL', value='http://localhost:8000')
    st.markdown('### 👤 Kullanici')
    user_id = st.text_input('Kullanici ID', placeholder='örn: user-123')
    with st.expander('➕ Yeni Kullanici Olustur'):
        new_name = st.text_input('Ad Soyad', key='new_name')
        new_email = st.text_input('E-posta', key='new_email')
        new_skill = st.selectbox('Seviye', ['beginner', 'intermediate', 'advanced'], key='new_skill',
                                  format_func=lambda x: {'beginner': 'Baslangic', 'intermediate': 'Orta', 'advanced': 'Ileri'}[x])
        if st.button('Olustur', key='create_user', use_container_width=True):
            try:
                r = httpx.post(f'{api_url}/users', json={
                    'name': new_name, 'email': new_email, 'skill_level': new_skill,
                    'interests': [], 'learning_style': 'reading', 'weekly_hours': 5,
                }, timeout=10)
                r.raise_for_status()
                uid = r.json()['id']
                st.success('Olusturuldu!')
                st.code(uid)
            except Exception as e:
                st.error(f'Hata: {e}')
    st.markdown('---')
    st.markdown('### Sayfalar')
    for fname, (icon, label) in _PAGE_MAP.items():
        if st.button(f'{icon} {label}', key=f'nav_{fname}', use_container_width=True):
            st.session_state._nav_page = fname
            st.rerun()
    st.markdown('---')
    st.caption('v2.0.0 • Groq LLM')


def load_page(filename: str) -> None:
    path = os.path.join(PAGES_DIR, filename)
    ns = {'__file__': path}
    with open(path, encoding='utf-8') as f:
        code = f.read()
    exec(compile(code, path, 'exec'), ns)
    if 'show' in ns:
        ns['show'](api_url=api_url, user_id=user_id)


current_page = st.session_state.get('_nav_page', 'coaching_chat.py')
load_page(current_page)
