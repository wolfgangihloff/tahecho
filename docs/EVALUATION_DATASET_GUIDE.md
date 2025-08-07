# Evaluation Dataset Guide

## Overview

This guide describes the current state of evaluation datasets for testing chat system performance in German public sector contexts, how to use them for evaluation, and how to extend or modify them.

## Current Dataset Structure

### Use Case-Based Organization

All datasets are organized by **use case** in `/tests/datasets/use_cases/`:

```
tests/datasets/use_cases/
├── factual_questions.json          # 716 questions - Priority 1 ⭐
├── summarization.json              # 4 questions - Priority 1 ⚠️ needs expansion
├── reasoning_questions.json        # 13 questions - Priority 1 ✅
├── comparison.json                 # 12 questions - Priority 2 ✅  
├── creative_writing.json           # 7 questions - Priority 2 ✅
├── rewriting.json                  # 1 question - Priority 2 ⚠️ needs expansion
├── use_case_summary.json           # Overview and statistics
└── administrative_validation_checklist.json  # Validation requirements
```

### Source Tracking System

**Fixed Issue:** Source tracking now correctly references actual documents instead of Excel files.

Each test case includes complete source information:
```json
"origin": {
  "excel_source_file": "PGA_Eval_Small_v20250409.xlsx",
  "content_source_documents": ["OJ_L_202401689_DE_TXT.pdf"],
  "content_source_directory": "/tests/test_content/EU AI Act",
  "content_document_count": 1,
  "content_description": "EU AI Act - Official Journal of the European Union",
  "source_type": "content_documents"
}
```

## Primary Dataset: Factual Questions (716 questions)

### Administrative Coverage
- **Original:** 486 questions (mainly Education focus)
- **Added:** 230 questions across 6 new administrative dimensions
- **Total:** 716 questions covering 8 administrative areas

### Administrative Dimensions
1. **Allgemeine Dienste** (87 questions) - General services, IT, personnel
2. **Bildungswesen** (404 questions) - Education, universities, scholarships
3. **Sicherheit & Ordnung** (40 questions) - Police, fire protection, emergency services
4. **Soziale Sicherung** (60 questions) - Social security, family support, job centers
5. **Gesundheit & Umwelt** (40 questions) - Health system, environmental protection
6. **Verkehr** (35 questions) - Transportation, mobility management
7. **Wohnungswesen** (30 questions) - Housing, urban planning
8. **Finanzverwaltung** (25 questions) - Tax administration, budget management

### Document Availability Distribution
- **With Documents:** 67.9% (486 questions)
- **Without Documents:** 32.1% (230 questions)
- **Target:** 50/50 split ⚠️ Need ~130 more "without documents" questions

### Quality Status
- **Ready for Evaluation:** 486 questions (validated)
- **Requires Expert Validation:** 230 questions (generated)
- **Has Baseline Responses:** 486 questions
- **Needs Baseline Responses:** 230 questions

## Source Documents Mapping

### Content Sources (`/tests/test_content/`)
```
EU AI Act/                    → 1 document  (OJ_L_202401689_DE_TXT.pdf)
BayHIG/                      → 4 documents (Innovation law documents)
Deutschlandstipendium/       → 3 documents (Annual reports 2021-2023)
Dokumente/                   → 11 documents (Various government docs)
Hochschulverträge/          → 34 documents (University contracts)
IT-Planungsrat/             → 37 documents (IT Planning Council decisions)
Kabinettsprotokolle/        → 7 documents (Cabinet protocols)
Personalstrategie/          → 4 documents (Personnel strategy docs)
Startups/                   → 2 documents (Startup ecosystem reports)
Nordstream/                 → 6 documents (Nordstream related)
```

## How to Use for Evaluation

### 1. Priority-Based Testing

**Start with Priority 1 use cases:**
```bash
# Factual Questions (ready for evaluation)
tests/datasets/use_cases/factual_questions.json

# Summarization (needs expansion)
tests/datasets/use_cases/summarization.json

# Reasoning Questions (ready for evaluation)  
tests/datasets/use_cases/reasoning_questions.json
```

