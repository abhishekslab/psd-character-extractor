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

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.requests import Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
from psd_tools import PSDImage
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
    all_components: Dict[str, List[Dict]]
    component_statistics: Dict[str, Dict]
    extractable_components: List[Dict]


class MappingUpdate(BaseModel):
    """Request model for mapping updates."""

    mapping: Dict[str, List[str]]


class ExtractionResponse(BaseModel):
    """Response model for extraction results."""

    job_id: str
    status: str
    results: Dict[str, List[Dict]]


class RawLayersResponse(BaseModel):
    """Response model for raw layers."""

    job_id: str
    status: str
    raw_layers: List[Dict]


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
    file: UploadFile = File(..., description="PSD file to process"),
):
    """
    Upload a PSD file and start processing.

    Args:
        file: PSD file upload

    Returns:
        Job information with job_id for tracking progress
    """
    # Validate file
    if not file.filename or not file.filename.lower().endswith(".psd"):
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
            message=f"File {file.filename} uploaded successfully",
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
        message=job.error_message,
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
            detail=f"Analysis not ready. Current status: {job.status.value}",
        )

    # Get component data from analysis result
    analysis_result = job.analysis_result or {}
    component_analysis = analysis_result.get("component_analysis", {})

    # Clean component data for serialization (remove layer_object references)
    cleaned_components = {}
    component_stats = {}
    extractable_components = []

    for category, components in component_analysis.items():
        cleaned_category_components = []
        extractable_count = 0

        for comp in components:
            # Create clean component data without layer_object
            clean_comp = {
                "name": comp["name"],
                "visible": comp.get("visible", False),
                "type": comp.get("type", "LAYER"),
                "width": comp.get("width", 0),
                "height": comp.get("height", 0),
                "x": comp.get("x", 0),
                "y": comp.get("y", 0),
            }

            # Add children_count for groups
            if comp.get("type") == "GROUP":
                clean_comp["children_count"] = comp.get("children_count", 0)

            cleaned_category_components.append(clean_comp)

            # Count extractable components
            if comp.get("type") == "LAYER":
                extractable_count += 1
                extractable_components.append(
                    {
                        "name": comp["name"],
                        "category": category,
                        "visible": comp.get("visible", False),
                        "dimensions": {
                            "width": comp.get("width", 0),
                            "height": comp.get("height", 0),
                            "x": comp.get("x", 0),
                            "y": comp.get("y", 0),
                        },
                    }
                )

        cleaned_components[category] = cleaned_category_components

        if extractable_count > 0:
            component_stats[category] = {
                "total": len(components),
                "extractable": extractable_count,
                "components": [
                    c["name"] for c in components if c.get("type") == "LAYER"
                ],
            }

    return AnalysisResponse(
        job_id=job.id,
        status=job.status.value,
        psd_info=analysis_result.get("basic_info", {}),
        available_expressions=job.available_expressions or [],
        mapping_suggestions=job.mapping_suggestions or {},
        current_mapping=job.current_mapping or {},
        all_components=cleaned_components,
        component_statistics=component_stats,
        extractable_components=extractable_components,
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
            detail=f"Job not ready for mapping updates. Current status: {job.status.value}",
        )

    # Update mapping
    success = await job_manager.update_mapping(job_id, mapping_update.mapping)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update mapping")

    return JobResponse(
        job_id=job.id,
        status=job.status.value,
        progress=job.progress,
        message="Mapping updated successfully",
    )


@app.post("/api/extract/{job_id}", response_model=JobResponse)
async def start_extraction(job_id: str, background_tasks: BackgroundTasks):
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
            detail=f"Job not ready for extraction. Current status: {job.status.value}",
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
        message="Extraction started",
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
            detail=f"Extraction not completed. Current status: {job.status.value}",
        )

    return ExtractionResponse(
        job_id=job.id, status=job.status.value, results=job.extraction_result or {}
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
            detail=f"Extraction not completed. Current status: {job.status.value}",
        )

    # Create download archive
    archive_path = await job_manager.create_download_archive(job_id)
    if not archive_path or not Path(archive_path).exists():
        raise HTTPException(status_code=500, detail="Failed to create download archive")

    return FileResponse(
        path=archive_path,
        filename=f"expressions_{job.psd_filename}_{job_id[:8]}.zip",
        media_type="application/zip",
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
                "Content-Disposition": f'inline; filename="{job_id}_composite.png"',
            },
        )

    except Exception as e:
        logger.error(f"Failed to generate composite preview for job {job_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate preview: {str(e)}"
        )


