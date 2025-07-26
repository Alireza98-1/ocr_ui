# app/schemas/ocr.py

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Union

# --- Output Schemas ---

class TaskQueueResponse(BaseModel):
    """The response returned after successfully queuing a task."""
    guid: str = Field(..., description="The unique identifier for the processed file.")
    filename: str = Field(..., description="The original filename of the uploaded file.")
    status: str = Field(..., description="The initial status of the task, always 'queued'.")
    task_id: str = Field(..., description="The main workflow task ID used for polling the final result.")


# --- Task Status Schemas ---

class FinalOCRResult(BaseModel):
    """The structure of the final successful OCR result data."""
    guid: str
    text: str  # This is a Base64 encoded string
    confidence: float
    status: str
    error: str = ""

class TaskErrorResult(BaseModel):
    """The structure for returning an error from a failed task."""
    error: str

class TaskStatusResponse(BaseModel):
    """The response structure for the task status polling endpoint."""
    task_id: str = Field(..., description="The ID of the task being polled.")
    status: str = Field(..., description="The current status of the task (e.g., PENDING, SUCCESS, FAILURE).")
    result: Optional[Union[FinalOCRResult, TaskErrorResult]] = Field(None, description="The final result, present on success or failure.")