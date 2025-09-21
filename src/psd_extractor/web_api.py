"""
FastAPI Web Application for PSD Character Extractor

Provides a REST API and web interface for uploading PSD files,
analyzing expressions, mapping them to lip sync states, and downloading results.
"""

import asyncio
import logging
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from pydantic import BaseModel

from .utils.async_extractor import AsyncPSDExtractor
from .utils.job_manager import JobManager, JobStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PSD Character Extractor",
    description="Web interface for extracting character expressions from PSD files",
    version="1.0.0",
)

# Global instances
job_manager = JobManager()
extractor = AsyncPSDExtractor()

# Templates and static files
templates = Jinja2Templates(directory="web/templates")
app.mount("/static", StaticFiles(directory="web/static"), name="static")


# Pydantic models for API
class JobResponse(BaseModel):
    """Response model for job operations."""
    job_id: str
    status: str
    progress: float
    message: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Response model for PSD analysis."""
    job_id: str
    status: str
    psd_info: Dict
    available_expressions: List[str]
    mapping_suggestions: Dict[str, List[str]]
    current_mapping: Dict[str, List[str]]


class MappingUpdate(BaseModel):
    """Request model for mapping updates."""
    mapping: Dict[str, List[str]]


class ExtractionResponse(BaseModel):
    """Response model for extraction results."""
    job_id: str
    status: str
    results: Dict[str, List[Dict]]


# Application lifecycle
@app.on_event("startup")
async def startup_event():
    """Initialize application components."""
    await job_manager.start()
    logger.info("PSD Character Extractor web interface started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup application components."""
    await job_manager.stop()
    extractor.close()
    logger.info("PSD Character Extractor web interface stopped")


# Web interface routes
@app.get("/")
async def index(request: Request):
    """Serve the main web interface."""
    return templates.TemplateResponse("index.html", {"request": request})


# API routes
@app.post("/api/upload", response_model=JobResponse)
async def upload_psd(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PSD file to process")
):
    """
    Upload a PSD file and start processing.

    Args:
        file: PSD file upload

    Returns:
        Job information with job_id for tracking progress
    """
    # Validate file
    if not file.filename or not file.filename.lower().endswith('.psd'):
        raise HTTPException(status_code=400, detail="Only PSD files are allowed")

    try:
        # Read file content
        file_content = await file.read()

        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # Create job
        job_id = await job_manager.create_job(file.filename, file_content)

        # Start background processing
        background_tasks.add_task(process_psd_analysis, job_id)

        return JobResponse(
            job_id=job_id,
            status=JobStatus.PENDING.value,
            progress=0.0,
            message=f"File {file.filename} uploaded successfully"
        )

    except Exception as e:
        logger.error(f"Failed to upload file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/job/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """
    Get job status and progress.

    Args:
        job_id: Job identifier

    Returns:
        Current job status and progress
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        job_id=job.id,
        status=job.status.value,
        progress=job.progress,
        message=job.error_message
    )


@app.get("/api/analyze/{job_id}", response_model=AnalysisResponse)
async def get_analysis_results(job_id: str):
    """
    Get PSD analysis results and mapping suggestions.

    Args:
        job_id: Job identifier

    Returns:
        Analysis results with mapping suggestions
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status not in [JobStatus.READY_FOR_MAPPING, JobStatus.COMPLETED]:
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not ready. Current status: {job.status.value}"
        )

    return AnalysisResponse(
        job_id=job.id,
        status=job.status.value,
        psd_info=job.analysis_result.get('basic_info', {}) if job.analysis_result else {},
        available_expressions=job.available_expressions or [],
        mapping_suggestions=job.mapping_suggestions or {},
        current_mapping=job.current_mapping or {}
    )


@app.post("/api/mapping/{job_id}", response_model=JobResponse)
async def update_mapping(job_id: str, mapping_update: MappingUpdate):
    """
    Update expression mapping for a job.

    Args:
        job_id: Job identifier
        mapping_update: New mapping configuration

    Returns:
        Updated job status
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.READY_FOR_MAPPING:
        raise HTTPException(
            status_code=400,
            detail=f"Job not ready for mapping updates. Current status: {job.status.value}"
        )

    # Update mapping
    success = await job_manager.update_mapping(job_id, mapping_update.mapping)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update mapping")

    return JobResponse(
        job_id=job.id,
        status=job.status.value,
        progress=job.progress,
        message="Mapping updated successfully"
    )


