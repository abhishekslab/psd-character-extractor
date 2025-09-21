function TestApp() {
  return (
    <div style={{
      padding: '20px',
      background: '#f0f0f0',
      minHeight: '100vh',
      width: '100%',
      position: 'fixed',
      top: 0,
      left: 0,
      zIndex: 9999
    }}>
      <h1 style={{ color: '#000' }}>Test App Working!</h1>
      <p style={{ color: '#333' }}>If you can see this, React is working correctly.</p>
      <p style={{ color: '#666' }}>Current time: {new Date().toLocaleTimeString()}</p>
    </div>
  );
}

export default TestApp;