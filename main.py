from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os

app = FastAPI()

# Mount static files (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

from services import extract_text, generate_resume_content, generate_cover_letter_content, generate_notes_content, extract_metadata
from docx_gen import create_resume_docx, create_simple_docx
import zipfile
import io
    
@app.post("/api/generate")
async def generate_documents(
    job_description: str = Form(...),
    resume: UploadFile = File(...),
    cover_letter: UploadFile = File(...)
):
    try:
        # 1. Extract Text
        resume_text = await extract_text(resume)
        cover_text = await extract_text(cover_letter)
        
        # 2. Generate Content (Parallelize in real app, sequential here for simplicity)
        # Note: In a real async app we should use asyncio.gather
        # 2. Generate Content
        # Note: In a real async app we should use asyncio.gather
        resume_content = await generate_resume_content(job_description, resume_text)
        cover_content = await generate_cover_letter_content(job_description, resume_text, cover_text)
        notes_content = await generate_notes_content(job_description)
        metadata = await extract_metadata(job_description)
        
        # 3. Create DOCX files
        # Sanitize filenames
        company = "".join(x for x in metadata.get("company", "Company") if x.isalnum() or x in [' ', '_', '-']).strip().replace(" ", "_")
        role = "".join(x for x in metadata.get("role", "Role") if x.isalnum() or x in [' ', '_', '-']).strip().replace(" ", "_")
        
        base_name = f"{company}_{role}"
        
        resume_filename = f"{base_name}_Resume.docx"
        cover_filename = f"{base_name}_CoverLetter.docx"
        notes_filename = f"{base_name}_Notes.docx"
        
        # Ensure 'out' directory exists
        os.makedirs("out", exist_ok=True)
        
        create_resume_docx(resume_content, f"out/{resume_filename}")
        create_simple_docx(cover_content, f"out/{cover_filename}")
        create_simple_docx(notes_content, f"out/{notes_filename}")
        
        # Create ZIP
        zip_filename = f"{base_name}_Application.zip"
        zip_path = f"out/{zip_filename}"
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(f"out/{resume_filename}", resume_filename)
            zipf.write(f"out/{cover_filename}", cover_filename)
            zipf.write(f"out/{notes_filename}", notes_filename)
            
        return FileResponse(zip_path, media_type='application/zip', filename=zip_filename)

        
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
