
# HireReadyAI - CV-to-Job Matching and Interview Assistant

AI-powered CV analysis, job matching, personalized learning, and interview preparation platform using LLM + RAG concepts.

This project allows users to upload a CV, compare it against a target job role, calculate a match percentage, identify missing skills, generate a personalized learning path, and practise interview questions with scored feedback.

The system supports company-context-aware interview generation, adaptive interview practice, coding-question execution, and RAG-grounded questions from uploaded learning material.

# Features

✅ Upload CV in PDF/TXT format  
✅ Extract skills from CV text, projects, and experience sections  
✅ Extract job skills from job descriptions using Mistral  
✅ Capture company context from job descriptions, including company name, industry domain, company context, and business problem  
✅ Compare CV skills against saved or newly extracted job roles  
✅ Calculate weighted match score with admin-adjustable skill weights  
✅ Show exact matched and missing skills by category for transparent fit analysis  
✅ Generate score explanation and category-wise match details  
✅ Generate personalized learning paths from skill gaps and interview performance  
✅ Download extracted job profiles and match outputs as JSON  
✅ Download generated interview question sets as JSON or PDF  
✅ Download complete interview preparation and adaptive interview reports as PDF  
✅ Interview Preparation Mode for focused single-skill practice  
✅ Company-context-aware interview generation for realistic organization-specific questions  
✅ Adaptive Interview Mode that switches skills based on learner performance  
✅ Hybrid answer evaluation using structured rubrics, Python code execution, test-based checks, and RAG-grounded context instead of relying only on raw LLM scoring  
✅ Python coding-question runner for live coding practice  
✅ RAG-grounded question generation from uploaded learning material  
✅ FAISS vector index lifecycle: use existing, update, or recreate  
✅ Admin-only RAG learning dashboard showing document ingestion, chunking, embeddings, FAISS storage, retrieval, and context sent to the LLM  
✅ Authentication, admin/user roles, settings, and deployable backend/frontend structure  
✅ Privacy-aware prototype aligned with AI governance principles


# Project Architecture

```text
CV + Job Description
        ↓
Text Extraction
        ↓
CV Skill Extraction + Job Skill Extraction
        ↓
Skill Normalization and Alias Matching
        ↓
Weighted Match Score + Skill Gap Analysis
        ↓
Personalized Learning Path
        ↓
Interview Preparation / Adaptive Interview
        ↓
LLM Scoring + Code Runner + RAG Grounding
        ↓
Rubric Scoring + Test-Based Scoring + Grounded RAG Scoring
        ↓
Feedback + Reports + Next Practice Plan
```

## Impact Areas and Applications

HireReadyAI is designed as a modular AI career-readiness platform, not only a
single job-matching script. Its core subsystems can support multiple business
and learning use cases.

```text
┌──────────────────────────────────────────────┐
│          HireReadyAI Core Subsystems          │
├──────────────────────────────────────────────┤
│ CV Parsing                                   │
│ Job Skill Extraction                         │
│ Skill Normalization and Matching             │
│ Transparent Match Scoring                    │
│ Interview Preparation                        │
│ Adaptive Learning                            │
│ Code Runner                                  │
│ RAG Grounding                                │
│ Downloadable Reports                         │
└───────────────────────┬──────────────────────┘
                        │
        ┌───────────────┼────────────────┬────────────────┐
        ▼               ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ B2B          │ │ Technical    │ │ HR Consulting│ │ Education &  │
│ Recruitment  │ │ Talent       │ │ & Agencies   │ │ Bootcamps    │
├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤
│ Skills-based │ │ Standardized │ │ Rapid client │ │ Personalized │
│ screening    │ │ readiness    │ │ job briefing │ │ learning     │
│ Transparent  │ │ profiles     │ │ Repeatable   │ │ Role-focused │
│ fit reports  │ │ Coding       │ │ screening    │ │ practice     │
│ Admin-tuned  │ │ sandbox      │ │ Explainable  │ │ Progress     │
│ score weights│ │ practice     │ │ reports      │ │ dashboards   │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
                        │
                        ▼
                ┌──────────────┐
                │ Individual   │
                │ Job Seekers  │
                ├──────────────┤
                │ Exact skill  │
                │ gap clarity  │
                │ Interview    │
                │ readiness    │
                │ Downloadable │
                │ reports      │
                └──────────────┘
```

### Business Applications

- **B2B corporate recruitment:** skills-based screening, transparent candidate
  shortlisting, internal mobility support, and admin-configurable scoring
  metrics aligned with role priorities.