@app.get("/api/preview/{job_id}/component/{component_name}")
async def get_component_preview(
    job_id: str, component_name: str, thumbnail: bool = True
):
    """
    Get preview image of a specific component (expressions, hair, clothing, etc.).

    Args:
        job_id: Job identifier
        component_name: Name of the component layer to preview
        thumbnail: Whether to return a thumbnail (256x256) or full size

    Returns:
        PNG image of the component preview
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not Path(job.psd_path).exists():
        raise HTTPException(status_code=404, detail="PSD file not found")

    # Check if component exists in available components
    analysis_result = job.analysis_result or {}
    component_analysis = analysis_result.get("component_analysis", {})

    component_found = False
    for category, components in component_analysis.items():
        if any(comp["name"] == component_name for comp in components):
            component_found = True
            break

    if not component_found:
        raise HTTPException(
            status_code=404, detail=f"Component '{component_name}' not found"
        )

    try:
        # Generate component preview image
        image_bytes = await generate_component_preview(
            job.psd_path, component_name, thumbnail
        )

        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=3600",
                "Content-Disposition": f'inline; filename="{job_id}_{component_name}.png"',
            },
        )

    except Exception as e:
        logger.error(
            f"Failed to generate component preview for {component_name} in job {job_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to generate component preview: {str(e)}"
        )


@app.get("/api/raw-layers/{job_id}", response_model=RawLayersResponse)
async def get_raw_layers(job_id: str):
    """
    Get all PSD layers as a flat list without classification.

    Args:
        job_id: Job identifier

    Returns:
        Raw layers list
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status not in [JobStatus.READY_FOR_MAPPING, JobStatus.COMPLETED]:
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not ready. Current status: {job.status.value}",
        )

    if not Path(job.psd_path).exists():
        raise HTTPException(status_code=404, detail="PSD file not found")

    try:
        from .extractor import CharacterExtractor

        # Get raw layers without classification
        extractor = CharacterExtractor(job.psd_path)
        raw_layers = extractor.get_raw_layers()

        # Clean the data for serialization (remove any problematic fields)
        cleaned_layers = []
        for layer in raw_layers:
            cleaned_layer = {
                "name": layer["name"],
                "visible": layer.get("visible", False),
                "type": layer.get("type", "LAYER"),
                "width": layer.get("width", 0),
                "height": layer.get("height", 0),
                "x": layer.get("x", 0),
                "y": layer.get("y", 0),
            }
            cleaned_layers.append(cleaned_layer)

        return RawLayersResponse(
            job_id=job.id, status=job.status.value, raw_layers=cleaned_layers
        )

    except Exception as e:
        logger.error(f"Failed to get raw layers for job {job_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get raw layers: {str(e)}"
        )


@app.get("/api/raw-preview/{job_id}/{layer_name}")
async def get_raw_layer_preview(job_id: str, layer_name: str, thumbnail: bool = True):
    """
    Get preview image of a single layer in complete isolation.

    Args:
        job_id: Job identifier
        layer_name: Name of the layer to preview
        thumbnail: Whether to return a thumbnail (256x256) or full size

    Returns:
        PNG image of the isolated layer
    """
    logger.info(
        f"Raw layer preview requested - Job: {job_id}, Layer: '{layer_name}', Thumbnail: {thumbnail}"
    )

    job = await job_manager.get_job(job_id)
    if not job:
        logger.error(f"Job {job_id} not found for raw layer preview")
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if not Path(job.psd_path).exists():
        logger.error(f"PSD file not found: {job.psd_path}")
        raise HTTPException(status_code=404, detail="PSD file not found")

    # Validate that job is in correct state for preview
    if job.status.value not in ["ready_for_mapping", "completed"]:
        logger.warning(
            f"Job {job_id} not ready for raw layer preview - Status: {job.status.value}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Job not ready for preview. Status: {job.status.value}",
        )

    try:
        # Generate isolated layer preview image
        image_bytes = await generate_raw_layer_preview(
            job.psd_path, layer_name, thumbnail
        )

        if not image_bytes:
            logger.error(
                f"No image data generated for raw layer '{layer_name}' in job {job_id}"
            )
            raise HTTPException(status_code=500, detail="No image data generated")

        logger.info(
            f"Successfully generated raw layer preview - Job: {job_id}, Layer: '{layer_name}', Size: {len(image_bytes)} bytes"
        )

        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",  # Disable caching for debugging
                "Pragma": "no-cache",
                "Expires": "0",
                "Content-Disposition": f'inline; filename="{job_id}_{layer_name}_raw.png"',
            },
        )

    except ValueError as ve:
        logger.error(
            f"Value error generating raw layer preview for {layer_name} in job {job_id}: {ve}"
        )
        raise HTTPException(status_code=400, detail=f"Layer error: {str(ve)}")
    except Exception as e:
        logger.error(
            f"Failed to generate raw layer preview for {layer_name} in job {job_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to generate raw layer preview: {str(e)}"
        )


