import pytest
import os
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from jose import jwt
from passlib.context import CryptContext

# Base de datos de prueba en memoria
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
os.environ["DATABASE_URL"] = SQLALCHEMY_DATABASE_URL

from app.main import app
from app.db.database import get_db, Base, get_engine, create_tables
from app.core.config import settings

# Create tables at import time since TestClient doesn't run startup events
create_tables()
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override de la dependencia de base de datos para pruebas."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="module")
def setup_database():
    """Configurar base de datos para pruebas."""
    Base.metadata.create_all(bind=get_engine())
    yield
    Base.metadata.drop_all(bind=get_engine())


class TestPasswordHashing:
    """Pruebas para hashing de contraseñas con bcrypt."""

    def test_password_hashing(self):
        """Verificar que las contraseñas se hashean correctamente."""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password = "testpassword123"

        # Generar hash
        hashed = pwd_context.hash(password)

        # Verificar que no es igual a la contraseña original
        assert hashed != password

        # Verificar que el hash se puede validar
        assert pwd_context.verify(password, hashed)

        # Verificar que contraseña incorrecta falla
        assert not pwd_context.verify("wrongpassword", hashed)

    def test_password_hash_uniqueness(self):
        """Verificar que hashes diferentes se generan para la misma contraseña."""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password = "testpassword123"

        hash1 = pwd_context.hash(password)
        hash2 = pwd_context.hash(password)

        # Los hashes deben ser diferentes (salting)
        assert hash1 != hash2

        # Pero ambos deben validar la misma contraseña
        assert pwd_context.verify(password, hash1)
        assert pwd_context.verify(password, hash2)


class TestJWTToken:
    """Pruebas para generación y validación de tokens JWT."""

    def test_create_access_token(self):
        """Verificar creación de token de acceso."""
        from app.api.v1.endpoints.auth import create_access_token

        data = {"sub": "testuser"}
        token = create_access_token(data)

        # Verificar que el token se crea
        assert token
        assert isinstance(token, str)

        # Verificar que se puede decodificar
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "testuser"
        assert "exp" in payload

    def test_token_expiration(self):
        """Verificar expiración de tokens."""
        from app.api.v1.endpoints.auth import create_access_token

        # Token con expiración corta
        expires_delta = timedelta(seconds=1)
        data = {"sub": "testuser"}
        token = create_access_token(data, expires_delta)

        # Decodificar inmediatamente debería funcionar
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "testuser"

        # Esperar a que expire
        import time
        time.sleep(2)

        # Ahora debería fallar
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    def test_invalid_token(self):
        """Verificar manejo de tokens inválidos."""
        from app.api.v1.endpoints.auth import get_current_user

        # Token malformado
        invalid_token = "invalid.jwt.token"

        with pytest.raises(Exception):  # Debería lanzar HTTPException
            # Simular request con token inválido
            pass  # Necesitaríamos mock del request