### 2. Upload to LangSmith

```bash
# Upload individual use cases
python scripts/upload_use_case_datasets.py --dataset factual_questions
python scripts/upload_use_case_datasets.py --dataset reasoning_questions

# Upload all evaluation-ready datasets
python scripts/upload_use_case_datasets.py --ready-only

# Upload all Priority 1 datasets
python scripts/upload_use_case_datasets.py --priority-1

# List available datasets
python scripts/upload_use_case_datasets.py --list
```

### 3. Filter by Administrative Dimension

```bash
# Filter factual questions by administrative area
jq '.test_cases[] | select(.metadata.use_case.administrative_dimension == "Sicherheit_Ordnung")' \
   tests/datasets/use_cases/factual_questions.json

# Filter by document availability
jq '.test_cases[] | select(.metadata.use_case.document_availability == "without_documents")' \
   tests/datasets/use_cases/factual_questions.json
```

### 4. Quality-Based Filtering

```bash
# Ready for evaluation (validated questions)
jq '.test_cases[] | select(.metadata.state == "curated" or .metadata.state == "auto_generated")' \
   tests/datasets/use_cases/factual_questions.json

# Requires validation (generated questions)
jq '.test_cases[] | select(.metadata.state == "draft")' \
   tests/datasets/use_cases/factual_questions.json
```

## How to Extend Datasets

### 1. Adding New Test Cases

**Template for new test case:**
```json
{
  "id": "use_case_NNNN_unique_hash",
  "input": "Your question here",
  "expected_output": {
    "contains": ["key", "terms", "expected"],
    "category": "Test Category",
    "file_set": "Source_Document_Set",
    "baseline_response": "Reference response...",
    "confidence_level": "high|medium|low"
  },
  "metadata": {
    "test_type": "public_sector_query",
    "category": "Test Category",
    "file_set": "Source_Document_Set",
    "domain": "public_sector",
    "language": "de",
    "origin": {
      "source_file": "your_source.pdf",
      "source_dataset": "manual|generated|curated",
      "original_id": "unique_id",
      "processing_date": "2024-XX-XX"
    },
    "dimensions": ["relevant", "dimensions"],
    "state": "draft|curated|validated",
    "tags": ["source:manual", "domain:area", "type:factual", "lang:de"],
    "use_case": {
      "primary": "use_case_name",
      "priority": 1,
      "document_availability": "with_documents|without_documents",
      "data_format": "plain_text|tabular_data|scanned_documents"
    }
  }
}
```

### 2. Adding New Administrative Dimensions

**Modify generation script:**
```python
# Edit: scripts/generate_administrative_factual_questions.py
ADMINISTRATIVE_DIMENSIONS["New_Dimension"] = {
    "current_coverage": 0,
    "target_questions": 30,
    "priority": 1,
    "sub_areas": ["Sub Area 1", "Sub Area 2"],
    "sample_questions": ["Sample question 1", "Sample question 2"]
}
```

### 3. Adding New Use Cases

**Create new use case dataset:**
```bash
# 1. Create JSON structure following existing pattern
cp tests/datasets/use_cases/factual_questions.json tests/datasets/use_cases/new_use_case.json

# 2. Update use case specifications in:
scripts/create_use_case_datasets.py

# 3. Add to USE_CASE_SPECS dictionary
"new_use_case": {
    "priority": 1,
    "document_distribution": {"with_documents": 0.7, "without_documents": 0.3},
    "description": "Description of new use case",
    "sub_dimensions": ["dimension1", "dimension2"]
}
```

## How to Edit Existing Datasets

### 1. Bulk Updates

**Use MultiEdit tool for systematic changes:**
```python
# Example: Update all questions in a category
# Use search_replace or MultiEdit with pattern matching
```

### 2. Quality Improvements

**Validate generated questions:**
```bash
# 1. Review questions needing validation
jq '.test_cases[] | select(.metadata.evaluation_focus.requires_expert_validation == true)' \
   tests/datasets/use_cases/factual_questions.json

# 2. Update state after validation
# Change "state": "draft" → "state": "validated"
# Add baseline responses
# Update quality metrics
```

