class DocumentClassifier:
    """Classifies document pages by content type based on structured content."""

    def classify(self, structured_content: dict) -> str:
        """Classify a page as 'notes', 'questions', or 'mixed'."""
        has_questions = len(structured_content.get("questions", [])) > 0
        has_text = (
            len(structured_content.get("headings", [])) > 0
            or len(structured_content.get("paragraphs", [])) > 0
        )
        has_formulas = len(structured_content.get("formulas", [])) > 0

        if has_questions and not has_text:
            return "questions"
        elif has_questions and has_text:
            return "mixed"
        elif has_text or has_formulas:
            return "notes"
        else:
            return "unknown"
