// frontend/src/App.jsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Cliente API con Interceptor
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
  const [view, setView] = useState('catalog'); // 'catalog' | 'cart' | 'orders' | 'admin'

  // --- Filtros ---
  const [searchTerm, setSearchTerm] = useState('');
  const [category, setCategory] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const LIMIT = 6;

  // --- Estado Admin (Nuevo) ---
  const [newProduct, setNewProduct] = useState({
    nombre_producto: '', descripcion: '', marca: '', categoria: '', precio: '', stock: '', imagen: ''
  });

  // --- Carga de datos ---
  useEffect(() => {
    const fetchData = async () => {
      if (token) {
        try {
          const params = new URLSearchParams();
          params.append('page', page);
          params.append('limit', LIMIT);
          if (searchTerm) params.append('search', searchTerm);
          if (category) params.append('category', category);

          const [prodRes, countRes, cartRes, ordersRes] = await Promise.all([
            apiClient.get(`/api/products?${params.toString()}`),
            apiClient.get(`/api/products/count?${params.toString()}`),
            apiClient.get('/api/cart'),
            apiClient.get('/api/orders')
          ]);

          setProducts(prodRes.data);
          setTotalPages(Math.ceil(countRes.data.total / LIMIT));
          setCart(cartRes.data);
          setOrders(ordersRes.data);

        } catch (err) {
          console.error("Error:", err);
          if (err.response?.status === 401) handleLogout();
        }
      }
    };
    
    const timeoutId = setTimeout(() => fetchData(), 300);
    return () => clearTimeout(timeoutId);
  }, [token, page, searchTerm, category, view]); // 'view' añadido para recargar al cambiar

  // --- Auth Handlers ---
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
    setProducts([]); setCart(null); setView('catalog');
  };

  // --- Tienda Handlers ---
  const handleAddToCart = async (id_producto) => {
    try {
      const response = await apiClient.post('/api/cart/add', { id_producto, cantidad: 1 });
      setCart(response.data);
      alert("Añadido al carrito");
    } catch (err) { alert(`Error: ${err.response?.data?.detail}`); }
  };

  const handleCheckout = async () => {
    if (!cart || cart.items.length === 0) return alert("Carrito vacío");
    if (!window.confirm(`¿Confirmar compra por $${calculateTotal()}?`)) return;

    try {
      const response = await apiClient.post('/api/orders');
      alert(`¡Compra exitosa! Orden #${response.data.id_pedido} generada.`);
      // Recargar datos y limpiar vista
      const newCart = await apiClient.get('/api/cart');
      const newOrders = await apiClient.get('/api/orders');
      setCart(newCart.data);
      setOrders(newOrders.data);
      setView('orders'); // Llevar al historial
    } catch (err) { 
      alert(`Error al comprar: ${err.response?.data?.detail || 'Error desconocido'}`); 
    }
  };

  const calculateTotal = () => {
    if (!cart) return 0;
    return cart.items.reduce((acc, item) => acc + (item.producto.precio * item.cantidad), 0).toFixed(2);
  };
  
  // --- ADMIN HANDLERS (Nuevo) ---
  const handleProductChange = (e) => setNewProduct({ ...newProduct, [e.target.name]: e.target.value });

  const handleCreateProduct = async (e) => {
    e.preventDefault();
    try {
      // Convertir tipos numéricos
      const productToSend = {
        ...newProduct,
        precio: parseFloat(newProduct.precio),
        stock: parseInt(newProduct.stock)
      };
      
      await apiClient.post('/api/products', productToSend);
      alert('¡Producto creado exitosamente!');
      setNewProduct({ nombre_producto: '', descripcion: '', marca: '', categoria: '', precio: '', stock: '', imagen: '' });
      setView('catalog'); // Volver al catálogo para verlo
    } catch (err) {
      if (err.response?.status === 403) {
        alert("⛔ ACCESO DENEGADO: No eres administrador.");
      } else {
        alert(`Error: ${err.response?.data?.detail}`);
      }
    }
  };


  // --- Renderizado ---
  if (!token) {
    return (
      <div className="App centered-container">
        <h1>Bienvenido a ElectroTech</h1>
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
        <h1 onClick={() => setView('catalog')} className="logo">ElectroTech</h1>
        <div className="nav-links">
          <button onClick={() => setView('catalog')} className={view==='catalog'?'active':''}>Catálogo</button>
          <button onClick={() => setView('orders')} className={view==='orders'?'active':''}>Mis Órdenes</button>
          <button onClick={() => setView('cart')} className={`cart-btn ${view==='cart'?'active':''}`}>
            🛒 Carrito ({cart ? cart.items.length : 0})
          </button>
          {/* BOTÓN DE ADMIN (NUEVO) */}
          <button onClick={() => setView('admin')} className={`admin-btn ${view==='admin'?'active':''}`}>
            ⚙️ Admin
          </button>
          <button onClick={handleLogout} className="logout-button">Salir</button>
        </div>
      </nav>

      <div className="main-content">
        {/* VISTA CATALOGO */}
        {view === 'catalog' && (
          <div className="catalog-container">
            <div className="filters-bar">
              <input 
                type="text" 
                placeholder="🔍 Buscar producto..." 
                value={searchTerm}
                onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
              />
              <select 
                value={category} 
                onChange={(e) => { setCategory(e.target.value); setPage(1); }}
              >
                <option value="">Todas las Categorías</option>
                <option value="Audio">Audio</option>
                <option value="Computación">Computación</option>
                <option value="Periféricos">Periféricos</option>
                <option value="Celulares">Celulares</option>
                <option value="Videojuegos">Videojuegos</option>
                <option value="Tablets">Tablets</option>
                <option value="Wearables">Wearables</option>
              </select>
            </div>

            <div className="product-grid">
              {products.length > 0 ? (
                products.map((p) => (
                  <div key={p.id_producto} className="product-card">
                    <img src={p.imagen || 'https://via.placeholder.com/150?text=No+Imagen'} alt={p.nombre_producto} className="product-image"/>
                    <h3>{p.nombre_producto}</h3>
                    <p className="price">${p.precio}</p>
                    <p className="stock">Stock: {p.stock}</p>
                    <button onClick={() => handleAddToCart(p.id_producto)}>Añadir al Carrito</button>
                  </div>
                ))
              ) : (
                <p className="no-results">No se encontraron productos.</p>
              )}
            </div>

            <div className="pagination">
              <button disabled={page <= 1} onClick={() => setPage(page - 1)}>Anterior</button>
              <span>Página {page} de {totalPages || 1}</span>
              <button disabled={page >= totalPages} onClick={() => setPage(page + 1)}>Siguiente</button>
            </div>
          </div>
        )}

        {/* VISTA CARRITO */}
        {view === 'cart' && (
          <div className="cart-view centered-view">
            <h2>Tu Carrito de Compras</h2>
            {(!cart || cart.items.length === 0) ? <p>El carrito está vacío.</p> : (
              <div className="cart-content">
                <table className="cart-table">
                  <thead>
                    <tr>
                      <th>Producto</th>
                      <th>Cant.</th>
                      <th>Precio Unit.</th>
                      <th>Subtotal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cart.items.map((item) => (
                      <tr key={item.id_item_carrito}>
                        <td>{item.producto.nombre_producto}</td>
                        <td>{item.cantidad}</td>
                        <td>${item.producto.precio}</td>
                        <td>${(item.producto.precio * item.cantidad).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="cart-summary">
                  <h3>Total a Pagar: ${calculateTotal()}</h3>
                  <button className="checkout-btn" onClick={handleCheckout}>✅ Finalizar Compra</button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* VISTA ORDENES */}
        {view === 'orders' && (
          <div className="orders-view centered-view">
            <h2>Historial de Órdenes</h2>
            {orders.length === 0 ? <p>No tienes órdenes aún.</p> : (
              <div className="orders-list">
                {orders.map((o) => (
                  <div key={o.id_pedido} className="order-card">
                    <div className="order-header">
                      <span>Orden #{o.id_pedido}</span>
                      <span className="date">{new Date(o.fecha_pedido).toLocaleDateString()}</span>
                      <span className={`status ${o.estado}`}>{o.estado}</span>
                    </div>
                    <div className="order-items">
                      {o.items.map(i => (
                        <div key={i.id_producto} className="order-item-row">
                          <span>{i.producto.nombre_producto}</span>
                          <span>x{i.cantidad}</span>
                        </div>
                      ))}
                    </div>
                    <div className="order-total">Total: ${o.total}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* VISTA ADMIN (NUEVO) */}
        {view === 'admin' && (
          <div className="admin-view centered-view">
            <h2>Panel de Administración</h2>
            <p className="admin-note">Nota: Solo usuarios con rol 'admin' pueden guardar productos.</p>
            <div className="form-container admin-form">
              <h3>Agregar Nuevo Producto</h3>
              <form onSubmit={handleCreateProduct}>
                <input name="nombre_producto" placeholder="Nombre del Producto" value={newProduct.nombre_producto} onChange={handleProductChange} required />
                <input name="descripcion" placeholder="Descripción" value={newProduct.descripcion} onChange={handleProductChange} />
                <input name="marca" placeholder="Marca" value={newProduct.marca} onChange={handleProductChange} required />
                <input name="categoria" placeholder="Categoría (ej: Periféricos)" value={newProduct.categoria} onChange={handleProductChange} required />
                <input name="precio" type="number" step="0.01" placeholder="Precio (ej: 99.99)" value={newProduct.precio} onChange={handleProductChange} required />
                <input name="stock" type="number" placeholder="Stock Inicial (ej: 50)" value={newProduct.stock} onChange={handleProductChange} required />
                <input name="imagen" placeholder="URL de la Imagen (opcional)" value={newProduct.imagen} onChange={handleProductChange} />
                <button type="submit" className="admin-submit-btn">Guardar Producto</button>
              </form>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default App;