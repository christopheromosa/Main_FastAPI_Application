from fastapi import FastAPI, Depends, HTTPException, Cookie, Response, Request, File, UploadFile
from sqlalchemy.orm import Session, joinedload
import models
import schemas


def get_users(db: Session):
    user = db.query(models.User).all()
    return user



def check_existing_user(username, db: Session):
    existing_user = db.query(models.User).filter_by(username=username).first()
    return existing_user


def create_user(user, db: Session, encrypted_password):
    new_user = models.User(username=user.username, email=user.email, occupation=user.occupation,
                           password=encrypted_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "message": f"Account created successfully for user {new_user.username}"
    }


def add_recommendation(recommmendation, db=Session):
    recommendation = models.Recommendation(
        disease_name=recommendation.disease_name, preventive_measure=recommendation.preventive_measure)
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return {"recommendation": recommendation, "message": "recommendation added"}


def get_recommendation(disease_name: str, db: Session):
    recommendation = db.query(models.Recommendation).filter(
        models.Recommendation.disease_name == disease_name)

    return {
        "disease_name": recommendation.disease_name,
        "recommendation": recommendation.preventive_measure
    }


def update_recommendation(recommendation_id: int, recommendation, db: Session):
    try:
        recommendation_result = db.query(models.Recommendation).filter(
            models.Recommendation.id == recommendation_id).first()
        if recommendation_result is None:
            raise HTTPException(
                status_code=404, detail="Recommendation not found")

        recommendation_result.disease_name = recommendation.disease_name
        recommendation_result.preventive_measure = recommendation.preventive_measure
        db.commit()
        db.refresh(recommendation_result)
        return recommendation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

        # will be populated in the history


# 2. History Tracking
# - Track user interactions and predictions made by users
# - Store user-specific prediction history in a database.
# - Provicde users with access to their  prediction history


def add_history(db: Session, user_id: str, image_path: str, prediction: str, confidence, preventive_measure:str):
    history = models.User_history(user_id=user_id, image_path=image_path, prediction=prediction,
                                  confidence=confidence,preventive_measure=preventive_measure)

    db.add(history)
    db.commit()
    db.refresh(history)
    return {"history": history, "message": "history added"}


def get_history(user_id: int, db: Session):
    history = db.query(models.User_history).filter(
        models.User_history.user_id == user_id).all()
    return history


def add_plant(plant_data, db=Session):
    plant = models.Plants(
        image_path=plant_data["image_path"], plant_name=plant_data["plant_name"], plant_description=plant_data["plant_description"])
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return {"plant": plant, "message": "plant added"}


def get_plants(db: Session):
    plants = db.query(models.Plants).options(joinedload(
        models.Plants.diseases), joinedload(models.Plants.types)).all()

    return {
        "plants": plants
    }


def get_plant_specific(plant_name: str, db: Session):
    plant = db.query(models.Plants).filter(
        models.Plants.plant_name == plant_name).options(joinedload(
            models.Plants.diseases), joinedload(models.Plants.types)).first()
    print(plant)

    return {
        "plant": plant,
    }


def update_plant(plant_id: int, plant, db: Session):
    try:
        plant_result = db.query(models.Plants).filter(
            models.Plants.id == plant_id).first()
        if plant_result is None:
            raise HTTPException(
                status_code=404, detail="plant not found")

        plant_result.image_path = plant.image_path
        plant_result.plant_name = plant.plant_name
        plant_result.plant_description = plant.plant_description

        db.commit()
        db.refresh(plant_result)
        return plant_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Plant Disease

def add_plant_disease(plant_disease_data, db=Session):
    plant_disease = models.PlantDiseases(
        image_path=plant_disease_data["image_path"], plant_disease_name=plant_disease_data["plant_disease_name"], plant_disease_description=plant_disease_data["plant_disease_description"], plant_disease_recommendation=plant_disease_data["plant_disease_recommendation"], plant_id=plant_disease_data["plant_id"])
    db.add(plant_disease)
    db.commit()
    db.refresh(plant_disease)
    return {"plant disease": plant_disease, "message": "plant disease added"}


def get_plant_diseases(db: Session):
    plants_disease = db.query(models.PlantDiseases).all()

    return {
        "plants_disease": plants_disease
    }


def get_plant_disease_specific(plant_id: int, db: Session):
    plant_disease = db.query(models.PlantDiseases).filter(
        models.PlantDiseases.id == plant_id).first()

    return {
        "plant_disease": plant_disease,
    }


def update_plant_disease(plant_id: int, plant, db: Session):
    try:
        plant_disease_result = db.query(models.PlantDiseases).filter(
            models.PlantDiseases.id == plant_id).first()
        if plant_disease_result is None:
            raise HTTPException(
                status_code=404, detail="plant disease not found")

        plant_disease_result.image_path = plant.image_path
        plant_disease_result.plant_disease_name = plant.plant_disease_name
        plant_disease_result.plant_disease_description = plant.plant_disease_description
        plant_disease_result.plant_disease_recommendation = plant.plant_disease_recommendation
        plant_disease_result.plant_id = plant.plant_id

        db.commit()
        db.refresh(plant_disease_result)
        return plant_disease_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Plant Types


def add_plant_type(plant_type, db=Session):
    plant_type_data = models.PlantTypes(
        image_path=plant_type["image_path"], plant_type_name=plant_type["plant_type_name"], plant_type_description=plant_type["plant_type_description"], plant_id=plant_type["plant_id"])
    db.add(plant_type_data)
    db.commit()
    db.refresh(plant_type_data)
    return {"plant_type": plant_type_data, "message": "plant type added"}


def get_plant_types(db: Session):
    plants_type = db.query(models.PlantTypes).all()

    return {
        "plants_type": plants_type
    }


def get_plant_type_specific(plant_id: int, db: Session):
    plant_type = db.query(models.PlantTypes).filter(
        models.PlantTypes.id == plant_id).first()

    return {
        "plant_type": plant_type,
    }

def update_plant_type(plant_id: int, plant, db: Session):
    try:
        plant_type_result = db.query(models.PlantTypes).filter(
            models.PlantTypes.id == plant_id).first()
        if plant_type_result is None:
            raise HTTPException(
                status_code=404, detail="plant not found")

        plant_type_result.image_path = plant.image_path
        plant_type_result.plant_type_name = plant.plant_type_name
        plant_type_result.plant_type_description = plant.plant_type_description
        plant_type_result.plant_id = plant.plant_id

        db.commit()
        db.refresh(plant_type_result)
        return plant_type_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
