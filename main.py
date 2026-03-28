from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Union, Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select

from model import Artist, Track, User

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = "19109197bd5e7c289b92b2b355083ea26c71dee2085ceccc19308a7291b2ea06"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def token_create(data: dict):
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

SessionDep = Annotated[Session, Depends(get_session)]

# Створення екземпляру FastAPI
app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


class TrackUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    artist: str = Field(min_length=1, max_length=100)
    album: Annotated[str | None, Field(min_length=2, max_length=100)]


@app.post("/token")
async def token_get(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):
    user_db = session.exec(select(User).where(User.login == form_data.username)).first()
    if not user_db or form_data.password != user_db.password:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    token = token_create({"username": user_db.login})
    return {"access_token": token, "token_type": "bearer"}


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


@app.patch("/tracks/{track_id}")
async def update_track(track_id: int, body: TrackUpdate, session: SessionDep, token: str = Depends(oauth2_scheme)):
    
    track = session.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    update_track = body.model_dump(exclude_unset=True)
    track.sqlmodel_update(update_track)
    session.add(track)
    session.commit()
    session.refresh(track)

    return {"message": "Track updated successfully", "track": track}


@app.post("/tracks/add")
async def add_new_track(track: Track, session: SessionDep, token: str = Depends(oauth2_scheme)):
    session.add(track)
    session.commit()
    session.refresh(track)
    return track


@app.delete("/tracks/delete/{track_id}")
async def delete_track(track_id: int, session: SessionDep, token: str = Depends(oauth2_scheme)):
    track = session.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    session.delete(track)
    session.commit()
    return {"message": "Track deleted successfully"}

@app.get("/search")
async def search_tracks(
        q: Annotated[str, Query(..., min_length=1, max_length=100, description="Search query for track title or artist")],
        session: SessionDep
    ):
    q = q.strip().lower()
    result = session.exec(select(Track).where(Track.name.ilike(f"%{q}%"))).all()
    if len(result) == 0:
        raise HTTPException(status_code=404, detail="No tracks found matching the query")

    else:
        return {'query': q, 'tracks': result}