- **Technical talent marketplaces:** standardized candidate readiness profiles,
  coding-practice evidence, role-fit scoring, and downloadable preparation
  reports.
- **HR consulting and agencies:** faster job briefing, repeatable screening
  criteria, client-specific evaluation datasets, and explainable candidate-role
  fit reports.
- **Universities and bootcamps:** role-focused interview preparation,
  personalized learning paths, progress dashboards, and RAG-grounded questions
  from course material.
- **Individual job seekers:** exact matched/missing skill visibility,
  focused interview practice, adaptive learning, and downloadable reports for
  self-review.

## RAG Architecture

```text
Uploaded Verified Material
        ↓
data/grounding/documents/
        ↓
LangChain RecursiveCharacterTextSplitter
        ↓
HuggingFace sentence-transformers/all-MiniLM-L6-v2
        ↓
384-dimensional embeddings
        ↓
FAISS vector index
        ↓
data/grounding/faiss_index/
        ↓
Retrieval Query from Role + Skill + Optional Grounding Query
        ↓
Retrieved Context
        ↓
Grounded Question Generation / Grounded Answer Evaluation
```

---

# 📂 Project Structure

```text
HireReadyAI/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI routes
│   │   ├── auth.py                  # Login, users, admin auth
│   │   ├── config.py                # Environment configuration
│   │   ├── schemas.py               # API request/response models
│   │   ├── services.py              # Backend service orchestration
│   │   ├── session_store.py         # Saved interview/session data
│   │   └── llm_client.py            # Mistral/OpenAI provider routing
│   │
│   ├── cv/
│   │   ├── cv_parser.py             # CV PDF/text parsing
│   │   ├── cv_skill_extractor.py    # CV skill/project extraction
│   │   └── cv_analyzer.py
│   │
│   ├── job_description/
│   │   ├── job_description_cleaner_mistral_api.py
│   │   └── job_profile_catalog.py
│   │
│   ├── matching/
│   │   ├── skill_matching_engine.py
│   │   └── cv_job_matching_pipeline.py
│   │
│   └── interview/
│       ├── preparation_interview.py
│       ├── adaptive_interview.py
│       ├── interview_assistant.py
│       ├── grounding_index.py       # LangChain + FAISS + HuggingFace RAG
│       ├── grounding_retriever.py
│       ├── code_runner.py
│       ├── expected_point_templates.py
│       └── python_test_case_templates.py
│
├── frontend/
│   ├── react-frontend/              # Current primary React UI
│   │   ├── index.html
│   │   ├── package.json
│   │   └── src/
│   └── streamlit-ui/                # Existing Streamlit prototype UIs kept for now
│       ├── app-cv-job-matching-engine.py
│       ├── app-cv-job-matching-with-new-job.py
│       ├── app-job-skill-extractor-mistral-api.py
│       └── path_setup.py
│
├── data/
│   ├── extracted_skills_mistral-large-latest/
│   │   ├── index.json
│   │   └── *_skills.json
│   ├── job_roles/raw_job_postings/
│   ├── grounding/
│   │   ├── documents/
│   │   ├── faiss_index/
│   │   └── document_registry.json
│   └── taxonomies/
│
├── prompts/
│   ├── job_description_data_extractor.yml
│   └── interview_preparation_question_generator.yml
│
├── tests/
├── requirements.txt
├── Dockerfile.backend
├── docker-compose.yml
├── README.md
├── .env.example
├── .env                         # Local only. Do not commit.
└── .gitignore
```

---

# Installation

## 1. Clone repository

```bash
git clone https://github.com/BarshaLamichhane/Lab4Tech-llm-rag-projects.git
cd Lab4Tech-LLM-RAG-Projects
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
python -m pip install -r HireReadyAI/requirements.txt
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

Create `HireReadyAI/.env`. The initial admin password is used only when
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
cd HireReadyAI
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### Windows

```bash
venv\Scripts\activate
cd HireReadyAI
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

- Admins can create user/admin accounts, run matching and interview practice, configure default scoring weights and skill aliases through the UI, and view their saved sessions.
- Regular users can run matching and interview practice and view only their own saved sessions.
- Users and matching/interview sessions are saved in the SQLite database at `data/app.db` by default.
- Admin settings are saved locally in `data/app_settings.json`; skill aliases update `data/taxonomies/skill_categories.json`.

Authentication uses PBKDF2 password hashes and signed, expiring JWT sessions stored
in HttpOnly cookies. Tokens are never exposed to React or browser local storage.
Users can rotate their password from the Account page; doing so invalidates existing
sessions.

