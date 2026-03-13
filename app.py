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
    date_of_birth: str
    gender: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    

@app.post("/patient/", status_code=status.HTTP_201_CREATED)
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

        cursor.close()
        conn.close()

        return {
            "message": "Patient created successfully"
        }

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.put("/patient/{patient_id}")
async def update_patient(patient: PatientCreate, patient_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)   # recommended: use dict results

        query = """
            UPDATE patients 
            SET first_name = %s, last_name = %s, date_of_birth = %s, gender = %s, phone_number = %s, email = %s
            WHERE patient_id = %s
        """
        values = (
            patient.first_name,
            patient.last_name,
            patient.date_of_birth,
            patient.gender,
            patient.phone_number,
            patient.email,
            patient_id
        )

        cursor.execute(query, values)
        conn.commit()

        cursor.close()
        conn.close()

        return {
            "message": "Patient updated successfully"
        }

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",               # ← change to this string format
        host="0.0.0.0",
        port=8000,
        reload=True
    )





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
            "message": "Patient deleted successfully"
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