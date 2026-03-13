from os import name

from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import mysql.connector
from mysql.connector import Error
from pydantic import BaseModel, EmailStr, constr
from typing import Annotated
from fastapi import Form

app = FastAPI(title="Simple Newsletter Signup")

# --- Templates & static files ---
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ── Database configuration ──
#    CHANGE THESE VALUES!
DB_CONFIG = {
    "host": "localhost",
    "database": "hospital_db",
    "user": "root",
    "password": "root",
    "port": 3306
}


# Pydantic model for validation
class Subscriber(BaseModel):
    email: EmailStr
    name: Annotated[str, constr(strip_whitespace=True, min_length=2, max_length=100)] | None = None
    message: Annotated[str, constr(strip_whitespace=True, max_length=500)] | None = None


def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


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
        "main:app",               # ← change to this string format
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
    query = "SELECT first_name, last_name, date_of_birth, gender, phone_number, email FROM patients"
    cursor.execute(query)
    patients = cursor.fetchall()
    cursor.close()
    conn.close()
    return patients

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

    