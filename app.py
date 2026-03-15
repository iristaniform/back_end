from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
from typing import Optional

app = FastAPI(title="Hospital Management System")


# -------------------- CORS --------------------
origins = ["*"]  # allow all for development

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------- DATABASE --------------------
DB_CONFIG = {
    "host": "localhost",
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


# -------------------- PATIENT MODEL --------------------
class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    gender: str
    phone_number: Optional[str] = None
    email: Optional[str] = None


# -------------------- DOCTOR MODEL --------------------
class DoctorCreate(BaseModel):
    first_name: str
    last_name: str
    specialization: str
    phone_number: Optional[str] = None
    email: Optional[str] = None


# =====================================================
# PATIENT ROUTES
# =====================================================

@app.post("/patient/", status_code=status.HTTP_201_CREATED)
async def create_patient(patient: PatientCreate):

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO patients
        (first_name, last_name, date_of_birth, gender, phone_number, email)
        VALUES (%s,%s,%s,%s,%s,%s)
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

    return {"message": "Patient created successfully"}


@app.get("/patients/list")
async def get_patients_list():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()

    cursor.close()
    conn.close()

    return patients


@app.put("/patient/{patient_id}")
async def update_patient(patient_id: int, patient: PatientCreate):

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        UPDATE patients
        SET first_name=%s,last_name=%s,date_of_birth=%s,gender=%s,phone_number=%s,email=%s
        WHERE patient_id=%s
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

    return {"message": "Patient updated successfully"}


@app.delete("/patients/{patient_id}")
async def delete_patient(patient_id: int):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM patients WHERE patient_id=%s", (patient_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return {"message": "Patient deleted successfully"}


# =====================================================
# DOCTOR ROUTES
# =====================================================

@app.post("/doctors", status_code=status.HTTP_201_CREATED)
async def create_doctor(doctor: DoctorCreate):

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO doctors
        (first_name,last_name,specialization,phone_number,email)
        VALUES (%s,%s,%s,%s,%s)
    """

    values = (
        doctor.first_name,
        doctor.last_name,
        doctor.specialization,
        doctor.phone_number,
        doctor.email
    )

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()

    return {"message": "Doctor created successfully"}


@app.get("/doctors/list")
async def get_doctors_list():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM doctors")
    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return doctors  


@app.put("/doctors/{doctor_id}")
async def update_doctor(doctor_id: int, doctor: DoctorCreate):

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        UPDATE doctors
        SET first_name=%s,last_name=%s,specialization=%s,phone_number=%s,email=%s
        WHERE doctor_id=%s
    """

    values = (
        doctor.first_name,
        doctor.last_name,
        doctor.specialization,
        doctor.phone_number,
        doctor.email,
        doctor_id
    )

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()

    return {"message": "Doctor updated successfully"}


@app.delete("/doctors/{doctor_id}")
async def delete_doctor(doctor_id: int):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM doctors WHERE doctor_id=%s", (doctor_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return {"message": "Doctor deleted successfully"}


@app.get("/doctors/count")
async def get_doctors_count():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM doctors")
    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return {"count": count}


# -------------------- RUN SERVER --------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )