# app/utils/text_processing.py
import re
import arabic_reshaper
from bidi.algorithm import get_display

def make_farsi_text_for_display(text: str) -> str:
    """Prepares Farsi text for display in libraries like Matplotlib."""
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

def make_farsi_text_for_pdf(text: str) -> str:
    """Prepares Farsi text for libraries like FPDF that need reshaping."""
    return arabic_reshaper.reshape(text)

def fix_mixed_text_order(text: str) -> str:
    """Corrects display order for strings with mixed RTL and LTR text."""
    persian_pattern = re.compile(r'[\u0600-\u06FF]+')
    tokens = re.findall(r'\S+|\s+', text)
    segments, temp_segment, is_persian = [], [], None
    for token in tokens:
        current_is_persian = bool(persian_pattern.search(token))
        if is_persian is None: is_persian = current_is_persian
        if current_is_persian == is_persian:
            temp_segment.append(token)
        else:
            segments.append((is_persian, temp_segment))
            temp_segment = [token]
            is_persian = current_is_persian
    if temp_segment: segments.append((is_persian, temp_segment))
    
    fixed_segments = []
    for is_persian, segment in segments:
        if not is_persian: segment.reverse()
        fixed_segments.append(''.join(segment))
    return ''.join(fixed_segments)