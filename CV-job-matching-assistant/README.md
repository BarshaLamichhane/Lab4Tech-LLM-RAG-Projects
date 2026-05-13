
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
lab4tech-cv-rag-assistant/
│
├── app.py
├── requirements.txt
├── README.md
├── .env
├── .gitignore
│
├── data/
│   ├── job_roles/
│   └── sample_cvs/
│
├── src/
│   ├── config.py
│   ├── cv_parser.py
│   ├── skill_extractor.py
│   ├── job_matcher.py
│   ├── rag_pipeline.py
│   ├── llm_service.py
│   └── utils.py
│
├── vectorstore/
│
└── prompts/
```

---

# Installation

## 1. Clone repository

```bash
git clone https://github.com/BarshaLamichhane/Lab4Tech-cv-rag-assistant.git
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

---

# 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Run Application

```bash
streamlit run app.py
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