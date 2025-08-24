from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# --- CORS setup ---
origins = [
    "http://localhost:3000",           # local dev
    "https://trail-genie.lovable.app"  # your Lovable frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # use ["*"] if debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Input model ---
class RaceInput(BaseModel):
    distance_miles: float        # target race distance in miles
    elevation_gain_ft: float     # total climb in feet
    pr_distance_miles: float     # PR distance (e.g. 3.1 for 5K, 26.2 for marathon)
    pr_time_minutes: float       # PR time in minutes


# --- Conversion constants ---
MILES_TO_KM = 1.60934
FEET_TO_METERS = 0.3048


@app.post("/predict")
def predict_time(data: RaceInput):
    # --- Convert inputs ---
    distance_km = data.distance_miles * MILES_TO_KM
    elevation_gain_m = data.elevation_gain_ft * FEET_TO_METERS
    pr_distance_km = data.pr_distance_miles * MILES_TO_KM

    # --- Calculate base speed from PR ---
    pr_pace_min_per_km = data.pr_time_minutes / pr_distance_km  # minutes per km
    pr_speed_kmh = 60 / pr_pace_min_per_km

    # --- Adjust speed based on distance scaling ---
    # Simple Riegel formula: T2 = T1 * (D2 / D1) ^ 1.06
    predicted_time_minutes_flat = data.pr_time_minutes * (distance_km / pr_distance_km) ** 1.06
    flat_speed_kmh = distance_km / (predicted_time_minutes_flat / 60)

    # --- Elevation penalty (very simple model) ---
    climb_penalty_minutes = (elevation_gain_m / 100.0) * 0.5  # 0.5 min per 100m
    total_time_minutes = predicted_time_minutes_flat + climb_penalty_minutes

    # --- Paces ---
    avg_pace_min_per_mile = total_time_minutes / data.distance_miles
    grade_adjusted_pace_min_per_mile = predicted_time_minutes_flat / data.distance_miles

    return {
        "predicted_time_minutes": round(total_time_minutes, 1),
        "predicted_time_hours": round(total_time_minutes / 60, 2),
        "average_pace_min_per_mile": round(avg_pace_min_per_mile, 2),
        "grade_adjusted_pace_min_per_mile": round(grade_adjusted_pace_min_per_mile, 2),
        "details": {
            "flat_time_minutes": round(predicted_time_minutes_flat, 1),
            "climb_penalty_minutes": round(climb_penalty_minutes, 1),
            "pr_pace_min_per_km": round(pr_pace_min_per_km, 2),
        }
    }
