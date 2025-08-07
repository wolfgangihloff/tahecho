#!/usr/bin/env python3
"""
Merge PGA evaluation datasets into a single comprehensive dataset.

This script combines multiple PGA evaluation datasets while preserving origin,
state, and dimension information for each element through proper tagging.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib


def load_dataset(file_path: str) -> Optional[Dict[str, Any]]:
    """Load a dataset from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def determine_dimensions(test_case: Dict[str, Any], source_info: Dict[str, Any]) -> List[str]:
    """
    Determine the experience dimensions for a test case based on content analysis.
    
    Args:
        test_case: The test case data
        source_info: Information about the source dataset
        
    Returns:
        List of applicable dimensions
    """
    dimensions = []
    
    # Analyze content to determine dimensions
    input_text = test_case.get("input", "").lower()
    category = test_case.get("expected_output", {}).get("category", "").lower()
    file_set = test_case.get("expected_output", {}).get("file_set", "").lower()
    
    # Content-based dimension mapping
    if any(term in input_text for term in ["was ist", "was sind", "definition", "erklär"]):
        dimensions.append("knowledge_retrieval")
    
    if any(term in input_text for term in ["wie hoch", "wie viele", "anzahl", "zahlen", "statistik"]):
        dimensions.append("quantitative_analysis")
    
    if any(term in input_text for term in ["zusammenfassen", "fasse", "kurz", "überblick"]):
        dimensions.append("summarization")
    
    if any(term in input_text for term in ["vergleich", "unterschied", "entwicklung", "trend"]):
        dimensions.append("comparative_analysis")
    
    if any(term in input_text for term in ["warum", "weshalb", "begründung", "ursache"]):
        dimensions.append("reasoning")
    
    # Domain-based dimensions
    if "deutschlandstipendium" in file_set:
        dimensions.append("education_policy")
    
    if "startup" in file_set or "gründer" in input_text:
        dimensions.append("innovation_policy")
    
    if "ai act" in file_set or "künstliche intelligenz" in input_text:
        dimensions.append("technology_regulation")
    
    if any(term in file_set for term in ["kabinett", "protokoll", "verwaltung"]):
        dimensions.append("administrative_processes")
    
    if "hochschul" in file_set or "universität" in input_text:
        dimensions.append("higher_education")
    
    # Complexity-based dimensions
    if len(input_text.split()) < 10:
        dimensions.append("simple_query")
    elif len(input_text.split()) > 20:
        dimensions.append("complex_query")
    else:
        dimensions.append("medium_query")
    
    # Ensure at least one dimension is assigned
    if not dimensions:
        dimensions.append("general_inquiry")
    
    return list(set(dimensions))  # Remove duplicates


def determine_state(test_case: Dict[str, Any], source_info: Dict[str, Any]) -> str:
    """
    Determine the current state/status of a test case.
    
    Args:
        test_case: The test case data
        source_info: Information about the source dataset
        
    Returns:
        State string
    """
    # Check if baseline response exists and is substantial
    baseline_response = test_case.get("expected_output", {}).get("baseline_response", "")
    
    if not baseline_response or len(baseline_response.strip()) < 50:
        return "draft"
    
    # Check if evaluation criteria are well-defined
    contains = test_case.get("expected_output", {}).get("contains", [])
    if not contains or len(contains) == 0:
        return "needs_validation"
    
    # Check source dataset quality
    if source_info.get("source_dataset") == "small":
        return "curated"
    elif source_info.get("source_dataset") == "collections":
        return "auto_generated"
    
    return "validated"


