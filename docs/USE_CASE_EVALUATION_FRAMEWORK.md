# Use Case-Based Evaluation Framework

## Overview

Successfully restructured the PGA evaluation data into **separate files per use case** following your detailed specifications. This approach is **much better** than the single unified file because it enables:

1. **Targeted evaluation** per use case
2. **Specific distribution requirements** tracking
3. **Priority-based testing** (Prio 1 vs Prio 2)
4. **Use case-specific metrics** and bias detection
5. **Systematic gap identification** and filling

## Created Use Case Datasets

### Priority 1 Use Cases (Current User Base Focus)

| Use Case | Test Cases | Compliance Status | Target | Actual |
|----------|------------|-------------------|---------|---------|
| **factual_questions** | 486 | ⚠️ Document distribution | 50%/50% with/without docs | 100%/0% |
| **summarization** | 4 | ✅ Document distribution | 80%/20% with/without docs | 100%/0% |
| **reasoning_questions** | 13 | ✅ Small dataset | N/A | Sufficient for pilot |

### Priority 2 Use Cases (Future Development)

| Use Case | Test Cases | Status | Notes |
|----------|------------|---------|-------|
| **comparison** | 12 | ✅ Ready | Good foundation |
| **creative_writing** | 7 | ✅ Ready | Needs expansion |
| **rewriting** | 1 | ⚠️ Insufficient | Need more cases |

### Missing Use Cases (Need Creation)

- **translation** (0 cases) - Multi-language support
- **content_expansion** (0 cases) - Content enhancement
- **conceptual_questions** (0 cases) - Conceptual understanding

## Key Findings & Issues

### 1. Document Distribution Problem
**Critical Issue:** Almost all current test cases assume document availability (100% with documents), but specifications require:
- **Factual Questions:** 50% with documents, 50% without
- **Summarization:** 80% with documents, 20% without

**Impact:** We can't properly test the system's ability to answer questions without document context.

### 2. Data Format Distribution
Current test cases are heavily skewed toward plain text:
- **Plain text:** ~95% (target: 70%)
- **Tabular data:** ~5% (target: 10%)
- **Scanned documents:** 0% (target: 10%)
- **Chart data/images:** 0% (target: 10%)

### 3. Insufficient Test Cases for Key Areas
- **Summarization:** Only 4 cases (need ~50+ for robust evaluation)
- **Rewriting:** Only 1 case (need target group variations)
- **Translation:** 0 cases (need multi-language coverage)

## Enhanced Evaluation Framework

### Critical Metrics (with Bias Detection)
```json
{
  "factual_accuracy": {
    "weight": 0.3,
    "critical_failures": ["fachlich_falsche_aussagen", "konzeptuelle_fehler"]
  },
  "hallucination_detection": {
    "weight": 0.2,
    "severity": "critical",
    "note": "Can lead to 0 score - removes credibility"
  },
  "language_quality": {
    "weight": 0.2,
    "issues": ["word_repetition_loops", "inappropriate_emojis", "html_output"]
  },
  "bias_detection": {
    "weight": 0.15,
    "types": ["gender_bias", "cultural_bias", "political_bias"]
  },
  "completeness": {
    "weight": 0.15
  }
}
```

### Technical Limitations Tracking
```json
{
  "outscoped": {
    "turn_count_followup": "Too complex for eval currently",
    "file_size_over_100mb": "Not supported",
    "sources_over_10": "Not supported",
    "pages_over_500": "Not supported",
    "non_general_services_domains": "Target users limitation",
    "metadata_usage": "Not supported",
    "relevance_noisiness": "Too complex for eval",
    "minority_languages": "Less than 4% population"
  }
}
```

## Sample Enhanced Test Case Structure

