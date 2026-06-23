
# Lab4Tech CV-to-Job Matching Assistant

AI-powered CV analysis and career guidance system using LLM + RAG concepts.

This project allows users to upload a CV, compare it against a target job role, calculate a match percentage, identify missing skills, and suggest alternative suitable career paths.


# Features

✅ Upload CV in PDF format  
✅ Extract text from CV  
✅ Detect technical skills automatically  
✅ Compare CV against selected job role  
✅ Generate job match percentage  
✅ Show matching and missing skills  
✅ Suggest alternative suitable roles  
✅ RAG-ready architecture for verified knowledge retrieval  
✅ Privacy-aware prototype aligned with Swiss AI recommendations


# Project Architecture

```text
User Uploads CV
        ↓
PDF Text Extraction
        ↓
Skill Extraction
        ↓
Job Role Requirement Retrieval
        ↓
Match Score Calculation
        ↓
AI Explanation + Suggestions
```

---

# 📂 Project Structure

```text
CV-job-matching-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI routes
│   │   ├── schemas.py           # API request/response models
│   │   └── services.py          # Backend service orchestration
│   ├── cv/                      # Backend-local CV parsing and skill extraction
│   ├── job_description/         # Backend-local job skill extraction
│   ├── matching/                # Backend-local matching engine
│   └── requirements.txt
│
├── frontend/
│   ├── angular-frontend/        # Angular UI
│   │   ├── angular.json
│   │   ├── package.json
│   │   └── src/
│   ├── react-frontend/          # React UI
│   │   ├── index.html
│   │   ├── package.json
│   │   └── src/
│   └── streamlit-ui/            # Existing Streamlit UIs kept for now
│       ├── app-cv-job-matching-engine.py
│       ├── app-cv-job-matching-with-new-job.py
│       ├── app-job-skill-extractor-mistral-api.py
│       └── path_setup.py
│
├── data/
│   ├── extracted_skills_mistral-large-latest/
│   ├── job_roles/
│   └── taxonomies/
│
├── prompts/
├── vectorstore/
├── requirements.txt
├── README.md
├── .env
└── .gitignore
```

---

# Installation

## 1. Clone repository

```bash
git clone https://github.com/BarshaLamichhane/Lab4Tech-llm-rag-projects.git
cd lab4tech-cv-rag-assistant
```

## 2. Create virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Mac/Linux

```bash
python -m venv venv
source venv/bin/activate
```
then do 

```bash 
which python
```
It should show python inside your venv for example '/Users/barshalamichhane/Documents/python-project/LLM-Projects/Lab4Tech-LLM-RAG-Projects/venv/bin/python' of your working directory not inside your global machine

---

# 📦 Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r CV-job-matching-assistant/requirements.txt
```
then do 
```bash 
which pip
```
It should show inside venv of your working directory something like this for example
'/Users/barshalamichhane/Documents/python-project/LLM-Projects/Lab4Tech-LLM-RAG-Projects/venv/bin/pip'

if you do only 
```bash
pip install --upgrade pip
```
without python -m then your library is not inside venv of your current working directory. it will be somewhere else, globally.

---
# Run Application

The current primary application uses the FastAPI backend and React frontend. Run them in two separate terminals.

Create `CV-job-matching-assistant/.env`. The initial admin password is used only when
the users database is empty:

```env
MISTRAL_API_KEY=your_mistral_api_key
APP_ENV=development
JWT_SECRET=replace-with-at-least-32-random-characters
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=replace-with-a-password-of-at-least-12-characters
```

## Terminal 1: FastAPI backend

From the repository root, activate the Python virtual environment and start the backend:

### Mac/Linux

```bash
source venv/bin/activate
cd CV-job-matching-assistant
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### Windows

```bash
venv\Scripts\activate
cd CV-job-matching-assistant
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Verify that the backend is running:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

The React application requires login:

- Admins can create user/admin accounts, run matching and interview practice, edit default score weights and aliases, and view their saved sessions.
- Regular users can run matching and interview practice and view only their own saved sessions.
- Users and matching/interview sessions are saved in the SQLite database at `data/app.db` by default.
- Admin settings are saved locally in `data/app_settings.json`; skill aliases update `data/taxonomies/skill_categories.json`.

Authentication uses PBKDF2 password hashes and signed, expiring JWT sessions stored
in HttpOnly cookies. Tokens are never exposed to React or browser local storage.
Users can rotate their password from the Account page; doing so invalidates existing
sessions.

Create additional users from the `CV-job-matching-assistant` directory:

```bash
python -m backend.app.create_user new-user
python -m backend.app.create_user another-admin --role admin
```

Reset a password locally:

```bash
python -m backend.app.reset_password admin
```

FastAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Terminal 2: React frontend

The React frontend does not require the Python virtual environment.

```bash
cd CV-job-matching-assistant/frontend/react-frontend
npm install
npm run dev
```

Open the application:

```text
http://localhost:5173/
```

The React frontend calls the FastAPI backend at `http://localhost:8000`.

