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

   # =====================================================
# APPOINTMENT MODEL
# =====================================================

class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: str          # format: "2025-04-15"
    appointment_time: str          # format: "14:30"
    status: Optional[str] = "pending"    # pending, confirmed, cancelled, completed
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


# =====================================================
# APPOINTMENT ROUTES
# =====================================================

@app.post("/appointments", status_code=status.HTTP_201_CREATED)
async def create_appointment(appointment: AppointmentCreate):

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO appointments
        (patient_id, doctor_id, appointment_date, appointment_time, status, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    values = (
        appointment.patient_id,
        appointment.doctor_id,
        appointment.appointment_date,
        appointment.appointment_time,
        appointment.status,
        appointment.notes
    )

    try:
        cursor.execute(query, values)
        conn.commit()
        new_id = cursor.lastrowid
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create appointment: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return {"message": "Appointment created successfully", "appointment_id": new_id}


@app.get("/appointments/list")
async def get_appointments_list():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT 
            a.appointment_id,
            a.patient_id,
            CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
            a.doctor_id,
            CONCAT(d.first_name, ' ', d.last_name) AS doctor_name,
            a.appointment_date,
            a.appointment_time,
            a.status,
            a.notes
        FROM appointments a
        LEFT JOIN patients p ON a.patient_id = p.patient_id
        LEFT JOIN doctors d ON a.doctor_id = d.doctor_id
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """

    cursor.execute(query)
    appointments = cursor.fetchall()

    cursor.close()
    conn.close()

    return appointments


@app.get("/appointments/{appointment_id}")
async def get_appointment(appointment_id: int):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT 
            a.appointment_id,
            a.patient_id,
            CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
            a.doctor_id,
            CONCAT(d.first_name, ' ', d.last_name) AS doctor_name,
            a.appointment_date,
            a.appointment_time,
            a.status,
            a.notes
        FROM appointments a
        LEFT JOIN patients p ON a.patient_id = p.patient_id
        LEFT JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.appointment_id = %s
    """

    cursor.execute(query, (appointment_id,))
    appointment = cursor.fetchone()

    cursor.close()
    conn.close()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return appointment


@app.put("/appointments/{appointment_id}")
async def update_appointment(appointment_id: int, appointment: AppointmentUpdate):

    conn = get_db_connection()
    cursor = conn.cursor()

    updates = []
    values = []

    if appointment.appointment_date is not None:
        updates.append("appointment_date = %s")
        values.append(appointment.appointment_date)
    if appointment.appointment_time is not None:
        updates.append("appointment_time = %s")
        values.append(appointment.appointment_time)
    if appointment.status is not None:
        updates.append("status = %s")
        values.append(appointment.status)
    if appointment.notes is not None:
        updates.append("notes = %s")
        values.append(appointment.notes)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    query = f"UPDATE appointments SET {', '.join(updates)} WHERE appointment_id = %s"
    values.append(appointment_id)

    try:
        cursor.execute(query, tuple(values))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Appointment not found")
        conn.commit()
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Update failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return {"message": "Appointment updated successfully"}


@app.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: int):

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM appointments WHERE appointment_id = %s", (appointment_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Appointment not found")
        conn.commit()
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Delete failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return {"message": "Appointment deleted successfully"} 


# -------------------- RUN SERVER --------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )