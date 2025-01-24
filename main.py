from fastapi import FastAPI, Depends, HTTPException, Cookie, Response, Request, File, UploadFile, Header
from fastapi.responses import FileResponse
from Auth.auth_handler import AuthHandler
from fastapi.middleware.cors import CORSMiddleware
import httpx
import jwt

from schemas import AuthDetails, LoginDetails, UpdateProfileSchema, RecommendationDetails, PlantDetails, UserHistoryDetails, PlantDiseasesDetails, PlantTypesDetails
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import crud  
from database import SessionLocal, engine
import uvicorn
from models import Base, User, User_history, Plants, PlantDiseases, PlantTypes
import base64
from fastapi.staticfiles import StaticFiles
import uuid
# test image upload
from pathlib import Path
import io
# from models import PlantDiseases, Plants, PlantTypes


##
app = FastAPI()
Base.metadata.create_all(bind=engine)
# Serve images from the 'uploadedImages' folder
# app.mount("/images", StaticFiles(directory="uploaded_images"), name="images")
# testing image
app.mount("/static", StaticFiles(directory="static"), name="static")
# Get the parent directory of the current file
project_dir = Path(__file__).parent
UPLOAD_DIRECTORY = project_dir / "static/History"
UPLOAD_PLANT_DIRECTORY = project_dir / "static/Plants"
UPLOAD_PLANT_DISEASE_DIRECTORY = project_dir / "static/Plants_diseases"
UPLOAD_PLANT_TYPES_DIRECTORY = project_dir / "static/Plants_types"

origins = [
    "http://localhost",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load environment variables from the .env file
load_dotenv()

# Access environment variables with defaults
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
REFRESH_TOKEN_EXPIRE_MINUTES = os.getenv(
    "REFRESH_TOKEN_EXPIRE_MINUTES", 10080)  # 7 days in minutes (60 * 24 * 7)
ALGORITHM = os.getenv("ALGORITHM", "HS256")
# Provide a default value if not specifiedPlantDiseases
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default_secret_key")
# Provide a default value if not specified
JWT_REFRESH_SECRET_KEY = os.getenv(
    "JWT_REFRESH_SECRET_KEY", "default_refresh_secret_key")


auth_handler = AuthHandler() 
# extracted from the database
users = []
# Dependency


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get('/protected')
def protected(username=Depends(auth_handler.auth_wrapper)):
    return {'name': username, "message": "successfully loggen in", }


def get_token(token: str = Cookie(default=None, httponly=True)):
    if token is None:
        raise HTTPException(status_code=401, detail='Not authenticated')
    return token


# Define the directory to store the uploaded images
UPLOAD_DIR = 'uploaded_images'
endpoint = "http://localhost:5000/predict"
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/JPG'}
# from the main-tf-serving


@app.post("/predict_with_fetch", tags=['predictions'])
async def predict_with_fetch(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    username=Depends(auth_handler.auth_wrapper)
):

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, detail="Invalid file format. Only JPEG, PNG,JPG, and GIF are allowed.")

    # Read image data as bytes
    content = await file.read()

    try:
        async with httpx.AsyncClient() as client:
            prediction_response = await client.post(
                endpoint,
                files={"file": (file.filename, content,
                                file.content_type)}
            )
    except httpx.ReadError as exc:
        raise HTTPException(
            status_code=500, detail=f"Error communicating with prediction server: {exc}")

    print(prediction_response)
    prediction_result = prediction_response.json()
    print(prediction_result)

    if prediction_result:
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        image_path = os.path.join(str(UPLOAD_DIRECTORY), filename)
        # Open the destination file in binary write mode
        with io.open(image_path, 'wb') as f:
            f.write(content)
        # function filter to retrieve the recommendation for a particular disease

        # recommendation = db.query(PlantDiseases).filter_by(
        #     plant_disease_name=prediction_result['class']).first()

        # print(recommendation.plant_disease_name,
        #       recommendation.plant_disease_recommendation)
        recommendations = {
            "Early Blight": "To manage potato early blight, it is important to practice crop rotation, avoid overhead irrigation, remove infected plant debris, and apply fungicides if necessary",
            "Late Blight": "To manage potato late blight, it is important to plant resistant potato varieties, practice crop rotation, monitor the crop for symptoms regularly, and apply fungicides preventively if conditions are favorable for disease development.",
            "Healthy": "No recommendations your potato is doing well"
        }

        # if not recommendation:
        #     recommendation = "No recommendations"
        # else:
        #     recommendation = recommendation.plant_disease_recommendation
        print("filename: ", filename)
        existing_user = db.query(User).filter_by(username=username).first()
        history = crud.add_history(db, user_id=existing_user.id,
                                   image_path=filename,
                                   prediction=prediction_result['class'],
                                   confidence=round(
                                       prediction_result['confidence'] * 100, 2),
                                   preventive_measure=recommendations[prediction_result['class']])

        return {
            "history": history,
            "class": prediction_result['class'],
            "confidence": round(prediction_result['confidence'] * 100, 2),
            "preventive_measure": recommendations[prediction_result['class']],
            "image_path": filename
        }
    else:
        raise HTTPException(status_code=500, detail="Error making API call")