def create_unified_test_case(test_case: Dict[str, Any], source_info: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Create a unified test case with enhanced metadata.
    
    Args:
        test_case: Original test case
        source_info: Source dataset information
        index: Index in the unified dataset
        
    Returns:
        Enhanced test case
    """
    # Generate unique ID based on content
    content_hash = hashlib.md5(
        f"{test_case.get('input', '')}{source_info.get('origin', '')}".encode()
    ).hexdigest()[:8]
    
    unified_case = {
        "id": f"pga_unified_{index:04d}_{content_hash}",
        "input": test_case.get("input", ""),
        "expected_output": {
            **test_case.get("expected_output", {}),
            "confidence_level": "medium"  # Default confidence
        },
        "metadata": {
            **test_case.get("metadata", {}),
            "origin": {
                "source_file": source_info.get("source_file", ""),
                "source_dataset": source_info.get("source_dataset", ""),
                "original_id": test_case.get("id", ""),
                "processing_date": datetime.now().isoformat()
            },
            "dimensions": determine_dimensions(test_case, source_info),
            "state": determine_state(test_case, source_info),
            "tags": create_tags(test_case, source_info),
            "quality_metrics": {
                "input_length": len(test_case.get("input", "")),
                "has_baseline": bool(test_case.get("expected_output", {}).get("baseline_response")),
                "has_validation_criteria": bool(test_case.get("expected_output", {}).get("contains")),
                "domain_specificity": calculate_domain_specificity(test_case)
            }
        }
    }
    
    return unified_case


def create_tags(test_case: Dict[str, Any], source_info: Dict[str, Any]) -> List[str]:
    """Create semantic tags for the test case."""
    tags = []
    
    # Source-based tags
    tags.append(f"source:{source_info.get('source_dataset', 'unknown')}")
    
    # Content-based tags
    file_set = test_case.get("expected_output", {}).get("file_set", "")
    if file_set:
        tags.append(f"domain:{file_set.lower().replace(' ', '_')}")
    
    category = test_case.get("expected_output", {}).get("category", "")
    if category:
        tags.append(f"type:{category.lower().replace(' ', '_')}")
    
    # Language tag
    language = test_case.get("metadata", {}).get("language", "de")
    tags.append(f"lang:{language}")
    
    # Complexity tags
    input_text = test_case.get("input", "")
    if len(input_text.split()) < 8:
        tags.append("complexity:simple")
    elif len(input_text.split()) > 15:
        tags.append("complexity:complex")
    else:
        tags.append("complexity:medium")
    
    return tags


def calculate_domain_specificity(test_case: Dict[str, Any]) -> float:
    """Calculate how domain-specific a test case is (0.0 to 1.0)."""
    input_text = test_case.get("input", "").lower()
    
    # Domain-specific terms
    specific_terms = [
        "deutschlandstipendium", "stipendiat", "baföG", "tum", "universität",
        "startup", "gründer", "finanzierung", "innovation",
        "ai act", "künstliche intelligenz", "algorithmus",
        "kabinett", "verwaltung", "behörde", "ministerium"
    ]
    
    matches = sum(1 for term in specific_terms if term in input_text)
    return min(matches / 3.0, 1.0)  # Normalize to 0-1 scale


def merge_pga_datasets() -> Dict[str, Any]:
    """
    Merge all PGA evaluation datasets into a unified structure.
    
    Returns:
        Unified dataset
    """
    datasets_dir = Path("/Users/wolfgang.ihloff/workspace/tahecho/tests/datasets")
    
    # Define source datasets
    source_datasets = [
        {
            "file": "pga_eval_small_public_sector.json",
            "source_dataset": "small",
            "priority": 1  # Higher priority for curated data
        },
        {
            "file": "pga_eval_collections_public_sector.json", 
            "source_dataset": "collections",
            "priority": 2  # Lower priority for auto-generated data
        }
    ]
    
    unified_cases = []
    source_stats = {}
    
    print("🔄 Merging PGA evaluation datasets...")
    
    for dataset_info in source_datasets:
        file_path = datasets_dir / dataset_info["file"]
        
        if not file_path.exists():
            print(f"⚠️  Dataset not found: {file_path}")
            continue
        
        print(f"\n📊 Processing: {dataset_info['file']}")
        
        dataset = load_dataset(str(file_path))
        if not dataset:
            continue
        
        test_cases = dataset.get("test_cases", [])
        
        source_info = {
            "source_file": dataset.get("source", ""),
            "source_dataset": dataset_info["source_dataset"],
            "priority": dataset_info["priority"]
        }
        
        # Process test cases
        processed_count = 0
        for i, test_case in enumerate(test_cases):
            if test_case.get("input", "").strip():  # Only include non-empty inputs
                unified_case = create_unified_test_case(
                    test_case, 
                    source_info, 
                    len(unified_cases)
                )
                unified_cases.append(unified_case)
                processed_count += 1
        
        source_stats[dataset_info["source_dataset"]] = {
            "total_cases": len(test_cases),
            "processed_cases": processed_count,
            "source_file": dataset.get("source", "")
        }
        
        print(f"  ✅ Processed {processed_count}/{len(test_cases)} test cases")
    
    # Create unified dataset structure
    unified_dataset = {
        "name": "pga_unified_evaluation_dataset",
        "description": "Unified public sector evaluation dataset combining multiple PGA sources with enhanced metadata and dimension tracking",
        "version": "1.0.0",
        "created_date": datetime.now().isoformat(),
        "domain": "public_sector",
        "language": "de",
        "test_cases": unified_cases,
        "metadata": {
            "total_test_cases": len(unified_cases),
            "source_datasets": source_stats,
            "dimensions": get_all_dimensions(unified_cases),
            "states": get_all_states(unified_cases),
            "tags": get_all_tags(unified_cases),
            "quality_distribution": get_quality_distribution(unified_cases)
        },
        "evaluation_criteria": {
            "knowledge_retrieval_weight": 0.25,
            "quantitative_accuracy_weight": 0.25,
            "summarization_quality_weight": 0.20,
            "reasoning_clarity_weight": 0.15,
            "language_appropriateness_weight": 0.15,
            "passing_score": 0.75
        },
        "dimension_definitions": {
            "knowledge_retrieval": "Questions asking for basic facts or definitions",
            "quantitative_analysis": "Questions requiring numerical data or statistics",
            "summarization": "Questions asking for summaries or overviews",
            "comparative_analysis": "Questions comparing different entities or time periods",
            "reasoning": "Questions requiring explanation of causes or reasoning",
            "education_policy": "Questions related to educational policies and programs",
            "innovation_policy": "Questions about startup and innovation policies",
            "technology_regulation": "Questions about AI and technology regulations",
            "administrative_processes": "Questions about government and administrative procedures",
            "higher_education": "Questions specifically about universities and higher education"
        },
        "state_definitions": {
            "draft": "Test case needs more development",
            "needs_validation": "Test case needs validation criteria",
            "auto_generated": "Test case was automatically generated",
            "curated": "Test case was manually curated",
            "validated": "Test case has been reviewed and validated"
        }
    }
    
    print(f"\n✅ Created unified dataset with {len(unified_cases)} test cases")
    return unified_dataset


def get_all_dimensions(test_cases: List[Dict[str, Any]]) -> Dict[str, int]:
    """Get count of all dimensions in the dataset."""
    dimension_counts = {}
    for case in test_cases:
        for dimension in case.get("metadata", {}).get("dimensions", []):
            dimension_counts[dimension] = dimension_counts.get(dimension, 0) + 1
    return dict(sorted(dimension_counts.items(), key=lambda x: x[1], reverse=True))


def get_all_states(test_cases: List[Dict[str, Any]]) -> Dict[str, int]:
    """Get count of all states in the dataset."""
    state_counts = {}
    for case in test_cases:
        state = case.get("metadata", {}).get("state", "unknown")
        state_counts[state] = state_counts.get(state, 0) + 1
    return dict(sorted(state_counts.items(), key=lambda x: x[1], reverse=True))


def get_all_tags(test_cases: List[Dict[str, Any]]) -> Dict[str, int]:
    """Get count of all tags in the dataset."""
    tag_counts = {}
    for case in test_cases:
        for tag in case.get("metadata", {}).get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    return dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True))


def get_quality_distribution(test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get quality metrics distribution."""
    total_cases = len(test_cases)
    has_baseline = sum(1 for case in test_cases 
                      if case.get("metadata", {}).get("quality_metrics", {}).get("has_baseline", False))
    has_validation = sum(1 for case in test_cases 
                        if case.get("metadata", {}).get("quality_metrics", {}).get("has_validation_criteria", False))
    
    avg_input_length = sum(case.get("metadata", {}).get("quality_metrics", {}).get("input_length", 0) 
                          for case in test_cases) / total_cases if total_cases > 0 else 0
    
    avg_domain_specificity = sum(case.get("metadata", {}).get("quality_metrics", {}).get("domain_specificity", 0.0) 
                                for case in test_cases) / total_cases if total_cases > 0 else 0
    
    return {
        "baseline_coverage": has_baseline / total_cases if total_cases > 0 else 0,
        "validation_coverage": has_validation / total_cases if total_cases > 0 else 0,
        "average_input_length": round(avg_input_length, 1),
        "average_domain_specificity": round(avg_domain_specificity, 2)
    }


def main():
    """Main function to merge PGA datasets."""
    print("🏛️  PGA Dataset Merger")
    print("=" * 50)
    
    # Create unified dataset
    unified_dataset = merge_pga_datasets()
    
    # Save unified dataset
    output_path = Path("/Users/wolfgang.ihloff/workspace/tahecho/tests/datasets/pga_unified_public_sector.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(unified_dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved unified dataset: {output_path}")
    
    # Print summary statistics
    print(f"\n📊 Dataset Summary:")
    print(f"  📋 Total test cases: {unified_dataset['metadata']['total_test_cases']}")
    print(f"  🏷️  Dimensions: {len(unified_dataset['metadata']['dimensions'])}")
    print(f"  📊 States: {list(unified_dataset['metadata']['states'].keys())}")
    print(f"  🎯 Quality metrics:")
    quality = unified_dataset['metadata']['quality_distribution']
    print(f"    - Baseline coverage: {quality['baseline_coverage']:.1%}")
    print(f"    - Validation coverage: {quality['validation_coverage']:.1%}")
    print(f"    - Avg input length: {quality['average_input_length']} words")
    print(f"    - Avg domain specificity: {quality['average_domain_specificity']:.2f}")
    
    print(f"\n📈 Top Dimensions:")
    for dim, count in list(unified_dataset['metadata']['dimensions'].items())[:5]:
        print(f"  - {dim}: {count} cases")
    
    print(f"\n🔧 Next steps:")
    print(f"  1. Review the unified dataset structure")
    print(f"  2. Validate dimension assignments")
    print(f"  3. Upload to evaluation platform")
    print(f"  4. Run comprehensive evaluations")


if __name__ == "__main__":
    main()
