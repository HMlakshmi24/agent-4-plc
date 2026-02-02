import React from "react";
import Profile from "./Profile";
import { useTheme } from "../context/ThemeContext";
import { FiSun, FiMoon } from "react-icons/fi"; // Assuming react-icons is installed

const Navbar = ({ onLoginClick, onRegisterClick, onTabClick, isLoggedIn, onLogout, token }) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 py-4 bg-black/50 backdrop-blur-md border-b border-white/10 text-white transition-colors duration-300 dark:bg-premium-black/80 dark:border-premium-border/50">
      <div
        className="text-2xl font-bold cursor-pointer tracking-tight bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent hover:opacity-80 transition-opacity"
        onClick={(e) => {
          e.stopPropagation();
          window.location.href = "/";
        }}
        aria-label="Home"
      >
        Parijat Controlware Inc.
      </div>

      <div className="flex items-center space-x-6">
        <NavButton onClick={() => window.location.href = "/"}>Home</NavButton>
        <NavButton onClick={(e) => { e.stopPropagation(); onTabClick("about"); }}>About Us</NavButton>

        <button
          onClick={toggleTheme}
          className="p-2 rounded-full hover:bg-white/10 transition-colors focus:outline-none"
          title="Toggle Theme"
        >
          {theme === 'dark' ? <FiSun className="w-5 h-5" /> : <FiMoon className="w-5 h-5" />}
        </button>

        {isLoggedIn ? (
          <Profile token={token} onLogout={onLogout} />
        ) : (
          <div className="flex space-x-4">
            <LoginButton onClick={(e) => { e.stopPropagation(); onLoginClick(e); }}>
              Login
            </LoginButton>
            <LoginButton onClick={(e) => { e.stopPropagation(); onRegisterClick(e); }} variant="primary">
              Register
            </LoginButton>
          </div>
        )}
      </div>
    </nav>
  );
};

const NavButton = ({ children, onClick }) => (
  <button
    onClick={onClick}
    className="text-sm font-medium text-white/80 hover:text-white transition-colors capitalize bg-transparent border-none cursor-pointer"
  >
    {children}
  </button>
);

const LoginButton = ({ children, onClick, variant = "secondary" }) => {
  const baseStyle = "px-5 py-2 rounded-lg text-sm font-semibold transition-all shadow-md hover:shadow-lg focus:outline-none transform hover:-translate-y-0.5";
  const variants = {
    primary: "bg-[#fcbf49] text-[#002b5b] hover:bg-[#ffca63]", // Keeping the brand gold
    secondary: "bg-white/10 text-white hover:bg-white/20 backdrop-blur-sm border border-white/10",
  };

  return (
    <button onClick={onClick} className={`${baseStyle} ${variants[variant] || variants.secondary}`}>
      {children}
    </button>
  );
};

export default Navbar;
