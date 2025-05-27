from fastapi import FastAPI, Depends
from sqlalchemy.sql import text
from database import get_db
from sqlalchemy.orm import Session
from consultas import consulta_get
from fastapi.middleware.cors import CORSMiddleware


# from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

origins = [
    "http://localhost:4200",
    "http://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# class CookieMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#             token = request.cookies.get('BBSSOToken')
#             if token:
#                 response = await call_next(request)
#             else:
#                 response = Response(content="Unauthorized", status_code=401)
#             return response

# app.add_middleware(CookieMiddleware)

@app.get('/teste')
def teste(session: Session = Depends(get_db)):
    query = """
        SELECT * FROM DB2PORTAL.PSTG
    """
    return consulta_get(query, session)