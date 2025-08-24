from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# --- Enable CORS for Lovable frontend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trail-genie.lovable.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RaceInput(BaseModel):
    distance_miles: float        # target race distance in miles
    elevation_gain_ft: float     # total climb in feet
    race_pr_minutes: float       # PR time (in minutes)
    race_pr_distance_miles: float  # distance of that PR in miles

MILES_TO_KM = 1.60934
FEET_TO_METERS = 0.3048

@app.post("/predict")
def predict_time(data: RaceInput):
    # --- Step 1: Adjust PR to target distance using Riegel’s formula ---
    pr_time_hours = data.race_pr_minutes / 60.0
    fatigue_exponent = 1.06 if data.distance_miles <= 26.2 else 1.08  # ultras slow more
    predicted_flat_time_hours = pr_time_hours * (data.distance_miles / data.race_pr_distance_miles) ** fatigue_exponent

    # --- Step 2: Base pace ---
    base_time_hours = predicted_flat_time_hours

    # --- Step 3: Uphill penalty ---
    elevation_gain_m = data.elevation_gain_ft * FEET_TO_METERS
    climb_penalty = (elevation_gain_m / 100.0) * 0.5 / 60.0  # extra hours

    # --- Step 4: Final total time ---
    total_time_hours = base_time_hours + climb_penalty
    total_time_minutes = total_time_hours * 60

    return {
        "predicted_time_hours": round(total_time_hours, 2),
        "predicted_time_minutes": round(total_time_minutes, 1),
        "details": {
            "base_time_hours_flat": round(base_time_hours, 2),
            "climb_penalty_hours": round(climb_penalty, 2),
            "fatigue_exponent_used": fatigue_exponent,
            "pr_distance_miles": data.race_pr_distance_miles,
            "target_distance_miles": data.distance_miles,
        }
    }