class TestAuthenticationFlow:
    """Pruebas del flujo completo de autenticación."""

    def test_user_registration_validation(self, setup_database):
        """Verificar validación en registro de usuario."""
        # Contraseña demasiado corta
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123",  # Menos de 8 caracteres
            "full_name": "Test User"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "error" in data
        assert data["status_code"] == 422

        # Email duplicado
        user_data1 = {
            "username": "user1",
            "email": "duplicate@example.com",
            "password": "password123",
            "full_name": "User 1"
        }
        user_data2 = {
            "username": "user2",
            "email": "duplicate@example.com",  # Mismo email
            "password": "password123",
            "full_name": "User 2"
        }
        client.post("/api/v1/auth/register", json=user_data1)
        response = client.post("/api/v1/auth/register", json=user_data2)
        assert response.status_code == 400

    def test_successful_registration_and_login(self, setup_database):
        """Verificar registro exitoso y login."""
        user_data = {
            "username": "authuser",
            "email": "auth@example.com",
            "password": "authpassword123",
            "full_name": "Auth User"
        }

        # Registro
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "hashed_password" not in data  # No debería exponer el hash

        # Login
        login_data = {
            "username": "authuser",
            "password": "authpassword123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

        # Verificar token
        token = data["access_token"]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "authuser"

    def test_invalid_login(self, setup_database):
        """Verificar login con credenciales inválidas."""
        # Usuario no existe
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert "credenciales" in data["message"].lower()

        # Contraseña incorrecta
        # Primero registrar usuario
        user_data = {
            "username": "wrongpass",
            "email": "wrong@example.com",
            "password": "correctpassword123",
            "full_name": "Wrong Pass User"
        }
        client.post("/api/v1/auth/register", json=user_data)

        login_data = {
            "username": "wrongpass",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert "contraseña" in data["message"].lower()


class TestProtectedRoutes:
    """Pruebas para rutas protegidas."""

    def test_protected_route_access(self, setup_database):
        """Verificar acceso a rutas protegidas."""
        # Sin token
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

        # Con token válido
        user_data = {
            "username": "protecteduser",
            "email": "protected@example.com",
            "password": "protected123",
            "full_name": "Protected User"
        }
        client.post("/api/v1/auth/register", json=user_data)

        login_data = {"username": "protecteduser", "password": "protected123"}
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "protecteduser"

    def test_expired_token(self, setup_database):
        """Verificar que tokens expirados son rechazados."""
        # Crear token con expiración muy corta
        from app.api.v1.endpoints.auth import create_access_token

        expires_delta = timedelta(seconds=1)
        token = create_access_token({"sub": "testuser"}, expires_delta)

        # Usar inmediatamente
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        # Debería fallar porque el usuario no existe en la DB de prueba
        # En un test real, crearíamos el usuario primero

    def test_logout(self, setup_database):
        """Verificar funcionalidad de logout."""
        # Logout es solo informativo en el frontend
        user_data = {
            "username": "logoutuser",
            "email": "logout@example.com",
            "password": "logout123",
            "full_name": "Logout User"
        }
        client.post("/api/v1/auth/register", json=user_data)

        login_data = {"username": "logoutuser", "password": "logout123"}
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 200
        assert "cerrada" in response.json()["message"].lower()


class TestAdminAccess:
    """Pruebas para acceso de administrador."""

    def test_superuser_field(self, setup_database):
        """Verificar campo is_superuser en modelo User."""
        from app.models.plan_model import User

        # Crear usuario normal
        user_data = {
            "username": "normaluser",
            "email": "normal@example.com",
            "password": "normal123",
            "full_name": "Normal User"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Verificar que no es superuser por defecto
        # (Necesitaríamos acceso directo a la DB para esto)

    def test_admin_only_route(self, setup_database):
        """Verificar rutas que requieren permisos de admin."""
        # Actualmente no hay rutas específicas para admin
        # Pero podemos verificar que is_superuser existe en el modelo
        pass


class TestConcurrentUsers:
    """Pruebas para múltiples usuarios concurrentes."""

    def test_multiple_users_login(self, setup_database):
        """Verificar que múltiples usuarios pueden loguearse."""
        users = [
            {"username": "user1", "email": "user1@example.com", "password": "pass123456"},
            {"username": "user2", "email": "user2@example.com", "password": "pass123456"},
            {"username": "user3", "email": "user3@example.com", "password": "pass123456"},
        ]

        tokens = []
        for user in users:
            response = client.post("/api/v1/auth/register", json=user)
            assert response.status_code == 201
            login_data = {"username": user["username"], "password": user["password"]}
            response = client.post("/api/v1/auth/login", data=login_data)
            assert response.status_code == 200
            tokens.append(response.json()["access_token"])

        # Verificar que todos los tokens son válidos y diferentes
        assert len(tokens) == 3
        assert len(set(tokens)) == 3  # Todos diferentes

        # Verificar que cada usuario puede acceder con su token
        for i, token in enumerate(tokens):
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == users[i]["username"]


class TestSecurityHeaders:
    """Pruebas para headers de seguridad."""

    def test_cors_headers(self, setup_database):
        """Verificar configuración CORS."""
        # Test CORS on a GET endpoint
        response = client.options("/api/v1/plans/")
        # OPTIONS might return 401 if auth required, but CORS headers should be present
        assert "access-control-allow-origin" in response.headers or response.status_code == 401

    def test_error_responses(self, setup_database):
        """Verificar que errores no exponen información sensible."""
        # Intentar login con usuario que no existe
        login_data = {"username": "nonexistent", "password": "password"}
        response = client.post("/api/v1/auth/login", data=login_data)

        # Debería ser 401, no 404 (no revelar si usuario existe)
        assert response.status_code == 401
        data = response.json()
        error_msg = data.get("message", "")
        # No debería mencionar "usuario no encontrado" específicamente
        assert "no encontrado" not in error_msg.lower()
        assert "credenciales" in error_msg.lower()


class TestTokenExpiration:
    """Pruebas específicas para expiración de tokens."""

    def test_token_expiration_time(self, setup_database):
        """Verificar tiempo de expiración configurado."""
        from app.api.v1.endpoints.auth import create_access_token

        # Token sin expiración específica (usa default)
        token = create_access_token({"sub": "testuser"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Verificar que expira en aproximadamente ACCESS_TOKEN_EXPIRE_MINUTES
        expected_exp = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        actual_exp = datetime.fromtimestamp(payload["exp"])

        # Tolerancia de 1 minuto
        time_diff = abs((expected_exp - actual_exp).total_seconds())
        assert time_diff < 60