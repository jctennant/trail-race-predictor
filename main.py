from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class RaceInput(BaseModel):
    distance_miles: float         # target race distance in miles
    elevation_gain_ft: float      # elevation gain in feet
    race_pr_minutes: float        # PR time (minutes)
    race_pr_type: str             # one of "5k", "10k", "half", "marathon"

# Conversion constants
MILES_TO_KM = 1.60934
FEET_TO_METERS = 0.3048

# Standard race distances in miles
STANDARD_DISTANCES = {
    "5k": 3.10686,
    "10k": 6.21371,
    "half": 13.1094,
    "marathon": 26.2188
}

@app.post("/predict")
def predict_time(data: RaceInput):
    # --- Step 1: validate race type ---
    if data.race_pr_type not in STANDARD_DISTANCES:
        return {"error": "race_pr_type must be one of '5k', '10k', 'half', 'marathon'"}
    
    # --- Step 2: calculate flat speed from PR ---
    pr_distance = STANDARD_DISTANCES[data.race_pr_type]
    pr_time_hours = data.race_pr_minutes / 60.0
    flat_speed_mph = pr_distance / pr_time_hours  # miles per hour
    
    # --- Step 3: base time on flat terrain ---
    base_time_hours = data.distance_miles / flat_speed_mph
    
    # --- Step 4: elevation penalty ---
    elevation_gain_m = data.elevation_gain_ft * FEET_TO_METERS
    climb_penalty = (elevation_gain_m / 100.0) * 0.5 / 60.0  # hours
    
    # --- Step 5: total predicted time ---
    total_time_hours = base_time_hours + climb_penalty
    total_time_minutes = total_time_hours * 60
    
    return {
        "predicted_time_hours": round(total_time_hours, 2),
        "predicted_time_minutes": round(total_time_minutes, 1),
        "details": {
            "flat_speed_mph": round(flat_speed_mph, 2),
            "base_time_hours": round(base_time_hours, 2),
            "climb_penalty_hours": round(climb_penalty, 2)
        }
    }
