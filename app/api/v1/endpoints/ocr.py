# app/api/v1/endpoints/ocr.py

from typing import Optional, Any
from celery.result import AsyncResult
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends

from app.core.logging import correlation_id_var
from app.worker.celery_app import app as celery_app
from app.schemas.ocr import TaskQueueResponse, TaskStatusResponse, FinalOCRResult, TaskErrorResult

# Define the router with a prefix and tags for organization
router = APIRouter(tags=["OCR Processing"])

@router.post("/ocr", response_model=TaskQueueResponse)
async def create_ocr_task(
    file: UploadFile = File(..., description="A single image or PDF file to process."),
    guid: str = Form(..., description="A unique client-provided identifier for this file."),
    webhook_url: Optional[str] = Form(None, description="Optional URL for webhook notifications."),
):
    """
    Accepts a file for asynchronous OCR processing and returns a task ID for polling.
    """
    try:
        file_bytes = await file.read()
        
        # This metadata structure matches what the Celery task expects.
        metadata = {"guid": guid, "file_type": file.content_type}
        
        # Call the Celery task by its string name to keep the API and worker decoupled.
        task_name = 'app.worker.tasks.process_ocr_task'
        async_result = celery_app.send_task(
            name=task_name,
            kwargs={
                'file_content': file_bytes,
                'metadata': metadata,
                'webhook_url': webhook_url,
                'correlation_id': correlation_id_var.get()
            }
        )
        
        # Block briefly to get the main workflow ID returned by the orchestrator task.
        main_workflow_id = async_result.get(timeout=10)

        if not main_workflow_id:
            raise HTTPException(status_code=500, detail="Failed to dispatch OCR workflow.")

        return TaskQueueResponse(
            guid=guid,
            filename=file.filename,
            status="queued",
            task_id=main_workflow_id
        )
    except Exception as e:
        # Catch potential timeouts or other exceptions
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")


@router.get("/ocr/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Retrieves the current status and final result of a task using its ID.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    status = task_result.status
    result_payload = None

    if task_result.ready():
        if task_result.successful():
            # On success, populate with the FinalOCRResult model
            success_data = task_result.get()
            result_payload = FinalOCRResult(**success_data)
        else:
            # On failure, populate with the TaskErrorResult model
            error_info = str(task_result.info) # .info contains the exception
            result_payload = TaskErrorResult(error=error_info)
            
    return TaskStatusResponse(
        task_id=task_id,
        status=status,
        result=result_payload
    )