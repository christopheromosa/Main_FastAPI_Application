from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, ForeignKey
from database import Base
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
import pytz


def get_nairobi_time():
    nairobi_timezone = pytz.timezone("Africa/Nairobi")
    utc_now = datetime.now(timezone.utc)
    return utc_now.astimezone(nairobi_timezone)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    occupation = Column(String(100), unique=False, nullable=True)
    password = Column(String(100), nullable=False)



class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, index=True)
    disease_name = Column(String, index=True, unique=True)
    preventive_measure = Column(String)


class User_history(Base):
    __tablename__ = 'user_histories'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    image_path = Column(String)
    prediction = Column(String)
    confidence = Column(Integer)
    preventive_measure = Column(String, nullable=True)
    timestamp = Column(DateTime, default=get_nairobi_time)


class Plants(Base):
    __tablename__ = 'plants'
    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, nullable=True, index=True)
    plant_name = Column(String, index=True, unique=True, nullable=False)
    plant_description = Column(String, nullable=True, index=True)
    diseases = relationship("PlantDiseases", back_populates="plant")
    types = relationship("PlantTypes", back_populates="plant")


class PlantDiseases(Base):
    __tablename__ = 'plant_diseases'
    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, nullable=True)
    plant_disease_name = Column(
        String, index=True, unique=True, nullable=False)
    plant_disease_description = Column(String, nullable=True, index=True)
    plant_disease_recommendation = Column(String, nullable=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"))
    plant = relationship("Plants", back_populates="diseases")


class PlantTypes(Base):
    __tablename__ = 'plant_types'
    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, nullable=True)
    plant_type_name = Column(String, index=True, unique=True, nullable=False)
    plant_type_description = Column(String, nullable=True)
    plant_id = Column(Integer, ForeignKey("plants.id"))
    plant = relationship('Plants', back_populates="types")
