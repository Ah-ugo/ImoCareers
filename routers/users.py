from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from models.user import UserUpdate, User, CV
from models.job import Application
from routers.auth import get_current_user
import cloudinary.uploader
from datetime import datetime
from bson import ObjectId
from database import JOBS_COLLECTION as Job

router = APIRouter()


@router.get("/me")
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me")
async def update_profile(
        user_update: UserUpdate,
        current_user: User = Depends(get_current_user)
):
    update_data = user_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()

    result = await User.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Update failed"
        )

    return {"message": "Profile updated successfully"}


@router.put("/me/cv")
async def update_cv(
        cv: CV,
        current_user: User = Depends(get_current_user)
):
    cv_dict = cv.dict(exclude_unset=True)

    result = await User.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {
            "$set": {
                "cv": cv_dict,
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Update failed"
        )

    return {"message": "CV updated successfully"}


@router.post("/me/upload-cv")
async def upload_cv(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF"
        )

    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="cvs",
            resource_type="raw"
        )

        # Update user's CV URL
        await User.update_one(
            {"_id": ObjectId(current_user["_id"])},
            {
                "$set": {
                    "cv.cv_url": result["secure_url"],
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return {"url": result["secure_url"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/me/applications")
async def get_my_applications(current_user: User = Depends(get_current_user)):
    applications = await Application.find(
        {"user_id": str(current_user["_id"])}
    ).to_list(None)

    # Get job details for each application
    for app in applications:
        job = await Job.find_one({"_id": ObjectId(app["job_id"])})
        app["job"] = {
            "title": job["title"],
            "company": job["company"],
            "logo_url": job.get("logo_url")
        }

    return applications