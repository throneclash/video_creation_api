"""
Job queue for managing background video processing tasks.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Enum for job statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PUBLISHED = "published"


class Job:
    """Represents a video processing job."""
    
    def __init__(self, job_id: str, template: str, params: Dict[str, Any]):
        """
        Initialize a job.
        
        Args:
            job_id: Unique job identifier
            template: Template type (A, B, or C)
            params: Template parameters
        """
        self.job_id = job_id
        self.template = template
        self.params = params
        self.status = JobStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary."""
        return {
            "job_id": self.job_id,
            "template": self.template,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "result": self.result
        }


class JobQueue:
    """In-memory job queue for managing background tasks."""
    
    def __init__(self):
        """Initialize the job queue."""
        self.jobs: Dict[str, Job] = {}
    
    def add_job(self, job: Job) -> None:
        """
        Add a job to the queue.
        
        Args:
            job: Job object to add
        """
        self.jobs[job.job_id] = job
        logger.info(f"Job {job.job_id} added to queue")
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get a job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job object or None if not found
        """
        return self.jobs.get(job_id)
    
    def update_job_status(self, job_id: str, status: JobStatus, 
                         error: Optional[str] = None, 
                         result: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update job status.
        
        Args:
            job_id: Job identifier
            status: New status
            error: Error message if applicable
            result: Result data if applicable
            
        Returns:
            True if successful, False if job not found
        """
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        job.status = status
        
        if status == JobStatus.PROCESSING and not job.started_at:
            job.started_at = datetime.utcnow()
        
        if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.PUBLISHED]:
            job.completed_at = datetime.utcnow()
        
        if error:
            job.error = error
        
        if result:
            job.result = result
        
        logger.info(f"Job {job_id} status updated to {status.value}")
        return True
    
    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all jobs as dictionaries.
        
        Returns:
            Dictionary of all jobs
        """
        return {job_id: job.to_dict() for job_id, job in self.jobs.items()}
    
    def get_pending_jobs(self) -> list:
        """
        Get all pending jobs.
        
        Returns:
            List of pending jobs
        """
        return [job for job in self.jobs.values() if job.status == JobStatus.PENDING]
    
    def get_processing_jobs(self) -> list:
        """
        Get all processing jobs.
        
        Returns:
            List of processing jobs
        """
        return [job for job in self.jobs.values() if job.status == JobStatus.PROCESSING]


# Global job queue instance
job_queue = JobQueue()
