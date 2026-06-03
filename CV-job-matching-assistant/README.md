
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

## FastAPI backend

From the repository root:

```bash
cd CV-job-matching-assistant
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Backend health check:

```bash
curl http://127.0.0.1:8000/health
```

## Angular frontend

In a second terminal:

```bash
cd CV-job-matching-assistant/frontend/angular-frontend
npm install
npm start
```

Open:

```text
http://localhost:4200/
```

The Angular UI calls the FastAPI backend at `http://localhost:8000`.

## React frontend

In a second terminal:

```bash
cd CV-job-matching-assistant/frontend/react-frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173/
```

The React UI calls the FastAPI backend at `http://localhost:8000`.

## Existing Streamlit UIs

The Streamlit apps are kept under `frontend/streamlit-ui/` for now:

```bash
streamlit run CV-job-matching-assistant/frontend/streamlit-ui/app-job-skill-extractor-mistral-api.py
streamlit run CV-job-matching-assistant/frontend/streamlit-ui/app-cv-job-matching-engine.py
streamlit run CV-job-matching-assistant/frontend/streamlit-ui/app-cv-job-matching-with-new-job.py
```

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
