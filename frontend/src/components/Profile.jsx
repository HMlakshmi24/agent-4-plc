import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./profile.css";
import { API } from '../config/api'; 

const Profile = ({ onLogout }) => {
  const [showModal, setShowModal] = useState(false);
  const [profile, setProfile] = useState({ email: "", name: "", phone: "" });
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState(localStorage.getItem("token")); // fetch token from localStorage

  // Watch localStorage changes (useful after login/logout)
  useEffect(() => {
    setToken(localStorage.getItem("token"));
  }, []);

  // Fetch profile when modal opens
  const fetchProfile = async () => {
    if (!token) {
      alert("Please login first!");
      return;
    }
    try {
      const res = await fetch(`${API}/profile/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch profile");
      const data = await res.json();
      setProfile(data);
    } catch (err) {
      console.error(err);
      alert("Error fetching profile. Please login again.");
    }
  };

  // Update profile
  const handleUpdate = async () => {
    if (!token) return alert("Not authenticated!");
    if (!profile.name.trim() && !profile.phone.trim()) {
      return alert("Please fill in name or phone to update!");
    }
    setLoading(true);
    try {
      const res = await fetch(`${API}/profile/update`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name: profile.name, phone: profile.phone }),
      });
      if (!res.ok) throw new Error("Update failed");
      const data = await res.json();
      setProfile(data.profile);
      alert("✅ Profile updated successfully!");
    } catch (err) {
      console.error(err);
      alert("Failed to update profile.");
    } finally {
      setLoading(false);
    }
  };

  // Logout
  const handleLogout = async () => {
    try {
      await fetch(`${API}/profile/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch (err) {
      console.warn("Logout API failed but clearing session.");
    }
    localStorage.removeItem("token"); // clear from storage
    setToken(null);
    onLogout && onLogout();
    setShowModal(false);
  };

  return (
    <div>
      {/* Profile Icon */}
      {token && (
        <motion.div
          className="profile-icon"
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => {
            fetchProfile();
            setShowModal(true);
          }}
        >
          👤
        </motion.div>
      )}

      {/* Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div
            className="profile-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="profile-modal"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <h2>Your Profile</h2>

              <div className="profile-field">
                <label>Email</label>
                <input type="text" value={profile.email} disabled />
              </div>

              <div className="profile-field">
                <label>Name</label>
                <input
                  type="text"
                  value={profile.name}
                  onChange={(e) =>
                    setProfile({ ...profile, name: e.target.value })
                  }
                  placeholder="Enter your name"
                />
              </div>

              <div className="profile-field">
                <label>Phone</label>
                <input
                  type="text"
                  value={profile.phone}
                  onChange={(e) =>
                    setProfile({ ...profile, phone: e.target.value })
                  }
                  placeholder="Enter your phone"
                />
              </div>

              <div className="profile-buttons">
                <button
                  className="cancel-btn"
                  onClick={() => setShowModal(false)}
                >
                  Close
                </button>
                <button
                  className="save-btn"
                  onClick={handleUpdate}
                  disabled={loading}
                >
                  {loading ? "Saving..." : "Save"}
                </button>
                <button className="logout-btn" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Profile;
