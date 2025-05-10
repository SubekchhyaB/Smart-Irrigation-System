from fastapi import FastAPI, Request, Depends, HTTPException, Form, Cookie,Body,Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from models import Base, SensorData, Control, SessionLocal, engine, User
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import and_
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
import jwt
import requests  # Add this at the top

# --------- Pydantic Schemas ---------
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    mac_address: str
    phone:str
    @classmethod
    def as_form(
        cls,
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        phone: str = Form(...),
        mac_address: str = Form(...),
    ) -> "UserCreate":
        return cls(username=username, email=email, password=password, mac_address=mac_address,phone=phone)

class OverrideModel(BaseModel):
    override: bool

# --------- JWT Setup ---------
SECRET_KEY = "12345678"  # Replace with a secure, random key in production
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --------- Password Hashing ---------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# --------- DB Setup ---------
Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------- User Authentication ---------
def get_current_user(
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --------- Routes ---------

@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse(url="/login")

@app.get("/signup", response_class=HTMLResponse)
def show_signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
def signup(
    user: UserCreate = Depends(UserCreate.as_form),
    db: Session = Depends(get_db),
):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered.")
    
    hashed_password = hash_password(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        phone=user.phone,
        mac_address=user.mac_address
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
def show_login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user or not verify_password(password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials.")
    
    token = create_access_token({"sub": str(db_user.id)})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

# --------- Cleanup Old Sensor Data ---------
def delete_old_data():
    db = SessionLocal()
    cutoff = datetime.utcnow() - timedelta(days=7)
    deleted = db.query(SensorData).filter(SensorData.timestamp < cutoff).delete()
    db.commit()
    db.close()
    print(f"[{datetime.utcnow()}] Deleted {deleted} old records.")

@app.on_event("startup")
def startup_event():
    delete_old_data()

# --------- Dashboard ---------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = db.query(SensorData).order_by(SensorData.id.desc()).first()
    control = db.query(Control).first()
    if not control:
        control = Control(override=False)
        db.add(control)
        db.commit()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "moisture": data.moisture if data else 0,
        "override": control.override,
        "username": user.username
    })

# --------- API: Latest Sensor Data ---------
@app.get("/api/latest")
def get_latest_data(db: Session = Depends(get_db)):
    latest = db.query(SensorData).order_by(SensorData.id.desc()).first()
    if latest:
        return {"moisture": latest.moisture, "pump_status": latest.pump_status}
    return {"moisture": 0, "pump_status": False}
# --------------------------------------send sms------------
def send_sms(message: str, phone_number: str):
    try:
        payload = {
            "to": phone_number,
            "from": "Demo",
            "token":"v2_vGYKISTQcB7D4BEurMsmztwVe4D.J1V6",
             "text": message
        }

        response = requests.post( "https://smsrelay-sparrow.onrender.com/relay_sms", data=payload)
        if response.status_code == 200:
            print("Message sent successfully!")
        else:
            print(f"Failed to send message. Status code: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error sending message: {e}")
# --------- API: Receive Sensor Data ---------
@app.post("/api/sensor")
async def sensor_data(
    moisture: float,
    mac_address: str,
    trigger_sms: bool = Query(False),
    db: Session = Depends(get_db)
):
    # 1. Match MAC to User
    user = db.query(User).filter(User.mac_address == mac_address).first()
    if not user:
        raise HTTPException(status_code=400, detail="MAC address not found.")

    # 2. Read override control flag (global)
    control = db.query(Control).first()
    if not control:
        control = Control(override=False)
        db.add(control)
        db.commit()

    # 3. Decide whether to pump or not
    pump_on = moisture < 30 and not control.override
    
     # 5. Send SMS only if moisture goes below the threshold and SMS hasn't been sent yet
    if moisture < 30 and not control.override and not  trigger_sms:
        send_sms(f"Warning: Moisture level is low at {moisture}%.", user.phone)
        trigger_sms= True  # Set the flag that SMS has been sent

    # 6. Reset SMS flag if moisture goes above the threshold
    if moisture >= 30 and  trigger_sms:
        send_sms(f"Good: Moisture level is Good at {moisture}%.", user.phone)
        trigger_sms= False  # Set the flag that SMS has been sent
    db.commit()

    # 4. Save sensor reading
    new_data = SensorData(
        moisture=moisture,
        pump_status=pump_on,
        user_id=user.id
    )
    db.add(new_data)
    db.commit()

    # 5. Send status back to Arduino
    return {"pump": pump_on}


# --------- API: Override Control ---------
@app.post("/api/override")
async def set_override(
    override: OverrideModel = Body(...),  # ⬅️ needed to parse JSON body
    db: Session = Depends(get_db)
):
    print("Received override payload:", override)
    control = db.query(Control).first()
    if control:
        control.override = override.override
    else:
        control = Control(override=override.override)
        db.add(control)
    db.commit()
    return {"status": "updated", "override": override.override}
    



# --------- History View ---------
@app.get("/history", response_class=HTMLResponse)
def history(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.now()
    yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_end = yesterday_start + timedelta(days=1)
    week_start = now - timedelta(days=7)

    yesterday_data = db.query(SensorData).filter(
        and_(
            SensorData.timestamp >= yesterday_start,
            SensorData.timestamp < yesterday_end
        )
    ).order_by(SensorData.timestamp.desc()).all()

    last_week_data = db.query(SensorData).filter(
        SensorData.timestamp >= week_start
    ).order_by(SensorData.timestamp.desc()).all()

    return templates.TemplateResponse("history.html", {
        "request": request,
        "yesterday_data": yesterday_data,
        "week_data": last_week_data
    })

# --------- Logout ---------
@app.post("/logout", response_class=HTMLResponse)
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response
    
@app.get("/api/control/status")
def control_status(db: Session = Depends(get_db)):
    control = db.query(Control).first()
    return {"override": control.override}

