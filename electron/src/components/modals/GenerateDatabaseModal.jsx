import React, { useEffect } from 'react';
import { Button, Modal } from 'react-bootstrap';
import useGenerateDatabase from '../../hooks/shared/useGenerateDatabase';

/**
 * Modal for generating a database from the DB canvas.
 * Shows generation status, results, and errors.
 */
const GenerateDatabaseModal = ({
    show,
    onHide,
    projectId
}) => {
    const {
        isGenerating,
        generateResult,
        generateError,
        handleGenerateDatabase,
        handleCloseModal
    } = useGenerateDatabase(projectId);

    const handleClose = () => {
        handleCloseModal();
        onHide();
    };

    return (
        <Modal
            show={show}
            onHide={handleClose}
            centered
            enforceFocus={false}
        >
            <Modal.Header closeButton>
                <Modal.Title>Generate Database</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                {isGenerating ? (
                    <div className="text-center py-3">
                        <div className="spinner-border text-primary" role="status">
                            <span className="visually-hidden">Generating database...</span>
                        </div>
                        <p className="mt-2">Generating database from schema...</p>
                        <small className="text-muted">
                            This populates your tables with synthetic data based on generators and constraints.
                        </small>
                    </div>
                ) : generateResult ? (
                    <div className="alert alert-success">
                        <strong>Database Generated Successfully!</strong><br />
                        {generateResult.message && <div className="mt-2">{generateResult.message}</div>}
                        <div className="mt-2">
                            <small className="text-muted">
                                You can now view the generated data in the Results panel,
                                or run a simulation from the Simulation tab.
                            </small>
                        </div>
                    </div>
                ) : generateError ? (
                    <div className="alert alert-danger">
                        <strong>Generation Failed</strong><br />
                        {generateError}
                    </div>
                ) : (
                    <div>
                        <p>Generate a database with synthetic data from your current schema configuration.</p>
                        <div className="mt-3">
                            <small className="text-muted">
                                This runs <strong>static generation only</strong> (Phase 1).
                                To run the full simulation, use the Run button on the Simulation tab.
                            </small>
                        </div>
                    </div>
                )}
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={handleClose}>
                    {generateResult || generateError ? 'Close' : 'Cancel'}
                </Button>
                {!generateResult && !generateError && (
                    <Button
                        variant="primary"
                        onClick={handleGenerateDatabase}
                        disabled={isGenerating}
                    >
                        {isGenerating ? 'Generating...' : 'Generate'}
                    </Button>
                )}
            </Modal.Footer>
        </Modal>
    );
};

export default GenerateDatabaseModal;
