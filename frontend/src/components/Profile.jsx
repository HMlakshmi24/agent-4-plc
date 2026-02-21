import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./profile.css";
import { API } from '../config/api';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

const Profile = ({ onLogout }) => {
  const { user, updateProfile } = useAuth(); // Use context
  const { theme } = useTheme();
  const [showDropdown, setShowDropdown] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const [tokens, setTokens] = useState({ used: 0, limit: 50000 });

  // Local state for editing in modal
  const [editData, setEditData] = useState({});

  const dropdownRef = useRef(null);

  // Fetch tokens for billing tab
  useEffect(() => {
    if (showModal && activeTab === 'billing' && user?.email) {
      const fetchTokens = async () => {
        try {
          const tokenStr = localStorage.getItem("automind_token") || localStorage.getItem("token");
          const headers = { "Content-Type": "application/json" };
          if (tokenStr && !tokenStr.startsWith("mock-")) headers["Authorization"] = `Bearer ${tokenStr}`;
          if (user.email) headers["X-User-Email"] = user.email;

          const res = await fetch(`${API}/api/tokens`, { headers });
          if (res.ok) {
            const data = await res.json();
            setTokens(data);
          }
        } catch (e) { console.error("Token fetch failed", e); }
      };
      fetchTokens();
    }
  }, [showModal, activeTab, user]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const openSettings = () => {
    setEditData({
      name: user.name || "",
      phone: user.phone || "",
      company: user.company || "",
      designation: user.designation || "",
      department: user.department || "",
      experience: user.experience || 0,
      industry_type: user.industry_type || "",
      default_plc: user.default_plc || "Siemens",
      default_language: user.default_language || "ST",
      strict_mode: user.strict_mode !== undefined ? user.strict_mode : true,
      api_key: user.api_key || "",
      license_type: user.license_type || "Pro"
    });
    setShowDropdown(false);
    setShowModal(true);
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const tokenStr = localStorage.getItem("automind_token") || localStorage.getItem("token");
      const headers = { "Content-Type": "application/json" };
      if (tokenStr && !tokenStr.startsWith("mock-")) headers["Authorization"] = `Bearer ${tokenStr}`;
      if (user.email) headers["X-User-Email"] = user.email;

      // Make sure experience is an int
      const payload = { ...editData, experience: parseInt(editData.experience) || 0 };

      const res = await fetch(`${API}/profile/update`, {
        method: "PUT",
        headers,
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Failed to update");

      const data = await res.json();
      updateProfile(data.profile);
      setShowModal(false);
      alert("✅ Settings updated successfully!");
    } catch (error) {
      console.error(error);
      alert("Failed to update profile");
    } finally {
      setLoading(false);
    }
  };

  const getInitials = (name) => {
    if (!name) return "U";
    return name.split(" ").map((n) => n[0]).join("").toUpperCase().substring(0, 2);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <motion.div
        className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-white flex items-center justify-center font-bold cursor-pointer shadow-md hover:shadow-lg border-2 border-white dark:border-slate-700 select-none"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setShowDropdown(!showDropdown)}
      >
        {getInitials(user?.name)}
      </motion.div>

      <AnimatePresence>
        {showDropdown && (
          <motion.div
            className="absolute right-0 mt-3 w-72 bg-white dark:bg-slate-800 rounded-xl shadow-2xl border border-slate-100 dark:border-slate-700 z-50 overflow-hidden"
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
          >
            <div className="p-5 border-b border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
              <p className="font-bold text-slate-800 dark:text-white text-lg truncate">{user?.name || "Engineer"}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 truncate">{user?.email}</p>
              <span className="inline-block mt-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-[10px] font-bold uppercase rounded-full tracking-wider">
                {user?.designation || "Automation Engineer"}
              </span>
            </div>

            <div className="py-2">
              <button onClick={() => { setActiveTab('profile'); openSettings(); }} className="w-full text-left px-5 py-3 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-3">
                <span>⚙️</span> Settings & Profile
              </button>
              <button onClick={() => { setActiveTab('company'); openSettings(); }} className="w-full text-left px-5 py-3 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-3">
                <span>🏢</span> Company Details
              </button>
              <button onClick={() => { setActiveTab('billing'); openSettings(); }} className="w-full text-left px-5 py-3 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-3">
                <span>📊</span> Usage & Billing
              </button>
            </div>

            <div className="border-t border-slate-100 dark:border-slate-700 p-2">
              <button onClick={onLogout} className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors flex items-center justify-center font-medium">
                Sign Out
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showModal && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 pt-16 mt-8">
            <motion.div
              className="bg-white dark:bg-slate-900 w-full max-w-4xl rounded-2xl shadow-2xl flex flex-col md:flex-row h-[70vh] min-h-[500px] overflow-hidden relative"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
            >
              {/* Sidebar */}
              <div className="w-full md:w-64 border-r border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex flex-col">
                <div className="p-6 border-b border-slate-200 dark:border-slate-800">
                  <h2 className="text-xl font-bold text-slate-800 dark:text-white">Workspace</h2>
                </div>
                <div className="flex-1 p-4 space-y-2">
                  <TabButton id="profile" icon="👤" label="Personal Profile" activeTab={activeTab} onClick={setActiveTab} />
                  <TabButton id="company" icon="🏢" label="Company Profile" activeTab={activeTab} onClick={setActiveTab} />
                  <TabButton id="settings" icon="⚙️" label="Generation Settings" activeTab={activeTab} onClick={setActiveTab} />
                  <TabButton id="billing" icon="📊" label="Usage & Billing" activeTab={activeTab} onClick={setActiveTab} />
                </div>
              </div>

              {/* Form Content */}
              <div className="flex-1 flex flex-col bg-white dark:bg-slate-900 overflow-y-auto">
                <div className="sticky top-0 right-0 z-20 flex justify-end p-4 pointer-events-none">
                  <button onClick={() => setShowModal(false)} className="pointer-events-auto w-8 h-8 flex items-center justify-center rounded-full bg-slate-200 dark:bg-slate-700 text-slate-600 hover:bg-slate-300 dark:hover:bg-slate-600 dark:text-white transition-colors">&times;</button>
                </div>

                <div className="p-8 flex-1">
                  {/* Read Only Header Block */}
                  <div className="mb-8 p-4 rounded-xl border border-blue-100 dark:border-blue-900/30 bg-blue-50 dark:bg-blue-900/10 flex items-center gap-4">
                    <div className="w-16 h-16 rounded-full bg-blue-600 text-white flex items-center justify-center text-2xl font-bold shadow-lg">
                      {getInitials(user?.name)}
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-slate-900 dark:text-white">{user?.name}</h3>
                      <p className="text-sm text-slate-500 dark:text-slate-400">{user?.email} | {user?.license_type || "Pro"} License</p>
                    </div>
                  </div>

                  {/* Profile Tab */}
                  {activeTab === 'profile' && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-bold text-slate-800 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-2">Personal Information</h3>
                      <div className="grid grid-cols-2 gap-6">
                        <InputField label="Full Name" value={editData.name} onChange={(v) => setEditData({ ...editData, name: v })} />
                        <InputField label="Mobile Number" value={editData.phone} onChange={(v) => setEditData({ ...editData, phone: v })} type="tel" />
                        <InputField label="Designation" value={editData.designation} onChange={(v) => setEditData({ ...editData, designation: v })} placeholder="e.g. Automation Engineer" />
                        <InputField label="Department" value={editData.department} onChange={(v) => setEditData({ ...editData, department: v })} placeholder="e.g. SCADA Systems" />
                        <InputField label="Years of Experience" value={editData.experience} onChange={(v) => setEditData({ ...editData, experience: v })} type="number" />
                      </div>
                    </div>
                  )}

                  {/* Company Tab */}
                  {activeTab === 'company' && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-bold text-slate-800 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-2">Company Details</h3>
                      <div className="grid grid-cols-2 gap-6">
                        <InputField label="Company Name" value={editData.company} onChange={(v) => setEditData({ ...editData, company: v })} />
                        <InputField label="Industry Type" value={editData.industry_type} onChange={(v) => setEditData({ ...editData, industry_type: v })} placeholder="e.g. Oil & Gas, Pharma, Packaging" />
                      </div>
                    </div>
                  )}

                  {/* Settings Tab */}
                  {activeTab === 'settings' && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-bold text-slate-800 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-2">AI Generation Defaults</h3>
                      <div className="grid grid-cols-2 gap-6">
                        <div>
                          <label className="block text-xs font-bold uppercase text-slate-500 mb-2">Default target Platform</label>
                          <select className="w-full p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-white outline-none"
                            value={editData.default_plc} onChange={(e) => setEditData({ ...editData, default_plc: e.target.value })}>
                            <option value="Siemens">Siemens TIA Portal</option>
                            <option value="Allen-Bradley">Allen-Bradley Studio5000</option>
                            <option value="Codesys">Codesys V3</option>
                            <option value="Schneider">Schneider EcoStruxure</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-bold uppercase text-slate-500 mb-2">Default Language</label>
                          <select className="w-full p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-white outline-none"
                            value={editData.default_language} onChange={(e) => setEditData({ ...editData, default_language: e.target.value })}>
                            <option value="ST">Structured Text (ST)</option>
                            <option value="LD">Ladder Logic (LD)</option>
                          </select>
                        </div>
                        <div className="flex items-center gap-3 bg-slate-50 dark:bg-slate-800 p-3 rounded-xl border border-slate-200 dark:border-slate-700">
                          <input type="checkbox" id="strict" className="w-5 h-5 rounded text-blue-600" checked={editData.strict_mode} onChange={(e) => setEditData({ ...editData, strict_mode: e.target.checked })} />
                          <label htmlFor="strict" className="text-sm font-semibold text-slate-700 dark:text-slate-300">Enforce Strict IEC 61131-3 Mode</label>
                        </div>
                        <div className="col-span-2">
                          <InputField label="Custom OpenAI API Key (Optional)" value={editData.api_key} onChange={(v) => setEditData({ ...editData, api_key: v })} type="password" placeholder="sk-..." />
                          <p className="text-[10px] text-slate-500 mt-1">Provide your own key to bypass token limits for the floating AI assistant.</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Billing Tab */}
                  {activeTab === 'billing' && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-bold text-slate-800 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-2">Usage & Billing</h3>
                      <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700 space-y-4">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-bold text-slate-500 uppercase tracking-wide">Current Plan</span>
                          <span className="bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 px-3 py-1 rounded-full text-sm font-bold">{user?.license_type || "Pro"}</span>
                        </div>

                        <div>
                          <div className="flex justify-between text-sm mb-2 font-semibold">
                            <span className="text-slate-700 dark:text-slate-300">Token Usage</span>
                            <span className="text-blue-600 dark:text-blue-400">{tokens.used.toLocaleString()} / {tokens.limit.toLocaleString()}</span>
                          </div>
                          <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3">
                            <div className="bg-blue-600 h-3 rounded-full transition-all" style={{ width: `${Math.min(100, Math.max(0, (tokens.used / tokens.limit) * 100))}%` }}></div>
                          </div>
                          <p className="text-[11px] text-slate-500 mt-2">Tokens are consumed during ST/LD generation and HMI synthesis.</p>
                        </div>
                      </div>
                      <div className="flex justify-start">
                        <button onClick={() => alert("Stripe Billing Portal integration coming soon in production.")} className="px-5 py-2 rounded-lg border border-red-200 dark:border-red-900/30 text-red-600 dark:text-red-400 font-semibold text-sm hover:bg-red-50 dark:hover:bg-red-900/20 transition-all">
                          Manage Subscription via Stripe →
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Footer Save Block (Hidden for Billing) */}
                {activeTab !== 'billing' && (
                  <div className="p-6 border-t border-slate-100 dark:border-slate-800 flex justify-end gap-3 bg-slate-50 dark:bg-slate-800/50">
                    <button onClick={() => setShowModal(false)} className="px-5 py-2.5 text-slate-600 dark:text-slate-300 font-medium hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors">Cancel</button>
                    <button onClick={handleSave} disabled={loading} className="px-8 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg shadow-lg hover:shadow-blue-500/30 transition-all disabled:opacity-70 disabled:cursor-not-allowed">
                      {loading ? "Saving..." : "Save Changes"}
                    </button>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Subcomponents for cleanliness
const TabButton = ({ id, icon, label, activeTab, onClick }) => (
  <button
    onClick={() => onClick(id)}
    className={`w-full text-left px-4 py-3 rounded-xl flex items-center gap-3 font-semibold transition-all ${activeTab === id ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400 shadow-sm' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800/80'}`}
  >
    <span className="text-xl">{icon}</span> {label}
  </button>
);

const InputField = ({ label, value, onChange, type = "text", placeholder = "" }) => (
  <div>
    <label className="block text-xs font-bold uppercase text-slate-500 mb-2">{label}</label>
    <input
      type={type}
      className="w-full p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all placeholder-slate-300 dark:placeholder-slate-600"
      value={value === undefined ? "" : value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  </div>
);

export default Profile;
