import React, { useState } from 'react';
import './App.css';

function SimpleApp() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      console.log('File selected:', file.name, file.size);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Avatar Assembly UI - Clean Architecture</h1>
        <div className="header-controls">
          <input
            type="file"
            accept=".psd"
            onChange={handleFileUpload}
            className="file-input"
            id="psd-file-input"
          />
          <label htmlFor="psd-file-input" className="file-input-label">
            📁 Load PSD
          </label>
        </div>
      </header>

      <div className="empty-state">
        <div className="empty-state-icon">🎨</div>
        <h2>Welcome to Avatar Assembly UI</h2>
        <p>Clean Architecture Implementation</p>
        {selectedFile ? (
          <p>Selected file: {selectedFile.name} ({Math.round(selectedFile.size / 1024)} KB)</p>
        ) : (
          <p>Upload a PSD file to get started extracting character expressions and building your avatar.</p>
        )}
        <label htmlFor="psd-file-input" className="file-input-label large">
          📁 Choose PSD File
        </label>
      </div>
    </div>
  );
}

export default SimpleApp;