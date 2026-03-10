import io
import tempfile
from pdf2image import convert_from_bytes
from PIL import Image


class PDFProcessor:
    """Converts PDF bytes into individual page images."""

    def __init__(self, dpi: int = 300):
        self.dpi = dpi

    def split_to_images(self, pdf_bytes: bytes) -> list[bytes]:
        """Split PDF into individual page images as PNG bytes."""
        images = convert_from_bytes(pdf_bytes, dpi=self.dpi)
        result = []
        for img in images:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            result.append(buf.getvalue())
        return result

    def get_page_count(self, pdf_bytes: bytes) -> int:
        """Return the number of pages in a PDF."""
        images = convert_from_bytes(pdf_bytes, dpi=72)
        return len(images)
