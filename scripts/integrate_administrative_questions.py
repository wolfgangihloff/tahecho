#!/usr/bin/env python3
"""
Integrate generated administrative questions into the main factual questions dataset.

This script merges the expansion dataset with the existing factual questions
while preserving all existing data and maintaining proper tracking.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


def load_dataset(file_path: str) -> Dict[str, Any]:
    """Load a dataset from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        raise


def integrate_administrative_questions():
    """
    Integrate generated administrative questions into the main factual questions dataset.
    """
    print("🔗 Integrating Administrative Questions")
    print("=" * 50)
    
    # Load existing factual questions dataset
    factual_questions_path = Path("/Users/wolfgang.ihloff/workspace/tahecho/tests/datasets/use_cases/factual_questions.json")
    expansion_path = Path("/Users/wolfgang.ihloff/workspace/tahecho/tests/datasets/use_cases/factual_questions_administrative_expansion.json")
    
    if not factual_questions_path.exists():
        print(f"❌ Main dataset not found: {factual_questions_path}")
        return
    
    if not expansion_path.exists():
        print(f"❌ Expansion dataset not found: {expansion_path}")
        return
    
    print(f"📊 Loading existing dataset: {factual_questions_path.name}")
    existing_dataset = load_dataset(str(factual_questions_path))
    existing_test_cases = existing_dataset.get("test_cases", [])
    
    print(f"📊 Loading expansion dataset: {expansion_path.name}")
    expansion_dataset = load_dataset(str(expansion_path))
    new_test_cases = expansion_dataset.get("test_cases", [])
    
    print(f"   - Existing questions: {len(existing_test_cases)}")
    print(f"   - New questions: {len(new_test_cases)}")
    
    # Combine test cases
    all_test_cases = existing_test_cases + new_test_cases
    
    # Update dataset metadata
    updated_dataset = {
        **existing_dataset,
        "test_cases": all_test_cases,
        "version": "1.1.0",  # Increment version
        "last_updated": datetime.now().isoformat(),
        "expansion_history": {
            "v1.1.0": {
                "date": datetime.now().isoformat(),
                "added_questions": len(new_test_cases),
                "source": "administrative_expansion",
                "administrative_dimensions_added": [
                    "Sicherheit_Ordnung",
                    "Soziale_Sicherung", 
                    "Gesundheit_Umwelt",
                    "Verkehr_Nachrichtenwesen",
                    "Wohnungswesen_Stadtebau",
                    "Finanzverwaltung"
                ]
            }
        }
    }
    
    # Update statistics
    total_cases = len(all_test_cases)
    
    # Count document distribution
    with_docs = sum(1 for case in all_test_cases 
                   if case.get("metadata", {}).get("use_case", {}).get("document_availability") == "with_documents")
    without_docs = total_cases - with_docs
    
    # Count by state
    state_counts = {}
    for case in all_test_cases:
        state = case.get("metadata", {}).get("state", "unknown")
        state_counts[state] = state_counts.get(state, 0) + 1
    
    # Count by administrative dimension
    admin_dim_counts = {}
    for case in all_test_cases:
        admin_dim = case.get("metadata", {}).get("use_case", {}).get("administrative_dimension")
        if admin_dim:
            admin_dim_counts[admin_dim] = admin_dim_counts.get(admin_dim, 0) + 1
    
    updated_dataset["statistics"] = {
        **existing_dataset.get("statistics", {}),
        "total_test_cases": total_cases,
        "document_distribution": {
            "with_documents": with_docs / total_cases,
            "without_documents": without_docs / total_cases
        },
        "document_distribution_compliance": {
            "target_with_documents": 0.5,
            "actual_with_documents": with_docs / total_cases,
            "target_without_documents": 0.5,
            "actual_without_documents": without_docs / total_cases,
            "compliance_improved": True if without_docs / total_cases > 0.3 else False
        },
        "state_distribution": state_counts,
        "administrative_dimension_coverage": admin_dim_counts,
        "quality_metrics": {
            "requires_expert_validation": len(new_test_cases),
            "ready_for_evaluation": len(existing_test_cases),
            "total_baseline_responses_needed": sum(1 for case in all_test_cases 
                                                  if not case.get("metadata", {}).get("quality_metrics", {}).get("has_baseline", True))
        }
    }
    
    # Create backup of original
    backup_path = factual_questions_path.parent / f"factual_questions_backup_v1.0.0_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    print(f"💾 Creating backup: {backup_path.name}")
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(existing_dataset, f, indent=2, ensure_ascii=False)
    
    # Save updated dataset
    print(f"💾 Saving updated dataset: {factual_questions_path.name}")
    
    with open(factual_questions_path, 'w', encoding='utf-8') as f:
        json.dump(updated_dataset, f, indent=2, ensure_ascii=False)
    
    # Print integration summary
    print(f"\n✅ Integration Complete!")
    print(f"📊 Updated Statistics:")
    print(f"   📋 Total questions: {existing_dataset.get('statistics', {}).get('total_test_cases', len(existing_test_cases))} → {total_cases}")
    print(f"   📈 Document distribution improvement:")
    print(f"      - With documents: 100% → {with_docs / total_cases:.1%}")
    print(f"      - Without documents: 0% → {without_docs / total_cases:.1%}")
    print(f"   🎯 Target compliance: {without_docs / total_cases:.1%} without docs (target: 50%)")
    
    print(f"\n🏛️  Administrative Coverage Added:")
    for dim, count in admin_dim_counts.items():
        print(f"   - {dim}: {count} questions")
    
    print(f"\n📊 Quality Status:")
    quality = updated_dataset["statistics"]["quality_metrics"]
    print(f"   ✅ Ready for evaluation: {quality['ready_for_evaluation']} questions")
    print(f"   📝 Requires expert validation: {quality['requires_expert_validation']} questions") 
    print(f"   📄 Needs baseline responses: {quality['total_baseline_responses_needed']} questions")
    
    print(f"\n🔧 Next Steps:")
    print(f"   1. Domain expert validation for {len(new_test_cases)} generated questions")
    print(f"   2. Create baseline responses for validated questions") 
    print(f"   3. Run bias and hallucination checks")
    print(f"   4. Upload to evaluation platform")
    print(f"   5. Begin systematic testing across administrative dimensions")
    
    # Create validation checklist
    validation_checklist_path = factual_questions_path.parent / "administrative_validation_checklist.json"
    
    validation_checklist = {
        "validation_required": {
            "total_questions": len(new_test_cases),
            "administrative_dimensions": list(admin_dim_counts.keys()),
            "expert_validation_needed": True,
            "baseline_responses_needed": True
        },
        "validation_process": {
            "step_1": "Domain expert review of generated questions",
            "step_2": "Fact-checking against official sources",
            "step_3": "Bias detection and correction",
            "step_4": "Baseline response creation",
            "step_5": "Integration testing"
        },
        "quality_gates": {
            "factual_accuracy": "Must be verified against official sources",
            "language_appropriateness": "Must use appropriate administrative German",
            "bias_check": "Must pass systematic bias detection",
            "hallucination_prevention": "Must not contain fabricated information",
            "completeness": "Must cover key aspects of administrative topic"
        },
        "administrative_experts_needed": {
            "Sicherheit_Ordnung": "Police and public safety expert",
            "Soziale_Sicherung": "Social services and welfare expert", 
            "Gesundheit_Umwelt": "Health administration and environmental protection expert",
            "Verkehr_Nachrichtenwesen": "Transportation and communication expert",
            "Wohnungswesen_Stadtebau": "Housing and urban planning expert",
            "Finanzverwaltung": "Financial administration expert"
        }
    }
    
    with open(validation_checklist_path, 'w', encoding='utf-8') as f:
        json.dump(validation_checklist, f, indent=2, ensure_ascii=False)
    
    print(f"\n📋 Created validation checklist: {validation_checklist_path.name}")


def main():
    """Main function to integrate administrative questions."""
    integrate_administrative_questions()


if __name__ == "__main__":
    main()
