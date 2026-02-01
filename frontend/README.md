# DailyDigest Frontend

React-based frontend for the DailyDigest AI-Powered Intelligence Digest System.

## Features

- 🎨 Modern, responsive UI with gradient design
- 📧 Email subscription form
- 🎯 Multiple category selection (GenAI News, Product Ideas, Technology, Startups)
- ⚙️ Frequency preferences (Daily, Weekly, Bi-weekly)
- ✅ Form validation and status feedback
- 🌙 Dark theme optimized

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on port 8000

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The app will open at http://localhost:3000

### Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Hero.jsx              # Hero section
│   │   ├── Hero.css
│   │   ├── Features.jsx          # Features showcase
│   │   ├── Features.css
│   │   ├── SubscriptionForm.jsx  # Main subscription form
│   │   └── SubscriptionForm.css
│   ├── App.jsx                   # Main app component
│   ├── App.css
│   ├── main.jsx                  # Entry point
│   └── index.css                 # Global styles
├── index.html
├── package.json
└── vite.config.js
```

## API Integration

The frontend connects to the backend API at `/api/subscribe` (proxied to http://localhost:8000).

Expected API endpoint:
- `POST /api/subscribe` - Create/update subscription
  - Body: `{ email: string, categories: string[], frequency: string }`

## Customization

### Colors

Edit CSS variables in `src/index.css`:
```css
:root {
  --primary-color: #6366f1;
  --secondary-color: #8b5cf6;
  /* ... */
}
```

### Categories

Modify the categories array in `src/components/SubscriptionForm.jsx`:
```javascript
const categories = [
  { id: 'genai', label: 'GenAI News', description: '...' },
  // Add more categories
]
```

## Technologies

- React 18
- Vite (build tool)
- Axios (HTTP client)
- CSS3 (styling)
