import re
from collections import Counter


class ConceptExtractor:
    """Extracts key concepts from document content and builds concept relationships."""

    # Common academic/technical concept patterns
    CONCEPT_INDICATORS = [
        "definition", "theorem", "lemma", "corollary", "proof",
        "formula", "equation", "principle", "law", "rule",
        "method", "algorithm", "technique", "property",
    ]

    def extract_concepts(self, structured_content: dict) -> list[dict]:
        """Extract key concepts from structured page content."""
        all_text = self._gather_text(structured_content)
        concepts = self._identify_concepts(all_text)
        
        # Associate questions with concepts
        questions = structured_content.get("questions", [])
        for concept in concepts:
            concept["question_indices"] = self._find_related_questions(
                concept["name"], questions
            )
        
        return concepts

    def build_concept_graph(self, all_concepts: list[dict]) -> list[dict]:
        """Build relationships between concepts across all pages."""
        concept_map = {}
        for c in all_concepts:
            name = c["name"].lower()
            if name not in concept_map:
                concept_map[name] = {
                    "name": c["name"],
                    "related_concepts": set(),
                    "question_indices": set(),
                }
            concept_map[name]["question_indices"].update(c.get("question_indices", []))

        # Find related concepts based on co-occurrence
        names = list(concept_map.keys())
        for i, n1 in enumerate(names):
            for n2 in names[i + 1:]:
                # If concepts share questions, they're related
                shared = concept_map[n1]["question_indices"] & concept_map[n2]["question_indices"]
                if shared:
                    concept_map[n1]["related_concepts"].add(concept_map[n2]["name"])
                    concept_map[n2]["related_concepts"].add(concept_map[n1]["name"])

        return [
            {
                "name": v["name"],
                "related_concepts": list(v["related_concepts"]),
                "question_indices": list(v["question_indices"]),
            }
            for v in concept_map.values()
        ]

    def _gather_text(self, content: dict) -> str:
        parts = []
        parts.extend(content.get("headings", []))
        parts.extend(content.get("paragraphs", []))
        for q in content.get("questions", []):
            parts.append(q.get("question", ""))
        return " ".join(parts)

    def _identify_concepts(self, text: str) -> list[dict]:
        """Identify concepts from text using heading patterns and noun phrase extraction."""
        concepts = []
        seen = set()

        # Extract capitalized multi-word phrases (likely concept names)
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        matches = re.findall(pattern, text)
        counter = Counter(matches)

        for phrase, count in counter.most_common(50):
            lower = phrase.lower()
            # Filter out common non-concept words
            if lower in ("the", "this", "that", "these", "those", "what", "which", "where", "when"):
                continue
            if len(phrase) < 3:
                continue
            if lower not in seen:
                seen.add(lower)
                concepts.append({"name": phrase, "frequency": count})

        return concepts

    def _find_related_questions(self, concept_name: str, questions: list[dict]) -> list[int]:
        indices = []
        lower_name = concept_name.lower()
        for i, q in enumerate(questions):
            q_text = q.get("question", "").lower()
            if lower_name in q_text:
                indices.append(i)
        return indices
