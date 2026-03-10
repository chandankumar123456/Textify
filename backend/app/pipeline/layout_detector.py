class LayoutRegion:
    """Represents a detected region in the document."""
    def __init__(self, region_type: str, content: str, order: int, bbox: dict = None):
        self.region_type = region_type  # heading, paragraph, formula, question, image
        self.content = content
        self.order = order
        self.bbox = bbox or {}

    def to_dict(self) -> dict:
        return {
            "region_type": self.region_type,
            "content": self.content,
            "order": self.order,
            "bbox": self.bbox,
        }


class LayoutDetector:
    """Organizes structured content from vision model output into layout regions."""

    def detect_regions(self, structured_content: dict) -> list[LayoutRegion]:
        """Convert structured content dict into ordered LayoutRegion objects."""
        regions = []
        order = 0

        for heading in structured_content.get("headings", []):
            regions.append(LayoutRegion("heading", heading, order))
            order += 1

        for para in structured_content.get("paragraphs", []):
            regions.append(LayoutRegion("paragraph", para, order))
            order += 1

        for formula in structured_content.get("formulas", []):
            regions.append(LayoutRegion("formula", formula, order))
            order += 1

        for q in structured_content.get("questions", []):
            q_text = q.get("question", "")
            regions.append(LayoutRegion("question", q_text, order, {"full_question": q}))
            order += 1

        return regions
