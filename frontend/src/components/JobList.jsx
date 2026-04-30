import { useState, useEffect, useCallback } from 'react';
import { getJobs } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import JobItem from './JobItem';

function JobList({ refreshTrigger }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [disconnectedTime, setDisconnectedTime] = useState(null);

  // fetch jobs from API
  const fetchJobs = async () => {
    try {
      const data = await getJobs();
      setJobs(data);
      setError(null);
    } catch (err) {
      setError('Failed to load jobs');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // check if there are any active jobs
  const hasActiveJobs = () => {
    return jobs.some(job => job.status === 'QUEUED' || job.status === 'PROCESSING');
  };

  // update job from WebSocket event
  const updateJobFromEvent = (job, event) => {
    const updated = { ...job };

    switch (event.type) {
      case 'processing':
        updated.status = 'PROCESSING';
        break;
      case 'progress':
        updated.progress = event.progress;
        break;
      case 'completed':
        updated.status = 'DONE';
        updated.progress = 100;
        updated.s3_key = event.s3_key;
        break;
      case 'failed':
        updated.status = 'ERROR';
        break;
      case 'status':
        // initial state on connect
        updated.status = event.status;
        updated.progress = event.progress;
        updated.s3_key = event.s3_key;
        break;
      default:
        break;
    }

    return updated;
  };

  // handle WebSocket messages
  const handleJobUpdate = useCallback((event) => {
    console.log('Job update received:', event);

    setJobs(prevJobs => {
      const jobExists = prevJobs.find(j => j.id === event.job_id);

      if (jobExists) {
        // update existing job
        return prevJobs.map(job => {
          if (job.id === event.job_id) {
            return updateJobFromEvent(job, event);
          }
          return job;
        });
      } else {
        // new job created elsewhere, fetch all jobs
        fetchJobs();
        return prevJobs;
      }
    });
  }, []);

  // WebSocket connection
  const { connected, error: wsError } = useWebSocket(handleJobUpdate);

  // initial fetch on mount
  useEffect(() => {
    fetchJobs();
  }, [refreshTrigger]);

  // fallback to polling if WebSocket disconnected for >30s
  useEffect(() => {
    if (!connected) {
      if (!disconnectedTime) {
        setDisconnectedTime(Date.now());
      }

      const elapsed = Date.now() - (disconnectedTime || Date.now());
      
      // start polling after 30s of disconnect
      if (elapsed > 30000 && hasActiveJobs()) {
        console.log('WebSocket disconnected for >30s, falling back to polling');
        const interval = setInterval(() => {
          console.log('Polling for job updates (fallback mode)');
          fetchJobs();
        }, 5000);

        return () => clearInterval(interval);
      }
    } else {
      // connected, reset disconnect time
      setDisconnectedTime(null);
    }
  }, [connected, disconnectedTime, jobs]);

  if (loading) {
    return (
      <div className="text-center my-5">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger" role="alert">
        {error}
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="alert alert-info" role="alert">
        No jobs yet. Create your first SEO analysis job above!
      </div>
    );
  }

  // sort jobs by created_at (newest first)
  const sortedJobs = [...jobs].sort((a, b) => 
    new Date(b.created_at) - new Date(a.created_at)
  );

  return (
    <div>
      <h3 className="mb-3">
        Jobs ({jobs.length})
        {connected ? (
          <span className="badge bg-success ms-2">Live</span>
        ) : (
          <span className="badge bg-warning ms-2">Reconnecting...</span>
        )}
      </h3>

      {wsError && !connected && (
        <div className="alert alert-warning alert-dismissible fade show" role="alert">
          Connection issues. Using fallback mode.
          <button 
            type="button" 
            className="btn-close" 
            onClick={() => setError(null)}
            aria-label="Close"
          ></button>
        </div>
      )}

      {sortedJobs.map(job => (
        <JobItem key={job.id} job={job} />
      ))}
    </div>
  );
}

export default JobList;
