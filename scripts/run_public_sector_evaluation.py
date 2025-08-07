#!/usr/bin/env python3
"""
Public Sector Evaluation Runner

This script runs evaluations on the public sector datasets following the framework
described in EVALUATION_DATASET_GUIDE.md
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import re


def load_use_case_dataset(use_case: str) -> Optional[Dict[str, Any]]:
    """Load a use case dataset."""
    dataset_path = Path(f"/Users/wolfgang.ihloff/workspace/tahecho/tests/datasets/use_cases/{use_case}.json")
    
    if not dataset_path.exists():
        print(f"❌ Dataset not found: {dataset_path}")
        return None
    
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return None


def analyze_dataset_quality(dataset: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the quality and readiness of a dataset."""
    test_cases = dataset.get("test_cases", [])
    
    # Count by state
    state_counts = {}
    for case in test_cases:
        state = case.get("metadata", {}).get("state", "unknown")
        state_counts[state] = state_counts.get(state, 0) + 1
    
    # Count by document availability
    doc_availability = {}
    for case in test_cases:
        doc_avail = case.get("metadata", {}).get("use_case", {}).get("document_availability", "unknown")
        doc_availability[doc_avail] = doc_availability.get(doc_avail, 0) + 1
    
    # Count by administrative dimension (for factual questions)
    admin_dimensions = {}
    for case in test_cases:
        admin_dim = case.get("metadata", {}).get("use_case", {}).get("administrative_dimension")
        if admin_dim:
            admin_dimensions[admin_dim] = admin_dimensions.get(admin_dim, 0) + 1
    
    # Count baseline response availability
    has_baseline = sum(1 for case in test_cases 
                      if case.get("metadata", {}).get("quality_metrics", {}).get("has_baseline", False))
    
    # Count validation criteria
    has_validation = sum(1 for case in test_cases 
                        if case.get("metadata", {}).get("quality_metrics", {}).get("has_validation_criteria", False))
    
    total_cases = len(test_cases)
    
    return {
        "total_test_cases": total_cases,
        "state_distribution": state_counts,
        "document_availability": doc_availability,
        "administrative_dimensions": admin_dimensions,
        "baseline_coverage": has_baseline / total_cases if total_cases > 0 else 0,
        "validation_coverage": has_validation / total_cases if total_cases > 0 else 0,
        "ready_for_evaluation": state_counts.get("curated", 0) + state_counts.get("auto_generated", 0),
        "needs_validation": state_counts.get("draft", 0)
    }


def simulate_evaluation_run(test_cases: List[Dict[str, Any]], max_cases: int = 10) -> Dict[str, Any]:
    """
    Simulate an evaluation run on a subset of test cases.
    This is a mock evaluation to demonstrate the framework.
    """
    print(f"\n🔄 Running mock evaluation on {min(len(test_cases), max_cases)} test cases...")
    
    results = []
    
    for i, test_case in enumerate(test_cases[:max_cases]):
        case_id = test_case.get("id", f"case_{i}")
        input_text = test_case.get("input", "")
        expected_contains = test_case.get("expected_output", {}).get("contains", [])
        
        # Mock evaluation logic
        mock_response = f"Mock response for: {input_text[:50]}..."
        
        # Simple mock scoring based on expected criteria
        contains_score = 0.8 if expected_contains else 1.0  # Mock: assume 80% contain expected terms
        language_score = 0.9  # Mock: good German language quality
        completeness_score = 0.7  # Mock: reasonably complete responses
        bias_score = 0.95  # Mock: minimal bias detected
        hallucination_score = 1.0  # Mock: no hallucinations detected
        
        # Calculate weighted score based on evaluation framework
        weighted_score = (
            contains_score * 0.3 +      # Factual accuracy
            hallucination_score * 0.2 + # Hallucination detection  
            language_score * 0.2 +      # Language quality
            bias_score * 0.15 +         # Bias detection
            completeness_score * 0.15   # Completeness
        )
        
        result = {
            "test_case_id": case_id,
            "input": input_text,
            "mock_response": mock_response,
            "expected_contains": expected_contains,
            "scores": {
                "factual_accuracy": contains_score,
                "hallucination_detection": hallucination_score,
                "language_quality": language_score,
                "bias_detection": bias_score,
                "completeness": completeness_score,
                "weighted_overall": weighted_score
            },
            "passed": weighted_score >= 0.75,  # 75% passing threshold
            "critical_failures": [],
            "administrative_dimension": test_case.get("metadata", {}).get("use_case", {}).get("administrative_dimension"),
            "document_availability": test_case.get("metadata", {}).get("use_case", {}).get("document_availability")
        }
        
        results.append(result)
        
        # Show progress
        if (i + 1) % 5 == 0:
            print(f"   Processed {i + 1}/{min(len(test_cases), max_cases)} cases...")
    
    return {
        "total_evaluated": len(results),
        "results": results,
        "summary": calculate_evaluation_summary(results)
    }


