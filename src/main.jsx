import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './app/App.jsx';
import { AppProvider, useApp } from './app/AppContext.jsx';
import { ToastRegion } from './components/Primitives.jsx';
import './styles/index.css';

function Application() {
  const { toasts, dismissToast } = useApp();
  return <><App /><ToastRegion toasts={toasts} dismissToast={dismissToast} /></>;
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AppProvider>
      <BrowserRouter><Application /></BrowserRouter>
    </AppProvider>
  </React.StrictMode>,
);
