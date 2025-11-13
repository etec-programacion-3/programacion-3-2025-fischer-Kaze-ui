// frontend/src/App.jsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css'; 

const apiClient = axios.create({
  baseURL: 'http://localhost:8000'
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

function App() {
  // --- Estados Auth ---
  const [registerForm, setRegisterForm] = useState({ nombre_usuario: '', email: '', password: '', nombre: '', apellido: '' });
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [error, setError] = useState('');
  
  // --- Estados Tienda ---
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState(null);
  const [orders, setOrders] = useState([]); 
  const [view, setView] = useState('catalog'); 

  // --- Estados Filtros y Paginación (NUEVO ISSUE 12) ---
  const [searchTerm, setSearchTerm] = useState('');
  const [category, setCategory] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const LIMIT = 6; // Productos por página

  // --- Carga de datos ---
  useEffect(() => {
    const fetchData = async () => {
      if (token) {
        try {
          // Construimos la URL con filtros
          const params = new URLSearchParams();
          params.append('page', page);
          params.append('limit', LIMIT);
          if (searchTerm) params.append('search', searchTerm);
          if (category) params.append('category', category);

          // Peticiones en paralelo
          const [prodRes, countRes, cartRes] = await Promise.all([
            apiClient.get(`/api/products?${params.toString()}`),
            apiClient.get(`/api/products/count?${params.toString()}`), // Para saber total de páginas
            apiClient.get('/api/cart')
          ]);
          
          setProducts(prodRes.data);
          setTotalPages(Math.ceil(countRes.data.total / LIMIT));
          setCart(cartRes.data);

        } catch (err) {
          console.error("Error cargando datos:", err);
          if (err.response && err.response.status === 401) handleLogout();
        }
      }
    };
    
    // Debounce pequeño para no saturar la API al escribir
    const timeoutId = setTimeout(() => fetchData(), 300);
    return () => clearTimeout(timeoutId);

  }, [token, page, searchTerm, category]); // Se ejecuta cuando cambian los filtros

  // --- Manejadores Auth ---
  const handleRegisterChange = (e) => setRegisterForm({ ...registerForm, [e.target.name]: e.target.value });
  const handleLoginChange = (e) => setLoginForm({ ...loginForm, [e.target.name]: e.target.value });
  
  const handleRegister = async (e) => {
    e.preventDefault(); setError('');
    try {
      await apiClient.post('/api/auth/register', registerForm);
      alert('¡Registro exitoso! Inicia sesión.');
      setRegisterForm({ nombre_usuario: '', email: '', password: '', nombre: '', apellido: '' });
    } catch (err) { setError(err.response?.data?.detail || 'Error en registro'); }
  };

  const handleLogin = async (e) => {
    e.preventDefault(); setError('');
    const formData = new URLSearchParams();
    formData.append('username', loginForm.username);
    formData.append('password', loginForm.password);
    formData.append('grant_type', 'password');

    try {
      const response = await apiClient.post('/api/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      setToken(response.data.access_token);
      localStorage.setItem('token', response.data.access_token);
    } catch (err) { setError(err.response?.data?.detail || 'Error en login'); }
  };

  const handleLogout = () => {
    setToken(null); localStorage.removeItem('token');
    setProducts([]); setCart(null); setOrders([]); setView('catalog');
    setPage(1); setSearchTerm(''); setCategory('');
  };

  // --- Manejadores Tienda ---
  const handleAddToCart = async (id_producto) => {
    try {
      const response = await apiClient.post('/api/cart/add', { id_producto, cantidad: 1 });
      setCart(response.data);
      alert("Añadido al carrito");
    } catch (err) { alert(`Error: ${err.response?.data?.detail}`); }
  };

  const loadOrders = async () => {
    const res = await apiClient.get('/api/orders');
    setOrders(res.data);
    setView('orders');
  };

  const handleCheckout = async () => {
    if (!cart || cart.items.length === 0) return alert("Carrito vacío");
    try {
      const response = await apiClient.post('/api/orders');
      alert(`¡Orden #${response.data.id_pedido} creada!`);
      const newCart = await apiClient.get('/api/cart');
      setCart(newCart.data);
      loadOrders(); // Ir a historial
    } catch (err) { alert(`Error: ${err.response?.data?.detail}`); }
  };

  // --- Renderizado ---
  if (!token) {
    return (
      <div className="App">
        {error && <p className="error">{error}</p>}
        <div className="auth-wrapper">
          <div className="form-container">
            <h2>Registrarse</h2>
            <form onSubmit={handleRegister}>
              <input name="nombre_usuario" placeholder="Usuario" onChange={handleRegisterChange} />
              <input name="email" placeholder="Email" onChange={handleRegisterChange} />
              <input name="password" type="password" placeholder="Contraseña" onChange={handleRegisterChange} />
              <input name="nombre" placeholder="Nombre" onChange={handleRegisterChange} />
              <input name="apellido" placeholder="Apellido" onChange={handleRegisterChange} />
              <button type="submit">Registrar</button>
            </form>
          </div>
          <div className="form-container">
            <h2>Login</h2>
            <form onSubmit={handleLogin}>
              <input name="username" placeholder="Usuario" onChange={handleLoginChange} />
              <input name="password" type="password" placeholder="Contraseña" onChange={handleLoginChange} />
              <button type="submit">Entrar</button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <nav className="navbar">
        <h1 onClick={() => setView('catalog')} style={{cursor: 'pointer'}}>Tienda E-Commerce</h1>
        <div className="nav-right">
          <button onClick={() => setView('catalog')}>Catálogo</button>
          <button onClick={loadOrders}>Mis Órdenes</button>
          <button onClick={() => setView('cart')} className="cart-btn">
            Carrito ({cart ? cart.items.length : 0})
          </button>
          <button onClick={handleLogout} className="logout-button">Salir</button>
        </div>
      </nav>

      {view === 'catalog' && (
        <div className="catalog-container">
          {/* --- BARRA DE FILTROS (Issue 12) --- */}
          <div className="filters-bar">
            <input 
              type="text" 
              placeholder="Buscar producto..." 
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
            />
            <select 
              value={category} 
              onChange={(e) => { setCategory(e.target.value); setPage(1); }}
            >
              <option value="">Todas las Categorías</option>
              <option value="Electronica">Electrónica</option>
              <option value="Periféricos">Periféricos</option>
              <option value="Ropa">Ropa</option>
              <option value="Hogar">Hogar</option>
            </select>
          </div>

          {/* Grid de Productos */}
          <div className="product-grid">
            {products.length > 0 ? (
              products.map((p) => (
                <div key={p.id_producto} className="product-card">
                  <img src={p.imagen || 'https://via.placeholder.com/150'} alt={p.nombre_producto} />
                  <h3>{p.nombre_producto}</h3>
                  <p className="price">${p.precio}</p>
                  <p className="stock">Stock: {p.stock}</p>
                  <button onClick={() => handleAddToCart(p.id_producto)}>Agregar al Carrito</button>
                </div>
              ))
            ) : (
              <p className="no-results">No se encontraron productos.</p>
            )}
          </div>

          {/* --- PAGINACIÓN (Issue 12) --- */}
          <div className="pagination">
            <button disabled={page <= 1} onClick={() => setPage(page - 1)}>Anterior</button>
            <span>Página {page} de {totalPages || 1}</span>
            <button disabled={page >= totalPages} onClick={() => setPage(page + 1)}>Siguiente</button>
          </div>
        </div>
      )}

      {view === 'cart' && (
        <div className="cart-view">
          <h2>Tu Carrito</h2>
          {(!cart || cart.items.length === 0) ? <p>El carrito está vacío.</p> : (
            <div>
              <ul className="cart-list">
                {cart.items.map((item) => (
                  <li key={item.id_item_carrito}>
                    <strong>{item.producto.nombre_producto}</strong> 
                    <span> x{item.cantidad}</span>
                    <span> = ${(item.producto.precio * item.cantidad).toFixed(2)}</span>
                  </li>
                ))}
              </ul>
              <div className="cart-actions">
                <button className="checkout-btn" onClick={handleCheckout}>Finalizar Compra</button>
              </div>
            </div>
          )}
        </div>
      )}

      {view === 'orders' && (
        <div className="orders-view">
          <h2>Historial de Órdenes</h2>
          {orders.length === 0 && <p>No tienes órdenes aún.</p>}
          {orders.map((o) => (
            <div key={o.id_pedido} className="order-card">
              <div className="order-header">
                <span>Orden #{o.id_pedido}</span>
                <span className={`status ${o.estado}`}>{o.estado}</span>
              </div>
              <p>Fecha: {new Date(o.fecha_pedido).toLocaleDateString()}</p>
              <p>Total: <strong>${o.total}</strong></p>
              <ul>
                {o.items.map(i => (
                  <li key={i.id_producto}>{i.producto.nombre_producto} (x{i.cantidad})</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;