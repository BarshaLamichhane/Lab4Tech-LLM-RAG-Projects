# HireReadyAI Job-Description Evaluation

This folder contains small gold datasets used to evaluate job-description skill
extraction.

Job-description samples are stored as structured JSON files in
`evaluation/job_descriptions/`. They mirror the job extraction schema from
`prompts/job_description_data_extractor.yml`, except `verbatim` is not required
for manually entered evaluation data.

Run the automated evaluation from the project root:

```bash
cd HireReadyAI
python -m evaluation.run_job_description_evaluation
```

If your shell does not expose `python`, use:

```bash
python3 -m evaluation.run_job_description_evaluation
```

The script compares saved Mistral-extracted job profile JSON files from
`data/extracted_skills_mistral-large-latest/` against
`expected_job_skills.json` and writes:

- `evaluation/reports/job_description_evaluation_report.json`
- `evaluation/reports/job_description_evaluation_report.md`

The report includes:

- role and company checks
- company-context check
- overall precision, recall, and F1
- category-level precision, recall, and F1 for:
  - `strongly_required_skills`
  - `required_skills`
  - `preferred_skills`
  - `tools_and_platforms`

This evaluation does not test CV extraction or CV-job matching. Those can be
added later after job extraction is stable.
