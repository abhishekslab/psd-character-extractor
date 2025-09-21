"""
FastAPI Web Application for PSD Character Extractor

Provides a REST API and web interface for uploading PSD files,
analyzing expressions, mapping them to lip sync states, and downloading results.
"""

import asyncio
import base64
import io
import logging
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from pydantic import BaseModel
from PIL import Image
from psd_tools import PSDImage

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


@app.get("/api/preview/{job_id}/composite")
async def get_composite_preview(job_id: str, thumbnail: bool = True):
    """
    Get composite preview image of the PSD file.

    Args:
        job_id: Job identifier
        thumbnail: Whether to return a thumbnail (256x256) or full size

    Returns:
        PNG image of the PSD composite
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not Path(job.psd_path).exists():
        raise HTTPException(status_code=404, detail="PSD file not found")

    try:
        # Generate preview image
        image_bytes = await generate_composite_preview(job.psd_path, thumbnail)

        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=3600",
                "Content-Disposition": f"inline; filename=\"{job_id}_composite.png\""
            }
        )

    except Exception as e:
        logger.error(f"Failed to generate composite preview for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")


@app.get("/api/preview/{job_id}/expression/{expression_name}")
async def get_expression_preview(job_id: str, expression_name: str, thumbnail: bool = True):
    """
    Get preview image of a specific expression.

    Args:
        job_id: Job identifier
        expression_name: Name of the expression layer to preview
        thumbnail: Whether to return a thumbnail (256x256) or full size

    Returns:
        PNG image of the expression preview
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not Path(job.psd_path).exists():
        raise HTTPException(status_code=404, detail="PSD file not found")

    # Check if expression exists in available expressions
    if not job.available_expressions or expression_name not in job.available_expressions:
        raise HTTPException(status_code=404, detail=f"Expression '{expression_name}' not found")

    try:
        # Generate expression preview image
        image_bytes = await generate_expression_preview(job.psd_path, expression_name, thumbnail)

        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=3600",
                "Content-Disposition": f"inline; filename=\"{job_id}_{expression_name}.png\""
            }
        )

    except Exception as e:
        logger.error(f"Failed to generate expression preview for {expression_name} in job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate expression preview: {str(e)}")


# Utility functions for image processing
async def generate_composite_preview(psd_path: str, thumbnail: bool = True) -> bytes:
    """
    Generate composite preview image from PSD file.

    Args:
        psd_path: Path to the PSD file
        thumbnail: Whether to generate thumbnail size

    Returns:
        PNG image data as bytes
    """
    loop = asyncio.get_event_loop()

    def _generate_preview():
        try:
            # Load PSD and create composite
            psd = PSDImage.open(psd_path)
            composite = psd.composite()

            # Convert to RGB if needed for better compatibility
            if composite.mode not in ('RGB', 'RGBA'):
                composite = composite.convert('RGBA')

            # Generate thumbnail if requested
            if thumbnail:
                composite.thumbnail((256, 256), Image.Resampling.LANCZOS)

            # Save to bytes
            img_buffer = io.BytesIO()
            composite.save(img_buffer, format='PNG', optimize=True)
            return img_buffer.getvalue()

        except Exception as e:
            logger.error(f"Error generating preview for {psd_path}: {e}")
            raise

    return await loop.run_in_executor(None, _generate_preview)


async def generate_expression_preview(psd_path: str, expression_name: str, thumbnail: bool = True) -> bytes:
    """
    Generate preview image for a specific expression.

    Args:
        psd_path: Path to the PSD file
        expression_name: Name of the expression layer to render
        thumbnail: Whether to generate thumbnail size

    Returns:
        PNG image data as bytes
    """
    loop = asyncio.get_event_loop()

    def _generate_expression_preview():
        try:
            # Load PSD
            psd = PSDImage.open(psd_path)

            # Find the target expression layer specifically in the Expression group
            target_layer = None
            original_visibility = {}

            def find_expression_layer(layers, target_name):
                for layer in layers:
                    if hasattr(layer, 'name') and layer.name == 'Expression' and hasattr(layer, '__iter__'):
                        # Found the Expression group, look for the target within it
                        try:
                            for expr_layer in layer:
                                if hasattr(expr_layer, 'name') and expr_layer.name == target_name:
                                    return expr_layer
                        except:
                            pass
                    elif hasattr(layer, '__iter__'):
                        # Recursively search other groups
                        try:
                            found = find_expression_layer(layer, target_name)
                            if found:
                                return found
                        except:
                            pass
                return None

            target_layer = find_expression_layer(psd, expression_name)

            if not target_layer:
                raise ValueError(f"Expression layer '{expression_name}' not found in Expression group")

            # Find the Expression group and manage visibility within it
            def manage_layer_visibility(layers, target_layer_name):
                for layer in layers:
                    if hasattr(layer, 'name') and hasattr(layer, 'visible'):
                        # Save original state
                        original_visibility[layer.name] = layer.visible

                        # Check if this is the Expression group
                        if layer.name == 'Expression' and hasattr(layer, '__iter__'):
                            # This is the Expression group, manage child layers
                            try:
                                for expr_layer in layer:
                                    if hasattr(expr_layer, 'name') and hasattr(expr_layer, 'visible'):
                                        # Save original state
                                        original_visibility[expr_layer.name] = expr_layer.visible

                                        # Show only the target expression, hide all others
                                        if expr_layer.name == target_layer_name:
                                            expr_layer.visible = True
                                        else:
                                            expr_layer.visible = False
                            except Exception as e:
                                logger.warning(f"Failed to process Expression group: {e}")

                    # Recursively handle other group layers
                    if hasattr(layer, '__iter__') and layer.name != 'Expression':
                        try:
                            manage_layer_visibility(layer, target_layer_name)
                        except:
                            pass

            try:
                # Manage layer visibility
                manage_layer_visibility(psd, target_layer.name)

                # Generate composite
                composite = psd.composite()

                # Convert to RGB if needed for better compatibility
                if composite.mode not in ('RGB', 'RGBA'):
                    composite = composite.convert('RGBA')

                # Generate thumbnail if requested
                if thumbnail:
                    composite.thumbnail((256, 256), Image.Resampling.LANCZOS)

                # Save to bytes
                img_buffer = io.BytesIO()
                composite.save(img_buffer, format='PNG', optimize=True)
                return img_buffer.getvalue()

            finally:
                # Restore original visibility states
                def restore_visibility(layers):
                    for layer in layers:
                        if hasattr(layer, 'name') and layer.name in original_visibility:
                            layer.visible = original_visibility[layer.name]
                        if hasattr(layer, '__iter__'):
                            try:
                                restore_visibility(layer)
                            except:
                                pass

                restore_visibility(psd)

        except Exception as e:
            logger.error(f"Error generating expression preview for {expression_name}: {e}")
            raise

    return await loop.run_in_executor(None, _generate_expression_preview)


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