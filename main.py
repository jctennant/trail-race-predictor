from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import math

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


def predict_time_tobler(distance_miles, elevation_gain_ft):
    """
    Predicts race time using Tobler’s hiking function scaled for running
    and an ultra-distance fatigue curve.
    """
    # --- Convert units ---
    distance_km = distance_miles * MILES_TO_KM
    elevation_gain_m = elevation_gain_ft * FEET_TO_METERS

    # --- Average slope ---
    slope = elevation_gain_m / (distance_km * 1000.0)

    # --- Tobler’s Hiking Function (base hiking speed in km/h) ---
    hiking_speed_kmh = 6 * math.exp(-3.5 * abs(slope + 0.05))

    # --- Scale for running (roughly 2.5x faster than hiking) ---
    running_speed_kmh = hiking_speed_kmh * 2.5

    # --- Tobler time ---
    tobler_time_hours = distance_km / running_speed_kmh
    tobler_time_minutes = tobler_time_hours * 60

    # --- Ultra-distance fatigue adjustment ---
    if distance_km > 42.2:
        fatigue_factor = 1 + 0.15 * math.log(distance_km / 42.2)
    else:
        fatigue_factor = 1.0

    adjusted_time_minutes = tobler_time_minutes * fatigue_factor

    return adjusted_time_minutes, tobler_time_minutes, fatigue_factor


@app.post("/predict")
def predict_time(data: RaceInput):
    # --- Base Tobler + fatigue prediction ---
    adjusted_time_minutes, tobler_time_minutes, fatigue_factor = predict_time_tobler(
        data.distance_miles,
        data.elevation_gain_ft
    )

    # --- Paces ---
    avg_pace_min_per_mile = adjusted_time_minutes / data.distance_miles
    grade_adjusted_pace_min_per_mile = tobler_time_minutes / data.distance_miles

    return {
        "predicted_time_minutes": round(adjusted_time_minutes, 1),
        "predicted_time_hours": round(adjusted_time_minutes / 60, 2),
        "average_pace_min_per_mile": round(avg_pace_min_per_mile, 2),
        "grade_adjusted_pace_min_per_mile": round(grade_adjusted_pace_min_per_mile, 2),
        "details": {
            "tobler_time_minutes": round(tobler_time_minutes, 1),
            "fatigue_factor": round(fatigue_factor, 3),
            "slope": round(data.elevation_gain_ft * FEET_TO_METERS / (data.distance_miles * MILES_TO_KM * 1000.0), 4),
        }
    }
