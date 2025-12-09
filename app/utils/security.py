from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import secrets
import string
from app.config.settings import settings
from app.schemas.auth.auth_schema import TokenPayload
from app.models.users.user_model import UserRole

# Contexto para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica que una contraseña en texto plano coincida con el hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Genera un hash de una contraseña.
    """
    return pwd_context.hash(password)


def generate_random_password(length: int = 12) -> str:
    """
    Genera una contraseña aleatoria segura.

    Args:
        length: Longitud de la contraseña (por defecto 12)

    Returns:
        Contraseña generada aleatoriamente con mayúsculas, minúsculas, números y símbolos
    """
    # Definir los caracteres a usar
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%&*"

    # Asegurar que la contraseña tenga al menos un carácter de cada tipo
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(symbols),
    ]

    # Rellenar el resto de la contraseña con caracteres aleatorios
    all_characters = lowercase + uppercase + digits + symbols
    password += [secrets.choice(all_characters) for _ in range(length - 4)]

    # Mezclar la contraseña
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


def create_access_token(user_id: int, business_id: int, role: UserRole) -> str:
    """
    Crea un access token JWT.
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "user_id": user_id,
        "business_id": business_id,
        "role": role.value,
        "exp": expire,
        "type": "access",
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: int, business_id: int, role: UserRole) -> str:
    """
    Crea un refresh token JWT.
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "user_id": user_id,
        "business_id": business_id,
        "role": role.value,
        "exp": expire,
        "type": "refresh",
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenPayload]:
    """
    Decodifica y valida un token JWT.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(
            user_id=payload.get("user_id"),
            business_id=payload.get("business_id"),
            role=UserRole(payload.get("role")),
            exp=payload.get("exp"),
        )
        return token_data
    except JWTError:
        return None
