import { useState, useEffect } from 'react';
import { initializeAuth } from './services/api';
import CreateJob from './components/CreateJob';
import JobList from './components/JobList';
import './App.css';

function App() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [authReady, setAuthReady] = useState(false);

  // initialize authentication on mount
  useEffect(() => {
    const init = async () => {
      try {
        await initializeAuth();
        setAuthReady(true);
      } catch (error) {
        console.error('Failed to initialize auth:', error);
      }
    };
    init();
  }, []);

  // handle job creation - trigger job list refresh
  const handleJobCreated = () => {
    setRefreshKey(prev => prev + 1);
  };

  if (!authReady) {
    return (
      <div className="container mt-5">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-2">Initializing...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mt-4">
      <header className="mb-4">
        <h1 className="display-4">SEO Analyzer</h1>
        <p className="lead text-muted">
          Analyze website SEO metrics including title, description, headings, and links
        </p>
      </header>

      <CreateJob onJobCreated={handleJobCreated} />

      <JobList refreshTrigger={refreshKey} />
    </div>
  );
}

export default App;
