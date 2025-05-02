import os
import motor.motor_asyncio
from pymongo import errors
from dotenv import load_dotenv
import logging
from typing import Dict, Any, Optional

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection settings
MONGODB_URI = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "job_board")

# Connection client
client = None
db = None

# Collection names
USERS_COLLECTION = "users"
JOBS_COLLECTION = "jobs"
APPLICATIONS_COLLECTION = "applications"


async def connect_to_mongodb():
    """
    Establishes connection to MongoDB.
    Called at application startup.
    """
    global client, db
    try:
        # Create a connection pool to MongoDB
        client = motor.motor_asyncio.AsyncIOMotorClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=10
        )

        # Verify connection
        await client.server_info()

        # Get database
        db = client[DATABASE_NAME]

        logger.info("Connected to MongoDB successfully")

        # Create indexes for better performance
        await setup_indexes()

    except errors.ServerSelectionTimeoutError:
        logger.error("Failed to connect to MongoDB. Check your connection string.")
        raise
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {str(e)}")
        raise


async def setup_indexes():
    """Creates indexes for better query performance"""
    try:
        # User indexes
        await db[USERS_COLLECTION].create_index("email", unique=True)

        # Job indexes
        await db[JOBS_COLLECTION].create_index("is_active")
        await db[JOBS_COLLECTION].create_index("title")
        await db[JOBS_COLLECTION].create_index("company")
        await db[JOBS_COLLECTION].create_index("location")
        await db[JOBS_COLLECTION].create_index("type")
        await db[JOBS_COLLECTION].create_index("tags")

        # Application indexes
        await db[APPLICATIONS_COLLECTION].create_index([("job_id", 1), ("user_id", 1)], unique=True)

        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error setting up database indexes: {str(e)}")
        raise


async def close_mongodb_connection():
    """
    Closes MongoDB connection.
    Called at application shutdown.
    """
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")


async def get_database():
    """
    Returns database instance.
    Ensures connection is established.
    """
    global db
    if not db:
        await connect_to_mongodb()
    return db


async def get_user_collection():
    """Returns the users collection"""
    database = await get_database()
    return database[USERS_COLLECTION]


async def get_job_collection():
    """Returns the jobs collection"""
    database = await get_database()
    return database[JOBS_COLLECTION]


async def get_application_collection():
    """Returns the applications collection"""
    database = await get_database()
    return database[APPLICATIONS_COLLECTION]


async def get_collection(collection_name: str):
    """
    General function to get any collection by name.
    Use with caution and only for collections not covered by specific getters.
    """
    database = await get_database()
    return database[collection_name]


async def insert_document(collection_name: str, document: Dict[str, Any]) -> str:
    """
    Inserts a document into the specified collection.
    Returns the inserted document ID.
    """
    try:
        collection = await get_collection(collection_name)
        result = await collection.insert_one(document)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error inserting document: {str(e)}")
        raise


async def find_document(
        collection_name: str,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None
):
    """
    Finds a single document matching the query.
    Returns None if no document found.
    """
    try:
        collection = await get_collection(collection_name)
        return await collection.find_one(query, projection)
    except Exception as e:
        logger.error(f"Error finding document: {str(e)}")
        raise


async def update_document(
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
):
    """
    Updates documents matching the query with the update operation.
    Returns the number of modified documents.
    """
    try:
        collection = await get_collection(collection_name)
        result = await collection.update_one(query, update)
        return result.modified_count
    except Exception as e:
        logger.error(f"Error updating document: {str(e)}")
        raise


async def delete_document(collection_name: str, query: Dict[str, Any]):
    """
    Deletes documents matching the query.
    Returns the number of deleted documents.
    """
    try:
        collection = await get_collection(collection_name)
        result = await collection.delete_one(query)
        return result.deleted_count
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise