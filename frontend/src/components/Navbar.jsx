import React from 'react';

const Navbar = ({ onLoginClick, onRegisterClick, onTabClick, isLoggedIn, onLogout }) => {
  return (
    <nav style={{ padding: '1rem', display: 'flex', justifyContent: 'space-between', backgroundColor: 'black', color: 'white' }}>
      <div
        style={{ fontWeight: 'bold', fontSize: '1.5rem', cursor: 'pointer' }}
        onClick={(e) => { e.stopPropagation(); window.location.href = '/'; }}
      >
        Parijat Controlware Inc.
      </div>
      <div>
        <button onClick={(e) => { e.stopPropagation(); window.location.href = '/'; }} style={navBtn}>Home</button>
        <button onClick={(e) => { e.stopPropagation(); onTabClick('support'); }} style={navBtn}>Support</button>
        <button onClick={(e) => { e.stopPropagation(); onTabClick('about'); }} style={navBtn}>About Us</button>
        <button onClick={(e) => { e.stopPropagation(); onTabClick('contact'); }} style={navBtn}>Contact Us</button>
        {
          isLoggedIn ? (
            <button onClick={(e) => { e.stopPropagation(); onLogout(); }} style={logoutBtn}>Logout</button>
          ) : (
            <>
              <button onClick={(e) => { e.stopPropagation(); onLoginClick(e); }} style={loginBtn}>Login</button>
              <button onClick={(e) => { e.stopPropagation(); onRegisterClick(e); }} style={loginBtn}>Register</button>
            </>
          )
        }
      </div>
    </nav>
  );
};

const navBtn = {
  margin: '0 0.5rem',
  background: 'transparent',
  border: 'none',
  color: 'white',
  fontSize: '1rem',
  cursor: 'pointer'
};

const loginBtn = {
  ...navBtn,
  backgroundColor: '#fcbf49',
  padding: '0.5rem 1rem',
  borderRadius: '4px',
  color: '#002b5b'
};

const logoutBtn = {
  ...navBtn,
  backgroundColor: 'red',
  padding: '0.5rem 1rem',
  borderRadius: '4px',
  color: 'white'
};

export default Navbar;
