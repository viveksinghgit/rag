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
        'Markdown and text files are parsed, split into ~512-word overlapping chunks, converted to 1024-dimensional embeddings by Mistral Embed, and upserted into Qdrant. Each chunk keeps a reference to its source file.',
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
      short: "Retrieved chunks become the LLM's context window.",
      detail:
        'The retrieved chunks are injected into a prompt as grounding context, then sent to Groq (Qwen3-32B) or locally to Ollama (qwen2.5). The LLM generates an answer based only on that context, making hallucination far less likely.',
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
    '📁 Upload your own documents via the Upload button',
    '🔑 Switch to Groq or Mistral for cloud inference',
    '☁️ Deploy to Azure with one ARM template deploy',
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
  const [uploadStatus, setUploadStatus] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [showDocuments, setShowDocuments] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (config?.storage_configured) {
      api.listDocuments().then(data => setDocuments(data.documents || [])).catch(() => {});
    }
  }, [config]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setShowIntro(false);
    const userMessage = { id: Date.now(), type: 'user', text: input, timestamp: new Date() };
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
      setMessages(prev => [
        ...prev,
        {
          id: Date.now(),
          type: 'assistant',
          text: response.message || 'Ingestion triggered successfully.',
          timestamp: new Date(),
        },
      ]);
    } catch (error) {
      onError('Ingestion failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = '';

    setUploadStatus({ state: 'uploading', name: file.name });
    try {
      const result = await api.uploadDocument(file);
      setUploadStatus({ state: 'success', name: file.name, message: result.message });
      // Refresh document list
      api.listDocuments().then(data => setDocuments(data.documents || [])).catch(() => {});
    } catch (error) {
      setUploadStatus({
        state: 'error',
        name: file.name,
        message: error.response?.data?.detail || error.message || 'Upload failed',
      });
    }
  };

  const uploadStatusColor = uploadStatus?.state === 'success'
    ? '#2e7d32'
    : uploadStatus?.state === 'error'
    ? '#c62828'
    : '#555';

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
          <div style={{ fontSize: '11px' }}>
            • Embeddings: {config?.embedding_model || 'Loading...'}
          </div>
        </div>

        {/* Upload document */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".md,.txt,.pdf"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <button
          onClick={handleUploadClick}
          disabled={loading || !config?.storage_configured}
          className="button-secondary"
          style={{ marginTop: '15px', width: '100%' }}
          title={
            config?.storage_configured
              ? 'Upload a document to Azure Blob Storage'
              : 'Azure Blob Storage not configured'
          }
        >
          📤 Upload Document
        </button>

        {uploadStatus && (
          <div style={{ marginTop: '6px', fontSize: '11px', color: uploadStatusColor }}>
            {uploadStatus.state === 'uploading' && `Uploading ${uploadStatus.name}…`}
            {uploadStatus.state === 'success' && `✓ ${uploadStatus.message}`}
            {uploadStatus.state === 'error' && `✗ ${uploadStatus.message}`}
          </div>
        )}

        {/* Uploaded documents list */}
        {config?.storage_configured && documents.length > 0 && (
          <div style={{ marginTop: '10px' }}>
            <button
              className="button-link"
              onClick={() => setShowDocuments(v => !v)}
              style={{ fontSize: '11px' }}
            >
              {showDocuments ? '▲ Hide' : '▼ Show'} uploaded files ({documents.length})
            </button>
            {showDocuments && (
              <div style={{ marginTop: '4px', fontSize: '11px', maxHeight: '120px', overflowY: 'auto' }}>
                {documents.map((doc, i) => (
                  <div key={i} style={{ padding: '2px 0', borderBottom: '1px solid #eee' }}>
                    📄 {doc.name}{' '}
                    <span style={{ color: '#999' }}>
                      ({doc.size ? `${(doc.size / 1024).toFixed(1)} KB` : '—'})
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <button
          onClick={handleIngest}
          disabled={loading}
          className="button-secondary"
          style={{ marginTop: '10px', width: '100%' }}
        >
          {loading ? 'Working...' : '🔄 Re-ingest Documents'}
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
