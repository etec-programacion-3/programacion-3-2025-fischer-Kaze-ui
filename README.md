# Proyecto Final E-Commerce (Full Stack)

Este repositorio contiene el proyecto final de la materia Programación 3. Es una aplicación web de e-commerce completa, que incluye un Backend (API REST) desarrollado en FastAPI y un Frontend (SPA) desarrollado en React.

El proyecto utiliza **SQLite** como base de datos para una máxima portabilidad y facilidad de ejecución (no requiere Docker ni PostgreSQL).

### Tecnologías Utilizadas

* **Backend:** Python, FastAPI, SQLAlchemy, Alembic (Migraciones), JWT (Autenticación), Passlib (Hashing).
* **Frontend:** React (Vite), Axios.
* **Base de Datos:** SQLite.
* **Gestión:** Git, GitHub (Issues y Pull Requests).

---

## 📋 Requisitos Previos (Arch Linux)

Para ejecutar este proyecto en Arch Linux, solo se necesita el software base de desarrollo:

```bash
# 1. Instalar Git, Python/Pip, y Node.js/NPM
sudo pacman -Syu git python python-pip nodejs npm

# 2. Instalar SQLite (herramienta de línea de comandos, opcional pero útil)
sudo pacman -S sqlite

🚀 Guía de Instalación y Ejecución
Siga estos pasos en orden. Se necesitarán dos terminales.

1. Clonar el Repositorio

git clone [URL_DE_TU_REPOSITORIO]
cd programacion-3-2025-fischer-Kaze-ui
2. Configurar y Ejecutar el BACKEND (Terminal 1)
Navegar al Backend:

cd backend
Crear y Activar Entorno Virtual:

python -m venv venv
source venv/bin/activate
Instalar Dependencias de Python:

pip install -r requirements.txt
Configurar Variables de Entorno (¡Importante!): El backend necesita una SECRET_KEY para los tokens JWT.

# 1. Copiar el archivo de ejemplo
cp .env.example .env

# 2. Editar el .env (ej. con nano) y reemplazar la clave
nano .env 
# (Reemplaza 'tu_clave_secreta_aqui...' por una clave real)
Ejecutar las Migraciones (Crear la Base de Datos): Este comando creará el archivo sql_app.db con todas las tablas.

alembic upgrade head
Iniciar el Servidor Backend:


python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
El Backend estará corriendo en http://localhost:8000/docs.

3. Configurar y Ejecutar el FRONTEND (Terminal 2)
Navegar al Frontend: (Abre una nueva terminal y ve a la raíz del proyecto).

cd frontend
Instalar Dependencias de Node.js:

npm install
Iniciar el Servidor Frontend:

npm run dev
La aplicación web estará disponible en http://localhost:5173/.

🧪 Probar el Proyecto
1. Registrar un Usuario (Admin)
El sistema está diseñado para que el registro web solo cree usuarios de tipo cliente. Para probar la funcionalidad de Administrador (como crear productos), debe "promover" a un usuario manualmente.

Regístrese normalmente desde el Frontend (http://localhost:5173/). (Ej: admin_user / password123)
ATENCION: la contraseña debe tener mas de 8 caracteres, de lo contrario, no te va a dejar registrarte
Acceda a la Base de Datos (en la terminal del backend, detenga el servidor con Ctrl+C temporalmente):

sqlite3 sql_app.db
Ejecute el SQL (reemplace 'admin_user' por el nombre_usuario que registró):

UPDATE usuario SET tipo_usuario = 'admin' WHERE nombre_usuario = 'admin_user';
.quit
Vuelva a iniciar el servidor (python3 -m uvicorn...).

2. Probar como Admin
Inicie sesión en el Frontend (http://localhost:5173/) como admin_user.

Navegue a la pestaña "⚙️ Admin".

Cree productos usando el formulario.

Vaya a "Catálogo" y verifique que los productos aparecen.

3. Probar como Cliente
Cierre Sesión (Logout).

Regístrese como un usuario nuevo (ej: cliente_normal).

Inicie Sesión como cliente_normal.

Verifique que puede ver los productos, añadirlos al carrito y finalizar la compra.