async def upload_image(image: UploadFile = File(...)):
    image_data = await image.read()
    print("Image data received in upload endpoint:", image_data)
    # Generate a unique filename
    filename = str(uuid.uuid4()) + os.path.splitext(image.filename)[1]
    image_path = os.path.join(str(UPLOAD_DIRECTORY), filename)

    # Read image data as bytes
    content = await image.read()

    # Open the destination file in binary write mode
    with io.open(image_path, 'wb') as f:
        f.write(content)

    return filename


@app.get("/images/{filename}")
async def get_image(filename: str):
    return FileResponse(f"{UPLOAD_DIR}/{filename}")


@app.get('/getusers', tags=["auth"],)
def getusers(request: Request, db: Session = Depends(get_db), username=Depends(auth_handler.auth_wrapper)):
    return crud.get_users(db)

# 1. User Management:
# - Impelement user Registration and authentication functionality.
# - Store user details securely <hashed passwords> in a database
# - Utilize authentication tokens <JWT>  for secure API authentication


@app.post("/register", tags=["auth"], status_code=201)
def register_user(user: AuthDetails, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter_by(
        username=user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=400, detail=f"Username '{user.username}' already registered")
    password = user.password
    encrypted_password = auth_handler.get_password_hash(password)
    new_user = crud.create_user(user, db, encrypted_password)
    return new_user


@app.post("/login", tags=["auth"])
def login(loginDetails: LoginDetails, response: Response, db: Session = Depends(get_db)):
    user = crud.check_existing_user(loginDetails.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username")
    hashed_pass = user.password
    if not auth_handler.verify_password(loginDetails.password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")
    token = auth_handler.encode_token(user.username)
    response.set_cookie(key='token', value=token, httponly=True)
    return {'token': token, "user": user}


@app.post('/logout', tags=["auth"])
def logout(request: Request, response: Response):
    # retrieve the cookie
    authorization_header = request.headers.get("authorization")
    if not authorization_header or not authorization_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Invalid authorization header")
    # token = authorization_header.split(" ")[1]
    token = authorization_header
    print(token)
    if not token:
        raise HTTPException(
            status_code=401, detail="Token not provided")
    # decode the cookie to get the username for the person
    try:

        payload = AuthHandler.decode_token({"token": token})
        username = payload['username']
        # set the cookie as expired or invalid
        response.delete_cookie(key='token')
        return {"detail": f"{username} logged out successfully"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error: {str(e)}")


@app.post('/change-password', tags=["auth"])
async def change_password(user: LoginDetails, db: Session = Depends(get_db)):
    existing_user = crud.check_existing_user(user, db)
    if existing_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")
    if not auth_handler.verify_password(existing_user.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid old password")
    encrypted_password = auth_handler.get_password_hash(user.new_password)
    user.password = encrypted_password
    db.commit()

    return {"message": "Password changed successfully"}


@app.post("/upload_profile", response_model=dict, tags=['profile'])
def update_profile(payload: UpdateProfileSchema):
    data_split = payload.image.split('base64,')
    encoded_data = data_split[1]
    data = base64.b64decode(encoded_data)
    with open("uploaded_image.png", "wb") as writer:
        writer.write(data)

    return {"detail": "Profile updated successful"}


# 3. Recommendations Handling:
# - Implement a recommendation system based on  user history or preferences.
# - Recommend similar plant type or preventive measures based on past interactions
# - Utilize collaborative filtering or content-based recommendation approaches

# from recommendation_system import get_recommendations


@app.post("/add_recommendation", tags=["recommendation"])
async def add_recommendation(recommendation: RecommendationDetails, db: Session = Depends(get_db)):
    try:
        recommendation = crud.add_recommendation(recommendation, db)
        return recommendation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/get_recommendations/{type_name}', tags=["recommendation"])
async def get_recommendation(type_name: str, db: Session = Depends(get_db)):
    recommendation = crud.get_recommendation(type_name, db)
    return recommendation


@app.put("/update_recommendation/{recommdendation_id}", tags=["recommendation"])
async def update_recommendation(recommendation: RecommendationDetails, recommendation_id: int, db: Session = Depends(get_db)):
    try:
        recommendation = crud.update_recommendation(
            recommendation_id, recommendation, db)
        if recommendation is None:
            raise HTTPException(
                status_code=404, detail="Recommendation not found")

        return {"recommendation": recommendation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

        # will be populated in the history


# 4. History Tracking
# - Track user interactions and predictions made by users
# - Store user-specific prediction history in a database.
# - Provicde users with access to their  prediction history

@app.post("/add_history", tags=["history"])
async def add_history(user_history: UserHistoryDetails, db: Session = Depends(get_db)):
    try:
        history = crud.add_history(user_history, db)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_histories/{user_id}", tags=["history"])
async def get_history(user_id: int, db: Session = Depends(get_db)):
    try:
        latest_history = crud.get_history(user_id, db)
        history = latest_history[-5:]
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail="user history not found")


# 5 creating endpoint for plant information to be manipulated by the admin
# creating post request for adding plant
@app.post("/add_plant", tags=["plants"])
async def add_plants(plant_name: str, plant_description: str, image: UploadFile = File(...), db: Session = Depends(get_db)):
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, detail="Invalid file format. Only JPEG, PNG,JPG, and GIF are allowed.")
    filename = str(uuid.uuid4()) + os.path.splitext(image.filename)[1]
    image_path = os.path.join(str(UPLOAD_PLANT_DIRECTORY), filename)
    # Read image data as bytes
    content = await image.read()

    with io.open(image_path, 'wb') as f:
        f.write(content)

    plant_data = {
        "plant_name": plant_name,
        "plant_description": plant_description,
        "image_path": filename
    }

    try:
        plant = crud.add_plant(plant_data, db)
        print(plant)
        return plant
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# creating get request for getting all plants


@app.get('/get_plants/', tags=["plants"])
async def get_plants(db: Session = Depends(get_db)):
    plants = crud.get_plants(db)
    return plants

# creating get request for getting specific  plants by id


@app.get('/get_plant_specific/{plant_name}', tags=["plants"])
async def get_plant_specific(plant_name: str, db: Session = Depends(get_db)):
    plant = crud.get_plant_specific(plant_name, db)
    return plant
# creating post request updating  plants information


@app.put("/update_plant/{plant_id}", tags=["plants"])
async def update_plant(plant: PlantDetails, plant_id: int, db: Session = Depends(get_db), image: UploadFile = File(...)):
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, detail="Invalid file format. Only JPEG, PNG,JPG, and GIF are allowed.")
    filename = str(uuid.uuid4()) + os.path.splitext(image.filename)[1]
    image_path = os.path.join(str(UPLOAD_PLANT_DIRECTORY), filename)
    # Read image data as bytes
    content = await image.read()

    with io.open(image_path, 'wb') as f:
        f.write(content)
    plant.image_path = filename
    try:
        plant = crud.update_plant(
            plant_id, plant, db)
        if plant is None:
            raise HTTPException(
                status_code=404, detail="Plant not found")

        return {"plant": plant}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# creating post request for deleting  plants information


@app.delete("/delete_plant/{plant_id}", tags=["plants"])
async def delete_plant(plant_id: int, db: Session = Depends(get_db)):
    plant_to_delete = db.query(Plants).filter(Plants.id == plant_id).first()

    if plant_to_delete:
        db.delete(plant_to_delete)
        db.commit()
        return {"plant data deleted successfully"}
    else:
        return {"message": "Plant not found"}


# 6 creating endpoint for plant disease information to be manipulated by the admin
# creating post request for adding plant disease


@app.post("/add_plant_disease", tags=['plants'])
async def add_plant_disease(plant_disease_name: str, plant_disease_description: str, plant_disease_recommendation: str, plant_id: int, image: UploadFile = File(...), db: Session = Depends(get_db)):
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, detail="Invalid file format. Only JPEG, PNG,JPG, and GIF are allowed.")
    filename = str(uuid.uuid4()) + os.path.splitext(image.filename)[1]
    image_path = os.path.join(str(UPLOAD_PLANT_DISEASE_DIRECTORY), filename)
    # Read image data as bytes
    content = await image.read()

    with io.open(image_path, 'wb') as f:
        f.write(content)

    plant_disease_data = {
        "image_path": filename,
        "plant_disease_name": plant_disease_name,
        "plant_disease_description": plant_disease_description,
        "plant_disease_recommendation": plant_disease_recommendation,
        "plant_id": plant_id
    }

    try:
        plant_disease = crud.add_plant_disease(plant_disease_data, db)
        return plant_disease
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# creating get request for getting all plants diseases


@app.get('/get_plant_diseases/', tags=["plants"])
async def get_plant_diseases(db: Session = Depends(get_db)):
    plants = crud.get_plant_diseases(db)
    return plants

# creating get request for getting specific  plants disease by id


@app.get('/get_plant_disease_specific/{plant_id}', tags=["plants"])
async def get_plant_disease_specific(plant_id: int, db: Session = Depends(get_db)):
    plant = crud.get_plant_disease_specific(plant_id, db)
    return plant
# creating post request updating  plants disease information


@app.put("/update_plant_disease/{plant_id}", tags=["plants"])
async def update_plant_disease(plant: PlantDiseasesDetails, plant_id: int, db: Session = Depends(get_db), image: UploadFile = File(...)):
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, detail="Invalid file format. Only JPEG, PNG,JPG, and GIF are allowed.")
    filename = str(uuid.uuid4()) + os.path.splitext(image.filename)[1]
    image_path = os.path.join(str(UPLOAD_PLANT_DISEASE_DIRECTORY), filename)
    # Read image data as bytes
    content = await image.read()

    with io.open(image_path, 'wb') as f:
        f.write(content)
    plant.image_path = filename
    try:
        plant = crud.update_plant_disease(
            plant_id, plant, db)
        if plant is None:
            raise HTTPException(
                status_code=404, detail="plant disease not found")

        return {"plant": plant}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# creating post request for deleting  plants information


@app.delete("/delete_plant_disease/{plant_id}", tags=["plants"])
async def delete_plant(plant_id: int, db: Session = Depends(get_db)):
    plant_disease_to_delete = db.query(PlantDiseases).filter(
        PlantDiseases.id == plant_id).first()

    if plant_disease_to_delete:
        db.delete(plant_disease_to_delete)
        db.commit()
        return {"plant disease data deleted successfully"}
    else:
        return {"message": "Plant Disease not found"}

# 7 creating endpoint for plant type information to be manipulated by the admin
# creating post request for adding plant type


@app.post("/add_plant_type", tags=["plants"])
async def add_plant_type(plant_type_name: str, plant_type_description: str, plant_id: int, image: UploadFile = File(...), db: Session = Depends(get_db)):
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, detail="Invalid file format. Only JPEG, PNG,JPG, and GIF are allowed.")
    filename = str(uuid.uuid4()) + os.path.splitext(image.filename)[1]
    image_path = os.path.join(str(UPLOAD_PLANT_TYPES_DIRECTORY), filename)
    # Read image data as bytes
    content = await image.read()

    with io.open(image_path, 'wb') as f:
        f.write(content)

    plant_type = {
        "plant_type_name": plant_type_name,
        "plant_type_description": plant_type_description,
        "plant_id": plant_id,
        "image_path": filename
    }
    try:
        plant = crud.add_plant_type(plant_type, db)
        return plant
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# creating get request for getting all plants types


