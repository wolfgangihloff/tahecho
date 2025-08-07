#!/usr/bin/env python3
"""
Create structured evaluation datasets based on specific use cases.

This script reorganizes the PGA data into separate files per use case,
following the detailed specifications for sub-dimensions, document availability,
and evaluation priorities.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
from collections import defaultdict


# Use case specifications from requirements
USE_CASE_SPECS = {
    "factual_questions": {
        "priority": 1,
        "target_questions_per_knowledge_area": 10,
        "document_distribution": {"with_documents": 0.5, "without_documents": 0.5},
        "data_formats": {
            "plain_text": 0.7,
            "tabular_data": 0.1,
            "scanned_documents": 0.1,
            "chart_data_images": 0.1
        },
        "description": "Direct factual questions requiring specific information retrieval",
        "sub_dimensions": ["knowledge_areas", "documents", "data_formats"]
    },
    "summarization": {
        "priority": 1,
        "document_distribution": {"with_documents": 0.8, "without_documents": 0.2},
        "content_types": {
            "single_topic": 0.9,
            "mixed_topics": 0.1
        },
        "description": "Document summarization tasks with varying complexity",
        "sub_dimensions": ["documents", "content"]
    },
    "rewriting": {
        "priority": 2,
        "document_distribution": {"with_documents": 1.0, "without_documents": 0.0},
        "target_groups": [
            "boss", "non_legal_coworkers", "citizen", "general_public"
        ],
        "special_requirements": ["einfache_sprache", "gender_mainstreaming"],
        "description": "Rewriting content for different target audiences",
        "sub_dimensions": ["documents", "content", "target_groups"]
    },
    "creative_writing": {
        "priority": 2,
        "target_questions_per_knowledge_area": 10,
        "description": "Creative content generation for public sector contexts",
        "sub_dimensions": ["knowledge_areas", "improvements", "content"]
    },
    "conceptual_questions": {
        "priority": 2,
        "description": "Questions requiring understanding of concepts and relationships",
        "sub_dimensions": ["reasoning", "comparison"]
    },
    "comparison": {
        "priority": 2,
        "document_distribution": {"with_documents": 0.8, "without_documents": 0.2},
        "description": "Comparative analysis tasks",
        "sub_dimensions": ["documents", "reasoning"]
    },
    "reasoning_questions": {
        "priority": 1,
        "description": "Questions requiring logical reasoning and explanation",
        "sub_dimensions": ["reasoning", "explanation"]
    },
    "translation": {
        "priority": 2,
        "languages": ["german", "english", "turkish", "ukrainian", "arabic", "spanish", "italian", "french"],
        "document_distribution": {"with_documents": 0.7, "without_documents": 0.3},
        "modes": ["target_language", "source_language", "interleaved"],
        "description": "Multi-language translation tasks",
        "sub_dimensions": ["languages", "documents", "modes"]
    },
    "content_expansion": {
        "priority": 3,
        "description": "Expanding existing content with additional information",
        "sub_dimensions": ["expansion_type", "source_integration"]
    }
}

# Evaluation metrics framework
EVALUATION_METRICS = {
    "factual_accuracy": {
        "weight": 0.3,
        "description": "Correctness of factual statements",
        "critical_failures": ["fachlich_falsche_aussagen", "konzeptuelle_fehler"]
    },
    "language_quality": {
        "weight": 0.2,
        "description": "German language proficiency and appropriateness",
        "issues": ["word_repetition_loops", "inappropriate_emojis", "html_output"]
    },
    "bias_detection": {
        "weight": 0.15,
        "description": "Detection of various bias types",
        "types": ["gender_bias", "cultural_bias", "political_bias"]
    },
    "hallucination_detection": {
        "weight": 0.2,
        "description": "Detection of fabricated information",
        "severity": "critical",  # Can lead to 0 score due to credibility loss
        "note": "Hallucinations remove credibility and may result in complete failure"
    },
    "completeness": {
        "weight": 0.15,
        "description": "How completely the response addresses the question"
    }
}

# Technical limitations to track
TECHNICAL_LIMITATIONS = {
    "outscoped": {
        "turn_count_followup": "Too complex for eval currently",
        "non_pdf_word_formats": "Not supported",
        "file_size_over_100mb": "Not supported",
        "sources_over_10": "Not supported",
        "pages_over_500": "Not supported",
        "non_general_services_domains": "Target users limitation",
        "metadata_usage": "Not supported",
        "relevance_noisiness": "Too complex for eval",
        "minority_languages": "Less than 4% population - too complex"
    }
}


def load_unified_dataset() -> Optional[Dict[str, Any]]:
    """Load the unified PGA dataset."""
    dataset_path = Path("/Users/wolfgang.ihloff/workspace/tahecho/tests/datasets/pga_unified_public_sector.json")
    
    if not dataset_path.exists():
        print(f"❌ Unified dataset not found: {dataset_path}")
        return None
    
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading unified dataset: {e}")
        return None


def classify_test_case_by_use_case(test_case: Dict[str, Any]) -> List[str]:
    """
    Classify a test case into one or more use cases based on content analysis.
    
    Args:
        test_case: The test case to classify
        
    Returns:
        List of applicable use case names
    """
    input_text = test_case.get("input", "").lower()
    category = test_case.get("expected_output", {}).get("category", "").lower()
    dimensions = test_case.get("metadata", {}).get("dimensions", [])
    
    applicable_use_cases = []
    
    # Factual Questions
    if any(dim in dimensions for dim in ["knowledge_retrieval", "quantitative_analysis"]) or \
       any(term in input_text for term in ["was ist", "wie hoch", "wie viele", "wer", "wo", "wann"]):
        applicable_use_cases.append("factual_questions")
    
    # Summarization
    if "summarization" in dimensions or \
       any(term in input_text for term in ["fasse zusammen", "überblick", "zusammenfassung", "kurz"]):
        applicable_use_cases.append("summarization")
    
    # Reasoning Questions
    if "reasoning" in dimensions or \
       any(term in input_text for term in ["warum", "weshalb", "begründung", "erklär", "wie funktioniert"]):
        applicable_use_cases.append("reasoning_questions")
    
    # Comparison
    if "comparative_analysis" in dimensions or \
       any(term in input_text for term in ["vergleich", "unterschied", "im verhältnis", "gegenüber"]):
        applicable_use_cases.append("comparison")
    
    # Translation (detect if multiple languages or translation keywords)
    if any(term in input_text for term in ["übersetze", "translate", "auf englisch", "in turkish"]):
        applicable_use_cases.append("translation")
    
    # Creative Writing (detect creative/generative tasks)
    if any(term in input_text for term in ["erstelle", "schreibe", "entwickle", "entwirf"]):
        applicable_use_cases.append("creative_writing")
    
    # Rewriting (detect rewriting/reformulation tasks)
    if any(term in input_text for term in ["umschreibe", "formuliere um", "vereinfache", "für bürger"]):
        applicable_use_cases.append("rewriting")
    
    # Default to factual_questions if no other classification
    if not applicable_use_cases:
        applicable_use_cases.append("factual_questions")
    
    return applicable_use_cases


def determine_document_availability(test_case: Dict[str, Any]) -> str:
    """Determine if test case has document context."""
    file_set = test_case.get("expected_output", {}).get("file_set", "")
    baseline_response = test_case.get("expected_output", {}).get("baseline_response", "")
    
    # If there's a specific file set mentioned, assume documents are available
    if file_set and file_set.strip():
        return "with_documents"
    
    # Check if baseline response mentions specific documents or sources
    if any(term in baseline_response.lower() for term in ["quelle:", "dokument", "bericht", "studie", "gesetz"]):
        return "with_documents"
    
    return "without_documents"


def determine_data_format(test_case: Dict[str, Any]) -> str:
    """Determine the primary data format for the test case."""
    input_text = test_case.get("input", "").lower()
    baseline_response = test_case.get("expected_output", {}).get("baseline_response", "").lower()
    
    # Check for tabular data indicators
    if any(term in input_text + baseline_response for term in ["tabelle", "statistik", "zahlen", "prozent", "%"]):
        if any(dim in test_case.get("metadata", {}).get("dimensions", []) for dim in ["quantitative_analysis"]):
            return "tabular_data"
    
    # Check for chart/image indicators
    if any(term in input_text + baseline_response for term in ["diagramm", "grafik", "chart", "abbildung"]):
        return "chart_data_images"
    
    # Check for scanned document indicators
    if any(term in input_text + baseline_response for term in ["scan", "pdf", "dokument"]):
        return "scanned_documents"
    
    # Default to plain text
    return "plain_text"


def create_use_case_dataset(use_case_name: str, test_cases: List[Dict[str, Any]], specs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a dataset for a specific use case.
    
    Args:
        use_case_name: Name of the use case
        test_cases: List of test cases for this use case
        specs: Use case specifications
        
    Returns:
        Use case dataset structure
    """
    # Add enhanced metadata to each test case
    enhanced_cases = []
    for i, case in enumerate(test_cases):
        enhanced_case = {
            **case,
            "id": f"{use_case_name}_{i:04d}_{case['id'].split('_')[-1]}",
            "metadata": {
                **case.get("metadata", {}),
                "use_case": {
                    "primary": use_case_name,
                    "priority": specs.get("priority", 2),
                    "document_availability": determine_document_availability(case),
                    "data_format": determine_data_format(case),
                    "sub_dimensions": specs.get("sub_dimensions", [])
                },
                "evaluation_focus": {
                    "critical_metrics": ["factual_accuracy", "hallucination_detection"],
                    "quality_metrics": ["language_quality", "completeness"],
                    "bias_check": True,
                    "technical_limitations": TECHNICAL_LIMITATIONS
                }
            }
        }
        enhanced_cases.append(enhanced_case)
    
    # Calculate distribution statistics
    doc_distribution = {}
    format_distribution = {}
    
    for case in enhanced_cases:
        doc_avail = case["metadata"]["use_case"]["document_availability"]
        doc_distribution[doc_avail] = doc_distribution.get(doc_avail, 0) + 1
        
        data_format = case["metadata"]["use_case"]["data_format"]
        format_distribution[data_format] = format_distribution.get(data_format, 0) + 1
    
    total_cases = len(enhanced_cases)
    
    dataset = {
        "name": f"pga_{use_case_name}_evaluation",
        "description": f"Evaluation dataset for {use_case_name}: {specs.get('description', '')}",
        "version": "1.0.0",
        "created_date": datetime.now().isoformat(),
        "use_case": use_case_name,
        "specifications": specs,
        "test_cases": enhanced_cases,
        "statistics": {
            "total_test_cases": total_cases,
            "priority": specs.get("priority", 2),
            "document_distribution": {k: v/total_cases for k, v in doc_distribution.items()},
            "data_format_distribution": {k: v/total_cases for k, v in format_distribution.items()},
            "target_distribution": specs.get("document_distribution", {}),
            "compliance_check": {
                "document_distribution_met": check_distribution_compliance(
                    doc_distribution, specs.get("document_distribution", {}), total_cases
                ),
                "format_distribution_met": check_distribution_compliance(
                    format_distribution, specs.get("data_formats", {}), total_cases
                )
            }
        },
        "evaluation_framework": {
            "metrics": EVALUATION_METRICS,
            "passing_score": 0.75,
            "critical_failure_conditions": [
                "hallucinations_detected",
                "factual_errors_in_primary_domain",
                "inappropriate_bias_detected"
            ]
        }
    }
    
    return dataset


