from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from models.user import UserUpdate, UserResponse, CV
from models.job import Application, Job
from routers.auth import get_current_user
import cloudinary.uploader
from datetime import datetime
from bson import ObjectId
from database import get_user_collection, get_job_collection, get_application_collection

router = APIRouter()


@router.get("/me")
async def get_current_user_profile(current_user: UserResponse = Depends(get_current_user)):
    return current_user


@router.put("/me")
async def update_profile(
        user_update: UserUpdate,
        current_user: UserResponse = Depends(get_current_user)
):
    users_collection = await get_user_collection()
    update_data = user_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()

    result = await users_collection.update_one(
        {"_id": ObjectId(current_user.id)},
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
        current_user: UserResponse = Depends(get_current_user)
):
    users_collection = await get_user_collection()
    cv_dict = cv.dict(exclude_unset=True)

    result = await users_collection.update_one(
        {"_id": ObjectId(current_user.id)},
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
        current_user: UserResponse = Depends(get_current_user)
):
    users_collection = await get_user_collection()

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
        # First check if cv field exists
        user_doc = await users_collection.find_one({"_id": ObjectId(current_user.id)})

        if "cv" in user_doc:
            # CV field exists, update the cv_url
            update_result = await users_collection.update_one(
                {"_id": ObjectId(current_user.id)},
                {
                    "$set": {
                        "cv.cv_url": result["secure_url"],
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        else:
            # CV field doesn't exist, create it with cv_url
            update_result = await users_collection.update_one(
                {"_id": ObjectId(current_user.id)},
                {
                    "$set": {
                        "cv": {"cv_url": result["secure_url"]},
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
async def get_my_applications(current_user: UserResponse = Depends(get_current_user)):
    applications_collection = await get_application_collection()
    jobs_collection = await get_job_collection()

    applications_cursor = applications_collection.find({"user_id": current_user.id})
    applications_list = []

    async for app in applications_cursor:
        # Convert MongoDB _id to string id
        app_dict = {**app, "id": str(app["_id"])}
        del app_dict["_id"]

        # Get job details for each application
        try:
            job = await jobs_collection.find_one({"_id": ObjectId(app["job_id"])})
            if job:
                app_dict["job"] = {
                    "title": job["title"],
                    "company": job["company"],
                    "logo_url": job.get("logo_url")
                }
        except Exception as e:
            # If job can't be found, just continue
            app_dict["job"] = {"title": "Unknown", "company": "Unknown"}

        applications_list.append(app_dict)

    return applications_list