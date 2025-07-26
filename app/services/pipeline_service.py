from typing import List, Tuple
import numpy as np
import structlog

from app.services.detection_service import DetectionService
from app.services.recognition_service import RecognitionService
from app.utils.image_processing import (
    crop_boxes_from_image,
    make_box_from_poly,
    crop_word_from_polygon
)
from app.utils.text_processing import fix_mixed_text_order

logger = structlog.get_logger(__name__)

class PipelineService:
    """
    Acts as a 'toolbox' of core OCR functions.
    It no longer controls the flow, but provides the implementation logic
    that Celery tasks will call.
    """
    def __init__(self, config: dict):
        self.detection_service = DetectionService(config['detection'])
        self.recognition_service = RecognitionService(config['recognition'])
        pipeline_config = config.get('pipeline', {})
        self.enable_recognition = pipeline_config.get('enable_recognition', True)
        logger.info("pipeline_service.initialized", recognition_enabled=self.enable_recognition)

    def detect_lines(self, image: np.ndarray) -> List[list]:
        """Detects all line bounding boxes in a single image."""
        line_boxes = self.detection_service.predict_line_boxes([image])['line_boxes'][0]
        # Sort lines top-to-bottom for correct reading order.
        return sorted(line_boxes, key=lambda box: box[1])

    def detect_words(self, image: np.ndarray, line_boxes: List[list]) -> List[list]:
        """Detects all word polygons within the given line boxes for an image."""
        if not line_boxes:
            return []
        line_crops = crop_boxes_from_image(line_boxes, image)
        return self.detection_service.predict_word_polygons(line_crops)['word_polygons']

    def recognize_page(self, image: np.ndarray, line_boxes: List[list], word_polygons_per_line: List[list]) -> Tuple[str, float]:
        """
        Recognizes text for an entire page and returns the full text and average confidence.
        """
        if not self.enable_recognition:
            return ("[RECOGNITION DISABLED]", 0.0)
        
        line_crops = crop_boxes_from_image(line_boxes, image)
        text_of_lines = []

        for line_idx, word_polygons in enumerate(word_polygons_per_line):
            if not word_polygons:
                continue
            
            line_crop = line_crops[line_idx]
            line_text, line_conf = self._recognize_line(line_crop, word_polygons)
            text_of_lines.append((line_text, line_conf))
        
        full_text = "\n".join(text for text, _ in text_of_lines)
        overall_conf = sum(conf for _, conf in text_of_lines) / len(text_of_lines) if text_of_lines else 0.0
        return full_text, overall_conf

    def _recognize_line(self, line_crop: np.ndarray, word_polygons: list) -> Tuple[str, float]:
        """Helper to recognize all words in a single line."""
        word_data = [
            {'crop': crop_word_from_polygon(line_crop, poly), 'box': make_box_from_poly(poly)}
            for poly in word_polygons
        ]
        
        all_word_crops = [item['crop'] for item in word_data]
        word_texts_with_probs = self.recognition_service(all_word_crops)

        for i, item in enumerate(word_data):
            item['text'], item['prob'] = word_texts_with_probs[i]

        sorted_words = sorted(word_data, key=lambda x: x['box'][0], reverse=True)
        
        text_line = " ".join(item['text'] for item in sorted_words)
        text_line = fix_mixed_text_order(text_line)
        
        line_probs = [item['prob'] for item in sorted_words]
        line_conf = sum(line_probs) / len(line_probs) if line_probs else 0.0
        return text_line, line_conf