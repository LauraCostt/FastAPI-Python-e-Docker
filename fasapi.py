from fastapi import FastAPI, APIRouter, Query, HTTPException
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from fastapi_pagination import Page, add_pagination, paginate
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class AtletaBase(BaseModel):
    nome: str
    cpf: str
    centro_treinamento: str
    categoria: str

class AtletaCreate(AtletaBase):
    pass

class AtletaResponse(AtletaBase):
    id: int

    class Config:
        orm_mode = True

class Atleta(Base):
    __tablename__ = "atletas"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    cpf = Column(String, unique=True, index=True)
    centro_treinamento = Column(String)
    categoria = Column(String)

Base.metadata.create_all(bind=engine)

app = FastAPI()
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/atletas", response_model=AtletaResponse)
async def create_atleta(atleta: AtletaCreate, db: SessionLocal = next(get_db())):
    try:
        novo_atleta = Atleta(**atleta.dict())
        db.add(novo_atleta)
        db.commit()
        db.refresh(novo_atleta)
        return novo_atleta
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=303, detail=f"Já existe um atleta cadastrado com o cpf: {atleta.cpf}")

@router.get("/atletas", response_model=Page[AtletaResponse])
async def get_atletas(
    nome: Optional[str] = Query(None), 
    cpf: Optional[str] = Query(None), 
    db: SessionLocal = next(get_db())
):
    query = db.query(Atleta)
    if nome:
        query = query.filter(Atleta.nome == nome)
    if cpf:
        query = query.filter(Atleta.cpf == cpf)
    return paginate(query.all())

app.include_router(router)
add_pagination(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