### 3. Document Distribution Balancing

**Add "without documents" questions:**
```bash
# Current need: ~130 more "without documents" questions for 50/50 balance
# Focus on general administrative knowledge that doesn't require specific documents
```

## Validation Workflow

### 1. Expert Validation Required

**230 generated questions need validation:**
- Sicherheit & Ordnung: 40 questions → Police/safety expert
- Soziale Sicherung: 60 questions → Social services expert  
- Gesundheit & Umwelt: 40 questions → Health administration expert
- Verkehr: 35 questions → Transportation expert
- Wohnungswesen: 30 questions → Housing/urban planning expert
- Finanzverwaltung: 25 questions → Financial administration expert

### 2. Quality Gates

**For each question validate:**
- ✅ Factual accuracy (against official sources)
- ✅ Language appropriateness (administrative German)
- ✅ Bias detection (systematic review)
- ✅ No hallucinations (cross-reference with official docs)
- ✅ Completeness (covers key aspects)

### 3. Baseline Response Creation

**After validation:**
- Domain experts create reference responses
- Cross-reference with official documentation
- Ensure administrative terminology accuracy
- Update confidence levels

## Evaluation Metrics Framework

### Critical Metrics (with Weights)
- **Factual Accuracy:** 30% - Correctness of statements
- **Hallucination Detection:** 20% - Critical failure condition
- **Language Quality:** 20% - German administrative language
- **Bias Detection:** 15% - Systematic bias review
- **Completeness:** 15% - Comprehensive response coverage

### Success Criteria
- **Passing Score:** 75% overall
- **Critical Failures:** Hallucinations, factual errors, inappropriate bias
- **Document Distribution Balance:** Target 50% with/without documents

## Scripts and Tools

### Key Scripts
```bash
# Generate administrative questions
scripts/generate_administrative_factual_questions.py

# Integrate new questions into existing datasets
scripts/integrate_administrative_questions.py

# Fix source tracking to reference actual documents
scripts/fix_source_tracking.py

# Create use case specific datasets
scripts/create_use_case_datasets.py

# Upload to LangSmith
scripts/create_jira_eval_dataset.py
```

### Useful Commands
```bash
# Count questions by administrative dimension
grep -c "administrative_dimension" tests/datasets/use_cases/factual_questions.json

# Check document distribution
grep -c "without_documents" tests/datasets/use_cases/factual_questions.json

# Find questions needing validation
grep -c '"state": "draft"' tests/datasets/use_cases/factual_questions.json
```

## Next Steps Priority

### Immediate (Priority 1)
1. **Expert validation** of 230 generated administrative questions
2. **Baseline response creation** for validated questions  
3. **Add ~130 "without documents" questions** for distribution balance
4. **Expand summarization dataset** (currently only 4 questions)

### Short-term (Priority 2)  
1. **Upload validated datasets** to evaluation platform
2. **Implement bias detection pipeline**
3. **Create missing use cases** (translation, content expansion)
4. **Panel review process** for quality assurance

### Medium-term
1. **Systematic benchmarking** against existing German LLM evaluations
2. **Integration with evaluation platform**
3. **Automated quality monitoring**
4. **Continuous dataset improvement**

## Quality Assurance

### Current Status
- **Total Questions:** 753 across all use cases
- **Ready for Evaluation:** 486 questions (64%)
- **Needs Validation:** 230 questions (31%)
- **Administrative Coverage:** 8 dimensions
- **Source Tracking:** Fixed and accurate

### Quality Metrics
- **Baseline Coverage:** 64% (target: 100%)
- **Validation Coverage:** 68% (target: 100%)
- **Document Distribution:** 68%/32% (target: 50%/50%)
- **Administrative Balance:** Good coverage across 8 areas

This dataset structure provides a solid foundation for systematic evaluation of chat system performance in German public sector contexts, with clear pathways for extension and improvement.