```json
{
  "id": "factual_questions_0000_b99ccbb5",
  "input": "Was ist das Deutschlandstipendium?",
  "expected_output": {
    "contains": ["300", "Stipendienprogramm-Gesetz (StipG)"],
    "confidence_level": "medium"
  },
  "metadata": {
    "origin": {
      "source_file": "PGA_Eval_Small_v20250409.xlsx",
      "source_dataset": "small",
      "processing_date": "2025-08-06T19:20:18.318613"
    },
    "use_case": {
      "primary": "factual_questions",
      "priority": 1,
      "document_availability": "with_documents",
      "data_format": "plain_text",
      "sub_dimensions": ["knowledge_areas", "documents", "data_formats"]
    },
    "evaluation_focus": {
      "critical_metrics": ["factual_accuracy", "hallucination_detection"],
      "quality_metrics": ["language_quality", "completeness"],
      "bias_check": true
    }
  }
}
```

## Recommendations

### Immediate Actions (Priority 1)

1. **Fix Document Distribution for Factual Questions**
   - Create ~240 factual questions WITHOUT document context
   - Test system's knowledge vs. document-dependent responses

2. **Expand Summarization Dataset**
   - Add ~46 more summarization test cases
   - Include mixed topic scenarios (10% target)

3. **Create Missing Data Formats**
   - Add tabular data questions (statistical analysis)
   - Add scanned document scenarios
   - Add chart/graph interpretation tasks

### Medium-term Actions (Priority 2)

4. **Build Missing Use Cases**
   - **Translation:** Multi-language test cases (DE↔EN, DE↔TR, etc.)
   - **Content Expansion:** Content enhancement scenarios
   - **Conceptual Questions:** Complex concept understanding

5. **Implement Evaluation Pipeline**
   - Automated bias detection
   - Hallucination detection with critical failure handling
   - Panel review process for edge cases

### Quality Assurance Framework

6. **Panel Review Process**
   - **Factual accuracy:** Subject matter expert review
   - **Conceptual correctness:** Domain expert validation
   - **Language quality:** German language expert review
   - **Bias detection:** Diversity & inclusion expert review

7. **Systematic Benchmarking**
   - Compare against existing German benchmarks:
     - `deutsche-telekom/Ger-RAG-eval`
     - `bjoernpl/GermanBenchmark`
     - `Eisvogel` evaluation framework
   - Position against Claude, ChatGPT, LLMoin, F13

## File Structure Benefits

### ✅ **Why Separate Files Are Better:**

1. **Targeted Testing:** Focus on specific capabilities
2. **Clear Requirements:** Each use case has specific distribution targets
3. **Priority Management:** Test Priority 1 use cases first
4. **Quality Control:** Track compliance per use case
5. **Scalability:** Easy to add new use cases
6. **Debugging:** Isolate issues to specific capabilities
7. **Team Coordination:** Different teams can own different use cases

### ✅ **vs. Single Unified File:**

- **Single File:** Good for overview, poor for systematic evaluation
- **Separate Files:** Excellent for systematic, targeted evaluation
- **Hybrid Approach:** Keep summary for overview, use separate files for evaluation

## Next Steps Integration

1. **Upload Priority 1 Use Cases** to LangSmith/evaluation platform
2. **Implement missing test case generation** for document distribution compliance
3. **Set up automated evaluation pipeline** with bias/hallucination detection
4. **Create panel review workflow** for quality assurance
5. **Benchmark against existing German LLM evaluations**
6. **Connect to Sharepoint dataset collection** for expansion

## Files Created

```
tests/datasets/use_cases/
├── factual_questions.json      # 486 cases, Priority 1 ⚠️ needs doc distribution fix
├── summarization.json          # 4 cases, Priority 1 ⚠️ needs expansion
├── reasoning_questions.json    # 13 cases, Priority 1 ✅
├── comparison.json            # 12 cases, Priority 2 ✅
├── creative_writing.json      # 7 cases, Priority 2 ✅
├── rewriting.json            # 1 case, Priority 2 ⚠️ needs expansion
└── use_case_summary.json     # Overview and statistics
```

This structured approach aligns perfectly with your evaluation requirements and provides a solid foundation for systematic testing with proper bias detection, hallucination handling, and quality metrics that model real user experience in the public sector context.
