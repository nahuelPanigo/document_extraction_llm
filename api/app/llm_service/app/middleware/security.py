from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv
load_dotenv()

auth_scheme = HTTPBearer()

EXPECTED_TOKEN = os.getenv("SERVICE_TOKEN")

async def verify_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    token = credentials.credentials
    print(f"token: {token}")
    print(f"expected token: {EXPECTED_TOKEN}")
    if token != EXPECTED_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token"
        )