@app.post("/api/extract/{job_id}", response_model=JobResponse)
async def start_extraction(
    job_id: str,
    background_tasks: BackgroundTasks
):
    """
    Start expression extraction with current mapping.

    Args:
        job_id: Job identifier

    Returns:
        Job status indicating extraction has started
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.READY_FOR_MAPPING:
        raise HTTPException(
            status_code=400,
            detail=f"Job not ready for extraction. Current status: {job.status.value}"
        )

    if not job.current_mapping:
        raise HTTPException(status_code=400, detail="No mapping configured")

    # Start background extraction
    background_tasks.add_task(process_extraction, job_id)

    # Update job status
    await job_manager.update_job_status(job_id, JobStatus.EXTRACTING, progress=50.0)

    return JobResponse(
        job_id=job.id,
        status=JobStatus.EXTRACTING.value,
        progress=50.0,
        message="Extraction started"
    )


@app.get("/api/results/{job_id}", response_model=ExtractionResponse)
async def get_extraction_results(job_id: str):
    """
    Get extraction results.

    Args:
        job_id: Job identifier

    Returns:
        Extraction results with file information
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Extraction not completed. Current status: {job.status.value}"
        )

    return ExtractionResponse(
        job_id=job.id,
        status=job.status.value,
        results=job.extraction_result or {}
    )


@app.get("/api/download/{job_id}")
async def download_results(job_id: str):
    """
    Download extraction results as a ZIP file.

    Args:
        job_id: Job identifier

    Returns:
        ZIP file containing extracted expressions
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Extraction not completed. Current status: {job.status.value}"
        )

    # Create download archive
    archive_path = await job_manager.create_download_archive(job_id)
    if not archive_path or not Path(archive_path).exists():
        raise HTTPException(status_code=500, detail="Failed to create download archive")

    return FileResponse(
        path=archive_path,
        filename=f"expressions_{job.psd_filename}_{job_id[:8]}.zip",
        media_type="application/zip"
    )


# Background processing functions
async def process_psd_analysis(job_id: str):
    """Process PSD analysis in the background."""
    try:
        # Update status
        await job_manager.update_job_status(job_id, JobStatus.ANALYZING, progress=10.0)

        # Get job
        job = await job_manager.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found for analysis")
            return

        # Perform analysis
        logger.info(f"Starting analysis for job {job_id}")

        # Get analysis results
        analysis_result = await extractor.analyze_psd(job.psd_path)
        available_expressions = await extractor.get_available_expressions(job.psd_path)
        mapping_suggestions = await extractor.create_mapping_suggestions(job.psd_path)

        # Update job with results
        await job_manager.set_analysis_result(
            job_id,
            analysis_result,
            available_expressions,
            mapping_suggestions
        )

        logger.info(f"Analysis completed for job {job_id}")

    except Exception as e:
        logger.error(f"Analysis failed for job {job_id}: {e}")
        await job_manager.update_job_status(
            job_id,
            JobStatus.FAILED,
            error_message=f"Analysis failed: {str(e)}"
        )


async def process_extraction(job_id: str):
    """Process expression extraction in the background."""
    try:
        # Get job
        job = await job_manager.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found for extraction")
            return

        # Update status
        await job_manager.update_job_status(job_id, JobStatus.EXTRACTING, progress=60.0)

        logger.info(f"Starting extraction for job {job_id}")

        # Perform extraction
        extraction_result = await extractor.extract_expressions(
            job.psd_path,
            job.current_mapping,
            job.output_dir
        )

        # Update job with results
        await job_manager.set_extraction_result(job_id, extraction_result)

        logger.info(f"Extraction completed for job {job_id}")

    except Exception as e:
        logger.error(f"Extraction failed for job {job_id}: {e}")
        await job_manager.update_job_status(
            job_id,
            JobStatus.FAILED,
            error_message=f"Extraction failed: {str(e)}"
        )


# Debug/monitoring endpoints
@app.get("/api/debug/jobs")
async def list_jobs():
    """List all jobs for debugging (development only)."""
    return await job_manager.get_job_list()


def main():
    """Main entry point for the web application."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()