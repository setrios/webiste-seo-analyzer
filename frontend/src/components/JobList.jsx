import { useState, useEffect } from 'react';
import { getJobs } from '../services/api';
import JobItem from './JobItem';

function JobList({ refreshTrigger }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  // initial fetch on mount
  useEffect(() => {
    fetchJobs();
  }, [refreshTrigger]);

  // polling every 5 seconds if there are active jobs
  useEffect(() => {
    if (!hasActiveJobs()) {
      return;
    }

    const interval = setInterval(() => {
      fetchJobs();
    }, 5000);

    return () => clearInterval(interval);
  }, [jobs]);

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
        {hasActiveJobs() && (
          <span className="badge bg-secondary ms-2">Auto-refreshing</span>
        )}
      </h3>
      {sortedJobs.map(job => (
        <JobItem key={job.id} job={job} />
      ))}
    </div>
  );
}

export default JobList;
