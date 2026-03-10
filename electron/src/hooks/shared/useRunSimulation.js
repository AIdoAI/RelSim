import { useState, useEffect, useCallback } from 'react';
import { getProjectDbConfig } from '../../utils/projectApi';
import { useConfigActions } from '../../stores/simulationConfigStore';
import { useToastContext } from '../../contexts/ToastContext';

/**
 * Custom hook for managing run simulation functionality.
 * Supports both:
 *   - Legacy: generate + simulate in one shot
 *   - Split: simulate on a pre-existing database (Phase 2+3 only)
 */
const useRunSimulation = (projectId, refreshTrigger = null) => {
  const { showError } = useToastContext();
  const { runSimulation, runSimulationOnly } = useConfigActions(projectId);

  // State for project database config
  const [projectDbConfig, setProjectDbConfig] = useState(null);

  // Available databases for simulation
  const [availableDatabases, setAvailableDatabases] = useState([]);
  const [selectedDatabase, setSelectedDatabase] = useState(null);

  // Run simulation state
  const [isRunning, setIsRunning] = useState(false);
  const [runResult, setRunResult] = useState(null);
  const [runError, setRunError] = useState(null);

  // Function to load project database config
  const loadProjectDbConfig = useCallback(async () => {
    if (!projectId) return;

    try {
      const result = await getProjectDbConfig(projectId);

      if (result.success && result.config) {
        setProjectDbConfig(result.config);
      } else {
        setProjectDbConfig(null);
      }
    } catch (error) {
      console.error('Failed to load project database config:', error);
      setProjectDbConfig(null);
    }
  }, [projectId]);

  // Scan for available generated databases
  const scanAvailableDatabases = useCallback(async () => {
    if (!projectId) return;

    try {
      const results = await window.api.scanProjectResults(projectId);
      if (results.success && results.results) {
        setAvailableDatabases(results.results);
        // Auto-select the most recent database if none selected
        if (!selectedDatabase && results.results.length > 0) {
          setSelectedDatabase(results.results[0]);
        }
      } else {
        setAvailableDatabases([]);
      }
    } catch (error) {
      console.error('Failed to scan available databases:', error);
      setAvailableDatabases([]);
    }
  }, [projectId]);

  // Load project database config and scan databases on mount
  useEffect(() => {
    loadProjectDbConfig();
    scanAvailableDatabases();
  }, [loadProjectDbConfig, scanAvailableDatabases, refreshTrigger]);

  // Listen for databaseGenerated events to refresh the list
  useEffect(() => {
    const handleDatabaseGenerated = (event) => {
      if (event.detail?.projectId === projectId) {
        scanAvailableDatabases();
      }
    };

    window.addEventListener('databaseGenerated', handleDatabaseGenerated);
    return () => window.removeEventListener('databaseGenerated', handleDatabaseGenerated);
  }, [projectId, scanAvailableDatabases]);

  // Get database config ID for simulation
  const dbConfigId = projectDbConfig?.id;

  // Handle running simulation on existing database (split workflow)
  const handleRunSimulation = useCallback(async () => {
    if (!dbConfigId) {
      showError('No database configuration available. Please ensure a database is configured for this project.');
      return;
    }

    setIsRunning(true);
    setRunError(null);
    setRunResult(null);

    try {
      let result;

      if (selectedDatabase) {
        // Split workflow: run simulation on existing database
        console.log('[useRunSimulation] Running simulation on existing database:', selectedDatabase.path);
        result = await runSimulationOnly(dbConfigId, selectedDatabase.path);
      } else {
        // Fallback: generate + simulate (legacy flow)
        console.log('[useRunSimulation] No existing database selected, running generate + simulate');
        result = await runSimulation(dbConfigId);
      }

      if (result?.success) {
        setRunResult(result);
        console.log('Simulation completed successfully!');

        // Trigger sidebar refresh
        window.dispatchEvent(new CustomEvent('refreshProjectResults', {
          detail: { projectId }
        }));
      } else {
        setRunError(result?.error || 'Simulation failed');
        showError(result?.error || 'Simulation failed');
      }
    } catch (error) {
      console.error('Simulation failed:', error);
      setRunError(error.message);
      showError(`Simulation failed: ${error.message}`);
    } finally {
      setIsRunning(false);
    }
  }, [dbConfigId, selectedDatabase, runSimulation, runSimulationOnly, showError, projectId]);

  // Reset run modal state when closing
  const handleCloseModal = useCallback(() => {
    setRunResult(null);
    setRunError(null);
    setIsRunning(false);
  }, []);

  return {
    // State
    projectDbConfig,
    dbConfigId,
    isRunning,
    runResult,
    runError,
    availableDatabases,
    selectedDatabase,

    // Actions
    handleRunSimulation,
    handleCloseModal,
    setSelectedDatabase,
    refreshDbConfig: loadProjectDbConfig,
    refreshDatabases: scanAvailableDatabases
  };
};

export default useRunSimulation;