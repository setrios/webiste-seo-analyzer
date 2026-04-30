import { useState } from 'react';
import { createJob } from '../services/api';

function CreateJob({ onJobCreated }) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [messageType, setMessageType] = useState('success');

  // validate URL format
  const isValidUrl = (url) => {
    return url.trim() !== '' && /^https?:\/\/.+/.test(url);
  };

  // handle form submit
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!isValidUrl(url)) {
      setMessage('Please enter a valid URL starting with http:// or https://');
      setMessageType('danger');
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const job = await createJob(url);
      setMessage(`Job created successfully! ID: ${job.id}`);
      setMessageType('success');
      setUrl('');
      
      // notify parent component to refresh job list
      if (onJobCreated) {
        onJobCreated(job);
      }
    } catch (error) {
      setMessage('Failed to create job: ' + (error.response?.data?.detail || error.message));
      setMessageType('danger');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card mb-4">
      <div className="card-body">
        <h5 className="card-title">Create New SEO Analysis Job</h5>
        
        {message && (
          <div className={`alert alert-${messageType} alert-dismissible fade show`} role="alert">
            {message}
            <button 
              type="button" 
              className="btn-close" 
              onClick={() => setMessage(null)}
              aria-label="Close"
            ></button>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="urlInput" className="form-label">Website URL</label>
            <input
              type="text"
              className="form-control"
              id="urlInput"
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={loading}
            />
            <div className="form-text">
              Enter the URL of the website you want to analyze
            </div>
          </div>
          
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={loading || !isValidUrl(url)}
          >
            {loading ? (
              <>
                <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Creating...
              </>
            ) : (
              'Create Job'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

export default CreateJob;
