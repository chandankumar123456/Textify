import os
from jinja2 import Environment, FileSystemLoader
from ..pipeline.math_parser import MathParser


class DocumentBuilder:
    """Builds HTML documents from structured content for PDF generation."""

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            template_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "templates"
            )
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.math_parser = MathParser()

    def build_notes_html(self, pages_content: list[dict], title: str = "Study Notes") -> str:
        """Build notes HTML from list of page contents."""
        template = self.env.get_template("notes_template.html")
        
        processed_pages = []
        for page in pages_content:
            processed = {
                "headings": page.get("headings", []),
                "paragraphs": [
                    self.math_parser.format_text_with_math(p)
                    for p in page.get("paragraphs", [])
                ],
                "formulas": page.get("formulas", []),
                "questions": page.get("questions", []),
            }
            processed_pages.append(processed)
        
        return template.render(title=title, pages=processed_pages)

    def build_practice_html(self, questions: list[dict], title: str = "Practice Questions") -> str:
        """Build practice PDF HTML from cleaned questions."""
        template = self.env.get_template("practice_template.html")
        
        processed_questions = []
        for i, q in enumerate(questions, 1):
            processed_questions.append({
                "number": i,
                "question": self.math_parser.format_text_with_math(q.get("question", "")),
                "options": [
                    self.math_parser.format_text_with_math(opt)
                    for opt in q.get("options", [])
                ],
            })
        
        return template.render(title=title, questions=processed_questions)
