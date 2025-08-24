from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class RaceInput(BaseModel):
    distance_miles: float        # race distance in miles
    elevation_gain_ft: float     # total climb in feet
    elevation_loss_ft: float     # total descent in feet
    flat_speed_mph: float        # your flat speed in mph

# Conversion constants
MILES_TO_KM = 1.60934
FEET_TO_METERS = 0.3048

@app.post("/predict")
def predict_time(data: RaceInput):
    # Convert to metric internally
    distance_km = data.distance_miles * MILES_TO_KM
    elevation_gain_m = data.elevation_gain_ft * FEET_TO_METERS
    elevation_loss_m = data.elevation_loss_ft * FEET_TO_METERS
    flat_speed_kmh = data.flat_speed_mph * MILES_TO_KM

    # --- Base time ---
    base_time_hours = distance_km / flat_speed_kmh

    # --- Uphill penalty ---
    climb_penalty = (elevation_gain_m / 100.0) * 0.5 / 60.0  # hours

    # --- Downhill adjustment ---
    avg_downhill_grade = elevation_loss_m / (distance_km * 1000)  # % grade in decimal (m/m)
    avg_downhill_grade_pct = avg_downhill_grade * 100

    if avg_downhill_grade_pct <= 5:
        # full benefit
        downhill_bonus = (elevation_loss_m / 100.0) * -0.1 / 60.0
    else:
        # taper: only count as if 5% grade
        effective_loss_m = (distance_km * 1000) * 0.05  # 5% grade max effective
        downhill_bonus = (effective_loss_m / 100.0) * -0.1 / 60.0

    # --- Total time ---
    total_time_hours = base_time_hours + climb_penalty + downhill_bonus
    total_time_minutes = total_time_hours * 60

    return {
        "predicted_time_hours": round(total_time_hours, 2),
        "predicted_time_minutes": round(total_time_minutes, 1),
        "details": {
            "base_time_hours": round(base_time_hours, 2),
            "climb_penalty_hours": round(climb_penalty, 2),
            "downhill_bonus_hours": round(downhill_bonus, 2),
            "avg_downhill_grade_pct": round(avg_downhill_grade_pct, 1)
        }
    }
