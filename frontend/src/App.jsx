import React, { useState, useEffect } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import * as api from './api';

function App() {
  const [status, setStatus] = useState('checking');
  const [config, setConfig] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      setStatus('checking');
      setError(null);

      // Check health
      const healthData = await api.healthCheck();
      console.log('Health check passed:', healthData);

      // Get configuration
      const configData = await api.getConfig();
      console.log('Configuration loaded:', configData);
      setConfig(configData);
      setStatus('healthy');
    } catch (err) {
      console.error('Failed to initialize app:', err);
      setError('Failed to connect to backend API. Make sure the server is running.');
      setStatus('error');
    }
  };

  return (
    <div className="app">
      <div className="container">
        <header>
          <h1>🤖 RAG Azure Chat</h1>
          <p>Retrieval-Augmented Generation powered by Azure</p>
          <div className={`status ${status}`}>
            {status === 'checking' && 'Checking...'}
            {status === 'healthy' && '✓ Connected'}
            {status === 'error' && '✗ Disconnected'}
          </div>
        </header>

        {error && <div className="error-message">{error}</div>}

        {status === 'healthy' ? (
          <ChatInterface config={config} onError={setError} />
        ) : (
          <div
            style={{
              textAlign: 'center',
              padding: '40px 20px',
              color: '#666',
            }}
          >
            <div className="loading" style={{ margin: '0 auto 20px' }}></div>
            <p>
              {status === 'checking' && 'Connecting to backend...'}
              {status === 'error' && 'Unable to connect to backend. Please try again later.'}
            </p>
            {status === 'error' && (
              <button
                onClick={initializeApp}
                style={{ marginTop: '20px' }}
              >
                Retry Connection
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
