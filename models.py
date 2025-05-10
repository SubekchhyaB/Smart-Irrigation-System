# models.py
from sqlalchemy import Column, Integer, Float, Boolean, create_engine, DateTime,String,ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,relationship
from datetime import datetime

Base = declarative_base()

engine = create_engine("sqlite:///system.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class SensorData(Base):
    __tablename__ = "sensor_data"
    id = Column(Integer, primary_key=True, index=True)
    moisture = Column(Float)
    pump_status = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))  # <-- This line is missing in your case
    user = relationship("User")

class Control(Base):
    __tablename__ = "control"
    id = Column(Integer, primary_key=True, index=True)
    override = Column(Boolean, default=False)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    email = Column(String, unique=True)
    phone = Column(String,unique=True)
    mac_address = Column(String, unique=True)  # Store MAC address
    is_active = Column(Boolean, default=True)

