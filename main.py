from fastapi import FastAPI, UploadFile, File
import gpxpy
import numpy as np
from scipy.signal import find_peaks

app = FastAPI()

@app.post("/upload")
async def upload_gpx(file: UploadFile = File(...)):
    contents = await file.read()
    gpx = gpxpy.parse(contents.decode("utf-8"))

    speeds = []
    for track in gpx.tracks:
        for segment in track.segments:
            for i in range(1, len(segment.points)):
                p1 = segment.points[i - 1]
                p2 = segment.points[i]
                delta_t = (p2.time - p1.time).total_seconds()
                if delta_t == 0:
                    continue
                dist = p1.distance_3d(p2) / 1000  # km
                speed = dist / (delta_t / 3600)  # km/h
                speeds.append(speed)

    hist, bins = np.histogram(speeds, bins=30, range=(0, 30))
    peaks, _ = find_peaks(hist, height=5)

    ranges = []
    for peak in peaks:
        low = bins[max(peak - 1, 0)]
        high = bins[min(peak + 1, len(bins) - 1)]
        ranges.append((low, high))

    result = []
    for speed in speeds:
        gait = "UNKNOWN"
        for i, (low, high) in enumerate(ranges):
            if low <= speed <= high:
                gait = ["WALK", "TROT", "GALLOP"][i] if i < 3 else "FAST"
                break
        result.append({"speed": round(speed, 2), "gait": gait})

    return {
        "stats": {
            "total_points": len(speeds),
            "gaits": {g: sum(1 for r in result if r["gait"] == g) for g in ["WALK", "TROT", "GALLOP", "UNKNOWN"]}
        }
    }