@app.get('/get_plant_types/', tags=["plants"])
async def get_plant_types(db: Session = Depends(get_db)):
    plants = crud.get_plant_types(db)
    return plants

# creating get request for getting specific  plants by id


@app.get('/get_plant_type_specific/{plant_id}', tags=["plants"])
async def get_plant_type_specific(plant_id: str, db: Session = Depends(get_db)):
    plant = crud.get_plant_type_specific(plant_id, db)
    return plant
# creating post request updating  plants information


@app.put("/update_plant_type/{plant_id}", tags=["plants"])
async def update_plant_type(plant: PlantTypesDetails, plant_id: int, db: Session = Depends(get_db), image: UploadFile = File(...)):
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, detail="Invalid file format. Only JPEG, PNG,JPG, and GIF are allowed.")
    filename = str(uuid.uuid4()) + os.path.splitext(image.filename)[1]
    image_path = os.path.join(str(UPLOAD_PLANT_TYPES_DIRECTORY), filename)
    # Read image data as bytes
    content = await image.read()

    with io.open(image_path, 'wb') as f:
        f.write(content)
    plant.image_path = filename

    try:
        plant = crud.update_plant_type(
            plant_id, plant, db)
        if plant is None:
            raise HTTPException(
                status_code=404, detail="plant_type not found")

        return {"plant": plant}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# creating post request for deleting  plants information


