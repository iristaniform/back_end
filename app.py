from os import name

from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import mysql.connector
from mysql.connector import Error
from pydantic import BaseModel, EmailStr, constr
from typing import Annotated
from fastapi import Form, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

app = FastAPI(title="Simple Newsletter Signup")


# ── Add this block for CORS ────────────────────────────────
origins = [
    "http://localhost",
    "http://localhost:3000",     # React/Vite dev server
    "http://localhost:5173",     # Vite default
    "http://127.0.0.1:3000",
    "https://your-frontend-domain.com",   # ← add your production frontend(s)
    "*"   # ← wildcard = allow everything (only for dev / testing!)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,                    # or just ["*"] for dev
    allow_credentials=True,                   # important if using cookies / auth headers
    allow_methods=["*"],                      # GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],                      # Content-Type, Authorization, etc.
)



# ── Database configuration ──
#    CHANGE THESE VALUES!
DB_CONFIG = {
    "host": "192.168.4.214",
    "database": "hospital_db",
    "user": "iris",
    "password": "Iris@2026",
    "port": 3306
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
    
# Define the input model (automatic validation + OpenAPI docs)
class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str          # or use date if frontend sends ISO date "YYYY-MM-DD"
    # date_of_birth: date       # ← preferred if possible
    gender: str
    phone_number: Optional[str] = None
    email: Optional[str] = None

    # Optional: add validators if needed
    # class Config:
    #     json_encoders = {date: lambda v: v.isoformat()}

@app.post("/patient/", status_code=status.HTTP_201_CREATED)
# Remove response_class=HTMLResponse unless this endpoint really returns HTML
# If it's an API → just let FastAPI return JSON automatically
async def create_patient(patient: PatientCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)   # recommended: use dict results

        query = """
            INSERT INTO patients 
            (first_name, last_name, date_of_birth, gender, phone_number, email)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            patient.first_name,
            patient.last_name,
            patient.date_of_birth,
            patient.gender,
            patient.phone_number,
            patient.email
        )

        cursor.execute(query, values)
        conn.commit()

        # Get the newly created ID
        new_id = cursor.lastrowid

        cursor.close()
        conn.close()

        # Return the created patient (with ID) — standard REST practice
        created_patient = patient.dict()
        created_patient["id"] = new_id   # or "patient_id" depending on your column name

        return {
            "message": "Patient created successfully",
            "patient": created_patient
        }

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@app.post("/patient/", response_class=HTMLResponse)
async def create_patient(
    request: Request,
    first_name: Annotated[str, Form()],
    last_name: Annotated[str, Form()],
    date_of_birth: Annotated[str, Form()],
    gender: Annotated[str, Form()],
    phone_number: Annotated[str, Form()] = None,
    email: Annotated[str, Form()] = None
):    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if patient already exists
        cursor.execute("SELECT id FROM patients WHERE first_name = %s AND last_name = %s", (first_name, last_name))
        if cursor.fetchone():
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "message": "", "error": "This patient already exists."}
            )

        # Insert new patient
        query = """
            INSERT INTO patients (first_name, last_name, date_of_birth, gender, phone_number, email)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (first_name, last_name, date_of_birth, gender, phone_number, email))
        conn.commit()

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "message": f"Thank you{', ' + last_name if last_name else ''}! You've been added as a new patient.",
                "error": ""
            }
        )

    except HTTPException as e:
        raise e
    except Error as e:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "message": "", "error": f"Database error: {str(e)}"}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "message": "", "error": "Something went wrong. Please try again."}
        )
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",               # ← change to this string format
        host="0.0.0.0",
        port=8000,
        reload=True
    )


@app.get("/", response_class=HTMLResponse)
async def show_form(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "message": "", "error": ""}
    )

# get total count of doctors
@app.get("/doctors/count")
async def get_doctors_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM doctors")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    # format as html response
    return HTMLResponse(content=f"<h1>Total doctors: {count}</h1>")
    # return {"count": count}
    
# get total count of female patients
@app.get("/patients/count/female")
async def get_female_patients_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM patients WHERE gender = 'Female'"
    cursor.execute(query)
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    # format as html response
    return HTMLResponse(content=f"<h1>Female Patients: {count}</h1>")

# get list of patients as json
@app.get("/patients/list")
async def get_patients_list():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # dictionary=True lets us use names like 'email'
    query = "SELECT * FROM patients"
    cursor.execute(query)
    patients = cursor.fetchall()
    cursor.close()
    conn.close()
    return patients

# delete patient using id
# Delete patient by ID
@app.delete("/patients/{patient_id}")
async def delete_patient(patient_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if patient exists first (good practice)
        cursor.execute("SELECT patient_id FROM patients WHERE patient_id = %s", (patient_id,))
        patient = cursor.fetchone()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {patient_id} not found"
            )
        
        # Perform the deletion
        cursor.execute("DELETE FROM patients WHERE patient_id = %s", (patient_id,))
        conn.commit()   # important! DELETE is a write operation
        
        return {
            "message": "Patient deleted successfully",
            "patient_id": patient_id
        }
    
    except Exception as e:
        conn.rollback()  # rollback on error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    
    finally:
        cursor.close()
        conn.close()

# get total count of patients using email
@app.get("/patient/count/email")
async def get_email_patients():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM patients WHERE email LIKE '%@email.com%'"
    cursor.execute(query)
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return HTMLResponse(content=f"<h1>Patients using email: {count}</h1>")


@app.post("/patients/search")
async def search_patients(patients_name: Annotated[str, Form()]):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # dictionary=True lets us use names like 'email'
    
    query = "SELECT * FROM patients WHERE first_name LIKE %s"
    cursor.execute(query, (f"%{patients_name}%",))
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()

    if result:
        return HTMLResponse(content=f"""
            <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
                <div style="border: 2px solid #28a745; display: inline-block; padding: 20px; border-radius: 10px;">
                    <h1 style="color: #28a745;">Patients Found!</h1>
                    <p><strong>Name:</strong> {result['first_name']}</p>
                    <p><strong>Email:</strong> {result['email']}</p>
                    <p><strong>Gender:</strong> {result['gender']}</p>
                    <a href="/" style="text-decoration: none; color: white; background: #28a745; padding: 10px 20px; border-radius: 5px;">New Search</a>
                </div>
            </body>
        """)
    else:
        return HTMLResponse(content="<h1>No patient found with that name.</h1><br><a href='/'>Try Again</a>")

    