@app.get("/api/preview/{job_id}/expression/{expression_name}")
async def get_expression_preview(
    job_id: str, expression_name: str, thumbnail: bool = True
):
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
    if (
        not job.available_expressions
        or expression_name not in job.available_expressions
    ):
        raise HTTPException(
            status_code=404, detail=f"Expression '{expression_name}' not found"
        )

    try:
        # Generate expression preview image
        image_bytes = await generate_expression_preview(
            job.psd_path, expression_name, thumbnail
        )

        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=3600",
                "Content-Disposition": f'inline; filename="{job_id}_{expression_name}.png"',
            },
        )

    except Exception as e:
        logger.error(
            f"Failed to generate expression preview for {expression_name} in job {job_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to generate expression preview: {str(e)}"
        )


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
            if composite.mode not in ("RGB", "RGBA"):
                composite = composite.convert("RGBA")

            # Generate thumbnail if requested
            if thumbnail:
                composite.thumbnail((256, 256), Image.Resampling.LANCZOS)

            # Save to bytes
            img_buffer = io.BytesIO()
            composite.save(img_buffer, format="PNG", optimize=True)
            return img_buffer.getvalue()

        except Exception as e:
            logger.error(f"Error generating preview for {psd_path}: {e}")
            raise

    return await loop.run_in_executor(None, _generate_preview)


async def generate_expression_preview(
    psd_path: str, expression_name: str, thumbnail: bool = True
) -> bytes:
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
                    if (
                        hasattr(layer, "name")
                        and layer.name == "Expression"
                        and hasattr(layer, "__iter__")
                    ):
                        # Found the Expression group, look for the target within it
                        try:
                            for expr_layer in layer:
                                if (
                                    hasattr(expr_layer, "name")
                                    and expr_layer.name == target_name
                                ):
                                    return expr_layer
                        except:
                            pass
                    elif hasattr(layer, "__iter__"):
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
                raise ValueError(
                    f"Expression layer '{expression_name}' not found in Expression group"
                )

            # Find the Expression group and manage visibility within it
            def manage_layer_visibility(layers, target_layer_name):
                for layer in layers:
                    if hasattr(layer, "name") and hasattr(layer, "visible"):
                        # Save original state
                        original_visibility[layer.name] = layer.visible

                        # Check if this is the Expression group
                        if layer.name == "Expression" and hasattr(layer, "__iter__"):
                            # This is the Expression group, manage child layers
                            try:
                                for expr_layer in layer:
                                    if hasattr(expr_layer, "name") and hasattr(
                                        expr_layer, "visible"
                                    ):
                                        # Save original state
                                        original_visibility[expr_layer.name] = (
                                            expr_layer.visible
                                        )

                                        # Show only the target expression, hide all others
                                        if expr_layer.name == target_layer_name:
                                            expr_layer.visible = True
                                        else:
                                            expr_layer.visible = False
                            except Exception as e:
                                logger.warning(
                                    f"Failed to process Expression group: {e}"
                                )

                    # Recursively handle other group layers
                    if hasattr(layer, "__iter__") and layer.name != "Expression":
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
                if composite.mode not in ("RGB", "RGBA"):
                    composite = composite.convert("RGBA")

                # Generate thumbnail if requested
                if thumbnail:
                    composite.thumbnail((256, 256), Image.Resampling.LANCZOS)

                # Save to bytes
                img_buffer = io.BytesIO()
                composite.save(img_buffer, format="PNG", optimize=True)
                return img_buffer.getvalue()

            finally:
                # Restore original visibility states
                def restore_visibility(layers):
                    for layer in layers:
                        if hasattr(layer, "name") and layer.name in original_visibility:
                            layer.visible = original_visibility[layer.name]
                        if hasattr(layer, "__iter__"):
                            try:
                                restore_visibility(layer)
                            except:
                                pass

                restore_visibility(psd)

        except Exception as e:
            logger.error(
                f"Error generating expression preview for {expression_name}: {e}"
            )
            raise

    return await loop.run_in_executor(None, _generate_expression_preview)


