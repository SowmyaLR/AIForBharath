"""
nhir/server — NHCX ABDM FHIR Conversion Microservice
Runs on port 8001. Standalone service, independent of the main VaidyaSaarathi server.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.convert import router as convert_router

app = FastAPI(
    title="NHCX FHIR Converter",
    description=(
        "Open-source microservice that ingests healthcare PDFs and converts them "
        "into ABDM FHIR R4 profiles and NHCX Claim bundles for the Indian healthcare ecosystem."
    ),
    version="1.0.0",
    contact={
        "name": "AIForBharath Hackathon",
        "url": "https://github.com/SowmyaLR/AIForBharath",
    },
    license_info={"name": "Apache 2.0"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(convert_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": "NHCX FHIR Converter",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "claim_pdf": "POST /convert/claim  (multipart PDF upload)",
            "claim_text": "POST /convert/text   (JSON text body)",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