To use a backend running on a different port:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8010 npm run dev
```

---

# Production Deployment

The provided Docker Compose setup serves React through Nginx and proxies `/api` to
FastAPI on the same origin. Application data is persisted in the
`hire-ready-data` Docker volume.

1. Create the production environment:

```bash
cp .env.example .env
openssl rand -hex 32
```

Put the generated value in `JWT_SECRET`, then set a strong
`INITIAL_ADMIN_PASSWORD`, your Mistral key, deployed domain, CORS origin, and
allowed hosts.

2. Build and start:

```bash
docker compose up --build -d
```

3. Open:

```text
http://localhost:8080
```

4. After the first successful startup, remove `INITIAL_ADMIN_PASSWORD` from the
deployment environment. The admin account remains in SQLite.

Create additional deployed users with:

```bash
docker compose exec backend python -m backend.app.create_user new-user
docker compose exec backend python -m backend.app.create_user another-admin --role admin
```
reset admin password. NOTE: do this only if required
```bash
cd CV-job-matching-assistant
python -m backend.app.reset_password admin
```

For public deployment, terminate TLS at a cloud load balancer or reverse proxy
and keep `COOKIE_SECURE=true`. Back up the Docker data volume regularly.

The included SQLite setup is intended for a single backend instance. Before
horizontal scaling to multiple backend replicas, move users and sessions to a
managed PostgreSQL database and use a shared rate limiter such as Redis.

Production defaults intentionally disable:

- FastAPI `/docs`
- Live Python code execution

Live code execution must run in a separate locked-down sandbox service before
enabling `CODE_EXECUTION_ENABLED=true` on a public deployment.

Important production variables are documented in [.env.example](.env.example).

## Restart after code changes

Vite updates React frontend changes automatically while `npm run dev` is running.

Restart FastAPI after backend Python changes:

```bash
# Stop the backend with Ctrl+C, then run:
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

For automatic backend reload during development:

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Port 8000 already in use

On Mac/Linux, find and stop the process using port `8000`:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```
it will show PID and then do 

```bash
kill <PID>
```
if it doesnt stop do 
```bash 
kill -9 <PID>
```
or  one line version 
```bash
lsof -tiTCP:<portno> -sTCP:LISTEN | xargs kill -9
```
or one line version
```bash
kill -9 $(lsof -tiTCP:8000 -sTCP:LISTEN)
kill -9 $(lsof -tiTCP:5173 -sTCP:LISTEN)
```
port no can be 8000, 8001 etc
for example 

```bash
lsof -tiTCP:8000 -sTCP:LISTEN | xargs kill -9
lsof -tiTCP:8001 -sTCP:LISTEN | xargs kill -9
```

Alternatively, start the backend on another port. If you do this, also update `API_BASE_URL` in `frontend/react-frontend/src/api.ts`.

## Optional legacy frontends

Angular and Streamlit interfaces remain in `frontend/`, but current UI development is focused on React.

---

# Current MVP (Minimal Viable Product) Features

The current MVP supports:

- CV upload
- PDF text extraction
- Skill detection
- Job-role comparison
- Match percentage calculation
- Missing skill analysis
- Alternative role recommendations

---

#  Technologies Used

- Python
- Streamlit
- FastAPI
- Angular
- React
- LangChain
- FAISS
- Sentence Transformers
- PyMuPDF
- Scikit-learn

---

#  AI Governance & Privacy

This prototype follows basic AI governance principles:

- Transparency that users interact with AI
- No unnecessary storage of personal CV data
- Retrieval-based responses to reduce hallucinations
- Focus on verified knowledge sources

Aligned conceptually with:
- EU AI Act transparency principles
- Swiss PFPDT chatbot recommendations

---

#  Example Workflow

```text
1. User uploads CV
2. User selects target role
3. System extracts skills
4. System compares with role requirements
5. System calculates match percentage
6. System suggests alternative roles
```

---

#  Future Improvements

Planned enhancements:

- Real RAG pipeline with embeddings
- Chroma/FAISS vector database
- LLM-generated career recommendations
- Multilingual support (French/English)
- Real Swiss job market integration
- Admin dashboard
- CV anonymization
- Feedback and evaluation system

---

#  Example Roles

Current sample roles include:

- AI Engineer
- Data Scientist
- Data Engineer
- Business Analyst
- Software Engineer

---

#  Learning Goals

This project is designed to explore:

- LLM applications
- Retrieval-Augmented Generation (RAG)
- AI-assisted career guidance
- Explainable AI systems
- AI governance and privacy-aware design

---

# 👩 Author

Barsha Lamichhane  
AI & Data Engineer | LLM • RAG • Computer Vision • NLP

Switzerland 🇨🇭

---

# 📄 License

This project is for educational and research purposes.

# INFO

## Use development when running locally without HTTPS.
## Change to production when deploying.
APP_ENV=development

## Signs login sessions. Keep secret and never change casually.
JWT_SECRET=your-generated-secret by running `openssl rand -hex 32`

JWT_ISSUER=hire-ready-ai

## Login session expires after 60 minutes.
ACCESS_TOKEN_MINUTES=60

AUTH_COOKIE_NAME=hire_ready_session

## Use false locally because localhost normally uses HTTP.
## Use true when deployed with HTTPS.
COOKIE_SECURE=false
COOKIE_SAMESITE=lax

## Creates the first admin only when data/app.db is empty.
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=ChooseYourStrongPassword123!


Important:

Replace INITIAL_ADMIN_PASSWORD=replace-with-a-strong-password.
Your password must contain at least 12 characters.
Remove INITIAL_ADMIN_PASSWORD after the first successful startup.
Do not upload .env to GitHub.

For Docker production deployment, use:

env

APP_ENV=production
COOKIE_SECURE=true
DATABASE_PATH=/app/data/app.db
CORS_ALLOWED_ORIGINS=https://your-domain.com
ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1
API_DOCS_ENABLED=false
CODE_EXECUTION_ENABLED=false
