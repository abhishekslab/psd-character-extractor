"""
Job Management System for Web Interface

Handles background processing jobs, status tracking, and file management
for the PSD Character Extractor web interface.
"""

import asyncio
import logging
import shutil
import tempfile
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    READY_FOR_MAPPING = "ready_for_mapping"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    """Job data structure."""
    id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    psd_filename: str
    psd_path: str
    output_dir: str
    analysis_result: Optional[Dict] = None
    available_expressions: Optional[List[str]] = None
    mapping_suggestions: Optional[Dict] = None
    current_mapping: Optional[Dict] = None
    extraction_result: Optional[Dict] = None
    error_message: Optional[str] = None
    progress: float = 0.0

    def to_dict(self) -> Dict:
        """Convert job to dictionary for JSON serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data


class JobManager:
    """Manages background processing jobs."""

    def __init__(self, upload_dir: str = "web/uploads", cleanup_hours: int = 24):
        """
        Initialize job manager.

        Args:
            upload_dir: Directory for uploaded files and temporary data
            cleanup_hours: Hours to keep job data before cleanup
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        self.cleanup_hours = cleanup_hours
        self.jobs: Dict[str, Job] = {}
        self._lock = asyncio.Lock()

        # Start cleanup task
        self._cleanup_task = None

    async def start(self):
        """Start background tasks."""
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def stop(self):
        """Stop background tasks and cleanup."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    def generate_job_id(self) -> str:
        """Generate unique job ID."""
        return str(uuid.uuid4())

    async def create_job(self, psd_filename: str, psd_data: bytes) -> str:
        """
        Create a new processing job.

        Args:
            psd_filename: Original filename of the PSD file
            psd_data: PSD file content

        Returns:
            Job ID string
        """
        async with self._lock:
            job_id = self.generate_job_id()

            # Create job directory
            job_dir = self.upload_dir / job_id
            job_dir.mkdir(parents=True, exist_ok=True)

            # Save PSD file
            psd_path = job_dir / "input.psd"
            psd_path.write_bytes(psd_data)

            # Create output directory
            output_dir = job_dir / "output"
            output_dir.mkdir(exist_ok=True)

            # Create job
            job = Job(
                id=job_id,
                status=JobStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                psd_filename=psd_filename,
                psd_path=str(psd_path),
                output_dir=str(output_dir)
            )

            self.jobs[job_id] = job
            logger.info(f"Created job {job_id} for file {psd_filename}")

            return job_id

    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        async with self._lock:
            return self.jobs.get(job_id)

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        progress: Optional[float] = None,
        error_message: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Update job status and additional data.

        Args:
            job_id: Job identifier
            status: New status
            progress: Progress percentage (0.0 to 100.0)
            error_message: Error message if status is FAILED
            **kwargs: Additional job data to update

        Returns:
            True if job was updated, False if job not found
        """
        async with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return False

            job.status = status
            job.updated_at = datetime.now()

            if progress is not None:
                job.progress = max(0.0, min(100.0, progress))

            if error_message:
                job.error_message = error_message

            # Update additional data
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)

            logger.info(f"Updated job {job_id} status to {status.value}")
            return True

    async def set_analysis_result(
        self,
        job_id: str,
        analysis_result: Dict,
        available_expressions: List[str],
        mapping_suggestions: Dict
    ) -> bool:
        """Set analysis results for a job."""
        return await self.update_job_status(
            job_id,
            JobStatus.READY_FOR_MAPPING,
            progress=25.0,
            analysis_result=analysis_result,
            available_expressions=available_expressions,
            mapping_suggestions=mapping_suggestions,
            current_mapping=mapping_suggestions
        )

    async def update_mapping(self, job_id: str, mapping: Dict) -> bool:
        """Update expression mapping for a job."""
        async with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return False

            job.current_mapping = mapping
            job.updated_at = datetime.now()
            logger.info(f"Updated mapping for job {job_id}")
            return True

    async def set_extraction_result(self, job_id: str, extraction_result: Dict) -> bool:
        """Set extraction results for a job."""
        return await self.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            progress=100.0,
            extraction_result=extraction_result
        )

    async def get_job_file_path(self, job_id: str) -> Optional[str]:
        """Get the PSD file path for a job."""
        job = await self.get_job(job_id)
        if job and Path(job.psd_path).exists():
            return job.psd_path
        return None

    async def get_job_output_dir(self, job_id: str) -> Optional[str]:
        """Get the output directory for a job."""
        job = await self.get_job(job_id)
        if job and Path(job.output_dir).exists():
            return job.output_dir
        return None

    async def create_download_archive(self, job_id: str) -> Optional[str]:
        """
        Create a ZIP archive of extracted expressions.

        Args:
            job_id: Job identifier

        Returns:
            Path to the created ZIP file, or None if failed
        """
        job = await self.get_job(job_id)
        if not job or job.status != JobStatus.COMPLETED:
            return None

        try:
            job_dir = Path(job.output_dir).parent
            archive_path = job_dir / f"extracted_expressions_{job_id}.zip"

            # Create ZIP archive
            shutil.make_archive(
                str(archive_path.with_suffix("")),
                'zip',
                job.output_dir
            )

            logger.info(f"Created archive for job {job_id}: {archive_path}")
            return str(archive_path)

        except Exception as e:
            logger.error(f"Failed to create archive for job {job_id}: {e}")
            return None

    async def delete_job(self, job_id: str) -> bool:
        """
        Delete a job and its associated files.

        Args:
            job_id: Job identifier

        Returns:
            True if job was deleted, False if job not found
        """
        async with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return False

            # Remove job directory
            job_dir = Path(job.psd_path).parent
            try:
                shutil.rmtree(job_dir)
                logger.info(f"Deleted job directory: {job_dir}")
            except Exception as e:
                logger.warning(f"Failed to delete job directory {job_dir}: {e}")

            # Remove from jobs dict
            del self.jobs[job_id]
            logger.info(f"Deleted job {job_id}")
            return True

    async def _periodic_cleanup(self):
        """Periodically clean up old jobs."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._cleanup_old_jobs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")

    async def _cleanup_old_jobs(self):
        """Clean up jobs older than cleanup_hours."""
        cutoff_time = datetime.now() - timedelta(hours=self.cleanup_hours)

        jobs_to_delete = []
        async with self._lock:
            for job_id, job in self.jobs.items():
                if job.updated_at < cutoff_time:
                    jobs_to_delete.append(job_id)

        for job_id in jobs_to_delete:
            await self.delete_job(job_id)

        if jobs_to_delete:
            logger.info(f"Cleaned up {len(jobs_to_delete)} old jobs")

    async def get_job_list(self) -> List[Dict]:
        """Get list of all jobs for debugging/monitoring."""
        async with self._lock:
            return [job.to_dict() for job in self.jobs.values()]