Create additional users from the `HireReadyAI` directory:

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

Useful Swagger endpoints for RAG/vector inspection:

```text
GET  /api/interview/grounding/sources
GET  /api/interview/grounding/chunks
GET  /api/interview/grounding/learning/status
GET  /api/interview/grounding/learning/index
POST /api/interview/grounding/learning/search
```

Some endpoints are admin-only. Login through the React app or call `POST /api/auth/login` from Swagger first.

## Terminal 2: React frontend

The React frontend does not require the Python virtual environment.

```bash
cd HireReadyAI/frontend/react-frontend
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
cd HireReadyAI
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
or 
```bash
lsof -i:8000
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

## Optional legacy frontend

Streamlit prototype interfaces remain in `frontend/streamlit-ui/`, but current UI development is focused on React.

---

# Current Full Prototype Features

The current full prototype supports:

- CV upload
- PDF text extraction
- CV skill, project, and experience extraction
- Job-description extraction using Mistral
- Company context extraction from job descriptions
- Saved role and new-job matching
- Weighted match percentage calculation
- Skill gap analysis by strongly required, required, preferred, tools/platforms, soft skills, and responsibilities
- Score explanation UI
- Personalized learning path generation
- Interview Preparation Mode
- Adaptive Interview Mode
- Coding-question execution for Python
- RAG-grounded question generation and answer evaluation
- Admin settings, user management, and learning dashboards

---

#  Technologies Used

- Python
- FastAPI
- React
- Streamlit
- LangChain
- FAISS
- HuggingFace Sentence Transformers
- Mistral API
- OpenAI-compatible provider option
- PyMuPDF
- Pydantic
- Scikit-learn
- SQLite
- Docker
- Git/GitHub

---

#  AI Governance & Privacy

This prototype follows basic AI governance principles:

- Transparency that users interact with AI
- No unnecessary storage of personal CV data
- Retrieval-based responses to reduce hallucinations
- Focus on verified knowledge sources
- Admin-only access for system learning/debug views
- Environment-based separation between local development and production

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
6. System explains exact matched and missing skills for transparency
7. System generates a personalized learning path
8. User practises focused interview questions
9. System scores answers and adapts the next question
10. User downloads reports or continues practice
```

---

# Interview Modes

## Preparation Mode

Preparation Mode is user-guided and focused on one selected skill at a time.

Users can choose:

- target job role
- one skill from matched or missing skill groups
- difficulty
- interview type
- question count
- LLM-only or grounded-material generation
- optional company context

When company context is enabled, questions can be adapted to the organization, industry domain, or business problem extracted from the job description.

## Adaptive Interview Mode

Adaptive Mode is system-guided.

```text
CV + target role
      ↓
Learner profile
      ↓
Start from highest-priority weak or strong skill
      ↓
Ask question
      ↓
Score answer
      ↓
Update learner profile
      ↓
Choose next skill based on performance
      ↓
Final readiness report and next learning path
```

---

# RAG and Vector Index Management

The project includes a grounded RAG pipeline for verified learning material.

Supported grounding documents:

- PDF
- TXT
- MD
- XML

Vector index lifecycle:

- `use_existing`: load the current FAISS index without rebuilding
- `update`: add new or changed documents and avoid duplicates using file hashes
- `recreate`: rebuild the FAISS index from the files currently in `data/grounding/documents`

The document registry stores:

- embedding model
- embedding dimensions
- splitter name
- chunk size
- chunk overlap
- filename
- file hash
- chunk count
- chunk IDs
- indexing timestamp

The admin-only RAG learning dashboard shows:

- document ingestion
- chunking
- tokenization
- embeddings
- FAISS positions
- LangChain document IDs
- metadata
- retrieval distances
- accepted/rejected chunks
- context that would be sent to the LLM

---

# Version Control

This project uses:

- Git for version control
- GitHub for source-code hosting and project sharing

Do not upload private or generated local files such as:

- `.env`
- API keys
- virtual environments
- `node_modules`
- `data/app.db`
- private CVs
- private uploaded documents
- generated reports
- FAISS indexes containing private material

---



# Future Improvements

Planned enhancements:

- PostgreSQL support for multi-user deployment
- Redis-backed rate limiting and background jobs
- Safer isolated code execution service
- More deterministic Python and SQL coding test templates
- More detailed adaptive learner profile over time
- Richer PDF report generation
- Multilingual support (French/English)
- Real Swiss job market integration
- CV anonymization
- Bias monitoring and fairness reporting

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
