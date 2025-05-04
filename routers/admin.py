from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from typing import List
from models.job import JobCreate, JobUpdate, Job, Application
from models.user import User
from routers.auth import get_current_user
import cloudinary.uploader
from datetime import datetime
from bson import ObjectId
from database import get_job_collection

router = APIRouter()


# async def get_admin_user(current_user: User = Depends(get_current_user)):
#     if current_user["role"] != "admin":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not authorized"
#         )
#     return current_user
async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":  # Changed from ["role"] to .role
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    return current_user


@router.post("/jobs")
async def create_job(
        job: JobCreate,
        current_user: User = Depends(get_admin_user)
):
    jobs_collection = await get_job_collection()  # Get the collection
    job_dict = job.dict()
    job_dict["created_at"] = datetime.utcnow()
    job_dict["updated_at"] = datetime.utcnow()
    job_dict["is_active"] = True  # Add default fields if needed
    job_dict["applications_count"] = 0

    result = await jobs_collection.insert_one(job_dict)  # Use the collection
    return {"id": str(result.inserted_id)}


@router.put("/jobs/{job_id}")
async def update_job(
        job_id: str,
        job: JobUpdate,
        current_user: User = Depends(get_admin_user)
):
    jobs_collection = await get_job_collection()
    job_dict = job.dict(exclude_unset=True)
    job_dict["updated_at"] = datetime.utcnow()

    result = await jobs_collection.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": job_dict}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return {"message": "Job updated successfully"}


@router.delete("/jobs/{job_id}")
async def delete_job(
        job_id: str,
        current_user: User = Depends(get_admin_user)
):
    jobs_collection = await get_job_collection()
    result = await jobs_collection.delete_one({"_id": ObjectId(job_id)})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return {"message": "Job deleted successfully"}


@router.post("/upload/logo")
async def upload_logo(
        file: UploadFile = File(...),
        current_user: User = Depends(get_admin_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="company_logos",
            allowed_formats=["jpg", "png", "jpeg"]
        )
        return {"url": result["secure_url"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/applications/{job_id}")
async def get_applications(
        job_id: str,
        current_user: User = Depends(get_admin_user)
):
    applications = await Application.find(
        {"job_id": job_id}
    ).to_list(None)

    # Get user details for each application
    for app in applications:
        user = await User.find_one({"_id": ObjectId(app["user_id"])})
        app["user"] = {
            "name": user["name"],
            "email": user["email"],
            "photo_url": user.get("photo_url")
        }

    return applications