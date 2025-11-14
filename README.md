# Proyecto Final E-Commerce (Full Stack)

**Alumno:** Ilán Fischer 
**Materia:** Programación 3  
**Año:** 2025

Este repositorio contiene el proyecto final de e-commerce completo, implementando un **Backend API REST** en FastAPI y un **Frontend** en React. El proyecto cumple con **todas las issues asignadas** (1-13), incluyendo autenticación JWT, gestión de productos, carrito persistente, sistema de órdenes transaccionales y mensajería entre usuarios.

---

##  Tabla de Contenidos

- [Tecnologías Utilizadas](#tecnologías-utilizadas)
- [Requisitos Previos](#requisitos-previos)
- [Instalación y Configuración](#instalación-y-configuración)
- [Ejecución del Proyecto](#ejecución-del-proyecto)
- [Pruebas del Backend](#pruebas-del-backend)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Issues Completadas](#issues-completadas)

---

##  Tecnologías Utilizadas

### Backend
- **Python 3.12**
- **FastAPI** (Framework web async)
- **SQLAlchemy** (ORM)
- **Alembic** (Migraciones de base de datos)
- **PostgreSQL** (Base de datos)
- **Bcrypt** (Hashing de contraseñas)
- **Python-Jose** (JWT)
- **Docker** (Contenedor de base de datos)

### Frontend
- **React 19** (con Vite)
- **Axios** (Cliente HTTP)

---

##  Requisitos Previos (Arch Linux)

Para ejecutar este proyecto en Arch Linux, instalar los siguientes paquetes del repositorio oficial:
```bash
# Instalar dependencias del sistema
sudo pacman -Syu git python python-pip nodejs npm docker docker-compose

# Iniciar y habilitar el servicio de Docker
sudo systemctl start docker
sudo systemctl enable docker

# Agregar tu usuario al grupo docker (para ejecutar sin sudo)
sudo usermod -aG docker $USER
# Cerrar sesión y volver a iniciar para que los cambios tomen efecto
```

---

## 📦 Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone <URL_DE_TU_REPOSITORIO>
cd <nombre-del-proyecto>
```

### 2. Configurar la Base de Datos (Docker)

Desde la raíz del proyecto, inicia el contenedor de PostgreSQL:
```bash
docker-compose up -d
```

Esto levanta una instancia de PostgreSQL en el puerto **5432**.

**Verificar que el contenedor esté corriendo:**
```bash
docker ps | grep postgres
```

### 3. Configurar el Backend

#### 3.1. Navegar a la carpeta backend
```bash
cd backend
```

#### 3.2. Crear y activar entorno virtual
```bash
python -m venv venv
source venv/bin/activate
```

#### 3.3. Instalar dependencias de Python
```bash
pip install -r requirements.txt
```

#### 3.4. Configurar variables de entorno

El archivo `.env` ya está incluido en el repositorio con la siguiente configuración:
```env
# Base de Datos (Usadas por database.py y docker-compose.yml)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=12345*
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=electro_tech_db

# Autenticación (JWT) (Usadas por auth.py)
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**⚠️ IMPORTANTE:** La contraseña de PostgreSQL (`POSTGRES_PASSWORD=12345*`) debe coincidir entre `.env` y `docker-compose.yml`.

#### 3.5. Ejecutar migraciones de base de datos

Esperar unos segundos a que PostgreSQL termine de iniciarse, luego:
```bash
alembic upgrade head
```

Este comando crea todas las tablas necesarias (usuario, productos, carrito, pedidos, mensajes, conversaciones, items_carrito, itemspedido) en el contenedor Docker.

### 4. Configurar el Frontend

Abrir una **segunda terminal** y navegar a la carpeta frontend:
```bash
cd frontend
```

#### 4.1. Instalar dependencias de Node.js
```bash
npm install
```

---

## Ejecución del Proyecto

### Iniciar el Backend

Desde la carpeta `backend` con el entorno virtual activado:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Acceso:**
- **API Base:** [http://localhost:8000](http://localhost:8000)
- **Documentación Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Documentación ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Iniciar el Frontend

Desde la carpeta `frontend` (en otra terminal):
```bash
npm run dev
```

**Acceso:**
- **Aplicación Web:** [http://localhost:5173](http://localhost:5173)

---

## 🧪 Pruebas del Backend

El archivo `backend/requests.http` contiene peticiones de ejemplo para **TODOS los endpoints** con ejemplos de CRUD completo.

### Uso con VS Code (Recomendado)

1. Instalar la extensión **REST Client** en VS Code:
```bash
   code --install-extension humao.rest-client
```

2. Abrir el archivo `backend/requests.http`

3. **IMPORTANTE - Configuración previa:**
   - El archivo usa variables para los tokens JWT
   - Primero debes ejecutar las peticiones de **login** para obtener los tokens
   - Los tokens se guardan automáticamente en las variables `{{admin_token}}` y `{{user_token}}`

4. **Crear un usuario administrador** (ver sección siguiente)

5. Hacer clic en **"Send Request"** sobre cada petición para probarlas

### Crear un Usuario Administrador

Los usuarios registrados desde el frontend o el endpoint `/register` tienen rol `cliente` por defecto. Para convertir un usuario en administrador:
```bash
# 1. Acceder al contenedor de PostgreSQL
docker exec -it electro_tech_db_container psql -U postgres -d electro_tech_db

# 2. Cambiar el rol del usuario (reemplazar 'Supertizinox' por tu usuario real)
UPDATE usuario SET tipo_usuario = 'admin' WHERE nombre_usuario = 'Supertizinox';

# 3. Verificar el cambio
SELECT nombre_usuario, tipo_usuario FROM usuario WHERE nombre_usuario = 'Supertizinox';

# 4. Salir
\q
```

Alternativamente, usar cualquier cliente SQL para Arch Linux:
```bash
# Instalar pgcli (cliente PostgreSQL moderno)
sudo pacman -S pgcli

# Conectarse
pgcli postgresql://postgres:12345*@localhost/electro_tech_db
```

##  Seguridad

- ✅ Contraseñas hasheadas con **bcrypt** (nunca se guardan en texto plano)
- ✅ Autenticación **stateless** con JWT (JSON Web Tokens)
- ✅ Tokens con expiración configurable (default: 30 minutos)
- ✅ Validación de roles mediante middleware (RBAC)
- ✅ **Sin credenciales hardcodeadas** - toda configuración sensible en `.env`
- ✅ Validación de datos de entrada con **Pydantic**
- ✅ Transacciones atómicas en la base de datos (checkout)


##  Notas Adicionales

### Autenticación y Autorización

- El backend utiliza **JWT** en el header `Authorization: Bearer <token>`
- Los endpoints de productos **GET son públicos** (no requieren autenticación)
- Los endpoints de **carrito, órdenes y mensajes** requieren usuario autenticado
- Los endpoints de **creación/edición/eliminación de productos** requieren rol `admin`

### Flujo de Autenticación

1. Usuario se registra en `/api/auth/register` (rol `cliente` por defecto)
2. Usuario hace login en `/api/auth/login` y recibe un JWT
3. El frontend guarda el token en `localStorage`
4. Cada petición subsiguiente incluye el token en el header `Authorization`

### Base de Datos

- PostgreSQL corre en un contenedor Docker (puerto 5432)
- Las migraciones se gestionan con Alembic
- Todas las tablas tienen relaciones definidas (Foreign Keys)
- Uso de transacciones para operaciones críticas (checkout)

---

##  Troubleshooting (Arch Linux)

### Docker no inicia
```bash
sudo systemctl status docker
sudo systemctl start docker
```

### Error de permisos con Docker
```bash
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar
```

### PostgreSQL no responde
```bash
# Verificar que el contenedor esté corriendo
docker ps

# Ver logs del contenedor
docker logs electro_tech_db_container

# Reiniciar el contenedor
docker-compose restart
```

### Error "ModuleNotFoundError" en Python
```bash
# Verificar que el venv esté activado
which python  # Debe mostrar la ruta del venv

# Reinstalar dependencias
pip install -r requirements.txt
```

### Error de conexión frontend → backend

Verificar que:
1. El backend esté corriendo en el puerto 8000
2. El frontend esté configurado para apuntar a `http://localhost:8000`
3. CORS esté habilitado en el backend (ya está configurado)

---

## Comandos Útiles
```bash
# Backend
cd backend
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend
npm run dev

# Base de Datos
docker-compose up -d                    # Iniciar
docker-compose down                     # Detener
docker-compose logs -f db               # Ver logs
docker exec -it electro_tech_db_container psql -U postgres -d electro_tech_db

# Migraciones
alembic revision --autogenerate -m "mensaje"
alembic upgrade head
alembic downgrade -1
