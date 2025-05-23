import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import 'reactflow/dist/style.css'
import './index.css'
import App from './App.tsx'
// import App from './App-test.tsx'
// import App from './AppDebug.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
