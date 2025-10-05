// components/LoginModal.jsx
import React, { useState } from 'react';
import { API } from '../config/api'; 

const LoginModal = ({ onClose, onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [pass, setPass] = useState('');

  const handleLogin = async () => {
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, password: pass }),
      });

      if (res.ok) {
        const data = await res.json();
        alert("Login successful ✅");
        localStorage.setItem("token", data.access_token); // store JWT
        onLoginSuccess();
      } else {
        const err = await res.json();
        alert(err.detail || "Login failed ❌");
      }
    } catch (error) {
      alert("Error connecting to server");
      console.error(error);
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
      backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex', justifyContent: 'center', alignItems: 'center'
    }}>
      <div style={{ background: 'white', padding: '2rem', borderRadius: '10px', width: '300px' }} onClick={(e) => e.stopPropagation()}>
        <h3 style={{ marginBottom: '1rem' }}>Login Please !!</h3>
        <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} style={{ width: '100%', padding: '0.5rem', marginBottom: '1rem' }} />
        <input type="password" placeholder="Password" value={pass} onChange={e => setPass(e.target.value)} style={{ width: '100%', padding: '0.5rem', marginBottom: '1rem' }} />
        <button onClick={handleLogin} style={{ width: '100%', padding: '0.5rem', backgroundColor: 'black', color: 'white', border: 'none' }}>Login</button>
        <button onClick={onClose} style={{ width: '100%', marginTop: '0.5rem', padding: '0.5rem', backgroundColor: '#ccc', border: 'none' }}>Cancel</button>
      </div>
    </div>
  );
};

const RegisterModal = ({ onClose, onRegisterSuccess }) => {
  const [email, setEmail] = useState('');
  const [pass, setPass] = useState('');

  const handleRegister = async () => {
    try {
      const res = await fetch(`${API}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, password: pass }),
      });

      if (res.ok) {
        const data = await res.json();
        alert(data.message || "Registered successfully ✅");
        onRegisterSuccess(email);
      } else {
        const err = await res.json();
        alert(err.detail || "Registration failed ❌");
      }
    } catch (error) {
      alert("Error connecting to server");
      console.error(error);
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
      backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex', justifyContent: 'center', alignItems: 'center'
    }}>
      <div style={{ background: 'white', padding: '2rem', borderRadius: '10px', width: '300px' }} onClick={(e) => e.stopPropagation()}>
        <h3 style={{ marginBottom: '1rem' }}>Register Here !!</h3>
        <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} style={{ width: '100%', padding: '0.5rem', marginBottom: '1rem' }} />
        <input type="password" placeholder="Password" value={pass} onChange={e => setPass(e.target.value)} style={{ width: '100%', padding: '0.5rem', marginBottom: '1rem' }} />
        <button onClick={handleRegister} style={{ width: '100%', padding: '0.5rem', backgroundColor: 'black', color: 'white', border: 'none' }}>Register</button>
        <button onClick={onClose} style={{ width: '100%', marginTop: '0.5rem', padding: '0.5rem', backgroundColor: '#ccc', border: 'none' }}>Cancel</button>
      </div>
    </div>
  );
};

export { LoginModal, RegisterModal };
