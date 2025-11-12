// frontend/src/App.jsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css'; // Vite incluye este archivo CSS

// 1. Creamos un "cliente" de API con la URL base de tu backend
const apiClient = axios.create({
  baseURL: 'http://localhost:8000'
});

function App() {
  // --- Estados para los formularios ---
  const [registerForm, setRegisterForm] = useState({
    nombre_usuario: '',
    email: '',
    password: '',
    nombre: '',
    apellido: ''
  });

  const [loginForm, setLoginForm] = useState({
    username: '', // Puede ser email o nombre_usuario
    password: ''
  });

  // --- Estado para el Token (Autenticación) ---
  // Intentamos leer el token de localStorage al iniciar
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [error, setError] = useState('');

  // --- Manejadores de cambios en los formularios ---
  const handleRegisterChange = (e) => {
    setRegisterForm({
      ...registerForm,
      [e.target.name]: e.target.value
    });
  };

  const handleLoginChange = (e) => {
    setLoginForm({
      ...loginForm,
      [e.target.name]: e.target.value
    });
  };

  // --- Manejadores de envío (Submit) ---
  
  const handleRegister = async (e) => {
    e.preventDefault(); // Evita que la página se recargue
    setError(''); // Limpia errores previos
    try {
      // Llamamos al endpoint de registro de tu API
      const response = await apiClient.post('/api/auth/register', registerForm);
      console.log('Usuario registrado:', response.data);
      alert('¡Registro exitoso! Ahora puedes iniciar sesión.');
      // Limpiamos el formulario (opcional)
      setRegisterForm({ nombre_usuario: '', email: '', password: '', nombre: '', apellido: '' });
      
    } catch (err) {
      // Si la API devuelve un error (ej: 400), lo mostramos
      console.error(err.response.data);
      setError(err.response.data.detail || 'Error en el registro');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    
    // IMPORTANTE: OAuth2PasswordRequestForm espera 'form-data', no JSON.
    // Usamos URLSearchParams para formatear los datos correctamente.
    const formData = new URLSearchParams();
    formData.append('username', loginForm.username);
    formData.append('password', loginForm.password);
    formData.append('grant_type', 'password'); // Requerido por la API

    try {
      // Llamamos al endpoint de login
      const response = await apiClient.post('/api/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      
      const newToken = response.data.access_token;
      setToken(newToken);
      // Guardamos el token en localStorage para persistir la sesión
      localStorage.setItem('token', newToken);
      console.log('Login exitoso:', newToken);

    } catch (err) {
      console.error(err.response.data);
      setError(err.response.data.detail || 'Error en el login');
    }
  };

  const handleLogout = () => {
    setToken(null);
    localStorage.removeItem('token');
  };

  // --- Renderizado (lo que se ve) ---

  // Si no tenemos token, mostramos los formularios de Login/Registro
  if (!token) {
    return (
      <div className="App">
        {error && <p className="error">{error}</p>}

        {/* Formulario de Registro */}
        <div className="form-container">
          <h2>Registrarse (Issue 11)</h2>
          <form onSubmit={handleRegister}>
            <input name="nombre_usuario" placeholder="Nombre de usuario" onChange={handleRegisterChange} />
            <input name="email" type="email" placeholder="Email" onChange={handleRegisterChange} />
            <input name="password" type="password" placeholder="Contraseña" onChange={handleRegisterChange} />
            <input name="nombre" placeholder="Nombre" onChange={handleRegisterChange} />
            <input name="apellido" placeholder="Apellido" onChange={handleRegisterChange} />
            <button type="submit">Registrarse</button>
          </form>
        </div>

        {/* Formulario de Login */}
        <div className="form-container">
          <h2>Iniciar Sesión (Issue 11)</h2>
          <form onSubmit={handleLogin}>
            <input name="username" placeholder="Usuario o Email" onChange={handleLoginChange} />
            <input name="password" type="password" placeholder="Contraseña" onChange={handleLoginChange} />
            <button type="submit">Iniciar Sesión</button>
          </form>
        </div>
      </div>
    );
  }

  // Si SÍ tenemos token, mostramos que está logueado
  return (
    <div className="App">
      <h2>¡Login Exitoso! (Issue 11)</h2>
      <p>Estás autenticado.</p>
      <button onClick={handleLogout}>Cerrar Sesión (Logout)</button>
      {/* Aquí es donde cargarías los productos (Issue 12) */}
    </div>
  );
}

export default App;