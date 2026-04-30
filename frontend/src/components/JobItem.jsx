import { useState } from 'react';
import { getJobResult } from '../services/api';

function JobItem({ job }) {
  const [loadingResult, setLoadingResult] = useState(false);

  // get status badge variant
  const getStatusVariant = (status) => {
    switch (status) {
      case 'QUEUED':
        return 'warning';
      case 'PROCESSING':
        return 'info';
      case 'DONE':
        return 'success';
      case 'ERROR':
        return 'danger';
      default:
        return 'secondary';
    }
  };

  // handle view result button click
  const handleViewResult = async () => {
    setLoadingResult(true);
    try {
      const presignedUrl = await getJobResult(job.id);
      window.open(presignedUrl, '_blank');
    } catch (error) {
      alert('Failed to get result: ' + error.message);
    } finally {
      setLoadingResult(false);
    }
  };

  // format timestamp
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <div className="card mb-3">
      <div className="card-body">
        <div className="d-flex justify-content-between align-items-start mb-2">
          <h5 className="card-title mb-0">
            <a href={job.url} target="_blank" rel="noopener noreferrer" className="text-decoration-none">
              {job.url}
            </a>
          </h5>
          <span className={`badge bg-${getStatusVariant(job.status)}`}>
            {job.status}
          </span>
        </div>

        <p className="text-muted small mb-2">
          Created: {formatDate(job.created_at)}
        </p>

        {/* progress bar for processing jobs */}
        {job.status === 'PROCESSING' && (
          <div className="mb-2">
            <div className="progress">
              <div
                className="progress-bar progress-bar-striped progress-bar-animated"
                role="progressbar"
                style={{ width: `${job.progress}%` }}
                aria-valuenow={job.progress}
                aria-valuemin="0"
                aria-valuemax="100"
              >
                {job.progress}%
              </div>
            </div>
          </div>
        )}

        {/* error message for failed jobs */}
        {job.status === 'ERROR' && (
          <div className="alert alert-danger mb-2" role="alert">
            <small>Error occurred during processing</small>
          </div>
        )}

        {/* view result button for completed jobs */}
        {job.status === 'DONE' && (
          <button
            className="btn btn-primary btn-sm"
            onClick={handleViewResult}
            disabled={loadingResult}
          >
            {loadingResult ? 'Loading...' : 'View Result'}
          </button>
        )}
      </div>
    </div>
  );
}

export default JobItem;
