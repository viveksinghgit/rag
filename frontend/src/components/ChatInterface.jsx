import React, { useState, useRef, useEffect } from 'react';
import * as api from '../api';

function RAGIntroPanel({ onDismiss }) {
  const [activeStep, setActiveStep] = useState(null);

  const steps = [
    {
      icon: '📄',
      title: 'Document Ingestion',
      short: 'Your documents are split into chunks and stored as vectors.',
      detail:
        'Markdown files from the docs/ folder are parsed, split into ~512-word overlapping chunks, converted to 768-dimensional embeddings by the embedding model, and upserted into Qdrant. Each chunk keeps a reference to its source file.',
    },
    {
      icon: '🔍',
      title: 'Semantic Search',
      short: 'Your query is embedded and matched against stored vectors.',
      detail:
        'When you ask a question, the same embedding model converts your query into a vector. Qdrant then runs a cosine-similarity search and returns the top-K most semantically relevant chunks — not just keyword matches.',
    },
    {
      icon: '🧠',
      title: 'Context + Generation',
      short: 'Retrieved chunks become the LLM\'s context window.',
      detail:
        'The retrieved chunks are injected into a prompt as grounding context, then sent to Groq (mixtral-8x7b) or locally to Ollama (qwen2.5). The LLM generates an answer based only on that context, making hallucination far less likely.',
    },
    {
      icon: '📊',
      title: 'Source Attribution',
      short: 'Every answer cites its sources with confidence scores.',
      detail:
        'The response includes each source document, its chunk index, and the cosine similarity score (0–1). This lets you trace every claim back to a specific passage in your knowledge base.',
    },
  ];

  const possibilities = [
    '📁 Index your own Markdown / PDF documents',
    '🔑 Switch to Groq or Mistral for cloud inference',
    '☁️ Deploy to Azure in one Terraform apply',
    '🔗 Integrate the /query API into any application',
    '📈 Add Application Insights for usage analytics',
    '🔒 Layer on Azure AD authentication',
    '⚡ Enable streaming responses for faster UX',
  ];

  return (
    <div className="rag-intro">
      <div className="rag-intro-header">
        <div>
          <h2 className="rag-intro-title">How This RAG System Works</h2>
          <p className="rag-intro-subtitle">
            Retrieval-Augmented Generation grounds AI answers in your own documents.
          </p>
        </div>
        <button className="rag-dismiss" onClick={onDismiss} title="Dismiss intro">
          ✕
        </button>
      </div>

      <div className="rag-what">
        <strong>What is RAG?</strong> Instead of relying solely on the LLM's training data, RAG
        first <em>retrieves</em> relevant passages from your knowledge base, then feeds them as
        context to the model. The result: accurate, cited answers grounded in your documents —
        not hallucinations.
      </div>

      <div className="rag-steps">
        {steps.map((step, i) => (
          <div
            key={i}
            className={`rag-step ${activeStep === i ? 'active' : ''}`}
            onClick={() => setActiveStep(activeStep === i ? null : i)}
          >
            <div className="rag-step-header">
              <span className="rag-step-icon">{step.icon}</span>
              <div>
                <div className="rag-step-num">Step {i + 1}</div>
                <div className="rag-step-title">{step.title}</div>
                <div className="rag-step-short">{step.short}</div>
              </div>
              <span className="rag-step-toggle">{activeStep === i ? '▲' : '▼'}</span>
            </div>
            {activeStep === i && <div className="rag-step-detail">{step.detail}</div>}
          </div>
        ))}
      </div>

      <div className="rag-pipeline-viz">
        <span className="rag-pill">Your Query</span>
        <span className="rag-arrow">→</span>
        <span className="rag-pill">Embed</span>
        <span className="rag-arrow">→</span>
        <span className="rag-pill">Qdrant Search</span>
        <span className="rag-arrow">→</span>
        <span className="rag-pill">LLM + Context</span>
        <span className="rag-arrow">→</span>
        <span className="rag-pill answer-pill">Cited Answer</span>
      </div>

      <div className="rag-possibilities">
        <strong>What more can you do with this system?</strong>
        <ul>
          {possibilities.map((p, i) => (
            <li key={i}>{p}</li>
          ))}
        </ul>
      </div>

      <button className="rag-start-btn" onClick={onDismiss}>
        Start chatting →
      </button>
    </div>
  );
}

function ChatInterface({ config, onError }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [topK, setTopK] = useState(5);
  const [showIntro, setShowIntro] = useState(true);
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

    setShowIntro(false);

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
      const response = await api.queryRag(input, topK);

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
      {showIntro ? (
        <RAGIntroPanel onDismiss={() => setShowIntro(false)} />
      ) : (
        <>
          <div className="messages">
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', color: '#999', paddingTop: '40px' }}>
                <p>Ask me anything about your documents.</p>
                <button
                  className="button-link"
                  onClick={() => setShowIntro(true)}
                  style={{ marginTop: '8px', fontSize: '12px' }}
                >
                  Show RAG explanation
                </button>
              </div>
            )}
            {messages.map(message => (
              <div key={message.id} className={`message ${message.type}`}>
                <p>{message.text}</p>
                {message.sources && message.sources.length > 0 && (
                  <div className="sources">
                    <strong>Sources:</strong>
                    {message.sources.map((source, idx) => (
                      <div key={idx} className="source-item">
                        • {source.source || 'Document'} — confidence:{' '}
                        {(source.score * 100).toFixed(1)}%
                      </div>
                    ))}
                  </div>
                )}
                {message.executionTime !== undefined && (
                  <div className="sources">
                    <em>
                      {message.executionTime.toFixed(0)} ms &nbsp;·&nbsp;{' '}
                      {message.tokensUsed} tokens
                    </em>
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="input-section">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask me anything about your documents..."
              disabled={loading}
            />
            <button type="submit" disabled={loading || !input.trim()}>
              {loading ? '⏳' : 'Send'}
            </button>
          </form>
        </>
      )}

      <div className="settings">
        <h3>Settings</h3>
        <div className="settings-item">
          <label>
            Top-K Results:
            <input
              type="number"
              min="1"
              max="20"
              value={topK}
              onChange={e =>
                setTopK(Math.max(1, Math.min(20, parseInt(e.target.value) || 1)))
              }
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
          <div style={{ fontSize: '11px' }}>
            • Embeddings: {config?.embedding_model || 'Loading...'}
          </div>
        </div>
        <button
          onClick={handleIngest}
          disabled={loading}
          className="button-secondary"
          style={{ marginTop: '15px', width: '100%' }}
        >
          {loading ? 'Working...' : 'Re-ingest Documents'}
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
