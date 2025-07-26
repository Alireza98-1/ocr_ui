import pickle
from typing import List, Any
import numpy as np
from redis import Redis
from app.core.config import settings

# A Redis client instance can be shared.
# It manages its own connection pool internally.
redis_client = Redis.from_url(settings.CELERY_BACKEND_URL)

class StateManager:
    """
    Manages the storage and retrieval of intermediate task data in Redis.
    This prevents passing large data blobs (like images) between Celery tasks,
    which is a critical best practice for distributed systems.
    """
    def __init__(self, request_id: str):
        """
        Initializes the manager with a unique ID for the current OCR request.

        Args:
            request_id (str): A unique identifier (e.g., a UUID) for the entire workflow.
        """
        if not request_id:
            raise ValueError("request_id cannot be empty.")
        self.request_id = request_id
        # Set a default TTL (Time-To-Live) of 2 hours for all keys related to this request.
        self.ttl_seconds = 7200

    def _get_key(self, key: str) -> str:
        """Constructs a unique, namespaced Redis key for the current request."""
        return f"ocr_state:{self.request_id}:{key}"

    def _set_data(self, key: str, data: Any):
        """Serializes data using pickle and stores it in Redis with a timeout."""
        redis_key = self._get_key(key)
        redis_client.set(redis_key, pickle.dumps(data), ex=self.ttl_seconds)

    def _get_data(self, key: str) -> Any:
        """Retrieves and deserializes data from Redis."""
        redis_key = self._get_key(key)
        serialized_data = redis_client.get(redis_key)
        if serialized_data is None:
            raise KeyError(f"Data for key '{key}' not found for request_id '{self.request_id}'. The key may have expired or was never set.")
        return pickle.loads(serialized_data)

    # --- Public methods for managing specific workflow data ---

    def save_initial_images(self, images: List[np.ndarray]):
        """Saves the list of initial page images to Redis."""
        self._set_data("initial_images", images)

    def load_page_image(self, page_index: int) -> np.ndarray:
        """Loads a single page image from the stored list."""
        images = self._get_data("initial_images")
        if page_index >= len(images):
            raise IndexError("Page index out of range.")
        return images[page_index]

    def save_page_result(self, page_index: int, text: str, confidence: float):
        """Saves the final OCR result for a single page."""
        page_result = {
            "page_index": page_index,
            "text": text,
            "confidence": confidence
        }
        self._set_data(f"page_result:{page_index}", page_result)

    def load_all_page_results(self, page_indices: List[int]) -> List[dict]:
        """Loads and returns all specified page results, sorted by page index."""
        results = []
        for i in sorted(page_indices):
            results.append(self._get_data(f"page_result:{i}"))
        return results
