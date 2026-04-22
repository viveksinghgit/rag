import React, { useState, useRef, useEffect } from 'react';
import * as api from '../api';

function ChatInterface({ config, onError }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [topK, setTopK] = useState(5);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!input.trim()) {
      return;
    }

    // Add user message to chat
    const userMessage = {
      id: Date.now(),
      type: 'user',
      text: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    onError(null);

    try {
      // Call RAG query endpoint
      const response = await api.queryRag(input, topK);

      // Add assistant message
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        text: response.answer,
        sources: response.sources || [],
        executionTime: response.execution_time_ms,
        tokensUsed: response.tokens_used,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Query error:', error);

      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        text: error.response?.data?.detail || error.message || 'Failed to get response',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
      onError('Query failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async () => {
    setLoading(true);
    onError(null);

    try {
      const response = await api.triggerIngestion();
      const message = {
        id: Date.now(),
        type: 'assistant',
        text: response.message || 'Ingestion triggered successfully.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, message]);
    } catch (error) {
      console.error('Ingestion error:', error);
      onError('Ingestion failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      {/* Messages Display */}
      <div className="messages">
        {messages.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#999', paddingTop: '40px' }}>
            <p>👋 Welcome! Start by asking a question.</p>
            <p style={{ fontSize: '12px', marginTop: '10px' }}>
              The system will search through your documents and provide relevant answers.
            </p>
          </div>
        ) : (
          messages.map(message => (
            <div key={message.id} className={`message ${message.type}`}>
              <p>{message.text}</p>
              {message.sources && message.sources.length > 0 && (
                <div className="sources">
                  <strong>📚 Sources:</strong>
                  {message.sources.map((source, idx) => (
                    <div key={idx} className="source-item">
                      • {source.source || 'Document'} (confidence: {(source.score * 100).toFixed(1)}%)
                    </div>
                  ))}
                </div>
              )}
              {message.executionTime !== undefined && (
                <div className="sources">
                  <em>⏱️ {message.executionTime.toFixed(0)}ms | 💬 {message.tokensUsed} tokens</em>
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Section */}
      <form onSubmit={handleSubmit} className="input-section">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask me anything about your documents..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          {loading ? '⏳' : '📤'}
        </button>
      </form>

      {/* Settings & Controls */}
      <div className="settings">
        <h3>⚙️ Settings</h3>
        <div className="settings-item">
          <label>
            Top-K Results:
            <input
              type="number"
              min="1"
              max="20"
              value={topK}
              onChange={e => setTopK(Math.max(1, Math.min(20, parseInt(e.target.value) || 1)))}
              style={{
                marginLeft: '8px',
                width: '50px',
                padding: '4px',
                border: '1px solid #ddd',
                borderRadius: '4px',
              }}
              disabled={loading}
            />
          </label>
        </div>
        <div className="settings-item" style={{ marginTop: '10px' }}>
          <strong>Model Configuration:</strong>
          <div style={{ marginTop: '5px', fontSize: '11px' }}>
            • LLM: {config?.llm_model || 'Loading...'}
          </div>
          <div style={{ fontSize: '11px' }}>• Embeddings: {config?.embedding_model || 'Loading...'}</div>
        </div>
        <button
          onClick={handleIngest}
          disabled={loading}
          className="button-secondary"
          style={{ marginTop: '15px', width: '100%' }}
        >
          {loading ? '⏳ Ingesting...' : '📥 Re-ingest Documents'}
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
