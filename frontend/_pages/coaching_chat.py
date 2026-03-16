import streamlit as st
import httpx
from datetime import datetime

_DEMO = [
    {'content': 'Harika bir hedef! Python icin once temel sozdizimini kavramanı oneririm. Degiskenler, donguler ve fonksiyonlarla baslayabilirsin.', 'suggested_resources': ['Python.org resmi tutorial', 'freeCodeCamp Python kursu'], 'next_step_hint': 'Ilk adim: degisken tanimlama pratigi yap.'},
    {'content': 'Ilerleme harika! Kucuk projeler yapman cok faydali olacak. Bir hesap makinesi veya to-do listesi uygulamasi dene.', 'suggested_resources': ['LeetCode Easy', 'Kaggle notebook'], 'next_step_hint': 'Bugun 30 dk pratik yap.'},
    {'content': 'Motivasyonunu korumak icin hedefleri kucuk parcalara bol! Her gun 25 dakika odakli calisma (Pomodoro) cok etkili.', 'suggested_resources': ['Pomodoro teknigi', 'Notion ile hedef takibi'], 'next_step_hint': 'Yarin 1 somut hedef belirle.'},
    {'content': 'Veri bilimi icin Python, NumPy ve Pandas ogrenmek iyi bir baslangic. Kaggle uzerinde pratik yapabilirsin.', 'suggested_resources': ['Kaggle Learn', 'Pandas dokumantasyonu'], 'next_step_hint': 'Kaggle\'da ilk notebook\'unu olustur.'},
]

_QUICK_QS = [
    'Python ogrenmek istiyorum, nereden baslamaliyim?',
    'Makine ogrenmesi icin kaynak onerir misin?',
    'Haftalik calisma programi nasil yapmaliyim?',
    'Motivasyonum dusuk, ne yapmaliyim?',
    'Veri bilimi yol haritasi nedir?',
    'JavaScript mi Python mi ogrenmeliyim?',
]

def _render_message(msg: dict) -> None:
    avatar = '👤' if msg['role'] == 'user' else '🎓'
    with st.chat_message(msg['role'], avatar=avatar):
        st.write(msg['content'])
        resources = msg.get('suggested_resources', [])
        if resources:
            with st.expander('📚 Kaynaklar', expanded=False):
                for res in resources:
                    if res.startswith('http'):
                        st.markdown(f'- [{res}]({res})')
                    else:
                        st.markdown(f'- {res}')
        hint = msg.get('next_step_hint', '')
        if hint:
            st.info(f'💡 Sonraki Adim: {hint}')
        if msg.get('time'):
            st.caption(msg['time'])


def show(api_url: str, user_id: str) -> None:
    st.title('AI Koc ile Sohbet')
    st.caption('Groq LLM destekli kisisel ogrenme kocunuz')

    demo_mode = not bool(user_id)
    if demo_mode:
        st.info('Demo mod aktif — sol panelden Kullanici ID girerek gercek AI kocla konusabilirsiniz.')

    if 'chat_initialized' not in st.session_state:
        st.session_state.chat_initialized = True
        st.session_state.chat_messages = [{
            'role': 'assistant',
            'content': 'Merhaba! Ben AI ogrenme kocunuzum. Ogrenme hedefleriniz, zorlandiginiz konular veya kariyer gelisiminiz hakkinda benimle konusabilirsiniz. Size nasil yardimci olabilirim?',
            'time': datetime.now().strftime('%H:%M'),
        }]

    # Toolbar
    col1, col2, col3 = st.columns([4, 1, 1])
    with col2:
        msg_count = len([m for m in st.session_state.get('chat_messages', []) if m['role'] == 'user'])
        st.metric('Mesaj', msg_count)
    with col3:
        if st.button('🗑 Temizle', use_container_width=True):
            st.session_state.chat_messages = []
            del st.session_state['chat_initialized']
            st.rerun()

    # Hizli sorular
    with st.expander('⚡ Hizli Sorular', expanded=False):
        cols = st.columns(2)
        for i, q in enumerate(_QUICK_QS):
            if cols[i % 2].button(q, key=f'qq_{i}', use_container_width=True):
                st.session_state._quick_input = q
                st.rerun()

    st.divider()

    # Mesajlar
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.get('chat_messages', []):
            _render_message(msg)

    # Input
    default_input = st.session_state.pop('_quick_input', '')
    user_input = st.chat_input('Kocunuza bir sey sorun...')

    if user_input or default_input:
        message = user_input or default_input
        now = datetime.now().strftime('%H:%M')
        st.session_state.chat_messages.append({'role': 'user', 'content': message, 'time': now})

        with st.spinner('Kocunuz dusunuyor...'):
            if demo_mode:
                import time; time.sleep(0.5)
                idx = len(st.session_state.chat_messages) % len(_DEMO)
                resp = _DEMO[idx]
                ai_msg = {
                    'role': 'assistant',
                    'content': resp['content'],
                    'suggested_resources': resp['suggested_resources'],
                    'next_step_hint': resp['next_step_hint'],
                    'time': datetime.now().strftime('%H:%M'),
                }
            else:
                try:
                    r = httpx.post(
                        f'{api_url}/coaching/chat',
                        json={'user_id': user_id, 'message': message},
                        timeout=45,
                    )
                    r.raise_for_status()
                    result = r.json()
                    ai_msg = {
                        'role': 'assistant',
                        'content': result.get('content', ''),
                        'suggested_resources': result.get('suggested_resources', []),
                        'next_step_hint': result.get('next_step_hint', ''),
                        'time': datetime.now().strftime('%H:%M'),
                    }
                except Exception as e:
                    ai_msg = {
                        'role': 'assistant',
                        'content': f'Baglanti hatasi: {e}',
                        'time': datetime.now().strftime('%H:%M'),
                    }

        st.session_state.chat_messages.append(ai_msg)
        st.rerun()