async def generate_component_preview(
    psd_path: str, component_name: str, thumbnail: bool = True
) -> bytes:
    """
    Generate preview image for a specific component (similar to expression preview but more general).

    Args:
        psd_path: Path to the PSD file
        component_name: Name of the component layer to render
        thumbnail: Whether to generate thumbnail size

    Returns:
        PNG image data as bytes
    """
    loop = asyncio.get_event_loop()

    def _generate_component_preview():
        try:
            from .extractor import CharacterExtractor

            # Use CharacterExtractor to extract the component
            extractor = CharacterExtractor(psd_path)
            component_image = extractor.extract_component(component_name)

            if not component_image:
                raise ValueError(f"Component '{component_name}' could not be extracted")

            # Convert to RGB if needed for better compatibility
            if component_image.mode not in ("RGB", "RGBA"):
                component_image = component_image.convert("RGBA")

            # Generate thumbnail if requested
            if thumbnail:
                component_image.thumbnail((256, 256), Image.Resampling.LANCZOS)

            # Save to bytes
            img_buffer = io.BytesIO()
            component_image.save(img_buffer, format="PNG", optimize=True)
            return img_buffer.getvalue()

        except Exception as e:
            logger.error(
                f"Error generating component preview for {component_name}: {e}"
            )
            raise

    return await loop.run_in_executor(None, _generate_component_preview)


async def generate_raw_layer_preview(
    psd_path: str, layer_name: str, thumbnail: bool = True
) -> bytes:
    """
    Generate preview image for a single layer in complete isolation.

    Args:
        psd_path: Path to the PSD file
        layer_name: Name of the layer to render
        thumbnail: Whether to generate thumbnail size

    Returns:
        PNG image data as bytes
    """
    loop = asyncio.get_event_loop()

    def _generate_raw_layer_preview():
        try:
            from .extractor import CharacterExtractor

            logger.info(
                f"Starting raw layer preview generation for layer: '{layer_name}' in PSD: {psd_path}"
            )

            # Use CharacterExtractor to extract the raw layer
            extractor = CharacterExtractor(psd_path)
            logger.debug(f"CharacterExtractor initialized for raw layer extraction")

            layer_image = extractor.extract_raw_layer(layer_name)
            logger.info(
                f"Raw layer extraction completed for '{layer_name}', image result: {layer_image is not None}"
            )

            if not layer_image:
                logger.error(
                    f"Layer '{layer_name}' could not be extracted - extractor returned None"
                )
                raise ValueError(f"Layer '{layer_name}' could not be extracted")

            # Log image properties for debugging
            logger.debug(
                f"Extracted layer image - Size: {layer_image.size}, Mode: {layer_image.mode}"
            )

            # Convert to RGB if needed for better compatibility
            if layer_image.mode not in ("RGB", "RGBA"):
                logger.debug(f"Converting image from {layer_image.mode} to RGBA")
                layer_image = layer_image.convert("RGBA")

            # Generate thumbnail if requested
            if thumbnail:
                original_size = layer_image.size
                layer_image.thumbnail((256, 256), Image.Resampling.LANCZOS)
                logger.debug(
                    f"Generated thumbnail - Original: {original_size}, Thumbnail: {layer_image.size}"
                )

            # Save to bytes
            img_buffer = io.BytesIO()
            layer_image.save(img_buffer, format="PNG", optimize=True)
            image_bytes = img_buffer.getvalue()
            logger.info(
                f"Raw layer preview generated successfully - Size: {len(image_bytes)} bytes"
            )
            return image_bytes

        except Exception as e:
            logger.error(
                f"Error generating raw layer preview for {layer_name}: {e}",
                exc_info=True,
            )
            raise

    return await loop.run_in_executor(None, _generate_raw_layer_preview)


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
            job_id, analysis_result, available_expressions, mapping_suggestions
        )

        logger.info(f"Analysis completed for job {job_id}")

    except Exception as e:
        logger.error(f"Analysis failed for job {job_id}: {e}")
        await job_manager.update_job_status(
            job_id, JobStatus.FAILED, error_message=f"Analysis failed: {str(e)}"
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
            job.psd_path, job.current_mapping, job.output_dir
        )

        # Update job with results
        await job_manager.set_extraction_result(job_id, extraction_result)

        logger.info(f"Extraction completed for job {job_id}")

    except Exception as e:
        logger.error(f"Extraction failed for job {job_id}: {e}")
        await job_manager.update_job_status(
            job_id, JobStatus.FAILED, error_message=f"Extraction failed: {str(e)}"
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
