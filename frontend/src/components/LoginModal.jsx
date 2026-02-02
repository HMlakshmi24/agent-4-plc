import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { API } from '../config/api'; 
import './LoginModal.css';

const LoginModal = ({ onClose, onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [pass, setPass] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleLogin = useCallback(async (e) => {
    e.preventDefault();
    if (!email || !pass) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, password: pass }),
      });

      const data = await res.json();

      if (res.ok) {
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("user", email);
        localStorage.setItem("userId", data.user_id || email);
        setSuccess("Login successful! ✅");
        setTimeout(() => {
          onLoginSuccess();
        }, 500);
      } else {
        const errorMsg = typeof data.detail === "string"
          ? data.detail
          : data.message || "Login failed";
        setError(errorMsg);
      }
    } catch (error) {
      setError("Connection error. Please try again.");
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [email, pass, onLoginSuccess]);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleLogin(e);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        className="auth-modal-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <motion.div
          className="auth-modal"
          initial={{ scale: 0.8, opacity: 0, y: -50 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.8, opacity: 0 }}
          transition={{ duration: 0.3 }}
          onClick={(e) => e.stopPropagation()}
        >
          <button className="modal-close-btn" onClick={onClose}>✕</button>
          
          <div className="auth-header">
            <h2>Login</h2>
            <p>Access your PLC generator account</p>
          </div>

          <form onSubmit={handleLogin} className="auth-form">
            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={loading}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                value={pass}
                onChange={(e) => setPass(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={loading}
                required
              />
            </div>

            {error && <div className="error-message">⚠️ {error}</div>}
            {success && <div className="success-message">✅ {success}</div>}

            <button
              type="submit"
              className="auth-btn-submit"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner"></span> Logging in...
                </>
              ) : (
                'Login'
              )}
            </button>
          </form>

          <button
            className="auth-btn-cancel"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

const RegisterModal = ({ onClose, onRegisterSuccess }) => {
  const [email, setEmail] = useState('');
  const [pass, setPass] = useState('');
  const [confirmPass, setConfirmPass] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleRegister = useCallback(async (e) => {
    e.preventDefault();
    
    if (!email || !pass || !confirmPass) {
      setError('Please fill in all fields');
      return;
    }

    if (pass !== confirmPass) {
      setError('Passwords do not match');
      return;
    }

    if (pass.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const res = await fetch(`${API}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, password: pass }),
      });

      const data = await res.json();

      if (res.ok) {
        setSuccess("Registered successfully! ✅");
        setTimeout(() => {
          onRegisterSuccess(email);
        }, 500);
      } else {
        const errorMsg = typeof data.detail === "string"
          ? data.detail
          : data.message || "Registration failed";
        setError(errorMsg);
      }
    } catch (error) {
      setError("Connection error. Please try again.");
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [email, pass, confirmPass, onRegisterSuccess]);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleRegister(e);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        className="auth-modal-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <motion.div
          className="auth-modal"
          initial={{ scale: 0.8, opacity: 0, y: -50 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.8, opacity: 0 }}
          transition={{ duration: 0.3 }}
          onClick={(e) => e.stopPropagation()}
        >
          <button className="modal-close-btn" onClick={onClose}>✕</button>
          
          <div className="auth-header">
            <h2>Register</h2>
            <p>Create your PLC generator account</p>
          </div>

          <form onSubmit={handleRegister} className="auth-form">
            <div className="form-group">
              <label htmlFor="register-email">Email Address</label>
              <input
                id="register-email"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="register-password">Password</label>
              <input
                id="register-password"
                type="password"
                placeholder="••••••••"
                value={pass}
                onChange={(e) => setPass(e.target.value)}
                disabled={loading}
                required
              />
              <small>Minimum 6 characters</small>
            </div>

            <div className="form-group">
              <label htmlFor="confirm-password">Confirm Password</label>
              <input
                id="confirm-password"
                type="password"
                placeholder="••••••••"
                value={confirmPass}
                onChange={(e) => setConfirmPass(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={loading}
                required
              />
            </div>

            {error && <div className="error-message">⚠️ {error}</div>}
            {success && <div className="success-message">✅ {success}</div>}

            <button
              type="submit"
              className="auth-btn-submit"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner"></span> Registering...
                </>
              ) : (
                'Register'
              )}
            </button>
          </form>

          <button
            className="auth-btn-cancel"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export { LoginModal, RegisterModal };