def check_distribution_compliance(actual: Dict[str, int], target: Dict[str, float], total: int) -> Dict[str, Any]:
    """Check if actual distribution meets target distribution."""
    compliance = {}
    
    for key, target_ratio in target.items():
        actual_count = actual.get(key, 0)
        actual_ratio = actual_count / total if total > 0 else 0
        variance = abs(actual_ratio - target_ratio)
        
        compliance[key] = {
            "target": target_ratio,
            "actual": actual_ratio,
            "variance": variance,
            "compliant": variance <= 0.2  # Allow 20% variance
        }
    
    return compliance


def main():
    """Main function to create use case datasets."""
    print("🎯 Use Case Dataset Creator")
    print("=" * 60)
    
    # Load unified dataset
    unified_data = load_unified_dataset()
    if not unified_data:
        return
    
    test_cases = unified_data.get("test_cases", [])
    print(f"📊 Loaded {len(test_cases)} test cases from unified dataset")
    
    # Classify test cases by use case
    use_case_assignments = defaultdict(list)
    
    for test_case in test_cases:
        use_cases = classify_test_case_by_use_case(test_case)
        for use_case in use_cases:
            if use_case in USE_CASE_SPECS:
                use_case_assignments[use_case].append(test_case)
    
    print(f"\n📋 Use Case Assignments:")
    for use_case, cases in use_case_assignments.items():
        priority = USE_CASE_SPECS[use_case].get("priority", 2)
        print(f"  - {use_case}: {len(cases)} cases (Priority {priority})")
    
    # Create output directory
    output_dir = Path("/Users/wolfgang.ihloff/workspace/tahecho/tests/datasets/use_cases")
    output_dir.mkdir(exist_ok=True)
    
    # Create datasets for each use case
    created_datasets = []
    
    for use_case_name, specs in USE_CASE_SPECS.items():
        cases = use_case_assignments.get(use_case_name, [])
        
        if not cases:
            print(f"\n⚠️  No test cases found for {use_case_name}")
            continue
        
        print(f"\n🔧 Creating dataset for {use_case_name}...")
        
        dataset = create_use_case_dataset(use_case_name, cases, specs)
        
        # Save dataset
        output_path = output_dir / f"{use_case_name}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        created_datasets.append({
            "use_case": use_case_name,
            "file": str(output_path),
            "test_cases": len(cases),
            "priority": specs.get("priority", 2)
        })
        
        print(f"  ✅ Created {output_path}")
        
        # Print compliance summary
        stats = dataset["statistics"]
        compliance = stats["compliance_check"]
        
        print(f"    📊 Document distribution compliance:")
        for key, check in compliance.get("document_distribution_met", {}).items():
            status = "✅" if check["compliant"] else "⚠️"
            print(f"      {status} {key}: {check['actual']:.1%} (target: {check['target']:.1%})")
    
    # Create summary report
    summary_path = output_dir / "use_case_summary.json"
    summary = {
        "created_date": datetime.now().isoformat(),
        "total_use_cases": len(created_datasets),
        "datasets": created_datasets,
        "evaluation_framework": EVALUATION_METRICS,
        "technical_limitations": TECHNICAL_LIMITATIONS,
        "next_steps": [
            "Review distribution compliance for priority 1 use cases",
            "Add more test cases for under-represented categories",
            "Implement bias detection evaluation pipeline",
            "Set up hallucination detection with critical failure handling",
            "Create panel review process for complex cases"
        ]
    }
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Created summary: {summary_path}")
    
    # Print final summary
    print(f"\n🎯 Use Case Datasets Created:")
    priority_1_cases = sum(d["test_cases"] for d in created_datasets if d["priority"] == 1)
    print(f"  📋 Total datasets: {len(created_datasets)}")
    print(f"  🔥 Priority 1 test cases: {priority_1_cases}")
    print(f"  📁 Output directory: {output_dir}")
    
    print(f"\n🔧 Next Steps:")
    print(f"  1. Review priority 1 use cases: factual_questions, summarization, reasoning_questions")
    print(f"  2. Check distribution compliance and add missing test cases")
    print(f"  3. Implement evaluation pipeline with bias detection")
    print(f"  4. Set up critical failure detection for hallucinations")
    print(f"  5. Create panel review process for quality assessment")


if __name__ == "__main__":
    main()
