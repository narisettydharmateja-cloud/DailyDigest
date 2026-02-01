import React from 'react'
import './Features.css'

function Features() {
  const features = [
    {
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a10 10 0 1 0 10 10 4 4 0 0 1-5-5 4 4 0 0 1-5-5" /><path d="M8.5 8.5v.01" /><path d="M16 12v.01" /><path d="M12 16v.01" /></svg>
      ),
      title: 'Local Intelligence',
      description: 'Powered by Ollama and Llama 3 models running locally. Your data never leaves your infrastructure.'
    },
    {
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
      ),
      title: 'Persona-Based Digests',
      description: 'Switch between "GenAI News" for technical updates or "Product Ideas" for market trends.'
    },
    {
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
      ),
      title: 'Noise Reduction',
      description: 'We score every article. Only the top 1% with high relevance scores make it to your inbox.'
    },
    {
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 17a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9.5C2 7 4 5 4 5h16s2 2 2 4.5V17z"/><path d="M12 5L7 17"/><path d="M12 5l5 12"/></svg>
      ),
      title: 'Multi-Channel',
      description: ' get your digest via beautiful HTML email or a concise Telegram summary.'
    }
  ]

  return (
    <div className="features-section">
      <div className="section-header">
        <h2 className="section-title">Why DailyDigest?</h2>
        <p className="section-subtitle">Built for information density, not engagement metrics.</p>
      </div>
      
      <div className="features-grid">
        {features.map((feature, index) => (
          <div key={index} className="feature-card">
            <div className="feature-icon-wrapper">
              {feature.icon}
            </div>
            <h3 className="feature-title">{feature.title}</h3>
            <p className="feature-description">{feature.description}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Features
