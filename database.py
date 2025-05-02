from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
db = client.imo_career_hub

# Collections
users = db.users
jobs = db.jobs
applications = db.applications


async def get_user_collection():
    return users


async def get_job_collection():
    return jobs


async def get_application_collection():
    return applications


# Indexes
async def setup_indexes():
    # Users collection indexes
    await users.create_index("email", unique=True)
    await users.create_index("role")

    # Jobs collection indexes
    await jobs.create_index([("title", "text"), ("company", "text"), ("description", "text")])
    await jobs.create_index("location")
    await jobs.create_index("type")
    await jobs.create_index("tags")
    await jobs.create_index("created_at")

    # Applications collection indexes
    await applications.create_index([("job_id", 1), ("user_id", 1)], unique=True)
    await applications.create_index("status")
    await applications.create_index("created_at")


# Initialize database
async def init_db():
    try:
        await setup_indexes()
        print("Database indexes created successfully!")
    except Exception as e:
        print(f"Error setting up database indexes: {e}")