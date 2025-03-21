// src/ChatInterface.js
import React, { useState } from 'react';
import axios from 'axios';
import './ChatInterface.css'; // Create styles for your component

const ChatInterface = () => {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [activeServer, setActiveServer] = useState('server1');

  // List of available servers (update these URLs as needed)
  const servers = [
    { id: 'server1', name: 'Server 1', url: 'http://localhost:8000' },
    { id: 'server2', name: 'Server 2', url: 'http://localhost:8001' }
  ];

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    // Update chat history with user's message
    setChatHistory(prev => [...prev, { sender: 'user', text: message }]);

    try {
      // Call your backend endpoint (e.g., /api/sendMessage)
      // Pass along the active server selection so your backend can forward the request accordingly.
      const response = await axios.post('/api/sendMessage', {
        message,
        server: activeServer
      });
      const reply = response.data.reply;
      setChatHistory(prev => [...prev, { sender: 'user', text: message }, { sender: 'bot', text: reply }]);
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