# Public Sector Chat Evaluation Setup

## Overview

This document describes the setup and creation of evaluation datasets for testing chat performance in public sector contexts, specifically using German governmental and administrative documents.

## Created Datasets

### 1. PGA Eval Small Dataset (`pga_eval_small_public_sector.json`)

**Source:** `PGA_Eval_Small_v20250409.xlsx`

**Statistics:**
- **Total Test Cases:** 11
- **Language:** German (DE)
- **Categories:**
  - Factual Questions: 7 test cases
  - Reasoning Questions: 1 test case
  - Summarization: 3 test cases

**File Sets Covered:**
- Deutschlandstipendium (German scholarship program)
- EU AI Act (European AI regulation)

**Sample Questions:**
- "Was ist das Deutschlandstipendium?" (What is the Germany Scholarship?)
- "Wie hoch sind die Stipendienzahlen an der TUM?" (What are the scholarship numbers at TUM?)
- "Fasse Artikel 13 des AI Act kurz zusammen." (Summarize Article 13 of the AI Act briefly.)

### 2. PGA Eval Collections Dataset (`pga_eval_collections_public_sector.json`)

**Source:** `PGA_Eval_Document_Collections_v20250411.xlsx` (first 1000 rows processed, 498 unique entries after deduplication)

**Statistics:**
- **Total Test Cases:** 498
- **Language:** German (DE)
- **Categories:**
  - Factual Question: 498 test cases

**File Sets Covered:**
- BayHIG (Bavarian Higher Education Innovation Law)
- Deutschlandstipendium (German scholarship program)
- Dokumente (Various government documents)
- Hochschulverträge (University contracts)
- IT-Planungsrat (IT Planning Council)
- Kabinettsprotokolle (Cabinet protocols)
- Personalstrategie (Personnel strategy)
- Startups (Startup-related documents)

**Sample Questions:**
- "Wie viele Startups und Gründer:innen werden im 11. Deutschen Startup Monitor repräsentiert?"
- "Welche drei Merkmale zeichnen deutsche Startups laut dem 11. Deutschen Startup Monitor aus?"
- "In welcher Entwicklungsphase befinden sich die meisten befragten Startups laut DSM?"

## Dataset Structure

Each evaluation dataset follows this structure:

```json
{
  "name": "dataset_name",
  "description": "Description of the dataset",
  "version": "1.0.0",
  "created_date": "2024-01-11",
  "source": "original_excel_file.xlsx",
  "domain": "public_sector",
  "language": "de",
  "test_cases": [
    {
      "id": "unique_test_id",
      "input": "Question or prompt for the chat system",
      "expected_output": {
        "contains": ["key", "terms", "that", "should", "appear"],
        "category": "Test category",
        "file_set": "Source document collection",
        "baseline_response": "Reference response from baseline model..."
      },
      "metadata": {
        "test_type": "public_sector_query",
        "category": "Question category",
        "file_set": "Document collection",
        "domain": "public_sector",
        "language": "de"
      }
    }
  ],
  "metadata": {
    "total_test_cases": 498,
    "categories": ["Factual Question"],
    "file_sets": ["BayHIG", "Deutschlandstipendium", ...],
    "category_counts": {"Factual Question": 498}
  },
  "evaluation_criteria": {
    "relevance_weight": 0.3,
    "accuracy_weight": 0.3,
    "completeness_weight": 0.2,
    "language_quality_weight": 0.2,
    "passing_score": 0.75
  }
}
```

## Evaluation Approach

### Key Evaluation Dimensions

1. **Relevance (30%)**: How well does the response address the specific question?
2. **Accuracy (30%)**: Are the facts and figures correct according to the source documents?
3. **Completeness (20%)**: Does the response provide comprehensive information?
4. **Language Quality (20%)**: Is the German language usage appropriate for public sector communication?

### Success Criteria

- **Passing Score:** 75% overall
- **Expected Contains:** Each test case includes key terms that should appear in a good response
- **Baseline Comparison:** Reference responses are provided from a baseline model for comparison

## Usage

### 1. Manual Review
Review the datasets in the `tests/datasets/` directory to understand the scope and nature of questions.

### 2. LangSmith Integration
Upload datasets to LangSmith for systematic evaluation:

```bash
cd /Users/wolfgang.ihloff/workspace/tahecho
python scripts/create_jira_eval_dataset.py --dataset pga_eval_small_public_sector
python scripts/create_jira_eval_dataset.py --dataset pga_eval_collections_public_sector
```

### 3. Local Testing
Use the datasets for local testing and validation of your chat system's responses to public sector queries.

## Files Generated

- `/tests/datasets/pga_eval_small_public_sector.json` - Evaluation dataset (11 test cases)
- `/tests/datasets/pga_eval_small_cleaned.json` - Cleaned source data
- `/tests/datasets/pga_eval_collections_public_sector.json` - Large evaluation dataset (498 test cases)
- `/tests/datasets/pga_eval_collections_cleaned.json` - Cleaned source data
- `/scripts/create_public_sector_eval_dataset.py` - Dataset creation script

## Next Steps

1. **Upload to LangSmith**: Use the existing upload script to push datasets to LangSmith for tracking
2. **Run Evaluations**: Test your chat system against these datasets
3. **Analyze Results**: Focus on areas where performance is weak
4. **Iterate**: Refine your system based on evaluation results
5. **Expand**: Add more test cases for areas not well covered

## Key Insights

- **Domain Coverage**: The datasets cover multiple important public sector domains including education, startup policy, AI regulation, and administrative processes
- **Language**: All content is in German, making this suitable for testing German public sector applications
- **Question Types**: Mix of factual questions, reasoning questions, and summarization tasks
- **Baseline Comparison**: Each test case includes a baseline response for comparison and evaluation

The evaluation setup provides a solid foundation for measuring and improving chat system performance in German public sector contexts.
