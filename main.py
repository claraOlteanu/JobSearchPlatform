from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from elasticsearch import Elasticsearch
import os

# Elasticsearch client initialization
es = Elasticsearch(hosts=["http://localhost:9200"])

# FastAPI app initialization
app = FastAPI()

# Elasticsearch index name for job postings
INDEX_NAME = "jobs"

class Job(BaseModel):
    title: str
    description: str
    company_name: str
    location: str
    salary_range: str
    job_type: str
    posted_date: str
    application_deadline: str
    status: str
    application_instructions: str


class User(BaseModel):
    name: str
    email: str
    password: str  # Ideally hashed, simplified for now
    phone_number: str
    address: str
    resume_url: Optional[str] = None
    skills: Optional[List[str]] = []
    experience: Optional[List[str]] = []
    education: Optional[List[str]] = []


class Application(BaseModel):
    user_id: int
    job_id: int
    resume_url: str
    cover_letter_url: Optional[str] = None
    status: str

@app.get("/api/jobs")
async def search_jobs(
        job_type: Optional[str] = None,
        location: Optional[str] = None,
        salary_range: Optional[str] = None
):
    query = {
        "bool": {
            "must": [],
            "filter": []
        }
    }

    if job_type:
        query["bool"]["filter"].append({"term": {"job_type": job_type}})

    if location:
        query["bool"]["filter"].append({"term": {"location": location}})

    if salary_range:
        query["bool"]["filter"].append({"range": {"salary_range": {"gte": salary_range}}})

    response = es.search(index=INDEX_NAME, body={"query": query})
    jobs = [hit["_source"] for hit in response["hits"]["hits"]]

    return jobs

@app.get("/api/jobs/{job_id}")
async def get_job_details(job_id: int):
    try:
        response = es.get(index=INDEX_NAME, id=job_id)
        return response["_source"]
    except Exception as e:
        raise HTTPException(status_code=404, detail="Job not found")

@app.post("/api/jobs/{job_id}/apply")
async def apply_to_job(job_id: int, user_id: int, application: Application):
    application_data = {
        "user_id": user_id,
        "job_id": job_id,
        "resume_url": application.resume_url,
        "cover_letter_url": application.cover_letter_url,
        "status": "pending"
    }
    # Store application in a database or Elasticsearch
    return {"msg": "Application submitted", "application": application_data}

@app.post("/api/users")
async def create_user(user: User):
    return {"msg": "User created successfully", "user": user}

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id, "name": "Sample User"}  # Placeholder for actual data

@app.post("/api/jobs")
async def create_job(job: Job):
    job_data = job.dict()
    # Index the job data in elasticsearch
    response = es.index(index=INDEX_NAME, document=job_data)
    return {"msg": "Job posted successfully", "job_id": response['_id']}

@app.get("/api/applications")
async def get_applications(user_id: int):
    # Fetch applications made by the user
    return [{"job_id": 1, "status": "pending"}, {"job_id": 2, "status": "accepted"}]  # Sample data

@app.delete("/api/applications/{application_id}")
async def withdraw_application(application_id: int):
    # Delete the application
    return {"msg": "Application withdrawn"}
