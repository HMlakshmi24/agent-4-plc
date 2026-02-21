import React from "react";
import Profile from "./Profile";
import TokenCircle from "./TokenCircle";
import { useTheme } from "../context/ThemeContext";
import { FiSun, FiMoon } from "react-icons/fi"; // Assuming react-icons is installed

const Navbar = ({ onLoginClick, onRegisterClick, onTabClick, user, onLogout }) => {
  const themeContext = useTheme();
  const { theme, toggleTheme } = themeContext || { theme: 'dark', toggleTheme: () => { } };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 py-4 bg-white/80 backdrop-blur-md border-b border-gray-200 text-gray-800 transition-colors duration-300 dark:bg-black/90 dark:border-white/10 dark:text-white">
      <div className="max-w-[95%] xl:max-w-[90rem] mx-auto px-6 flex items-center justify-between">
        <div
          className="text-3xl font-bold cursor-pointer tracking-tight bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent hover:opacity-80 transition-opacity"
          onClick={(e) => {
            e.stopPropagation();
            window.location.href = "/";
          }}
          aria-label="Home"
        >
          Parijat Controlware Inc.
        </div>

        <div className="flex items-center gap-8 md:gap-12">
          {/* Always show main navigation links */}
          <div className="flex items-center gap-8">
            <NavButton onClick={() => window.location.href = "/"}>Home</NavButton>
            <NavButton onClick={(e) => { e.stopPropagation(); onTabClick("about"); }}>About Us</NavButton>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={toggleTheme}
              className="p-3 rounded-full hover:bg-white/10 transition-colors focus:outline-none"
              title="Toggle Theme"
            >
              {theme === 'dark' ? <FiSun className="w-6 h-6" /> : <FiMoon className="w-6 h-6" />}
            </button>

            {user ? (
              <div className="flex items-center gap-4">
                <TokenCircle user={user} />
                <div className="hidden md:flex flex-col items-end mr-2">
                  <span className="text-sm font-semibold tracking-wide dark:text-white text-slate-800">
                    👋 Welcome, {user.name || user.email.split('@')[0]}
                  </span>
                  {user.company && (
                    <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                      {user.company}
                    </span>
                  )}
                </div>
                <Profile user={user} onLogout={onLogout} />
              </div>
            ) : (
              <div className="flex gap-4">
                <LoginButton onClick={(e) => { e.stopPropagation(); onLoginClick(e); }}>
                  Login
                </LoginButton>
                <LoginButton onClick={(e) => { e.stopPropagation(); onRegisterClick(e); }} variant="primary">
                  Register
                </LoginButton>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

const NavButton = ({ children, onClick }) => (
  <button
    onClick={onClick}
    className="text-lg font-semibold text-gray-700 hover:text-blue-600 dark:text-white/90 dark:hover:text-blue-400 transition-colors capitalize bg-transparent border-none cursor-pointer tracking-wide"
  >
    {children}
  </button>
);

const LoginButton = ({ children, onClick, variant = "secondary" }) => {
  const baseStyle = "px-5 py-2 rounded-lg text-sm font-semibold transition-all shadow-md hover:shadow-lg focus:outline-none transform hover:-translate-y-0.5";
  const variants = {
    primary: "bg-[#fcbf49] text-[#002b5b] hover:bg-[#ffca63]", // Keeping the brand gold
    secondary: "bg-gray-100 text-gray-800 hover:bg-gray-200 border border-gray-300 dark:bg-white/10 dark:text-white dark:hover:bg-white/20 dark:border-white/10",
  };

  return (
    <button onClick={onClick} className={`${baseStyle} ${variants[variant] || variants.secondary}`}>
      {children}
    </button>
  );
};

export default Navbar;
