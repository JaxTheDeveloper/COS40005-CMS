import React, { useState, useRef, useEffect } from "react";
import { api } from "../services/api";

const SUGGESTIONS = [
  "How do I write a strong introduction for my essay?",
  "What's a good way to manage my time for homework?",
  "What are the major differences between democracy and monarchy?",
  "What's the best way to handle group projects?",
  "How can I prepare effectively for exams?",
];

export default function AskAI() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll to top of page on mount
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  // Auto-scroll to latest message (only when there are messages)
  useEffect(() => {
    if (messages.length > 0 || loading) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);

  const sendMessage = async (text) => {
    const userMsg = text || input.trim();
    if (!userMsg || loading) return;

    // Build history from existing messages (for multi-turn context)
    const history = messages.map((m) => ({
      role: m.role,
      text: m.text,
    }));

    // Add user message to UI immediately
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setInput("");
    setLoading(true);

    try {
      const response = await api.post("/askai/chat/", {
        message: userMsg,
        history,
      });

      setMessages((prev) => [
        ...prev,
        { role: "model", text: response.data.reply },
      ]);
    } catch (err) {
      const errorMsg =
        err.response?.data?.error ||
        "Something went wrong. Please try again.";
      setMessages((prev) => [
        ...prev,
        { role: "error", text: errorMsg },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage();
  };

  const handleSuggestionClick = (suggestion) => {
    setInput(suggestion);
    sendMessage(suggestion);
  };

  const clearChat = () => {
    setMessages([]);
    setInput("");
    inputRef.current?.focus();
  };

  return (
    <section className="askai-chat-wrapper">
      {/* Header */}
      <div className="askai-chat-header">
        <div className="askai-chat-header-left">
          <span className="askai-chat-logo">✦</span>
          <div>
            <h2 className="askai-chat-title">Ask AI</h2>
            <span className="askai-chat-subtitle">
              Powered by Gemini — your study assistant
            </span>
          </div>
        </div>
        {messages.length > 0 && (
          <button className="askai-clear-btn" onClick={clearChat} title="New chat">
            ✕ Clear
          </button>
        )}
      </div>

      {/* Messages Area */}
      <div className="askai-chat-messages">
        {messages.length === 0 && !loading && (
          <div className="askai-empty-state">
            <div className="askai-empty-icon">🎓</div>
            <h3 className="askai-empty-title">How can I help you today?</h3>
            <p className="askai-empty-subtitle">
              Ask me anything about your studies, assignments, or student life.
            </p>
            <div className="askai-suggestions">
              {SUGGESTIONS.map((s, idx) => (
                <button
                  key={idx}
                  className="askai-suggestion-chip"
                  onClick={() => handleSuggestionClick(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`askai-message askai-message-${msg.role}`}
          >
            {msg.role === "model" && (
              <span className="askai-avatar askai-avatar-ai">✦</span>
            )}
            <div className={`askai-bubble askai-bubble-${msg.role}`}>
              {msg.role === "error" && <span className="askai-error-icon">⚠ </span>}
              <span className="askai-bubble-text">{msg.text}</span>
            </div>
            {msg.role === "user" && (
              <span className="askai-avatar askai-avatar-user">You</span>
            )}
          </div>
        ))}

        {loading && (
          <div className="askai-message askai-message-model">
            <span className="askai-avatar askai-avatar-ai">✦</span>
            <div className="askai-bubble askai-bubble-model">
              <div className="askai-typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form className="askai-chat-input-bar" onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your question here..."
          className="askai-chat-input"
          disabled={loading}
        />
        <button
          type="submit"
          className="askai-chat-send"
          disabled={!input.trim() || loading}
          title={!input.trim() ? "Enter a message" : "Send"}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </form>
    </section>
  );
}