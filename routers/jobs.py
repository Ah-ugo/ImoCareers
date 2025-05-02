from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from models.job import JobCreate, JobUpdate, Job, Application
from models.user import User, UserResponse
from routers.auth import get_current_user
from utils.ai import ai_helper
import cloudinary.uploader
from datetime import datetime
from bson import ObjectId
from database import get_job_collection, get_application_collection, get_user_collection

router = APIRouter()


@router.get("/")
async def get_jobs(
        search: Optional[str] = None,
        location: Optional[str] = None,
        type: Optional[str] = None,
        tags: Optional[List[str]] = None
):
    # Get collection
    jobs_collection = await get_job_collection()

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

    # Get jobs from database
    jobs_cursor = jobs_collection.find(query)
    jobs_list = []

    # Convert MongoDB documents to Job models
    async for job in jobs_cursor:
        job_dict = {**job, "id": str(job["_id"])}
        del job_dict["_id"]
        jobs_list.append(Job(**job_dict))

    return jobs_list


@router.get("/{job_id}")
async def get_job(job_id: str):
    jobs_collection = await get_job_collection()

    try:
        job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format"
        )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Convert MongoDB document to Job model
    job_dict = {**job, "id": str(job["_id"])}
    del job_dict["_id"]

    return Job(**job_dict)


# @router.post("/apply/{job_id}")
# async def apply_for_job(
#         job_id: str,
#         application: Application,
#         current_user: UserResponse = Depends(get_current_user)
# ):
#     jobs_collection = await get_job_collection()
#     applications_collection = await get_application_collection()
#
#     # Check if job exists
#     try:
#         job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
#     except Exception:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid job ID format"
#         )
#
#     if not job:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Job not found"
#         )
#
#     # Convert job for AI helper
#     job_dict = {**job, "id": str(job["_id"])}
#     del job_dict["_id"]
#     job_model = Job(**job_dict)
#
#     # Check if already applied
#     existing_application = await applications_collection.find_one({
#         "job_id": job_id,
#         "user_id": current_user.id
#     })
#
#     if existing_application:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Already applied for this job"
#         )
#
#     # Generate cover letter if not provided
#     if not application.cover_letter:
#         application.cover_letter = await ai_helper.generate_cover_letter(
#             job_model,
#             current_user
#         )
#
#     # Create application
#     application_dict = application.dict()
#     application_dict["user_id"] = current_user.id
#     application_dict["job_id"] = job_id
#     application_dict["created_at"] = datetime.utcnow()
#     application_dict["updated_at"] = datetime.utcnow()
#
#     # Save application
#     result = await applications_collection.insert_one(application_dict)
#
#     # Update job applications count
#     await jobs_collection.update_one(
#         {"_id": ObjectId(job_id)},
#         {"$inc": {"applications_count": 1}}
#     )
#
#     return {"message": "Application submitted successfully", "application_id": str(result.inserted_id)}

@router.post("/apply/{job_id}")
async def apply_for_job(
        job_id: str,
        application: Application,
        generate_cover_letter: bool = False,
        current_user: UserResponse = Depends(get_current_user)
):
    # Validate job
    jobs_collection = await get_job_collection()
    applications_collection = await get_application_collection()

    try:
        job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
    except Exception:
        raise HTTPException(400, "Invalid job ID")

    if not job or not job.get("is_active"):
        raise HTTPException(404, "Job not available")

    # Get user's CV
    users_collection = await get_user_collection()
    user = await users_collection.find_one(
        {"_id": ObjectId(current_user.id)},
        {"cv": 1}
    )

    if not user.get("cv", {}).get("cv_url"):
        raise HTTPException(400, "Complete your CV before applying")

    # Convert job to model
    job_dict = {**job, "id": str(job["_id"])}
    del job_dict["_id"]
    job_model = Job(**job_dict)

    # Handle cover letter generation
    if generate_cover_letter or not application.cover_letter:
        try:
            application.cover_letter = await ai_helper.generate_cover_letter(
                job_model,
                current_user,
                user["cv"]
            )
        except Exception as e:
            raise HTTPException(500, f"Cover letter generation failed: {str(e)}")

    # Create application document
    application_dict = application.dict()
    application_dict.update({
        "user_id": current_user.id,
        "job_id": job_id,
        "cv_url": user["cv"]["cv_url"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    # Save application
    try:
        result = await applications_collection.insert_one(application_dict)
    except Exception as e:
        raise HTTPException(500, "Application submission failed")

    # Update applications count
    await jobs_collection.update_one(
        {"_id": ObjectId(job_id)},
        {"$inc": {"applications_count": 1}}
    )

    return {
        "message": "Application submitted",
        "application_id": str(result.inserted_id),
        "cv_url": application_dict["cv_url"],
        "cover_letter": application.cover_letter[:100] + "..."  # Preview snippet
    }


@router.post("/{job_id}/preview-cover-letter")
async def preview_cover_letter(
        job_id: str,
        current_user: UserResponse = Depends(get_current_user)
):
    # Validate job
    jobs_collection = await get_job_collection()

    try:
        job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
    except Exception:
        raise HTTPException(400, "Invalid job ID")

    if not job:
        raise HTTPException(404, "Job not found")

    # Get user's CV data
    users_collection = await get_user_collection()
    user = await users_collection.find_one(
        {"_id": ObjectId(current_user.id)},
        {"cv": 1}
    )

    # Convert job to model
    job_dict = {**job, "id": str(job["_id"])}
    del job_dict["_id"]
    job_model = Job(**job_dict)

    # Generate cover letter
    try:
        cover_letter = await ai_helper.generate_cover_letter(
            job_model,
            current_user,
            user.get("cv", {})
        )
    except Exception as e:
        raise HTTPException(500, f"Generation failed: {str(e)}")

    return {
        "cover_letter": cover_letter,
        "job_title": job["title"],
        "company": job["company"]
    }