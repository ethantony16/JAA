import os
import aiohttp
import json
from fastapi import UploadFile
import docx
from pypdf import PdfReader
import io

# API Key from environment
API_KEY = os.environ.get("DASHSCOPE_API_KEY")

async def extract_text(file: UploadFile) -> str:
    content = await file.read()
    file_obj = io.BytesIO(content)
    text = ""
    
    if file.filename.endswith('.pdf'):
        try:
            reader = PdfReader(file_obj)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            text = f"[Error reading PDF: {e}]"
    elif file.filename.endswith('.docx'):
        try:
            doc = docx.Document(file_obj)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            text = f"[Error reading DOCX: {e}]"
    else:
        # Fallback for text files
        try:
            text = content.decode('utf-8')
        except:
            pass
            
    return text

async def generate_content(prompt: str):
    if not API_KEY:
        return "Error: DASHSCOPE_API_KEY is not set."

    # DashScope API (OpenAI Compatible)
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }

    data = {
        "model": "qwen-plus",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    async with aiohttp.ClientSession() as session:
        for attempt in range(5):
            try:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 429:
                        wait_time = (2 ** attempt) + 1 
                        print(f"Rate limit hit. Retrying in {wait_time}s...")
                        import asyncio
                        await asyncio.sleep(wait_time)
                        continue
                        
                    if response.status != 200:
                        text = await response.text()
                        print(f"Error calling Qwen: {response.status} - {text}")
                        return f"Error calling Qwen API: {response.status}"
                    
                    result = await response.json()
                    try:
                        return result['choices'][0]['message']['content']
                    except (KeyError, IndexError):
                        return "Error parsing Qwen/DashScope response."
            except Exception as e:
                 print(f"Exception calling Qwen: {e}")
                 return f"Error: {e}"
        return "Error: Rate limit exceeded after retries."

async def generate_resume_content(job_desc: str, resume_text: str) -> str:
    prompt = f"""
    You are an expert career coach and resume writer.
    
    JOB DESCRIPTION:
    {job_desc}
    
    RESUME:
    {resume_text}
    
    TASK:
    Rewrite the resume to perfectly tailor it to the Job Description. 
    Crucial requirement: You must highlight changes.
    - Wrap ANY new or modified text in <ins> tags (e.g. <ins>New Skill</ins>).
    - Wrap removed text in <del> tags (e.g. <del>Old Irrelevant Skill</del>).
    - Keep the formatting clean and professional using Markdown.
    - Use `###` for Section Headers (e.g. ### Experience).
    - Use `**` for Bold text (e.g. **Role**).
    - Use `-` for Bullet points.
    - Output ONLY the body of the resume text.
    - Example format:
      ### Experience
      **Software Engineer** - Google
      - <ins>Led team...</ins>
    
    At the very end of your response, strictly separated by the delimiter "[[THINKING_PROCESS]]", provide a detailed explanation of your thinking process. Explain why you made specific changes, added certain keywords, or removed sections.
    """
    return await generate_content(prompt)

async def generate_cover_letter_content(job_desc: str, resume_text: str, cover_letter_text: str) -> str:
    prompt = f"""
    You are an expert career coach.
    
    JOB DESCRIPTION:
    {job_desc}
    
    RESUME:
    {resume_text}
    
    OLD COVER LETTER:
    {cover_letter_text}
    
    TASK:
    Write a customized cover letter for this specific job. 
    - Highlight specific experiences from the resume that match the job requirements.
    - Use a professional yet enticing tone.
    - Structure it properly (Header, Salutation, Body, Closing).
    
    At the very end of your response, strictly separated by the delimiter "[[THINKING_PROCESS]]", provide a detailed explanation of your thinking process. Explain how you connected the resume to the JD and why you chose this structure.
    """
    return await generate_content(prompt)

async def generate_notes_content(job_desc: str) -> str:
    prompt = f"""
    You are a thorough job interview researcher.
    
    JOB DESCRIPTION:
    {job_desc}
    
    TASK:
    Analyze the JD and use your internal knowledge to provide a prep document.
    Include ONLY factual info. If you do not know something, state "Not available". Do NOT hallucinate.
    
    SECTIONS REQUIRED:
    1. Main Job Responsibilities (Summarized from JD)
    2. Company Size and Founding Year
    3. Key Products/Services
    4. Target Customers
    5. Main Competitors
    6. General Reviews/Reputation (if known widely)
    7. Hiring Manager / Team Info (if found in JD)
    8. Company Website Link (Find based on company name, e.g. https://www.company.com)
    9. Company LinkedIn Page (Find based on company name, e.g. https://www.linkedin.com/company/company-name)
    
    At the very end of your response, strictly separated by the delimiter "[[THINKING_PROCESS]]", provide a detailed explanation of your thinking process. Explain how you extracted or inferred this information.
    """
    return await generate_content(prompt)

async def extract_metadata(job_desc: str) -> dict:
    prompt = f"""
    JOB DESCRIPTION:
    {job_desc}
    
    TASK:
    Extract the COMPANY NAME and the JOB TITLE from the text above.
    Return ONLY a JSON object with keys "company" and "role".
    If not found, use "UnknownCompany" and "UnknownRole".
    Example: {{"company": "Google", "role": "Software Engineer"}}
    """
    response_text = await generate_content(prompt)
    try:
        # Clean up code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
             response_text = response_text.split("```")[1].split("```")[0].strip()
             
        data = json.loads(response_text)
        return data
    except:
        return {"company": "Company", "role": "Role"}


