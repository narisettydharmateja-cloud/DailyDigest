import { useState } from 'react'
import axios from 'axios'
import './SubscriptionForm.css'

function SubscriptionForm() {
  const [formData, setFormData] = useState({
    email: '',
    categories: [],
    frequency: 'daily'
  })
  const [status, setStatus] = useState({ type: '', message: '' })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const categories = [
    { id: 'genai', label: 'GenAI News', description: 'Latest in LLMs, Agents & Research' },
    { id: 'product', label: 'Product Ideas', description: 'Market gaps & startup trends' },
    { id: 'tech', label: 'Deep Tech', description: 'Hardware, Rust, & Engineering' },
    { id: 'startup', label: 'VC & Funding', description: 'Who is raising what' }
  ]

  const handleEmailChange = (e) => {
    setFormData({ ...formData, email: e.target.value })
    setStatus({ type: '', message: '' })
  }

  const handleCategoryToggle = (categoryId) => {
    const newCategories = formData.categories.includes(categoryId)
      ? formData.categories.filter(c => c !== categoryId)
      : [...formData.categories, categoryId]
    
    setFormData({ ...formData, categories: newCategories })
  }

  const handleFrequencyChange = (e) => {
    setFormData({ ...formData, frequency: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Validation
    if (!formData.email) {
      setStatus({ type: 'error', message: 'Please enter your email address' })
      return
    }
    
    if (formData.categories.length === 0) {
      setStatus({ type: 'error', message: 'Select at least one topic' })
      return
    }

    setIsSubmitting(true)
    setStatus({ type: '', message: '' })

    try {
      const response = await axios.post('/api/subscribe', formData)
      
      setStatus({ 
        type: 'success', 
        message: 'You are in. Check your inbox.' 
      })
      
      setFormData({ email: '', categories: [], frequency: 'daily' })
    } catch (error) {
      setStatus({ 
        type: 'error', 
        message: error.response?.data?.detail || 'Something went wrong. Try again.' 
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="subscription-section">
      <div className="subscription-wrapper">
        <div className="subscription-header">
          <h2 className="subscription-title">Access the 1%</h2>
          <p className="subscription-subtitle">
            Join 10,000+ engineers receiving the DailyDigest.
          </p>
        </div>

        <div className="subscription-card">
          <form onSubmit={handleSubmit} className="subscription-form">
            {/* Email Input */}
            <div className="form-group">
              <label htmlFor="email" className="form-label">
                Where should we send it?
              </label>
              <input
                type="email"
                id="email"
                className="form-input"
                placeholder="name@company.com"
                value={formData.email}
                onChange={handleEmailChange}
                required
              />
            </div>

            {/* Categories Selection */}
            <div className="form-group">
              <label className="form-label">Select your interests</label>
              <div className="categories-grid">
                {categories.map((category) => (
                  <div
                    key={category.id}
                    className={`category-item ${
                      formData.categories.includes(category.id) ? 'selected' : ''
                    }`}
                    onClick={() => handleCategoryToggle(category.id)}
                  >
                    <div className="checkbox-custom">
                       {formData.categories.includes(category.id) && <span className="checkmark">✓</span>}
                    </div>
                    <div className="category-info">
                      <span className="category-name">{category.label}</span>
                      <span className="category-desc">{category.description}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Frequency Selection */}
            <div className="form-group">
              <label htmlFor="frequency" className="form-label">
                Frequency
              </label>
              <div className="frequency-selector">
                {['daily', 'weekly', 'biweekly'].map((freq) => (
                  <button
                    key={freq}
                    type="button"
                    className={`freq-btn ${formData.frequency === freq ? 'active' : ''}`}
                    onClick={() => setFormData({ ...formData, frequency: freq })}
                  >
                    {freq.charAt(0).toUpperCase() + freq.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Status Message */}
            {status.message && (
              <div className={`status-display ${status.type}`}>
                {status.message}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              className="submit-btn"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Joining...' : 'Join DailyDigest'}
            </button>
            
            <p className="privacy-note">
              No spam. Unsubscribe anytime. High signal only.
            </p>
          </form>
        </div>
      </div>
    </div>
  )
}

export default SubscriptionForm
