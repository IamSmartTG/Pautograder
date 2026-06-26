from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.problems import router as problems_router
from routes.submit import router as submit_router

app = FastAPI(title="Pautograder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(problems_router, prefix="/api")
app.include_router(submit_router, prefix="/api")
