"""Koçluk Sohbeti."""
import streamlit as st
import httpx
from datetime import datetime

_DEMO = [
    {
        "content": "Harika bir hedef! Python için önce temel sözdizimini kavramanı öneririm. Değişkenler, döngüler ve fonksiyonlarla başla.",
        "suggested_resources": ["Python.org resmi tutorial", "freeCodeCamp Python kursu", "Automate the Boring Stuff"],
        "next_step_hint": "İlk adım: değişken tanımlamayı öğren ve küçük bir hesap makinesi yaz.",
    },
    {
        "content": "İlerleme harika görünüyor! Öğrendiklerini pekiştirmek için küçük projeler yapman çok faydalı olacak.",
        "suggested_resources": ["LeetCode Easy problemleri", "Kaggle başlangıç notebook'ları"],
        "next_step_hint": "Bugün 30 dakika pratik yap.",
    },
    {
        "content": "Motivasyonunu korumak için hedeflerini küçük parçalara bölmeni öneririm. Her gün 1 saat bile büyük fark yaratır!",
        "suggested_resources": ["Pomodoro tekniği", "Notion ile hedef takibi"],
        "next_step_hint": "Yarın için 1 somut öğrenme hedefi belirle.",
    },
]

def show(api_url: str, user_id: str) -> None:
    st.title("💬 AI Koç ile Sohbet")
    st.caption("Groq LLM destekli kişisel öğrenme koçunuz")

    demo_mode = not bool(user_id)
    if demo_mode:
        st.info("💡 Demo mod aktif — sol panelden Kullanıcı ID girerek gerçek AI koçla konuşabilirsiniz.")

    # Sohbet geçmişini başlat
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [{
            "role": "assistant",
            "content": "👋 Merhaba! Ben AI öğrenme koçunuzum. Öğrenme hedefleriniz, zorlandığınız konular veya motivasyon hakkında benimle konuşabilirsiniz. Size nasıl yardımcı olabilirim?",
            "time": datetime.now().strftime("%H:%M"),
        }]

    # Araç çubuğu
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🗑 Temizle", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()

    with st.expander("🚀 Hızlı Sorular"):
        quick_qs = [
            "Python öğrenmek istiyorum, nereden başlamalıyım?",
            "Bugün motive olamıyorum, ne yapmalıyım?",
            "Makine öğrenmesi için kaynak önerir misin?",
            "Haftalık çalışma programı nasıl yapmalıyım?",
        ]
        cols = st.columns(2)
        for i, q in enumerate(quick_qs):
            if cols[i % 2].button(q, key=f"qq_{i}", use_container_width=True):
                st.session_state._quick_input = q
                st.rerun()

    st.divider()

    # Mesajları göster
    for msg in st.session_state.chat_messages:
        avatar = "👤" if msg["role"] == "user" else "🎓"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])
            for res in msg.get("suggested_resources", []):
                st.markdown(f"  📌 {res}")
            hint = msg.get("next_step_hint", "")
            if hint:
                st.info(f"💡 **Sonraki Adım:** {hint}")
            if msg.get("time"):
                st.caption(msg["time"])

    # Giriş
    default_input = st.session_state.pop("_quick_input", "")
    user_input = st.chat_input("Koçunuza bir şey sorun...")

    if user_input or default_input:
        message = user_input or default_input
        now = datetime.now().strftime("%H:%M")
        st.session_state.chat_messages.append({"role": "user", "content": message, "time": now})

        with st.spinner("🤔 Koçunuz düşünüyor..."):
            if demo_mode:
                idx = len(st.session_state.chat_messages) % len(_DEMO)
                resp = _DEMO[idx]
                ai_msg = {
                    "role": "assistant",
                    "content": resp["content"],
                    "suggested_resources": resp["suggested_resources"],
                    "next_step_hint": resp["next_step_hint"],
                    "time": datetime.now().strftime("%H:%M"),
                }
            else:
                try:
                    r = httpx.post(f"{api_url}/coaching/chat",
                                   json={"user_id": user_id, "message": message}, timeout=30)
                    r.raise_for_status()
                    result = r.json()
                    ai_msg = {
                        "role": "assistant",
                        "content": result.get("content", ""),
                        "suggested_resources": result.get("suggested_resources", []),
                        "next_step_hint": result.get("next_step_hint", ""),
                        "time": datetime.now().strftime("%H:%M"),
                    }
                except Exception as e:
                    ai_msg = {
                        "role": "assistant",
                        "content": f"⚠️ API bağlantısı kurulamadı: {e}",
                        "time": datetime.now().strftime("%H:%M"),
                    }

        st.session_state.chat_messages.append(ai_msg)
        st.rerun()
