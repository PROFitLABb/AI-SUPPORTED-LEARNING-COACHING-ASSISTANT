<div align="center">

<img src="https://img.shields.io/badge/AI-Learning%20Coach-7c3aed?style=for-the-badge&logo=graduation-cap&logoColor=white" alt="AI Learning Coach"/>

# 🎓 AI Learning Coach

### *Kişiselleştirilmiş yapay zeka destekli öğrenme koçunuz*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3%2070B-F55036?style=flat-square&logo=groq&logoColor=white)](https://groq.com)
[![SQLite](https://img.shields.io/badge/SQLite-Async-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-06b6d4?style=flat-square)](LICENSE)

<br/>

> **Groq'un LLaMA 3.3 70B modeli** ile güçlendirilmiş, öğrenme hedeflerinizi anlayan,  
> kişiselleştirilmiş planlar oluşturan ve sizi motive eden akıllı bir öğrenme asistanı.

<br/>

```
┌─────────────────────────────────────────────────────────┐
│  💬 AI Koç  │  📊 Dashboard  │  📚 Plan  │  📈 İlerleme │
└─────────────────────────────────────────────────────────┘
         Groq LLaMA 3.3 70B  ·  FastAPI  ·  SQLite
```

</div>

---

## ✨ Özellikler

### 🤖 AI Koçluk Sohbeti
- **Groq LLaMA 3.3 70B** ile gerçek zamanlı, akıllı yanıtlar
- Sadece eğitim ve kariyer konularında uzmanlaşmış sistem prompt
- Sohbet geçmişi veritabanında saklanır, bağlam korunur
- Kaynak önerileri ve "Sonraki Adım" ipuçları
- 6 hızlı soru şablonu ile anında başlangıç
- Demo mod — API key olmadan da test edilebilir

### 🗺️ AI ile Öğrenme Planı Oluşturma
- Kullanıcı profiline göre **otomatik 4-8 adımlı plan** üretimi
- Seviye, ilgi alanı, haftalık saat ve öğrenme stiline göre kişiselleştirme
- Her adımda gerçek kaynak linkleri (URL dahil)
- Manuel plan oluşturma ve adım güncelleme
- Adım başlatma / tamamlama takibi

### 📊 Gösterge Paneli
- Genel ilerleme yüzdesi ve plan bazlı breakdown
- Günlük çalışma serisi (streak) takibi
- Zaman dağılımı bar grafiği
- Motivasyon alıntıları
- Hızlı erişim butonları

### 📈 İlerleme & Analitik
- 6 temel metrik (ilerleme, tamamlanan konu, süre, seri, mesaj, verimlilik)
- Tamamlanan vs tahmini süre karşılaştırma grafiği
- **9 başarı rozeti** sistemi (konu, seri, saat bazlı)
- Konu arama ve filtreleme
- Aktivite özeti sekmesi

### 🎨 Premium UI
- Derin mor/indigo + cyan renk paleti
- Tüm bileşenlerde tutarlı dark tema
- Gradient butonlar, hover animasyonları
- Responsive layout

---

## 🏗️ Mimari

```
ai-learning-coach/
│
├── 🖥️  frontend/                  # Streamlit UI
│   ├── app.py                     # Ana uygulama + navigasyon + CSS
│   ├── .streamlit/config.toml     # Tema konfigürasyonu
│   └── _pages/
│       ├── coaching_chat.py       # AI sohbet arayüzü
│       ├── dashboard.py           # Gösterge paneli
│       ├── learning_plan.py       # Plan yönetimi
│       └── progress_view.py       # İlerleme & rozetler
│
├── 🔧  backend/                   # FastAPI REST API
│   ├── main.py                    # Uygulama giriş noktası
│   ├── agents/
│   │   ├── coaching_agent.py      # LLM koçluk yanıtları
│   │   ├── learning_agent.py      # AI plan oluşturma
│   │   └── feedback_agent.py      # İlerleme değerlendirme
│   ├── api/routes/
│   │   ├── coaching_routes.py     # /coaching/chat, /history
│   │   ├── learning_routes.py     # /plans, /plans/ai-generate
│   │   ├── analytics_routes.py    # /analytics/{user_id}
│   │   └── user_routes.py         # /users CRUD
│   ├── models/                    # SQLAlchemy + Pydantic modeller
│   ├── services/                  # İş mantığı katmanı
│   ├── database/                  # DB bağlantısı + migration
│   └── nlp/                       # Intent classifier, goal extractor
│
├── 🧠  ai_core/                   # AI altyapısı
│   ├── agent_workflows/           # Koçluk, değerlendirme, öğrenme workflow
│   └── memory/                    # Kullanıcı bağlam belleği
│
├── ⚙️  config/
│   ├── settings.py                # Pydantic Settings (.env okur)
│   ├── llm_config.py              # Groq/OpenAI/Ollama konfigürasyonu
│   └── prompts.yaml               # Sistem prompt şablonları
│
├── .env                           # API anahtarları (git'e ekleme!)
└── requirements.txt
```

---

## 🚀 Kurulum

### Gereksinimler
- Python 3.11+
- [Groq API Key](https://console.groq.com) (ücretsiz)

### 1. Repoyu klonla

```bash
git clone https://github.com/kullanici/ai-learning-coach.git
cd ai-learning-coach
```

### 2. Sanal ortam oluştur

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Bağımlılıkları yükle

```bash
pip install -r requirements.txt
```

### 4. `.env` dosyasını oluştur

```env
# Groq API (https://console.groq.com → ücretsiz)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile

# Veritabanı
DATABASE_URL=sqlite+aiosqlite:///./ai_learning_coach.db

# Güvenlik
SECRET_KEY=gizli-anahtar-buraya

DEBUG=true
```

### 5. Backend'i başlat

```bash
uvicorn backend.main:app --reload
```

> API: http://localhost:8000  
> Swagger Docs: http://localhost:8000/docs

### 6. Frontend'i başlat (yeni terminal)

```bash
streamlit run frontend/app.py
```

> Uygulama: http://localhost:8501

---

## 🔌 API Endpoints

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `POST` | `/users` | Yeni kullanıcı oluştur |
| `GET` | `/users/{id}` | Kullanıcı bilgisi |
| `POST` | `/coaching/chat` | AI koç ile sohbet |
| `GET` | `/coaching/history/{user_id}` | Sohbet geçmişi |
| `POST` | `/plans/ai-generate` | AI ile plan oluştur |
| `POST` | `/plans` | Manuel plan oluştur |
| `GET` | `/plans/{id}` | Plan detayı |
| `GET` | `/plans/user/{user_id}` | Kullanıcı planları |
| `PUT` | `/plans/{id}/steps/{step_id}` | Adım durumu güncelle |
| `GET` | `/analytics/{user_id}` | İlerleme analitikleri |
| `GET` | `/health` | Sağlık kontrolü |

---

## 🤖 Desteklenen LLM Sağlayıcıları

| Sağlayıcı | Model | Hız | Ücretsiz |
|-----------|-------|-----|----------|
| **Groq** ⭐ | LLaMA 3.3 70B | ⚡ Çok hızlı | ✅ |
| Groq | LLaMA 3.1 8B (fallback) | ⚡⚡ Ultra hızlı | ✅ |
| OpenAI | GPT-4o-mini | 🔵 Orta | ❌ |
| Ollama | LLaMA3 (local) | 🟡 Değişken | ✅ |

`.env` dosyasında `LLM_PROVIDER=groq` ile Groq kullanılır.

---

## 🎮 Kullanım

### Demo Mod (API key gerekmez)
Uygulamayı açtığınızda sol panelde **Kullanıcı ID** boş bırakırsanız demo mod aktif olur. Tüm sayfalar örnek verilerle çalışır.

### Gerçek Kullanım
1. Sol panelden **"Yeni Kullanıcı Oluştur"** ile hesap aç
2. Oluşturulan **Kullanıcı ID**'yi kopyala ve üstteki alana yapıştır
3. **AI Koç ile Sohbet** sayfasında öğrenme hedefini yaz
4. **Öğrenme Planı** → **AI ile Plan Oluştur** sekmesinden otomatik plan al
5. Plan adımlarını tamamladıkça **İlerleme** sayfasında rozetleri kazan

---

## 🌐 Deploy

### Streamlit Cloud (Frontend) — Ücretsiz

1. Repoyu GitHub'a yükle
2. [share.streamlit.io](https://share.streamlit.io) → GitHub ile giriş
3. `ai-learning-coach/frontend/app.py` yolunu seç
4. Secrets bölümüne `.env` içeriğini ekle
5. Deploy

### Render.com (Backend) — Ücretsiz Tier

```
Root Directory : ai-learning-coach
Build Command  : pip install -r requirements.txt
Start Command  : uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Environment Variables bölümüne `.env` değerlerini ekle.

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Frontend | Streamlit 1.32+ |
| Backend | FastAPI + Uvicorn |
| AI/LLM | Groq API (LLaMA 3.3 70B) |
| Veritabanı | SQLite + SQLAlchemy (async) |
| ORM | SQLAlchemy 2.0 (async) |
| Validasyon | Pydantic v2 |
| HTTP Client | httpx (async) |
| Göç | Alembic |

---

## 📁 Önemli Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `backend/agents/coaching_agent.py` | LLM koçluk yanıt motoru, retry + JSON parse |
| `backend/agents/learning_agent.py` | AI plan oluşturma, 4-8 adım garantisi |
| `backend/agents/feedback_agent.py` | Kural tabanlı + LLM ilerleme değerlendirme |
| `config/llm_config.py` | Groq/OpenAI/Ollama sağlayıcı seçimi |
| `frontend/app.py` | Navigasyon + global CSS tema |

---

## 🤝 Katkı

```bash
# Fork → Branch → Commit → PR
git checkout -b feature/yeni-ozellik
git commit -m "feat: harika bir özellik eklendi"
git push origin feature/yeni-ozellik
```

---

## 📄 Lisans

MIT © 2026 — Dilediğiniz gibi kullanın, geliştirin, dağıtın.

---

<div align="center">

**Groq ⚡ · FastAPI 🔧 · Streamlit 🎨 · LLaMA 3.3 🧠**

*Öğrenmek bir hazinedir, sahibini her yerde takip eder.*

</div>
