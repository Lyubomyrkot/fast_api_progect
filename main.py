from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Union, Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select

from model import Artist, Track

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# Створення екземпляру FastAPI
app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

tracks = [
    {"id": 1, 
     "name": "MEMORIZING", 
     "artist": "DJ DELACROIX",
     "album": "MEMORIZING"},
    {"id": 2, 
     "name": "Focus 2", 
     "artist": "quietshadow",
     "album": "Focus"}
]

class TrackUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    artist: str = Field(min_length=1, max_length=100)
    album: Annotated[str | None, Field(min_length=2, max_length=100)]

# Маршрут, який обробляє GET-запити на кореневий шлях
@app.get("/")
async def index():
    return "Hello FastAPI!"


@app.get("/tracks/all")
async def get_all_tracks(session: SessionDep):
    tracks = session.exec(select(Track)).all()
    return {"tracks": tracks}


@app.get("/tracks/{track_id}")
async def get_track(track_id: int, session: SessionDep):
    track = session.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return {"track": track}


@app.put("/tracks/{track_id}")
async def update_track(track_id: int, body: TrackUpdate):
    update_track = body.model_dump()
    for track in tracks:
        if track["id"] == track_id:
            track.update(update_track)
            return {"message": "Track updated successfully", "track": track}

        
    return {"error": "Track not found"}


@app.post("/tracks/add")
async def add_new_track(track: Track, session: SessionDep):
    session.add(track)
    session.commit()
    session.refresh(track)
    return track


@app.delete("/tracks/delete/{track_id}")
async def delete_track(track_id: int, session: SessionDep):
    track = session.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    session.delete(track)
    session.commit()
    return {"message": "Track deleted successfully"}

@app.get("/search")
async def search_tracks(q: str = Query(..., min_length=1, max_length=100, description="Search query for track title or artist")
                        ):
    q = q.strip().lower()
    result = [track for track in tracks if q in track["title"].lower() or q in track["artist"].lower()]
    if result:
        return {'query': q, 'tracks': result}
    else:
        return {'message': 'No tracks found matching the query.'}
