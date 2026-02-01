import { useState } from 'react'
import './App.css'
import Navbar from './components/Navbar'
import SubscriptionForm from './components/SubscriptionForm'
import Hero from './components/Hero'
import Features from './components/Features'

function App() {
  return (
    <div className="App">
      <Navbar />
      <Hero />
      <div id="features">
        <Features />
      </div>
      <div id="subscribe">
        <SubscriptionForm />
      </div>
      <footer className="footer">
        <p>&copy; 2026 DailyDigest. AI-Powered Intelligence Digest System</p>
      </footer>
    </div>
  )
}

export default App
