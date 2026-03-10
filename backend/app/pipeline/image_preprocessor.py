import io
import numpy as np
from PIL import Image


class ImagePreprocessor:
    """Preprocesses page images for better OCR/vision model results."""

    def preprocess(self, image_bytes: bytes) -> bytes:
        """Apply preprocessing pipeline to an image."""
        img = Image.open(io.BytesIO(image_bytes))
        img = self._convert_to_rgb(img)
        img = self._auto_orient(img)
        img = self._normalize_size(img)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    def _convert_to_rgb(self, img: Image.Image) -> Image.Image:
        if img.mode != "RGB":
            return img.convert("RGB")
        return img

    def _auto_orient(self, img: Image.Image) -> Image.Image:
        """Auto-orient based on EXIF data."""
        try:
            from PIL import ImageOps
            return ImageOps.exif_transpose(img)
        except Exception:
            return img

    def _normalize_size(self, img: Image.Image, max_dim: int = 4096) -> Image.Image:
        """Resize if any dimension exceeds max_dim, preserving aspect ratio."""
        w, h = img.size
        if max(w, h) > max_dim:
            scale = max_dim / max(w, h)
            new_w, new_h = int(w * scale), int(h * scale)
            return img.resize((new_w, new_h), Image.LANCZOS)
        return img
