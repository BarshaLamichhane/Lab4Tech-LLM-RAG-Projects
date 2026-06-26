# HireReadyAI Job-Description Extraction Evaluation

Generated at: `2026-06-26T10:44:59.676541+00:00`

## Summary

- Cases: `3`
- Evaluated saved profiles: `2`
- Missing saved profiles: `1`
- Average overall F1: `0.3933`
- Average category F1: `0.2803`

## Cases

### ai_engineer_role

- Profile file: `data/extracted_skills_mistral-large-latest/ai_engineer_unknown_company_2026.json`
- Profile match level: `explicit_file`
- Role match: `True`
- Company match: `False`
- Company context contains expected terms: `False`
- Overall F1: `0.4138`

`strongly_required_skills` F1: `0.5714`
- Missing expected: API integration
- Unexpected actual: LLM-based agents, Agent frameworks

`required_skills` F1: `0.0`
- Missing expected: FastAPI, LangChain, Vector databases, Docker, SQL
- Unexpected actual: Large language models (LLMs), Retrieval-augmented generation (RAG), AI workflow orchestration, API integration (REST / GraphQL)

`preferred_skills` F1: `0.0`
- Missing expected: Mistral API, React, pytest

`tools_and_platforms` F1: `0.1818`
- Missing expected: FAISS, Git
- Unexpected actual: LangChain, LangGraph, CrewAI, AWS Bedrock, Microsoft Foundry, Kubernetes, Vector databases

### ai_research_scientist_role

- Profile file: `data/extracted_skills_mistral-large-latest/ai_research_scientist_giotto_ai_2026.json`
- Profile match level: `explicit_file`
- Role match: `True`
- Company match: `True`
- Company context contains expected terms: `True`
- Overall F1: `0.3729`

`strongly_required_skills` F1: `0.75`
- Unexpected actual: Hugging Face ecosystem, LLM training, fine-tuning, evaluation, or inference

`required_skills` F1: `0.3077`
- Missing expected: Hugging Face Transformers, Model evaluation, Experiment tracking
- Unexpected actual: Model training and deployment, Experiment design and hypothesis testing, Mathematical foundations in linear algebra, probability, statistics, and optimization, Research paper implementation and prototyping, Training dynamics and optimization, Evaluation methodology and benchmarking

`preferred_skills` F1: `0.25`
- Missing expected: LoRA, PEFT
- Unexpected actual: LLM reasoning and planning, Multimodal learning, Program synthesis or structured prediction, Synthetic data generation, Model merging, distillation, and compression, Reinforcement learning or preference optimization, Evaluation of reasoning and generalization, Mechanistic interpretability or model analysis, Agentic systems and tool-using models, Low-level inference optimization

`tools_and_platforms` F1: `0.1818`
- Missing expected: Git
- Unexpected actual: Hugging Face Transformers, Hugging Face Datasets, CUDA-aware GPU training, Weights & Biases, GitLab CI, GCP / cloud GPU infrastructure, Ray, PyTorch Distributed, FSDP, DeepSpeed, Accelerate, PEFT / LoRA / QLoRA, vLLM, pytest, Triton, GCS, Vector databases

### data_engineer_role

Saved Mistral profile: `not found`
