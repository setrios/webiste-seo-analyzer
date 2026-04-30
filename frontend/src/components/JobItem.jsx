import { useState } from 'react';
import { getJobResultData } from '../services/api';

function JobItem({ job }) {
  const [loadingResult, setLoadingResult] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [resultData, setResultData] = useState(null);

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
      const data = await getJobResultData(job.id);
      setResultData(data);
      setShowModal(true);
    } catch (error) {
      alert('Failed to get result: ' + error.message);
    } finally {
      setLoadingResult(false);
    }
  };

  // close modal
  const handleCloseModal = () => {
    setShowModal(false);
  };

  // format timestamp
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <>
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

      {/* result modal */}
      {showModal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">SEO Analysis Results</h5>
                <button type="button" className="btn-close" onClick={handleCloseModal} aria-label="Close"></button>
              </div>
              <div className="modal-body">
                {resultData ? (
                  <table className="table table-bordered">
                    <tbody>
                      <tr>
                        <th scope="row" style={{ width: '40%' }}>Page Title</th>
                        <td>{resultData.title || 'N/A'}</td>
                      </tr>
                      <tr>
                        <th scope="row">Meta Description</th>
                        <td>{resultData.description || 'N/A'}</td>
                      </tr>
                      <tr>
                        <th scope="row">H1 Headings</th>
                        <td>{resultData.h1_count !== undefined ? resultData.h1_count : 'N/A'}</td>
                      </tr>
                      <tr>
                        <th scope="row">H2 Headings</th>
                        <td>{resultData.h2_count !== undefined ? resultData.h2_count : 'N/A'}</td>
                      </tr>
                      <tr>
                        <th scope="row">Total Links</th>
                        <td>{resultData.link_count !== undefined ? resultData.link_count : 'N/A'}</td>
                      </tr>
                    </tbody>
                  </table>
                ) : (
                  <div className="text-center">
                    <div className="spinner-border text-primary" role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default JobItem;
