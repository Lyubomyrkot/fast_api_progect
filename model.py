from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select


class Artist(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    bio: Annotated[str | None, Field(min_length=2, max_length=500)]
    tracks: list["Track"] = Relationship(back_populates="artist")

class Track(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    artist_id: str = Field(foreign_key="artist.id")
    album: Annotated[str | None, Field(min_length=2, max_length=100)]

    artist: Artist = Relationship(back_populates="tracks")

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, min_length=3, max_length=100)
    login: str = Field(index=True, min_length=3, max_length=100, unique=True)
    password: str = Field(min_length=8, max_length=100)
