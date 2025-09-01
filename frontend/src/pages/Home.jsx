// pages/Home.jsx
import React, { useState, useEffect } from 'react';

import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import InfoSection from '../components/plc_to_st';
import { LoginModal, RegisterModal } from '../components/LoginModal';
import Footer from '../components/Footer';
import TransparentCard from '../components/TransparentCard';

const Home = () => {
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [activeTab, setActiveTab] = useState(null);
  const [showLoggedInMsg, setShowLoggedInMsg] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('isLoggedIn') === 'true';
    setIsLoggedIn(stored);
  }, []);

  const handleLoginSuccess = () => {
    localStorage.setItem('isLoggedIn', 'true');
    setIsLoggedIn(true);
    setShowLogin(false);

    setShowLoggedInMsg(true);
    setTimeout(() => {
      setShowLoggedInMsg(false);
    }, 2000);
  };

  const handleRegisterSuccess = (username) => {
    alert(`Registered successfully as ${username}`);
    setShowRegister(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('isLoggedIn');
    setIsLoggedIn(false);
    setActiveTab(null);
  };

  return (
    <div onClick={() => setActiveTab(null)}>
      <Navbar
        onLoginClick={(e) => {
          e.stopPropagation();
          setShowLogin(true);
        }}
        onRegisterClick={(e) => {
          e.stopPropagation();
          setShowRegister(true);
        }}
        onTabClick={(tab) => setActiveTab(tab)}
        isLoggedIn={isLoggedIn}
        onLogout={handleLogout}
      />
      <Hero />
      {activeTab && <TransparentCard tab={activeTab} onClose={() => setActiveTab(null)} />}
      <InfoSection />
      <Footer />
      {showLogin && (
        <LoginModal
          onClose={() => setShowLogin(false)}
          onLoginSuccess={handleLoginSuccess}
        />
      )}
      {showRegister && (
        <RegisterModal
          onClose={() => setShowRegister(false)}
          onRegisterSuccess={handleRegisterSuccess}
        />
      )}
      {showLoggedInMsg && (
        <div style={{
          position: 'fixed',
          top: '20%',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: 'grey',
          color: 'white',
          padding: '1rem 2rem',
          borderRadius: '8px',
          fontSize: '1.2rem',
          zIndex: 10000,
          boxShadow: '0 0 10px rgba(0,0,0,0.3)'
        }}>
          You are logged in Successfully!!.
        </div>
      )}
    </div>
  );
};

export default Home;
