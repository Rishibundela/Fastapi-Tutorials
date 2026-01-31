from fastapi import FastAPI,Path, Query,HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal
import json

app = FastAPI()

class Patient(BaseModel):
  id: str = Field(..., description="Unique identifier for the patient", example="P001")
  name: str = Field(..., description="Full name of the patient", example="John Doe")
  city: str = Field(..., description="City of residence", example="New York")
  age: int = Field(..., description="Age of the patient in years", example=30, ge=0)
  gender: Literal["male", "female"] = Field(..., description="Gender of the patient", example="male")
  height: float = Field(..., description="Height of the patient in meters", example=1.75, ge=0)
  weight: float = Field(..., description="Weight of the patient in kilograms", example=75, ge=0)

  @computed_field
  @property
  def bmi(self) -> float:
    return round(self.weight / (self.height ** 2), 2)
  
  @computed_field
  @property
  def verdict(self) -> str:
    bmi = self.bmi
    if bmi < 18.5:
      return "Underweight"
    elif 18.5 <= bmi < 24.9:
      return "Normal weight"
    elif 25 <= bmi < 29.9:
      return "Overweight"
    else:
      return "Obese"
    
class PatientUpdate(BaseModel):
  name: Annotated[str | None, Field(description="Full name of the patient", example="John Doe")] = None
  city: Annotated[str | None, Field(description="City of residence", example="New York")] = None
  age: Annotated[int | None, Field(description="Age of the patient in years", example=30, ge=0)] = None
  gender: Annotated[Literal["male", "female"] | None, Field(description="Gender of the patient", example="male")] = None
  height: Annotated[float | None, Field(description="Height of the patient in meters", example=1.75, ge=0)] = None
  weight: Annotated[float | None, Field(description="Weight of the patient in kilograms", example=75, ge=0)] = None

# ---------------------------------- Utility Functions ---------------------------------- 
# Load patient data from JSON file
def load_data():
  with open('patients.json', 'r') as f:
    data = json.load(f)
  return data

# Save patient data to JSON file
def save_data(data):
  with open('patients.json', 'w') as f:
    json.dump(data, f, indent=4)

# ---------------------------------- API Endpoints ----------------------------------
@app.get('/')
def hello():
  return {"message": "Patient Management System API"}

@app.get('/about')
def about():
  return {"message": "A fully functional API to manage patient records efficiently."}

@app.get('/patients')
def view_data():
  data = load_data()
  return data

@app.get('/patients/{patient_id}')
def get_patient(patient_id: str = Path(..., description="The ID of the patient to retrieve",example="P001")):
  data = load_data()
  patient = data.get(patient_id)
  if patient:
    return patient
  raise HTTPException(status_code=404, detail="Patient not found")

@app.get('/sort')
def sort_patients(sort_by: str = Query(..., description="The attribute to sort patients by (e.g. age, bmi, weight, height)", example="age"), order: str = Query('asc', description="Sort order: 'asc' for ascending, 'desc' for descending", example="asc")):
  
  if sort_by not in ['age', 'bmi', 'weight', 'height']:
    raise HTTPException(status_code=400, detail="Invalid sort attribute")
  if order not in ['asc', 'desc']:
    raise HTTPException(status_code=400, detail="Invalid sort order")
  
  data = load_data()
  sort_order = True if order == 'desc' else False
  sorted_patients = dict(sorted(data.items(), key=lambda item: item[1][sort_by], reverse=sort_order))
  return sorted_patients

@app.post('/create')
def create_patient(patient: Patient):
  # Load existing data
  data = load_data()
  
  # Check if patient ID already exists
  if patient.id in data:
    raise HTTPException(status_code=400, detail="Patient ID already exists")
  
  # New patient record
  data[patient.id] = patient.model_dump(exclude={'id'})
  
  # Save updated data back to the file
  save_data(data)
  
  return JSONResponse(status_code=201, content={"message": "Patient record created successfully", "patient": data[patient.id]})

@app.put('/update/{patient_id}')
def update_patient(patient_id: str = Path(..., description="The ID of the patient to update",example="P001"), patient_update: PatientUpdate = ...):
  data = load_data()
  if patient_id not in data:
    raise HTTPException(status_code=404, detail="Patient not found")
  
  # Update patient data
  for field, value in patient_update.model_dump(exclude_unset=True).items():
    data[patient_id][field] = value

  # Recalculate BMI and verdict if height or weight is updated
  pydantic_patient = Patient(id=patient_id, **data[patient_id])
  data[patient_id] = pydantic_patient.model_dump(exclude={'id'})

  save_data(data)
  return JSONResponse(status_code=200, content={"message": "Patient record updated successfully", "patient": data[patient_id]})

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str = Path(..., description="The ID of the patient to delete",example="P001")):
  data = load_data()
  if patient_id in data:
    del data[patient_id]
    save_data(data)
    return JSONResponse(status_code=200, content={"message": "Patient record deleted successfully"})
  raise HTTPException(status_code=404, detail="Patient not found")