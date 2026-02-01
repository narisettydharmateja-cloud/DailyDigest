import React from 'react'
import './Hero.css'

function Hero() {
  return (
    <div className="hero">
      <div className="hero-glow"></div>
      <div className="hero-content">
        <div className="hero-badge">New: Llama 3 Intelligence</div>
        <h1 className="hero-title">
          Curated intelligence,<br />
          <span className="gradient-text">delivered daily.</span>
        </h1>
        <p className="hero-subtitle">
          Stop scrolling. Start knowing.
        </p>
        <p className="hero-description">
          We use local LLMs to read thousands of articles, filter out the noise, 
          and deliver only the 1% that actually matters to your career.
        </p>
        
        <div className="hero-actions">
          <button className="btn-primary" onClick={() => document.getElementById('subscribe').scrollIntoView({ behavior: 'smooth' })}>
            Subscribe for free
          </button>
          <button className="btn-secondary" onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}>
            How it works
          </button>
        </div>

        <div className="hero-stats">
          <div className="stat-item">
            <span className="stat-value">10k+</span>
            <span className="stat-label">Sources Daily</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-item">
            <span className="stat-value">AI</span>
            <span className="stat-label">Curation</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-item">
            <span className="stat-value">0%</span>
            <span className="stat-label">Noise</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Hero
