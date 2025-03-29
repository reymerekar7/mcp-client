// src/ChatInterface.js
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './ChatInterface.css';

const ChatInterface = () => {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [activeServer, setActiveServer] = useState('weather');
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef(null);

  // List of available servers with their script paths
  const servers = [
    { id: 'weather', name: 'Weather Server', script: 'server/weather.py' },
    { id: 'github', name: 'GitHub Server', script: 'server/github.py' }
  ];

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const handleSendMessage = async (e) => {
    e?.preventDefault(); // Handle both button click and form submit
    if (!message.trim() || isLoading) return;

    setIsLoading(true);
    setChatHistory(prev => [...prev, { sender: 'user', text: message }]);

    const activeServerInfo = servers.find(server => server.id === activeServer);
    const payload = {
      query: message,
      server_script: activeServerInfo.script
    };

    try {
      const response = await axios.post('http://127.0.0.1:8000/query', payload);
      setChatHistory(prev => [...prev, { 
        sender: 'bot', 
        text: response.data.response,
        server: activeServerInfo.name 
      }]);
    } catch (error) {
      console.error('Error:', error);
      setChatHistory(prev => [...prev, { 
        sender: 'bot', 
        text: 'Error: Failed to get response from server.',
        error: true 
      }]);
    } finally {
      setIsLoading(false);
      setMessage('');
    }
  };

  return (
    <div className="chat-container">
      <div className="server-toggle">
        <label htmlFor="server-select">Active Server: </label>
        <select 
          id="server-select" 
          value={activeServer} 
          onChange={(e) => setActiveServer(e.target.value)}
          disabled={isLoading}
        >
          {servers.map(server => (
            <option key={server.id} value={server.id}>
              {server.name}
            </option>
          ))}
        </select>
      </div>
      
      <div className="chat-history">
        {chatHistory.map((msg, index) => (
          <div 
            key={index} 
            className={`chat-message ${msg.sender} ${msg.error ? 'error' : ''}`}
          >
            {msg.sender === 'bot' && msg.server && (
              <div className="server-tag">{msg.server}</div>
            )}
            <div className="message-text">{msg.text}</div>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>
      
      <form onSubmit={handleSendMessage} className="chat-input">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;