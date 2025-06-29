/**
 * Processing Progress Component
 * 
 * Displays real-time progress updates for audio processing jobs with WebSocket integration.
 */

import { useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Box,
  Chip,
  IconButton,
  Alert,
  Collapse,
  Button,
} from '@mui/material';
import {
  Cancel,
  CheckCircle,
  Error,
  Info,
  Download,
  Refresh,
} from '@mui/icons-material';
import type { ProcessingJobState } from '@/hooks/useProcessingJob';

interface ProcessingProgressProps {
  state: ProcessingJobState;
  connectionState: string;
  isConnected: boolean;
  onCancel?: () => void;
  onDownload?: (url: string) => void;
  onRetry?: () => void;
  formatProgress: () => string;
  formatTimeRemaining: () => string;
  formatElapsedTime: () => string;
}

/**
 * Get status color based on job status
 */
const getStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
  switch (status) {
    case 'idle':
      return 'default';
    case 'creating':
    case 'queued':
      return 'info';
    case 'processing':
      return 'primary';
    case 'completed':
      return 'success';
    case 'failed':
      return 'error';
    case 'cancelled':
      return 'warning';
    default:
      return 'default';
  }
};

/**
 * Get status icon based on job status
 */
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircle />;
    case 'failed':
      return <Error />;
    case 'cancelled':
      return <Cancel />;
    default:
      return <Info />;
  }
};

/**
 * Get connection status message
 */
const getConnectionStatus = (connectionState: string, isConnected: boolean): { message: string; severity: 'info' | 'warning' | 'error' | 'success' } => {
  if (isConnected) {
    return { message: 'Real-time updates connected', severity: 'success' };
  }
  
  switch (connectionState) {
    case 'connecting':
      return { message: 'Connecting to real-time updates...', severity: 'info' };
    case 'reconnecting':
      return { message: 'Reconnecting to real-time updates...', severity: 'warning' };
    case 'error':
      return { message: 'Real-time updates unavailable', severity: 'error' };
    case 'disconnected':
    default:
      return { message: 'Real-time updates disconnected', severity: 'warning' };
  }
};

const ProcessingProgress: React.FC<ProcessingProgressProps> = ({
  state,
  connectionState,
  isConnected,
  onCancel,
  onDownload,
  onRetry,
  formatProgress,
  formatTimeRemaining,
  formatElapsedTime,
}) => {
  const connectionStatus = getConnectionStatus(connectionState, isConnected);

  // Auto-scroll to this component when processing starts
  useEffect(() => {
    if (state.status === 'processing' || state.status === 'queued') {
      const element = document.getElementById('processing-progress');
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [state.status]);

  // Don't render if idle
  if (state.status === 'idle') {
    return null;
  }

  return (
    <Card id="processing-progress" sx={{ width: '100%', mt: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {getStatusIcon(state.status)}
            Processing Status
          </Typography>
          
          <Chip
            label={state.status.charAt(0).toUpperCase() + state.status.slice(1)}
            color={getStatusColor(state.status)}
            variant="filled"
          />
        </Box>

        {/* Job Information */}
        {state.jobId && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Job ID: {state.jobId}
            </Typography>
          </Box>
        )}

        {/* Progress Bar */}
        {(state.status === 'processing' || state.status === 'queued') && (
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="body2">
                {state.currentStage ? `Stage: ${state.currentStage}` : 'Processing...'}
              </Typography>
              <Typography variant="body2" color="primary.main" fontWeight="bold">
                {formatProgress()}
              </Typography>
            </Box>
            
            <LinearProgress
              variant="determinate"
              value={state.progress}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: 'action.hover',
                '& .MuiLinearProgress-bar': {
                  borderRadius: 4,
                },
              }}
            />
            
            {/* Time Information */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Elapsed: {formatElapsedTime()}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Remaining: {formatTimeRemaining()}
              </Typography>
            </Box>
          </Box>
        )}

        {/* Queue Information */}
        {state.status === 'queued' && state.queuePosition > 0 && (
          <Box sx={{ mb: 2 }}>
            <Alert severity="info" sx={{ mb: 1 }}>
              Position in queue: {state.queuePosition}
              {state.estimatedCompletion && (
                <>
                  <br />
                  Estimated completion: {new Date(state.estimatedCompletion).toLocaleTimeString()}
                </>
              )}
            </Alert>
          </Box>
        )}

        {/* Status Message */}
        {state.message && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {state.message}
            </Typography>
          </Box>
        )}

        {/* Connection Status */}
        <Collapse in={!isConnected || connectionState === 'reconnecting'}>
          <Alert severity={connectionStatus.severity} sx={{ mb: 2 }}>
            {connectionStatus.message}
          </Alert>
        </Collapse>

        {/* Error Display */}
        {state.error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {state.error}
          </Alert>
        )}

        {/* Success with Download */}
        {state.status === 'completed' && state.outputFileUrl && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Processing completed successfully! Your audio is ready for download.
          </Alert>
        )}

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          {/* Cancel Button */}
          {state.canCancel && onCancel && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<Cancel />}
              onClick={onCancel}
            >
              Cancel Job
            </Button>
          )}

          {/* Download Button */}
          {state.status === 'completed' && state.outputFileUrl && onDownload && (
            <Button
              variant="contained"
              color="success"
              startIcon={<Download />}
              onClick={() => onDownload(state.outputFileUrl!)}
            >
              Download Result
            </Button>
          )}

          {/* Retry Button */}
          {state.status === 'failed' && onRetry && (
            <Button
              variant="outlined"
              color="primary"
              startIcon={<Refresh />}
              onClick={onRetry}
            >
              Retry Processing
            </Button>
          )}
        </Box>

        {/* Debug Information (only in development) */}
        {process.env.NODE_ENV === 'development' && (
          <Box sx={{ mt: 2, p: 1, backgroundColor: 'action.hover', borderRadius: 1 }}>
            <Typography variant="caption" color="text.secondary">
              <strong>Debug:</strong> Status: {state.status}, Progress: {state.progress}%, 
              Connection: {connectionState}, Job: {state.jobId || 'none'}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default ProcessingProgress;