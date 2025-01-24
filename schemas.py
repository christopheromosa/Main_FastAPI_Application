from pydantic import BaseModel,EmailStr
from fastapi import UploadFile
class AuthDetails(BaseModel):
    username: str
    email: EmailStr
    occupation:str
    password: str
   


class LoginDetails(BaseModel):
    username: str
    password: str


class RecommendationDetails(BaseModel):
    disease_name:str
    preventive_measure:str

class UserHistoryDetails(BaseModel):
    user_id: int
    image_path :bytes
    prediction: str
    confidence :int
    preventive_measure :str
    timestamp :str

class UpdateProfileSchema(BaseModel):
    email:EmailStr
    picture:bytes

class PlantDetails(BaseModel):
    plant_name:str
    plant_description:str
    image: UploadFile


class PlantDiseasesDetails(BaseModel):
    plant_disease_name: str
    plant_disease_description: str
    plant_disease_recommendation: str
    plant_id: int
    image: UploadFile

class PlantTypesDetails(BaseModel):
    plant_type_name: str
    plant_type_description: str
    plant_id: int
    image: UploadFile



