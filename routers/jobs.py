from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from models.job import JobCreate, JobUpdate, Job, Application
from models.user import User
from routers.auth import get_current_user
from utils.ai import ai_helper
from datetime import datetime
from bson import ObjectId

router = APIRouter()


@router.get("/")
async def get_jobs(
        search: Optional[str] = None,
        location: Optional[str] = None,
        type: Optional[str] = None,
        tags: Optional[List[str]] = None
):
    # Build query
    query = {"is_active": True}
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"company": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    if location:
        query["location"] = location
    if type:
        query["type"] = type
    if tags:
        query["tags"] = {"$in": tags}

    # Get jobs
    jobs = await Job.find(query).to_list(None)
    return jobs


@router.get("/{job_id}")
async def get_job(job_id: str):
    job = await Job.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return job


@router.post("/apply/{job_id}")
async def apply_for_job(
        job_id: str,
        application: Application,
        current_user: User = Depends(get_current_user)
):
    # Check if job exists
    job = await Job.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Check if already applied
    existing_application = await Application.find_one({
        "job_id": job_id,
        "user_id": str(current_user["_id"])
    })
    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already applied for this job"
        )

    # Generate cover letter if not provided
    if not application.cover_letter:
        application.cover_letter = await ai_helper.generate_cover_letter(
            job,
            current_user
        )

    # Create application
    application_dict = application.dict()
    application_dict["user_id"] = str(current_user["_id"])
    application_dict["created_at"] = datetime.utcnow()

    # Save application
    await Application.insert_one(application_dict)

    # Update job applications count
    await Job.update_one(
        {"_id": ObjectId(job_id)},
        {"$inc": {"applications_count": 1}}
    )

    return {"message": "Application submitted successfully"}