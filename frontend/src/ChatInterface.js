// src/ChatInterface.js
import React, { useState, useEffect, useRef } from 'react';
import './ChatInterface.css';
import axios from 'axios';

const ChatInterface = () => {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef(null);
  
  // Server states
  const [activeServers, setActiveServers] = useState({
    weather: false,
    github: false
  });

  const servers = {
    weather: {
      name: 'Weather Server',
      script: 'server/weather.py'
    },
    github: {
      name: 'GitHub Server',
      script: 'server/github.py'
    }
  };

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const handleServerToggle = (serverId) => {
    setActiveServers(prev => ({
      ...prev,
      [serverId]: !prev[serverId]
    }));
  };

  const handleSendMessage = async (e) => {
    e?.preventDefault();
    if (!message.trim() || isLoading) return;

    // Check if any server is active
    const enabledServers = Object.entries(activeServers)
      .filter(([_, isEnabled]) => isEnabled)
      .map(([id]) => servers[id]);

    if (enabledServers.length === 0) {
      setChatHistory(prev => [...prev, {
        sender: 'system',
        text: 'Please enable at least one server to process your query.'
      }]);
      return;
    }

    setIsLoading(true);
    setChatHistory(prev => [...prev, { sender: 'user', text: message }]);

    try {
      // Send query to each active server
      const responses = await Promise.all(
        enabledServers.map(server => 
          axios.post('http://127.0.0.1:8000/query', {
            query: message,
            server_script: server.script
          })
        )
      );

      // Add responses to chat history
      responses.forEach((response, index) => {
        setChatHistory(prev => [...prev, {
          sender: 'bot',
          text: response.data.response,
          server: enabledServers[index].name
        }]);
      });
    } catch (error) {
      console.error('Error:', error);
      setChatHistory(prev => [...prev, {
        sender: 'system',
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
      <div className="server-toggles">
        {Object.entries(servers).map(([id, server]) => (
          <div key={id} className="server-toggle">
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={activeServers[id]}
                onChange={() => handleServerToggle(id)}
                disabled={isLoading}
              />
              <span className="toggle-slider"></span>
            </label>
            <span className="server-name">{server.name}</span>
          </div>
        ))}
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