def calculate_evaluation_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics from evaluation results."""
    if not results:
        return {}
    
    total_cases = len(results)
    passed_cases = sum(1 for r in results if r["passed"])
    
    # Average scores
    avg_scores = {}
    score_types = ["factual_accuracy", "hallucination_detection", "language_quality", "bias_detection", "completeness", "weighted_overall"]
    
    for score_type in score_types:
        scores = [r["scores"][score_type] for r in results]
        avg_scores[score_type] = sum(scores) / len(scores)
    
    # Performance by administrative dimension
    dimension_performance = {}
    for result in results:
        dim = result.get("administrative_dimension", "unknown")
        if dim not in dimension_performance:
            dimension_performance[dim] = {"total": 0, "passed": 0}
        dimension_performance[dim]["total"] += 1
        if result["passed"]:
            dimension_performance[dim]["passed"] += 1
    
    # Performance by document availability
    doc_performance = {}
    for result in results:
        doc_avail = result.get("document_availability", "unknown")
        if doc_avail not in doc_performance:
            doc_performance[doc_avail] = {"total": 0, "passed": 0}
        doc_performance[doc_avail]["total"] += 1
        if result["passed"]:
            doc_performance[doc_avail]["passed"] += 1
    
    return {
        "overall_pass_rate": passed_cases / total_cases,
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "failed_cases": total_cases - passed_cases,
        "average_scores": avg_scores,
        "performance_by_dimension": {
            dim: stats["passed"] / stats["total"] if stats["total"] > 0 else 0 
            for dim, stats in dimension_performance.items()
        },
        "performance_by_document_availability": {
            doc: stats["passed"] / stats["total"] if stats["total"] > 0 else 0 
            for doc, stats in doc_performance.items()
        }
    }


def print_evaluation_report(use_case: str, analysis: Dict[str, Any], evaluation: Dict[str, Any]):
    """Print a comprehensive evaluation report."""
    print(f"\n📊 EVALUATION REPORT: {use_case.upper()}")
    print("=" * 60)
    
    # Dataset Quality Analysis
    print(f"\n📋 Dataset Quality Analysis:")
    print(f"   Total Test Cases: {analysis['total_test_cases']}")
    print(f"   Ready for Evaluation: {analysis['ready_for_evaluation']}")
    print(f"   Needs Validation: {analysis['needs_validation']}")
    print(f"   Baseline Coverage: {analysis['baseline_coverage']:.1%}")
    print(f"   Validation Coverage: {analysis['validation_coverage']:.1%}")
    
    # Document Distribution
    print(f"\n📄 Document Distribution:")
    for doc_type, count in analysis['document_availability'].items():
        percentage = count / analysis['total_test_cases'] * 100
        print(f"   {doc_type}: {count} ({percentage:.1f}%)")
    
    # Administrative Dimensions (for factual questions)
    if analysis['administrative_dimensions']:
        print(f"\n🏛️ Administrative Dimensions:")
        for dim, count in analysis['administrative_dimensions'].items():
            print(f"   {dim}: {count} questions")
    
    # Evaluation Results
    if evaluation:
        summary = evaluation['summary']
        print(f"\n🎯 Mock Evaluation Results:")
        print(f"   Overall Pass Rate: {summary['overall_pass_rate']:.1%}")
        print(f"   Cases Evaluated: {summary['total_cases']}")
        print(f"   Passed: {summary['passed_cases']}")
        print(f"   Failed: {summary['failed_cases']}")
        
        print(f"\n📈 Average Scores:")
        for score_type, score in summary['average_scores'].items():
            print(f"   {score_type.replace('_', ' ').title()}: {score:.2f}")
        
        if summary.get('performance_by_dimension'):
            print(f"\n🏛️ Performance by Administrative Dimension:")
            for dim, pass_rate in summary['performance_by_dimension'].items():
                print(f"   {dim}: {pass_rate:.1%}")
        
        if summary.get('performance_by_document_availability'):
            print(f"\n📄 Performance by Document Availability:")
            for doc_type, pass_rate in summary['performance_by_document_availability'].items():
                print(f"   {doc_type}: {pass_rate:.1%}")


def run_priority_evaluation():
    """Run evaluation on Priority 1 use cases as recommended in the guide."""
    print("🚀 Public Sector Evaluation Runner")
    print("=" * 60)
    print("Following EVALUATION_DATASET_GUIDE.md recommendations...")
    
    # Priority 1 use cases from the guide
    priority_1_use_cases = [
        ("factual_questions", True),   # Ready for evaluation
        ("reasoning_questions", True), # Ready for evaluation  
        ("summarization", False)       # Needs expansion (only 4 questions)
    ]
    
    evaluation_results = {}
    
    for use_case, ready_for_eval in priority_1_use_cases:
        print(f"\n{'='*20} {use_case.upper()} {'='*20}")
        
        # Load dataset
        dataset = load_use_case_dataset(use_case)
        if not dataset:
            continue
        
        # Analyze dataset quality
        analysis = analyze_dataset_quality(dataset)
        
        # Run evaluation if ready
        evaluation = None
        if ready_for_eval and analysis['ready_for_evaluation'] > 0:
            # Filter to ready test cases
            ready_cases = [
                case for case in dataset['test_cases'] 
                if case.get("metadata", {}).get("state") in ["curated", "auto_generated"]
            ]
            evaluation = simulate_evaluation_run(ready_cases, max_cases=20)
        else:
            print(f"⚠️  {use_case} not ready for evaluation:")
            print(f"   - Needs validation: {analysis['needs_validation']} questions")
            print(f"   - Ready: {analysis['ready_for_evaluation']} questions")
        
        # Print report
        print_evaluation_report(use_case, analysis, evaluation)
        
        evaluation_results[use_case] = {
            "analysis": analysis,
            "evaluation": evaluation,
            "ready_for_production": ready_for_eval and analysis['ready_for_evaluation'] > 10
        }
    
    # Overall summary
    print(f"\n🎯 OVERALL EVALUATION SUMMARY")
    print("=" * 60)
    
    total_ready_cases = sum(result["analysis"]["ready_for_evaluation"] for result in evaluation_results.values())
    total_needs_validation = sum(result["analysis"]["needs_validation"] for result in evaluation_results.values())
    
    print(f"📊 Total across Priority 1 use cases:")
    print(f"   Ready for evaluation: {total_ready_cases} questions")
    print(f"   Needs validation: {total_needs_validation} questions")
    
    production_ready = [uc for uc, result in evaluation_results.items() if result["ready_for_production"]]
    print(f"   Production ready use cases: {', '.join(production_ready) if production_ready else 'None'}")
    
    print(f"\n🔧 Next Steps (from EVALUATION_DATASET_GUIDE.md):")
    print(f"   1. Expert validation of {total_needs_validation} generated questions")
    print(f"   2. Baseline response creation for validated questions")
    print(f"   3. Expand summarization dataset (currently only 4 questions)")
    print(f"   4. Add ~130 more 'without documents' questions for distribution balance")
    print(f"   5. Upload validated datasets to LangSmith platform")
    
    return evaluation_results


def main():
    """Main function."""
    if len(sys.argv) > 1:
        use_case = sys.argv[1]
        dataset = load_use_case_dataset(use_case)
        if dataset:
            analysis = analyze_dataset_quality(dataset)
            evaluation = simulate_evaluation_run(dataset['test_cases'], max_cases=10)
            print_evaluation_report(use_case, analysis, evaluation)
    else:
        run_priority_evaluation()


if __name__ == "__main__":
    main()
