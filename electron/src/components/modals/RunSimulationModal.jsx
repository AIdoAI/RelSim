import React, { useEffect } from 'react';
import { Button, Modal, Form } from 'react-bootstrap';
import useRunSimulation from '../../hooks/shared/useRunSimulation';

/**
 * Modal component for running simulations.
 * Shows available databases for simulation and allows the user to select one.
 * Supports both:
 *   - Running on a pre-generated database (split workflow)
 *   - Generating + simulating in one shot (legacy fallback)
 */
const RunSimulationModal = ({
  show,
  onHide,
  projectId,
  yamlContent
}) => {
  const {
    projectDbConfig,
    dbConfigId,
    isRunning,
    runResult,
    runError,
    availableDatabases,
    selectedDatabase,
    handleRunSimulation,
    handleCloseModal,
    setSelectedDatabase,
    refreshDbConfig,
    refreshDatabases
  } = useRunSimulation(projectId);

  // Refresh when the modal is shown
  useEffect(() => {
    if (show) {
      refreshDbConfig();
      refreshDatabases();
    }
  }, [show, refreshDbConfig, refreshDatabases]);

  const handleClose = () => {
    handleCloseModal();
    onHide();
  };

  const handleDatabaseSelect = (dbIndex) => {
    const db = availableDatabases[parseInt(dbIndex)];
    setSelectedDatabase(db || null);
  };

  return (
    <Modal
      show={show}
      onHide={handleClose}
      centered
      enforceFocus={false}
    >
      <Modal.Header closeButton>
        <Modal.Title>Run Simulation</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {!dbConfigId ? (
          <div className="alert alert-warning">
            <strong>No Database Configuration</strong><br />
            {!projectId ?
              'Database configuration is required for simulation.' :
              'Please configure a database for this project before running the simulation.'
            }
          </div>
        ) : isRunning ? (
          <div className="text-center py-3">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Running simulation...</span>
            </div>
            <p className="mt-2">Running simulation...</p>
            {selectedDatabase && (
              <small className="text-muted">
                Using database: {selectedDatabase.name || selectedDatabase.id}
              </small>
            )}
          </div>
        ) : runResult ? (
          <div className="alert alert-success">
            <strong>Simulation Completed Successfully!</strong><br />
            {runResult.message && <div className="mt-2">{runResult.message}</div>}
          </div>
        ) : runError ? (
          <div className="alert alert-danger">
            <strong>Simulation Failed</strong><br />
            {runError}
          </div>
        ) : (
          <div>
            {availableDatabases.length > 0 ? (
              <>
                <p>Select a generated database to run the simulation on:</p>
                <Form.Group className="mb-3">
                  <Form.Label>Database</Form.Label>
                  <Form.Select
                    value={selectedDatabase ? availableDatabases.indexOf(selectedDatabase) : 0}
                    onChange={(e) => handleDatabaseSelect(e.target.value)}
                  >
                    {availableDatabases.map((db, index) => (
                      <option key={db.id || index} value={index}>
                        {db.name || db.id || `Database ${index + 1}`}
                      </option>
                    ))}
                  </Form.Select>
                </Form.Group>
                <small className="text-muted">
                  The simulation will run on the selected database and apply formula resolution afterwards.
                </small>
              </>
            ) : (
              <div className="alert alert-info">
                <strong>No Generated Databases Found</strong><br />
                Please generate a database first from the Database tab using the
                <strong> Generate</strong> button, then come back here to run the simulation.
              </div>
            )}
            <div className="mt-3">
              <small className="text-muted">
                Database Configuration: {projectDbConfig ? `Available ✓` : 'Missing ✗'}<br />
                Simulation Configuration: {yamlContent ? 'Available ✓' : 'Missing ✗'}
              </small>
            </div>
          </div>
        )}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose}>
          {runResult || runError ? 'Close' : 'Cancel'}
        </Button>
        {!runResult && !runError && (
          <Button
            variant="primary"
            onClick={handleRunSimulation}
            disabled={isRunning || !dbConfigId || !yamlContent || availableDatabases.length === 0}
          >
            {isRunning ? 'Running...' : 'Run Simulation'}
          </Button>
        )}
      </Modal.Footer>
    </Modal>
  );
};

export default RunSimulationModal;