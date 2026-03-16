import streamlit as st
import httpx

_DEMO_PLAN = {
    'id': 'demo-1', 'title': 'Python ile Veri Bilimi', 'total_weeks': 12, 'status': 'active',
    'steps': [
        {'id': 's1', 'order': 1, 'title': 'Python Temelleri', 'description': 'Degiskenler, donguler, fonksiyonlar.',
         'estimated_hours': 8, 'status': 'completed', 'deadline': '2026-02-01',
         'resources': [{'title': 'Python.org Tutorial', 'url': 'https://docs.python.org/3/tutorial/', 'type': 'article', 'provider': 'Python.org', 'estimated_hours': 3}]},
        {'id': 's2', 'order': 2, 'title': 'NumPy & Pandas', 'description': 'Veri manipülasyonu ve analizi.',
         'estimated_hours': 10, 'status': 'in_progress', 'deadline': '2026-03-01',
         'resources': [{'title': 'Pandas Docs', 'url': 'https://pandas.pydata.org/docs/', 'type': 'article', 'provider': 'Pandas', 'estimated_hours': 5}]},
        {'id': 's3', 'order': 3, 'title': 'Veri Görselleştirme', 'description': 'Matplotlib ve Seaborn ile grafikler.',
         'estimated_hours': 8, 'status': 'pending', 'deadline': '2026-04-01',
         'resources': [{'title': 'Matplotlib Tutorial', 'url': 'https://matplotlib.org/stable/tutorials/', 'type': 'article', 'provider': 'Matplotlib', 'estimated_hours': 4}]},
        {'id': 's4', 'order': 4, 'title': 'Makine Ogrenmesi Giris', 'description': 'Scikit-learn ile temel modeller.',
         'estimated_hours': 15, 'status': 'pending', 'deadline': '2026-05-01',
         'resources': [{'title': 'Scikit-learn Guide', 'url': 'https://scikit-learn.org/stable/user_guide.html', 'type': 'article', 'provider': 'Scikit-learn', 'estimated_hours': 8}]},
    ],
}

_STATUS_ICONS = {'completed': '✅', 'in_progress': '🔄', 'pending': '⏳'}
_STATUS_LABELS = {'completed': 'Tamamlandi', 'in_progress': 'Devam Ediyor', 'pending': 'Bekliyor'}
_TYPE_ICONS = {'course': '🎓', 'video': '🎬', 'article': '📄', 'book': '📖'}


def _render_plan(plan: dict, api_url: str, demo_mode: bool) -> None:
    steps = plan.get('steps', [])
    done = sum(1 for s in steps if s.get('status') == 'completed')
    total = len(steps)
    pct = done / total * 100 if total > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Plan', plan.get('title', '')[:20])
    c2.metric('Hafta', plan.get('total_weeks', '-'))
    c3.metric('Tamamlanan', f'{done}/{total}')
    c4.metric('Ilerleme', f'{pct:.0f}%')
    st.progress(pct / 100.0)
    st.divider()

    for step in sorted(steps, key=lambda s: s.get('order', 0)):
        status = step.get('status', 'pending')
        icon = _STATUS_ICONS.get(status, '⏳')
        label = _STATUS_LABELS.get(status, status)
        expanded = status == 'in_progress'
        with st.expander(f"{icon} Adim {step.get('order', '')}: {step.get('title', '')} — {label}", expanded=expanded):
            st.write(step.get('description', ''))
            ca, cb = st.columns(2)
            ca.metric('Sure', f"{step.get('estimated_hours', 0):.0f}h")
            cb.metric('Son Tarih', str(step.get('deadline', '-')))

            resources = step.get('resources', [])
            if resources:
                st.markdown('**Kaynaklar:**')
                for res in resources:
                    ti = _TYPE_ICONS.get(res.get('type', ''), '🔗')
                    url = res.get('url', '#')
                    title = res.get('title', '')
                    provider = res.get('provider', '')
                    hours = res.get('estimated_hours', 0)
                    st.markdown(f'  {ti} [{title}]({url}) — {provider} ({hours:.0f}h)')

            if status != 'completed' and not demo_mode:
                col_a, col_b = st.columns(2)
                if col_a.button('✔ Tamamlandi', key=f"done_{step['id']}", use_container_width=True):
                    try:
                        r = httpx.put(f"{api_url}/plans/{plan['id']}/steps/{step['id']}", params={'status': 'completed'}, timeout=10)
                        r.raise_for_status()
                        st.success('Tamamlandi!')
                        r2 = httpx.get(f"{api_url}/plans/{plan['id']}", timeout=10)
                        st.session_state.current_plan = r2.json()
                        st.rerun()
                    except Exception as e:
                        st.error(f'Hata: {e}')
                if col_b.button('▶ Basladi', key=f"start_{step['id']}", use_container_width=True):
                    try:
                        r = httpx.put(f"{api_url}/plans/{plan['id']}/steps/{step['id']}", params={'status': 'in_progress'}, timeout=10)
                        r.raise_for_status()
                        r2 = httpx.get(f"{api_url}/plans/{plan['id']}", timeout=10)
                        st.session_state.current_plan = r2.json()
                        st.rerun()
                    except Exception as e:
                        st.error(f'Hata: {e}')
            elif status == 'completed':
                st.success('Bu adim tamamlandi! 🎉')


