import React, { createContext, useState, useEffect, useContext } from 'react';
import { API } from '../config/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for stored token and user data on mount
        const token = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user_details');

        if (token && storedUser) {
            try {
                setUser(JSON.parse(storedUser));
            } catch (e) {
                console.error("Failed to parse user details", e);
                localStorage.removeItem('user_details');
            }
        }
        setLoading(false);
    }, []);

    const login = (userData, token, storeInDb = false) => {
        const fullUserData = { ...userData, storeInDb };
        localStorage.setItem('token', token);
        localStorage.setItem('user_details', JSON.stringify(fullUserData));
        setUser(fullUserData);
    };

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user_details');
        // Legacy cleanup
        localStorage.removeItem('user');
        localStorage.removeItem('userId');
        setUser(null);
    };

    const updateProfile = async (newDetails) => {
        // Optimistic update
        const updatedUser = { ...user, ...newDetails };
        setUser(updatedUser);
        localStorage.setItem('user_details', JSON.stringify(updatedUser));
        return updatedUser;
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, updateProfile, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
