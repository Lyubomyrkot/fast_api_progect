from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Union 


# Створення екземпляру FastAPI
app = FastAPI()
tracks = [
    {"id": 1, 
     "title": "MEMORIZING", 
     "artist": "DJ DELACROIX"},
    {"id": 2, 
     "title": "Focus 2", 
     "artist": "quietshadow"}
]

class Track(BaseModel):
    id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=100)
    artist: str = Field(min_length=1, max_length=100)

class TrackUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    artist: str = Field(min_length=1, max_length=100)

# Маршрут, який обробляє GET-запити на кореневий шлях
@app.get("/")
async def index():
    return "Hello FastAPI!"


@app.get("/tracks/all")
async def get_all_tracks():
    return {"tracks": tracks}


@app.get("/tracks/{track_id}")
async def get_track(track_id: int):
    for track in tracks:
        if track["id"] == track_id:
            return {"track": track}
    return {"error": "Track not found"}


@app.put("/tracks/{track_id}")
async def update_track(track_id: int, body: TrackUpdate):
    update_track = body.model_dump()
    for track in tracks:
        if track["id"] == track_id:
            track.update(update_track)
            return {"message": "Track updated successfully", "track": track}

        
    return {"error": "Track not found"}


@app.post("/tracks/add")
async def add_new_track(track: Track):
    track_dict = track.model_dump()
    tracks.append(track_dict)
    return {"message": "Track added successfully", 
            "track": track_dict}


@app.delete("/tracks/delete/{track_id}")
async def delete_track(track_id: int):
    for track in tracks:
        if track["id"] == track_id:
            tracks.remove(track)
            return {"message": "Track deleted successfully"}
    return {"error": "Track not found"}

@app.get("/search")
async def search_tracks(q: str = Query(..., min_length=1, max_length=100, description="Search query for track title or artist")
                        ):
    q = q.strip().lower()
    result = [track for track in tracks if q in track["title"].lower() or q in track["artist"].lower()]
    if result:
        return {'query': q, 'tracks': result}
    else:
        return {'message': 'No tracks found matching the query.'}
