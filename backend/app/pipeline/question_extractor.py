class QuestionExtractor:
    """Extracts and processes questions from structured content."""

    def extract_questions(self, structured_content: dict) -> list[dict]:
        """Extract question blocks from structured page content."""
        questions = []
        for q in structured_content.get("questions", []):
            question = {
                "question": q.get("question", "").strip(),
                "options": [opt.strip() for opt in q.get("options", []) if opt.strip()],
                "answer": q.get("answer", "").strip(),
                "explanation": q.get("explanation", "").strip(),
            }
            if question["question"]:
                questions.append(question)
        return questions

    def create_practice_questions(self, questions: list[dict]) -> list[dict]:
        """Remove answers, explanations, and marks from questions for practice mode."""
        practice = []
        for q in questions:
            practice_q = {
                "question": q["question"],
                "options": self._clean_options(q.get("options", [])),
            }
            practice.append(practice_q)
        return practice

    def _clean_options(self, options: list[str]) -> list[str]:
        """Remove check marks, circles, highlights from options."""
        cleaned = []
        for opt in options:
            # Remove common answer indicators
            opt = opt.replace("✓", "").replace("✔", "").replace("☑", "")
            opt = opt.replace("●", "").replace("○", "")
            opt = opt.replace("(correct)", "").replace("[correct]", "")
            opt = opt.replace("★", "").replace("⭐", "")
            opt = opt.strip()
            if opt:
                cleaned.append(opt)
        return cleaned
