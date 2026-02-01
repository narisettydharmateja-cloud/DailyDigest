import React, { useState, useEffect } from 'react';
import './Navbar.css';

function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav className={`navbar ${scrolled ? 'scrolled' : ''}`}>
      <div className="navbar-container">
        <div className="navbar-logo">
          <div className="logo-icon"></div>
          <span className="logo-text">DailyDigest</span>
        </div>
        
        <div className="navbar-links">
          <a href="#features" className="nav-link">Features</a>
          <a href="#about" className="nav-link">How it Works</a>
        </div>

        <button className="nav-cta" onClick={() => document.getElementById('subscribe').scrollIntoView({ behavior: 'smooth' })}>
          Get Started
        </button>
      </div>
    </nav>
  );
}

export default Navbar;