@app.delete("/delete_plant_type/{plant_id}", tags=["plants"])
async def delete_plant(plant_id: int, db: Session = Depends(get_db)):
    plant_type_to_delete = db.query(PlantTypes).filter(
        PlantTypes.id == plant_id).first()

    if plant_type_to_delete:
        db.delete(plant_type_to_delete)
        db.commit()
        return {"plant type data deleted successfully"}
    else:
        return {"message": "Plant Type not found"}

# testing image upload and display


@app.post("/upload-image")
async def upload_image(image: UploadFile = File(...)):
    # Generate a unique filename
    filename = str(uuid.uuid4()) + os.path.splitext(image.filename)[1]
    image_path = os.path.join(str(UPLOAD_DIRECTORY), filename)

    # Read image data as bytes
    content = await image.read()

    # Open the destination file in binary write mode
    with io.open(image_path, 'wb') as f:
        f.write(content)

    return {"message": "Image uploaded successfully!", "filename": filename}


async def save_uploaded_image(file: UploadFile = File(...)):
    # Generate a unique filename
    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
    image_path = os.path.join(str(UPLOAD_DIRECTORY), filename)

    # Read image data as bytes
    content = await file.read()

    file = io.open(image_path, 'wb')  # Open the file
    try:
        file.write(content)
    finally:
        file.close()  # Close the file even if there's an exception

    return {
        "message": "Image uploaded successfully!",
        "filename": filename,
        "full_path": os.path.join(str(UPLOAD_DIRECTORY), filename)
    }
if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8000)
