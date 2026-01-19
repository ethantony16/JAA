import zipfile
import os

os.makedirs("out", exist_ok=True)

# Create dummy files if they don't exist
files = ["out/Application_Docs_Resume.docx", "out/Application_Docs_CoverLetter.docx", "out/Application_Docs_Notes.docx"]
for f in files:
    if not os.path.exists(f):
        with open(f, "w") as fp:
            fp.write("dummy content")

zip_path = "out/Application_Docs.zip"
print(f"Creating zip at {zip_path}")

try:
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for f in files:
            arcname = os.path.basename(f)
            print(f"Adding {f} as {arcname}")
            zipf.write(f, arcname)

    print("Zip created successfully.")
    
    if os.path.exists(zip_path):
        print(f"File exists. Size: {os.path.getsize(zip_path)} bytes")
    else:
        print("File DOES NOT exist after creation!")
        
except Exception as e:
    print(f"Error: {e}")
