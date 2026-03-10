import pytest
from backend.app.pipeline.math_parser import MathParser
from backend.app.pipeline.question_extractor import QuestionExtractor
from backend.app.pipeline.concept_extractor import ConceptExtractor
from backend.app.pipeline.document_classifier import DocumentClassifier
from backend.app.pipeline.layout_detector import LayoutDetector
from backend.app.pipeline.image_preprocessor import ImagePreprocessor


class TestMathParser:
    def setup_method(self):
        self.parser = MathParser()

    def test_parse_inline_formulas(self):
        text = "The formula $x^2 + y^2 = r^2$ is a circle equation."
        formulas = self.parser.parse_formulas(text)
        assert len(formulas) == 1
        assert "x^2 + y^2 = r^2" in formulas[0]

    def test_parse_display_formulas(self):
        text = "Consider $$\\int_0^1 x^2 dx$$"
        formulas = self.parser.parse_formulas(text)
        assert len(formulas) == 1

    def test_wrap_latex(self):
        result = self.parser.wrap_latex("x^2")
        assert "\\(x^2\\)" in result

    def test_format_text_with_math(self):
        text = "The value $x^2$ is important"
        result = self.parser.format_text_with_math(text)
        assert "\\(x^2\\)" in result


class TestQuestionExtractor:
    def setup_method(self):
        self.extractor = QuestionExtractor()

    def test_extract_questions(self):
        content = {
            "questions": [
                {
                    "question": "What is 2+2?",
                    "options": ["A) 3", "B) 4", "C) 5", "D) 6"],
                    "answer": "B",
                    "explanation": "Simple addition",
                }
            ]
        }
        questions = self.extractor.extract_questions(content)
        assert len(questions) == 1
        assert questions[0]["question"] == "What is 2+2?"
        assert len(questions[0]["options"]) == 4

    def test_extract_empty(self):
        content = {"questions": []}
        questions = self.extractor.extract_questions(content)
        assert len(questions) == 0

    def test_create_practice_questions(self):
        questions = [
            {
                "question": "What is 2+2?",
                "options": ["A) 3 ✓", "B) 4", "C) 5", "D) 6"],
                "answer": "A",
                "explanation": "Simple addition",
            }
        ]
        practice = self.extractor.create_practice_questions(questions)
        assert len(practice) == 1
        assert "answer" not in practice[0]
        assert "explanation" not in practice[0]
        # Check that check marks are removed
        assert "✓" not in practice[0]["options"][0]


class TestConceptExtractor:
    def setup_method(self):
        self.extractor = ConceptExtractor()

    def test_extract_concepts(self):
        content = {
            "headings": ["Linear Algebra", "Vector Spaces"],
            "paragraphs": ["Linear Algebra is the study of vectors and matrices."],
            "questions": [{"question": "What is a Vector Space?"}],
            "formulas": [],
        }
        concepts = self.extractor.extract_concepts(content)
        assert len(concepts) > 0
        names = [c["name"] for c in concepts]
        # Check at least one concept containing "Linear" or "Vector" is extracted
        assert any("Linear" in n or "Vector" in n for n in names)

    def test_build_concept_graph(self):
        concepts = [
            {"name": "Linear Algebra", "question_indices": [0, 1]},
            {"name": "Vector Space", "question_indices": [0]},
            {"name": "Eigenvalues", "question_indices": [2]},
        ]
        graph = self.extractor.build_concept_graph(concepts)
        assert len(graph) == 3


class TestDocumentClassifier:
    def setup_method(self):
        self.classifier = DocumentClassifier()

    def test_classify_notes(self):
        content = {
            "headings": ["Chapter 1"],
            "paragraphs": ["Some text"],
            "questions": [],
            "formulas": [],
        }
        assert self.classifier.classify(content) == "notes"

    def test_classify_questions(self):
        content = {
            "headings": [],
            "paragraphs": [],
            "questions": [{"question": "What?"}],
            "formulas": [],
        }
        assert self.classifier.classify(content) == "questions"

    def test_classify_mixed(self):
        content = {
            "headings": ["Title"],
            "paragraphs": ["Text"],
            "questions": [{"question": "What?"}],
            "formulas": [],
        }
        assert self.classifier.classify(content) == "mixed"

    def test_classify_unknown(self):
        content = {
            "headings": [],
            "paragraphs": [],
            "questions": [],
            "formulas": [],
        }
        assert self.classifier.classify(content) == "unknown"


class TestLayoutDetector:
    def setup_method(self):
        self.detector = LayoutDetector()

    def test_detect_regions(self):
        content = {
            "headings": ["Title"],
            "paragraphs": ["Some text"],
            "formulas": ["x^2"],
            "questions": [{"question": "What?"}],
        }
        regions = self.detector.detect_regions(content)
        assert len(regions) == 4
        types = [r.region_type for r in regions]
        assert "heading" in types
        assert "paragraph" in types
        assert "formula" in types
        assert "question" in types

    def test_region_to_dict(self):
        content = {"headings": ["Title"], "paragraphs": [], "formulas": [], "questions": []}
        regions = self.detector.detect_regions(content)
        d = regions[0].to_dict()
        assert d["region_type"] == "heading"
        assert d["content"] == "Title"


class TestImagePreprocessor:
    def setup_method(self):
        self.preprocessor = ImagePreprocessor()

    def test_preprocess_valid_image(self):
        # Create a simple test PNG image
        from PIL import Image
        import io

        img = Image.new("RGB", (100, 100), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()

        result = self.preprocessor.preprocess(img_bytes)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_preprocess_large_image(self):
        from PIL import Image
        import io

        # Create a large image that should be resized
        img = Image.new("RGB", (5000, 5000), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()

        result = self.preprocessor.preprocess(img_bytes)
        # Verify the result is a valid image
        result_img = Image.open(io.BytesIO(result))
        assert max(result_img.size) <= 4096
