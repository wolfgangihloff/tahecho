#!/usr/bin/env python3
"""
Generate targeted factual questions to improve coverage across German administrative dimensions.

This script analyzes the current distribution and creates new factual questions
to fill gaps in administrative coverage, following the detailed dimension specifications.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib


# Current distribution from analysis
CURRENT_DISTRIBUTION = {
    "BayHIG": 146,
    "Deutschlandstipendium": 26,
    "Dokumente": 68,
    "EU AI Act": 10,
    "Hochschulverträge": 378,
    "IT-Planungsrat": 238,
    "Kabinettsprotokolle": 2,
    "Personalstrategie": 8,
    "Startups": 96
}

# Administrative dimensions mapping with priority and target questions
ADMINISTRATIVE_DIMENSIONS = {
    # Priority 1: Core areas that are underrepresented
    "Allgemeine_Dienste": {
        "current_coverage": CURRENT_DISTRIBUTION.get("Personalstrategie", 0) + CURRENT_DISTRIBUTION.get("IT-Planungsrat", 0) // 3,
        "target_questions": 50,
        "priority": 1,
        "sub_areas": [
            "Politische Führung und zentrale Verwaltung",
            "Personalwesen und Personalentwicklung",
            "IT-Strategie und Digitalisierung",
            "Öffentlichkeitsarbeit und Kommunikation",
            "Organisation und Strategie"
        ],
        "sample_questions": [
            "Wie ist die Personalentwicklung in der öffentlichen Verwaltung strukturiert?",
            "Welche Rolle spielt die Digitalisierungsstrategie in deutschen Behörden?",
            "Was umfasst das betriebliche Gesundheitsmanagement im öffentlichen Dienst?",
            "Wie funktioniert das Ideenmanagement in der Verwaltung?",
            "Welche Aufgaben hat der behördliche Datenschutzbeauftragte?"
        ]
    },
    
    "Sicherheit_Ordnung": {
        "current_coverage": 0,  # No specific coverage identified
        "target_questions": 40,
        "priority": 1,
        "sub_areas": [
            "Polizei und öffentliche Ordnung",
            "Brandschutz und Rettungsdienst",
            "Katastrophenschutz",
            "Bürgerdienste und Einwohnermeldewesen",
            "Verkehrssicherheit"
        ],
        "sample_questions": [
            "Wie ist der Rettungsdienst in Deutschland organisiert?",
            "Welche Aufgaben hat das Einwohnermeldewesen?",
            "Wie funktioniert der Katastrophenschutz auf kommunaler Ebene?",
            "Was umfasst die Gewerbeaufsicht?",
            "Welche Rolle spielt die Bußgeldstelle?"
        ]
    },
    
    "Soziale_Sicherung": {
        "current_coverage": 0,  # No specific coverage identified
        "target_questions": 60,
        "priority": 1,
        "sub_areas": [
            "Sozialversicherung und Arbeitslosenversicherung",
            "Familienhilfe und Wohlfahrtspflege",
            "Kinder- und Jugendhilfe",
            "Arbeitsmarktpolitik",
            "Leistungen nach SGB XII"
        ],
        "sample_questions": [
            "Wie funktioniert das Arbeitslosengeld II System?",
            "Was umfasst die Kinder- und Jugendhilfe?",
            "Welche Leistungen bietet die Familienhilfe?",
            "Wie ist die Sozialversicherung strukturiert?",
            "Was sind die Aufgaben der Jobcenter?"
        ]
    },
    
    "Gesundheit_Umwelt": {
        "current_coverage": 0,  # No specific coverage identified
        "target_questions": 40,
        "priority": 1,
        "sub_areas": [
            "Gesundheitswesen und Gesundheitsschutz",
            "Umwelt- und Naturschutz",
            "Sport und Erholung",
            "Arbeitsschutz",
            "Klimaschutz"
        ],
        "sample_questions": [
            "Wie ist das Gesundheitswesen in Deutschland strukturiert?",
            "Welche Maßnahmen umfasst der Umweltschutz?",
            "Was sind die Aufgaben der Gesundheitsverwaltung?",
            "Wie funktioniert der Arbeitsschutz?",
            "Welche Rolle spielt der Klimaschutz in der Kommunalpolitik?"
        ]
    },
    
    # Priority 2: Areas with some coverage, but need expansion
    "Bildungswesen": {
        "current_coverage": CURRENT_DISTRIBUTION.get("Deutschlandstipendium", 0) + CURRENT_DISTRIBUTION.get("Hochschulverträge", 0),
        "target_questions": 30,  # Already well covered, just fill specific gaps
        "priority": 2,
        "sub_areas": [
            "Allgemeinbildende Schulen",
            "Berufliche Schulen", 
            "Volkshochschulen und Weiterbildung",
            "Lehrerfortbildung"
        ],
        "sample_questions": [
            "Wie ist das berufliche Schulwesen strukturiert?",
            "Welche Rolle spielen Volkshochschulen?",
            "Was umfasst die Lehrerfortbildung?",
            "Wie funktioniert die Schulaufsicht?"
        ]
    },
    
    "Verkehr_Nachrichtenwesen": {
        "current_coverage": 0,
        "target_questions": 35,
        "priority": 2,
        "sub_areas": [
            "Straßenbau und Verkehrsplanung",
            "Öffentlicher Personennahverkehr",
            "Verkehrsüberwachung",
            "Mobilitätsmanagement"
        ],
        "sample_questions": [
            "Wie ist der öffentliche Personennahverkehr organisiert?",
            "Was umfasst die Verkehrsplanung?",
            "Welche Aufgaben hat die Verkehrsüberwachung?",
            "Wie funktioniert das Mobilitätsmanagement?"
        ]
    },
    
    "Wohnungswesen_Stadtebau": {
        "current_coverage": 0,
        "target_questions": 30,
        "priority": 2,
        "sub_areas": [
            "Wohnungsbauförderung",
            "Städtebauförderung",
            "Bauaufsicht",
            "Raumordnung und Landesplanung"
        ],
        "sample_questions": [
            "Wie funktioniert die Wohnungsbauförderung?",
            "Was umfasst die Städtebauförderung?",
            "Welche Aufgaben hat die Bauaufsicht?",
            "Wie ist die Raumordnung organisiert?"
        ]
    },
    
    "Finanzverwaltung": {
        "current_coverage": 0,
        "target_questions": 25,
        "priority": 2,
        "sub_areas": [
            "Steuerverwaltung",
            "Haushaltsmanagement",
            "Beteiligungssteuerung",
            "Rechnungsprüfung"
        ],
        "sample_questions": [
            "Wie ist die Steuerverwaltung aufgebaut?",
            "Was umfasst das Haushaltsmanagement?",
            "Welche Rolle spielt die Beteiligungssteuerung?",
            "Wie funktioniert die Rechnungsprüfung?"
        ]
    }
}


def generate_factual_question(dimension: str, sub_area: str, question_type: str, index: int) -> Dict[str, Any]:
    """
    Generate a structured factual question for a specific administrative dimension.
    
    Args:
        dimension: Administrative dimension
        sub_area: Specific sub-area within the dimension
        question_type: Type of question (definition, process, structure, etc.)
        index: Question index for ID generation
        
    Returns:
        Complete test case structure
    """
    
    # Question templates by type
    question_templates = {
        "definition": [
            "Was ist {topic}?",
            "Was umfasst {topic}?",
            "Wie ist {topic} definiert?"
        ],
        "structure": [
            "Wie ist {topic} organisiert?",
            "Wie ist {topic} strukturiert?",
            "Wie ist {topic} aufgebaut?"
        ],
        "process": [
            "Wie funktioniert {topic}?",
            "Wie läuft {topic} ab?",
            "Welche Schritte umfasst {topic}?"
        ],
        "responsibility": [
            "Wer ist für {topic} zuständig?",
            "Welche Behörde ist für {topic} verantwortlich?",
            "Welche Aufgaben hat {topic}?"
        ],
        "legal_basis": [
            "Welche Rechtsgrundlage hat {topic}?",
            "Auf welcher gesetzlichen Basis funktioniert {topic}?",
            "Welche Gesetze regeln {topic}?"
        ]
    }
    
    # Topic mapping for sub-areas
    topic_mapping = {
        "Personalwesen und Personalentwicklung": "die Personalentwicklung im öffentlichen Dienst",
        "IT-Strategie und Digitalisierung": "die Digitalisierungsstrategie in Behörden",
        "Polizei und öffentliche Ordnung": "die öffentliche Ordnung",
        "Sozialversicherung und Arbeitslosenversicherung": "die Sozialversicherung",
        "Gesundheitswesen und Gesundheitsschutz": "das Gesundheitswesen",
        "Straßenbau und Verkehrsplanung": "die Verkehrsplanung",
        "Wohnungsbauförderung": "die Wohnungsbauförderung",
        "Steuerverwaltung": "die Steuerverwaltung"
    }
    
    # Get or generate topic
    topic = topic_mapping.get(sub_area, sub_area.lower())
    
    # Select question template
    templates = question_templates.get(question_type, question_templates["definition"])
    question = templates[index % len(templates)].format(topic=topic)
    
    # Generate expected output criteria
    expected_contains = []
    if question_type == "definition":
        expected_contains = ["definition", "aufgaben", "zweck"]
    elif question_type == "structure":
        expected_contains = ["organisation", "struktur", "ebenen"]
    elif question_type == "process":
        expected_contains = ["verfahren", "schritte", "ablauf"]
    elif question_type == "responsibility":
        expected_contains = ["zuständig", "behörde", "verantwortlich"]
    elif question_type == "legal_basis":
        expected_contains = ["gesetz", "rechtsgrundlage", "basis"]
    
    # Generate unique ID
    content_hash = hashlib.md5(f"{dimension}_{sub_area}_{question}".encode()).hexdigest()[:8]
    
    test_case = {
        "id": f"factual_questions_{dimension.lower()}_{index:04d}_{content_hash}",
        "input": question,
        "expected_output": {
            "contains": expected_contains,
            "category": "Factual Questions",
            "file_set": f"Administrative_{dimension}",
            "baseline_response": f"[Generated question for {dimension} - {sub_area}. Requires domain expert validation.]",
            "confidence_level": "to_be_validated"
        },
        "metadata": {
            "test_type": "public_sector_query",
            "category": "Factual Questions",
            "file_set": f"Administrative_{dimension}",
            "domain": "public_sector",
            "language": "de",
            "origin": {
                "source_file": "generated_administrative_questions.py",
                "source_dataset": "generated",
                "original_id": f"{dimension}_{index}",
                "processing_date": datetime.now().isoformat()
            },
            "dimensions": [
                "knowledge_retrieval",
                dimension.lower().replace("_", "_"),
                "administrative_processes"
            ],
            "state": "draft",
            "tags": [
                "source:generated",
                f"domain:{dimension.lower()}",
                "type:factual_questions",
                "lang:de",
                f"complexity:medium",
                f"question_type:{question_type}"
            ],
            "quality_metrics": {
                "input_length": len(question),
                "has_baseline": False,  # Generated questions need expert validation
                "has_validation_criteria": True,
                "domain_specificity": 0.8  # High domain specificity for administrative questions
            },
            "use_case": {
                "primary": "factual_questions",
                "priority": 1,
                "document_availability": "without_documents",  # Help balance the distribution
                "data_format": "plain_text",
                "sub_dimensions": ["knowledge_areas", "administrative_dimensions"],
                "administrative_dimension": dimension,
                "administrative_sub_area": sub_area,
                "question_type": question_type
            },
            "evaluation_focus": {
                "critical_metrics": ["factual_accuracy", "hallucination_detection"],
                "quality_metrics": ["language_quality", "completeness"],
                "bias_check": True,
                "requires_expert_validation": True,
                "note": "Generated question - requires domain expert review and baseline response"
            }
        }
    }
    
    return test_case


def generate_administrative_questions() -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate factual questions across all administrative dimensions.
    
    Returns:
        Dictionary with questions organized by dimension
    """
    generated_questions = {}
    question_types = ["definition", "structure", "process", "responsibility", "legal_basis"]
    
    print("🏛️  Generating Administrative Factual Questions")
    print("=" * 60)
    
    for dimension, specs in ADMINISTRATIVE_DIMENSIONS.items():
        print(f"\n📊 Generating questions for: {dimension}")
        print(f"   Current coverage: {specs['current_coverage']} questions")
        print(f"   Target: {specs['target_questions']} questions")
        print(f"   Priority: {specs['priority']}")
        
        gap = specs['target_questions'] - specs['current_coverage']
        if gap <= 0:
            print(f"   ✅ Already meeting target")
            continue
        
        dimension_questions = []
        questions_per_sub_area = max(1, gap // len(specs['sub_areas']))
        
        for sub_area_idx, sub_area in enumerate(specs['sub_areas']):
            for q_idx in range(questions_per_sub_area):
                question_type = question_types[q_idx % len(question_types)]
                
                question = generate_factual_question(
                    dimension, 
                    sub_area, 
                    question_type, 
                    sub_area_idx * questions_per_sub_area + q_idx
                )
                dimension_questions.append(question)
        
        # If we need more questions to reach target, add extras
        while len(dimension_questions) < gap:
            extra_idx = len(dimension_questions)
            sub_area = specs['sub_areas'][extra_idx % len(specs['sub_areas'])]
            question_type = question_types[extra_idx % len(question_types)]
            
            question = generate_factual_question(dimension, sub_area, question_type, extra_idx)
            dimension_questions.append(question)
        
        generated_questions[dimension] = dimension_questions[:gap]  # Limit to exact gap
        print(f"   ✅ Generated {len(generated_questions[dimension])} questions")
    
    return generated_questions


def create_expansion_dataset(generated_questions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Create a dataset with all generated questions for adding to existing factual questions.
    
    Args:
        generated_questions: Generated questions by dimension
        
    Returns:
        Expansion dataset structure
    """
    all_questions = []
    for dimension, questions in generated_questions.items():
        all_questions.extend(questions)
    
    # Calculate statistics
    priority_1_count = sum(len(questions) for dim, questions in generated_questions.items() 
                          if ADMINISTRATIVE_DIMENSIONS[dim]['priority'] == 1)
    
    dimension_counts = {dim: len(questions) for dim, questions in generated_questions.items()}
    
    dataset = {
        "name": "pga_factual_questions_administrative_expansion",
        "description": "Additional factual questions to improve coverage across German administrative dimensions",
        "version": "1.0.0",
        "created_date": datetime.now().isoformat(),
        "purpose": "Expand existing factual_questions.json with balanced administrative coverage",
        "expansion_strategy": {
            "approach": "Add targeted questions rather than redistribute existing ones",
            "focus": "Fill gaps in administrative dimension coverage",
            "preserve_existing": "Maintain all existing test cases and their quality metrics"
        },
        "test_cases": all_questions,
        "statistics": {
            "total_generated_questions": len(all_questions),
            "priority_1_questions": priority_1_count,
            "priority_2_questions": len(all_questions) - priority_1_count,
            "dimensions_covered": len(generated_questions),
            "dimension_distribution": dimension_counts,
            "document_availability": {
                "without_documents": len(all_questions),  # All generated questions are without documents
                "with_documents": 0
            },
            "validation_required": len(all_questions)  # All need expert validation
        },
        "integration_plan": {
            "target_file": "tests/datasets/use_cases/factual_questions.json",
            "method": "Append to existing test_cases array",
            "validation_needed": "All generated questions need expert review and baseline responses",
            "expected_total_after_integration": 486 + len(all_questions)
        },
        "quality_assurance": {
            "expert_validation_required": True,
            "baseline_responses_needed": True,
            "domain_expert_review": "Required for each administrative dimension",
            "bias_check": "Systematic review for administrative bias",
            "hallucination_prevention": "Cross-reference with official administrative sources"
        }
    }
    
    return dataset


def main():
    """Main function to generate administrative factual questions."""
    
    # Generate questions
    generated_questions = generate_administrative_questions()
    
    if not generated_questions:
        print("\n✅ All administrative dimensions already have sufficient coverage")
        return
    
    # Create expansion dataset
    expansion_dataset = create_expansion_dataset(generated_questions)
    
    # Save expansion dataset
    output_dir = Path("/Users/wolfgang.ihloff/workspace/tahecho/tests/datasets/use_cases")
    output_path = output_dir / "factual_questions_administrative_expansion.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(expansion_dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved expansion dataset: {output_path}")
    
    # Print summary
    stats = expansion_dataset["statistics"]
    print(f"\n📊 Generation Summary:")
    print(f"  📋 Total generated questions: {stats['total_generated_questions']}")
    print(f"  🔥 Priority 1 questions: {stats['priority_1_questions']}")
    print(f"  📝 Priority 2 questions: {stats['priority_2_questions']}")
    print(f"  🏛️  Administrative dimensions covered: {stats['dimensions_covered']}")
    
    print(f"\n📈 Dimension Breakdown:")
    for dim, count in stats['dimension_distribution'].items():
        priority = ADMINISTRATIVE_DIMENSIONS[dim]['priority']
        print(f"  - {dim}: {count} questions (Priority {priority})")
    
    print(f"\n🔧 Next Steps:")
    print(f"  1. Review generated questions for quality and accuracy")
    print(f"  2. Have domain experts validate each administrative dimension")
    print(f"  3. Create baseline responses for all generated questions")
    print(f"  4. Integrate into existing factual_questions.json")
    print(f"  5. Run bias and hallucination checks")
    
    print(f"\n📊 Impact on Distribution:")
    print(f"  Current factual questions: 486")
    print(f"  After integration: {486 + stats['total_generated_questions']}")
    print(f"  Document distribution improvement:")
    print(f"    - Without documents: 0% → {stats['total_generated_questions']/(486 + stats['total_generated_questions']):.1%}")
    print(f"    - With documents: 100% → {486/(486 + stats['total_generated_questions']):.1%}")


if __name__ == "__main__":
    main()
