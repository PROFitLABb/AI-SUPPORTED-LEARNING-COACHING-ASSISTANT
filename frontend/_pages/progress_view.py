import streamlit as st
import httpx
import pandas as pd
from datetime import datetime

_DEMO = {
    'progress_percentage': 42.5,
    'streak_days': 7,
    'total_messages': 24,
    'active_plans': 2,
    'completed_topics': ['Python Temelleri', 'Degiskenler & Tipler', 'Donguler', 'Fonksiyonlar'],
    'time_distribution': [
        {'plan_id': '1', 'title': 'Python Programlama', 'estimated_hours': 40, 'completed_hours': 17},
        {'plan_id': '2', 'title': 'Veri Analizi', 'estimated_hours': 30, 'completed_hours': 8},
        {'plan_id': '3', 'title': 'Makine Ogrenmesi', 'estimated_hours': 50, 'completed_hours': 5},
    ],
}

_BADGES = [
    ('🥇', 'Ilk Adim', 'Ilk konuyu tamamladin!', 'topics', 1),
    ('🔥', 'Haftalik Seri', '7 gün üst üste!', 'streak', 7),
    ('📚', 'Kitap Kurdu', '5 konu tamamladin!', 'topics', 5),
    ('⚡', 'Hiz Treni', '10 saat öğrendin!', 'hours', 10),
    ('🏆', 'Sampiyon', '20 konu tamamladin!', 'topics', 20),
    ('💬', 'Konuskan', '10 AI mesaji!', 'messages', 10),
    ('🌟', 'Yildiz', '30 günlük seri!', 'streak', 30),
    ('🎯', 'Odakli', '50 saat öğrendin!', 'hours', 50),
    ('🚀', 'Roket', '10 konu tamamladin!', 'topics', 10),
]


def show(api_url: str, user_id: str) -> None:
    st.title('Ilerleme Görünümü')
    st.caption('Detayli öğrenme analitigi ve basari rozetleri')

    demo_mode = not bool(user_id)
    if demo_mode:
        st.info('Demo mod — sol panelden Kullanici ID girerek kendi verilerinizi görün.')
        data = _DEMO
    else:
        with st.spinner('Yukleniyor...'):
            try:
                r = httpx.get(f'{api_url}/analytics/{user_id}', timeout=10)
                r.raise_for_status()
                data = r.json()
            except Exception:
                st.warning('API\'den veri alinamadi, demo veri gösteriliyor.')
                data = _DEMO

    pct = data.get('progress_percentage', 0.0)
    completed = data.get('completed_topics', [])
    time_dist = data.get('time_distribution', [])
    streak = data.get('streak_days', 0)
    total_msgs = data.get('total_messages', 0)
    active_plans = data.get('active_plans', 0)
    total_est = sum(i.get('estimated_hours', 0) for i in time_dist)
    total_comp = sum(i.get('completed_hours', 0) for i in time_dist)
    efficiency = round(total_comp / max(total_est, 1) * 100, 1)

    # Metrikler
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric('Ilerleme', f'{pct:.1f}%')
    c2.metric('Tamamlanan', len(completed))
    c3.metric('Toplam Sure', f'{total_comp:.0f}h')
    c4.metric('Seri', f'{streak} gün')
    c5.metric('Mesaj', total_msgs)
    c6.metric('Verimlilik', f'{efficiency}%')

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(['📊 Grafikler', '✅ Konular', '🏆 Rozetler', '📅 Aktivite'])

    with tab1:
        if time_dist:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader('Tamamlanan vs Tahmini Sure')
                df = pd.DataFrame([
                    {
                        'Plan': i['title'],
                        'Tamamlanan (h)': i.get('completed_hours', 0),
                        'Kalan (h)': max(i.get('estimated_hours', 0) - i.get('completed_hours', 0), 0),
                    }
                    for i in time_dist
                ]).set_index('Plan')
                st.bar_chart(df, color=['#2979FF', '#1a2a4a'])

            with col2:
                st.subheader('Plan Bazli Ilerleme')
                for item in time_dist:
                    est = item.get('estimated_hours', 1)
                    comp = item.get('completed_hours', 0)
                    p = min(comp / est * 100, 100) if est > 0 else 0
                    ca, cb = st.columns([3, 1])
                    ca.write(f"**{item['title']}**")
                    cb.write(f'{comp:.0f}h / {est:.0f}h')
                    st.progress(p / 100.0)

            st.divider()
            col3, col4 = st.columns(2)
            with col3:
                st.subheader('Günlük Seri')
                st.progress(min(streak / 30, 1.0))
                st.caption(f'{streak} / 30 gün hedefi')
            with col4:
                st.subheader('Genel Ilerleme')
                st.progress(pct / 100.0)
                st.caption(f'{pct:.1f}% tamamlandi')
        else:
            st.info('Henüz plan verisi yok. Bir öğrenme plani olustur!')

    with tab2:
        st.subheader('Tamamlanan Konular')
        if completed:
            search = st.text_input('Konu ara...', placeholder='Arama...')
            filtered = [t for t in completed if search.lower() in t.lower()] if search else completed
            cols = st.columns(2)
            for i, topic in enumerate(filtered):
                with cols[i % 2]:
                    st.success(f'✅ {topic}')
            st.caption(f'Toplam: {len(completed)} konu')
        else:
            st.info('Henüz tamamlanan konu yok. Öğrenmeye basla!')

    with tab3:
        st.subheader('Basari Rozetleri')
        earned_count = 0
        cols = st.columns(3)
        for idx, (emoji, name, desc, kind, threshold) in enumerate(_BADGES):
            if kind == 'topics':
                earned = len(completed) >= threshold
            elif kind == 'streak':
                earned = streak >= threshold
            elif kind == 'messages':
                earned = total_msgs >= threshold
            else:
                earned = total_comp >= threshold

            if earned:
                earned_count += 1

            with cols[idx % 3]:
                if earned:
                    st.success(f'{emoji} **{name}**\n\n{desc}')
                else:
                    remaining = ''
                    if kind == 'topics':
                        remaining = f'{max(0, threshold - len(completed))} konu kaldi'
                    elif kind == 'streak':
                        remaining = f'{max(0, threshold - streak)} gün kaldi'
                    elif kind == 'messages':
                        remaining = f'{max(0, threshold - total_msgs)} mesaj kaldi'
                    else:
                        remaining = f'{max(0, threshold - total_comp):.0f}h kaldi'
                    st.markdown(f'🔒 ~~{name}~~\n\n*{desc}*\n\n`{remaining}`')

        st.divider()
        st.metric('Kazanilan Rozet', f'{earned_count} / {len(_BADGES)}')
        st.progress(earned_count / len(_BADGES))

    with tab4:
        st.subheader('Aktivite Özeti')
        col1, col2 = st.columns(2)
        with col1:
            st.metric('AI ile Konusma', total_msgs)
            st.metric('Aktif Plan', active_plans)
        with col2:
            st.metric('Öğrenme Serisi', f'{streak} gün')
            st.metric('Toplam Öğrenme', f'{total_comp:.0f} saat')

        if not demo_mode:
            st.divider()
            if st.button('Ilerlemeyi Yenile', use_container_width=True):
                st.rerun()
