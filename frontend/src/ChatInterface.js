// src/ChatInterface.js
import React, { useState } from 'react';
import axios from 'axios';
import './ChatInterface.css';

const ChatInterface = () => {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [activeServer, setActiveServer] = useState('weather');

  // List of available servers with their script paths
  const servers = [
    { id: 'weather', name: 'Weather Server', script: 'server/weather.py' },
    { id: 'github', name: 'GitHub Server', script: 'server/github.py' }
  ];

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    // Append user's message
    setChatHistory(prev => [...prev, { sender: 'user', text: message }]);

    // Find the active server's script path
    const activeServerInfo = servers.find(server => server.id === activeServer);
    const payload = {
      query: message,
      server_script: activeServerInfo.script
    };

    console.log("Sending payload:", payload);

    try {
      // Assume your FastAPI backend is running at a fixed URL (e.g., http://localhost:8000)
      const response = await axios.post(`http://127.0.0.1:8000/query`, payload, {
        headers: { "Content-Type": "application/json" }
      });
      const reply = response.data.response;
      setChatHistory(prev => [...prev, { sender: 'bot', text: reply }]);
    } catch (error) {
      console.error('Error sending message:', error);
      setChatHistory(prev => [...prev, { sender: 'bot', text: 'Error sending message.' }]);
    }
    setMessage('');
  };

  const handleToggleServer = (e) => {
    setActiveServer(e.target.value);
  };

  return (
    <div className="chat-container">
      <div className="server-toggle">
        <label htmlFor="server-select">Active Server: </label>
        <select id="server-select" value={activeServer} onChange={handleToggleServer}>
          {servers.map(server => (
            <option key={server.id} value={server.id}>
              {server.name}
            </option>
          ))}
        </select>
      </div>
      
      <div className="chat-history">
        {chatHistory.map((msg, index) => (
          <div key={index} className={`chat-message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
      </div>
      
      <div className="chat-input">
        <input
          type="text"
          value={message}
          onChange={e => setMessage(e.target.value)}
          placeholder="Type your message..."
        />
        <button onClick={handleSendMessage}>Send</button>
      </div>
    </div>
  );
};

export default ChatInterface;