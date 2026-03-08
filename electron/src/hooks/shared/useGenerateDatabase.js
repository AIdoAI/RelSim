import { useState, useCallback } from 'react';
import { getProjectDbConfig } from '../../utils/projectApi';
import { useToastContext } from '../../contexts/ToastContext';

/**
 * Custom hook for generating a database from the DB canvas.
 * Handles saving the db config, calling the generate endpoint,
 * and dispatching events so the simulation tab knows a DB is available.
 */
const useGenerateDatabase = (projectId) => {
    const { showError } = useToastContext();

    const [isGenerating, setIsGenerating] = useState(false);
    const [generateResult, setGenerateResult] = useState(null);
    const [generateError, setGenerateError] = useState(null);

    const handleGenerateDatabase = useCallback(async () => {
        if (!projectId) {
            showError('No project context. Please open a project first.');
            return;
        }

        setIsGenerating(true);
        setGenerateError(null);
        setGenerateResult(null);

        try {
            // 1. Load the saved DB config to get its ID
            const dbConfigResult = await getProjectDbConfig(projectId);
            if (!dbConfigResult.success || !dbConfigResult.config) {
                showError('Database configuration not found. Please save your database schema first.');
                setIsGenerating(false);
                return;
            }

            const dbConfigId = dbConfigResult.config.id;

            // 2. Generate a timestamped name for the database
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const dbName = `generated_${timestamp}`;

            // 3. Call the generate-database API
            const result = await window.api.generateDatabase({
                config_id: dbConfigId,
                project_id: projectId,
                output_dir: 'output',
                name: dbName
            });

            if (result?.success) {
                setGenerateResult(result);
                console.log('[useGenerateDatabase] Database generated successfully:', result);

                // 4. Dispatch event so the sim tab knows a DB is available
                window.dispatchEvent(new CustomEvent('databaseGenerated', {
                    detail: {
                        projectId,
                        databasePath: result.database_path
                    }
                }));

                // 5. Refresh sidebar results
                window.dispatchEvent(new CustomEvent('refreshProjectResults', {
                    detail: { projectId }
                }));
            } else {
                const errorMsg = result?.error || 'Database generation failed';
                setGenerateError(errorMsg);
                showError(errorMsg);
            }
        } catch (error) {
            console.error('[useGenerateDatabase] Generation failed:', error);
            setGenerateError(error.message);
            showError(`Database generation failed: ${error.message}`);
        } finally {
            setIsGenerating(false);
        }
    }, [projectId, showError]);

    const handleCloseModal = useCallback(() => {
        setGenerateResult(null);
        setGenerateError(null);
        setIsGenerating(false);
    }, []);

    return {
        isGenerating,
        generateResult,
        generateError,
        handleGenerateDatabase,
        handleCloseModal
    };
};

export default useGenerateDatabase;
