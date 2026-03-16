import streamlit as st
import httpx
from datetime import datetime
import random

_DEMO_DATA = {
    'progress_percentage': 42.5,
    'completed_topics': ['Python Temelleri', 'Degiskenler & Tipler', 'Donguler', 'Fonksiyonlar'],
    'streak_days': 7,
    'total_messages': 24,
    'active_plans': 2,
    'time_distribution': [
        {'plan_id': '1', 'title': 'Python Programlama', 'estimated_hours': 40, 'completed_hours': 17},
        {'plan_id': '2', 'title': 'Veri Analizi', 'estimated_hours': 30, 'completed_hours': 8},
        {'plan_id': '3', 'title': 'Makine Ogrenmesi', 'estimated_hours': 50, 'completed_hours': 5},
    ],
}

_QUOTES = [
    '"Ogrenmek bir hazinedir, sahibini her yerde takip eder." — Cin Atasozü',
    '"Basari, her gun tekrarlanan kucuk cabalarin toplamıdır." — Robert Collier',
    '"Bugün zor olan, yarin aliskanlik olur."',
    '"Bilgi paylastikca cogar." — Türk Atasözü',
    '"Her uzman, bir zamanlar acemiydi."',
]

def show(api_url: str, user_id: str) -> None:
    import pandas as pd

    st.title('Gösterge Paneli')

    demo_mode = not bool(user_id)
    if demo_mode:
        st.info('Demo mod — sol panelden Kullanici ID girerek kendi verilerinizi görün.')
        data = _DEMO_DATA
        user_name = 'Demo Kullanici'
    else:
        with st.spinner('Veriler yukleniyor...'):
            try:
                r = httpx.get(f'{api_url}/analytics/{user_id}', timeout=10)
                r.raise_for_status()
                data = r.json()
            except Exception:
                st.warning('API\'den veri alinamadi, demo veri gösteriliyor.')
                data = _DEMO_DATA
            try:
                r2 = httpx.get(f'{api_url}/users/{user_id}', timeout=10)
                r2.raise_for_status()
                user_name = r2.json().get('name', user_id)
            except Exception:
                user_name = user_id

    pct = data.get('progress_percentage', 0.0)
    completed = data.get('completed_topics', [])
    time_dist = data.get('time_distribution', [])
    streak = data.get('streak_days', 0)
    total_msgs = data.get('total_messages', 0)
    active_plans = data.get('active_plans', 0)
    total_h = sum(i.get('completed_hours', 0) for i in time_dist)

    hour = datetime.now().hour
    greeting = 'Günaydın' if hour < 12 else ('Iyi öğlenler' if hour < 17 else 'Iyi aksamlar')
    st.markdown(f'### {greeting}, {user_name}!')
    st.caption(f'Bugün: {datetime.now().strftime("%d %B %Y")}')
    st.divider()

    # Ana metrikler
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric('Genel Ilerleme', f'{pct:.1f}%', delta=None)
    c2.metric('Tamamlanan Konu', len(completed))
    c3.metric('Günlük Seri', f'{streak} gün', delta=f'+{streak}' if streak > 0 else None)
    c4.metric('Toplam Sure', f'{total_h:.0f}h')
    c5.metric('Aktif Plan', active_plans)

    st.divider()

    # Ilerleme bar
    col_prog, col_chat = st.columns([2, 1])
    with col_prog:
        st.subheader('Genel Ilerleme')
        st.progress(pct / 100.0)
        st.caption(f'{pct:.1f}% tamamlandi')

        if time_dist:
            st.subheader('Plan Bazli Ilerleme')
            for item in time_dist:
                est = item.get('estimated_hours', 1)
                comp = item.get('completed_hours', 0)
                p = min(comp / est * 100, 100) if est > 0 else 0
                ca, cb = st.columns([3, 1])
                ca.write(f"**{item['title']}**")
                cb.write(f"{comp:.0f}h / {est:.0f}h")
                st.progress(p / 100.0)

    with col_chat:
        st.subheader('Istatistikler')
        st.metric('AI Mesaj Sayisi', total_msgs)
        st.metric('Seri Hedefi', f'{streak}/30 gün')
        st.progress(min(streak / 30, 1.0))
        st.divider()
        st.markdown(f'*{random.choice(_QUOTES)}*')

    st.divider()

    # Grafik
    if time_dist:
        st.subheader('Zaman Dagilimi')
        df = pd.DataFrame([
            {
                'Plan': i['title'],
                'Tamamlanan (h)': i.get('completed_hours', 0),
                'Kalan (h)': max(i.get('estimated_hours', 0) - i.get('completed_hours', 0), 0),
            }
            for i in time_dist
        ]).set_index('Plan')
        st.bar_chart(df, color=['#2979FF', '#1a2a4a'])

    st.divider()

    # Tamamlanan konular
    st.subheader('Tamamlanan Konular')
    if completed:
        cols = st.columns(3)
        for i, topic in enumerate(completed):
            cols[i % 3].success(f'✅ {topic}')
    else:
        st.info('Henüz tamamlanan konu yok. Öğrenmeye basla!')

    # Hizli erisim
    st.divider()
    st.subheader('Hizli Erisim')
    b1, b2, b3 = st.columns(3)
    if b1.button('💬 Koca Sor', use_container_width=True):
        st.session_state._nav_page = 'coaching_chat.py'
        st.rerun()
    if b2.button('📚 Plan Görüntüle', use_container_width=True):
        st.session_state._nav_page = 'learning_plan.py'
        st.rerun()
    if b3.button('📈 Ilerleme Detayi', use_container_width=True):
        st.session_state._nav_page = 'progress_view.py'
        st.rerun()