def show(api_url: str, user_id: str) -> None:
    st.title('Ogrenme Plani')
    demo_mode = not bool(user_id)
    if demo_mode:
        st.info('Demo mod — sol panelden Kullanici ID girerek gercek planlarinizi görün.')

    tab1, tab2, tab3 = st.tabs(['📋 Mevcut Plan', '🤖 AI ile Plan Olustur', '✏️ Manuel Plan'])

    # ── TAB 1: Mevcut Plan ────────────────────────────────────────────────────
    with tab1:
        if demo_mode:
            _render_plan(_DEMO_PLAN, api_url, demo_mode=True)
        else:
            # Kullanicinin planlarini listele
            if st.button('Planlarimi Yükle', use_container_width=True):
                try:
                    r = httpx.get(f'{api_url}/plans/user/{user_id}', timeout=10)
                    r.raise_for_status()
                    plans = r.json()
                    st.session_state.user_plans = plans
                except Exception as e:
                    st.error(f'Planlar yuklenemedi: {e}')

            plans = st.session_state.get('user_plans', [])
            if plans:
                plan_titles = {p['id']: p['title'] for p in plans}
                selected_id = st.selectbox('Plan Sec', options=list(plan_titles.keys()), format_func=lambda x: plan_titles[x])
                if selected_id:
                    selected = next((p for p in plans if p['id'] == selected_id), None)
                    if selected:
                        st.session_state.current_plan = selected
            elif 'current_plan' not in st.session_state:
                pid = st.text_input('veya Plan ID girin', placeholder='Plan ID')
                if pid and st.button('Yukle'):
                    try:
                        r = httpx.get(f'{api_url}/plans/{pid}', timeout=10)
                        r.raise_for_status()
                        st.session_state.current_plan = r.json()
                    except Exception as e:
                        st.error(f'Plan bulunamadi: {e}')

            plan = st.session_state.get('current_plan')
            if plan:
                _render_plan(plan, api_url, demo_mode=False)

    # ── TAB 2: AI ile Plan Olustur ────────────────────────────────────────────
    with tab2:
        st.subheader('AI ile Kisisellestirilmis Plan Olustur')
        if demo_mode:
            st.warning('AI plan olusturmak icin Kullanici ID girin.')
        else:
            st.markdown('AI koçunuz, profilinize göre adim adim bir öğrenme yolu olusturacak.')
            with st.form('ai_plan_form'):
                col1, col2 = st.columns(2)
                name = col1.text_input('Adiniz', placeholder='örn: Ahmet')
                goal = col2.text_input('Öğrenme Hedefiniz', placeholder='örn: Python ile web gelistirme')
                skill = col1.selectbox('Seviyeniz', ['beginner', 'intermediate', 'advanced'],
                                       format_func=lambda x: {'beginner': 'Baslangic', 'intermediate': 'Orta', 'advanced': 'Ileri'}[x])
                hours = col2.slider('Haftalik Calisma Saati', 1, 40, 5)
                interests = st.text_input('Ilgi Alanlari (virgülle ayirin)', placeholder='örn: web, veri, oyun')
                style = st.selectbox('Öğrenme Stili', ['reading', 'visual', 'hands-on'],
                                     format_func=lambda x: {'reading': 'Okuyarak', 'visual': 'Görsel', 'hands-on': 'Pratik yaparak'}[x])
                submitted = st.form_submit_button('🤖 AI ile Plan Olustur', use_container_width=True)

            if submitted:
                if not name or not goal:
                    st.error('Ad ve hedef zorunludur.')
                else:
                    interest_list = [i.strip() for i in interests.split(',') if i.strip()]
                    with st.spinner('AI planınızı olusturuyor... (10-20 saniye)'):
                        try:
                            r = httpx.post(
                                f'{api_url}/plans/ai-generate',
                                json={
                                    'user_id': user_id,
                                    'name': name,
                                    'skill_level': skill,
                                    'interests': interest_list,
                                    'weekly_hours': hours,
                                    'learning_style': style,
                                    'goal': goal,
                                },
                                timeout=60,
                            )
                            r.raise_for_status()
                            plan = r.json()
                            st.session_state.current_plan = plan
                            st.success(f'Plan olusturuldu: **{plan["title"]}** ({len(plan.get("steps", []))} adim)')
                            st.rerun()
                        except Exception as e:
                            st.error(f'AI plan olusturulamadi: {e}')

    # ── TAB 3: Manuel Plan ────────────────────────────────────────────────────
    with tab3:
        st.subheader('Manuel Ogrenme Plani Olustur')
        if demo_mode:
            st.warning('Plan olusturmak icin Kullanici ID girin.')
        else:
            with st.form('manual_plan_form'):
                title = st.text_input('Plan Basligi', placeholder='örn: Python ile Veri Bilimi')
                weeks = st.slider('Toplam Hafta', 1, 52, 8)
                n = st.number_input('Adim Sayisi', 1, 10, 3)
                steps_data = []
                for i in range(int(n)):
                    st.markdown(f'**Adim {i+1}**')
                    ca, cb = st.columns(2)
                    t = ca.text_input('Baslik', key=f'st_{i}', placeholder=f'Adim {i+1}')
                    h = cb.number_input('Saat', 1, 100, 5, key=f'sh_{i}')
                    d = st.text_area('Aciklama', key=f'sd_{i}', height=60)
                    steps_data.append({'title': t, 'description': d, 'estimated_hours': h, 'order': i+1})
                submitted = st.form_submit_button('Plan Olustur', use_container_width=True)

            if submitted:
                if not title:
                    st.error('Baslik bos olamaz.')
                else:
                    try:
                        r = httpx.post(
                            f'{api_url}/plans',
                            json={'user_id': user_id, 'title': title, 'total_weeks': weeks, 'steps': steps_data},
                            timeout=15,
                        )
                        r.raise_for_status()
                        result = r.json()
                        st.success('Plan olusturuldu!')
                        st.session_state.current_plan = result
                        st.rerun()
                    except Exception as e:
                        st.error(f'Hata: {e}')
