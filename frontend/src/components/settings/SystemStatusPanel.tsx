/**
 * System Status Panel Component
 * 
 * Displays real-time system status and model health information
 */

import React, { useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Alert,
  LinearProgress,
  Avatar,
  Divider,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  CheckCircleRounded as CheckIcon,
  ErrorRounded as ErrorIcon,
  WarningRounded as WarningIcon,
  RefreshRounded as RefreshIcon,
  SpeedRounded as SpeedIcon,
  QueueRounded as QueueIcon,
} from '@mui/icons-material';
import { useSettings } from '@/hooks/useSettings';
import type { SystemStatus, ModelName } from '@/types/settings';
import { MODEL_DISPLAY_NAMES } from '@/types/settings';

/**
 * Status Indicator Component
 */
interface StatusIndicatorProps {
  status: 'healthy' | 'warning' | 'error';
  label: string;
  details?: string;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, label, details }) => {
  const getStatusColor = () => {
    switch (status) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'healthy': return <CheckIcon />;
      case 'warning': return <WarningIcon />;
      case 'error': return <ErrorIcon />;
      default: return <CheckIcon />;
    }
  };

  return (
    <ListItem>
      <ListItemIcon>
        <Avatar sx={{ bgcolor: `${getStatusColor()}.main`, width: 32, height: 32 }}>
          {getStatusIcon()}
        </Avatar>
      </ListItemIcon>
      <ListItemText
        primary={label}
        secondary={details}
      />
      <Chip
        label={status.charAt(0).toUpperCase() + status.slice(1)}
        color={getStatusColor()}
        size="small"
        variant="outlined"
      />
    </ListItem>
  );
};

/**
 * Model Health Component
 */
interface ModelHealthProps {
  modelHealth: Record<ModelName, boolean>;
  availableModels: ModelName[];
}

const ModelHealth: React.FC<ModelHealthProps> = ({ modelHealth, availableModels }) => (
  <Card>
    <CardContent>
      <Typography variant="h6" gutterBottom>
        AI Model Status
      </Typography>
      
      <List dense>
        {availableModels.map((model, index) => {
          const isHealthy = modelHealth[model] ?? false;
          return (
            <React.Fragment key={model}>
              <StatusIndicator
                status={isHealthy ? 'healthy' : 'error'}
                label={MODEL_DISPLAY_NAMES[model] || model}
                details={isHealthy ? 'Ready for processing' : 'Model unavailable'}
              />
              {index < availableModels.length - 1 && <Divider />}
            </React.Fragment>
          );
        })}
      </List>
    </CardContent>
  </Card>
);

/**
 * System Performance Component
 */
interface SystemPerformanceProps {
  systemStatus: SystemStatus;
}

const SystemPerformance: React.FC<SystemPerformanceProps> = ({ systemStatus }) => {
  const getLoadColor = (load: number) => {
    if (load < 0.5) return 'success';
    if (load < 0.8) return 'warning';
    return 'error';
  };

  const getLoadStatus = (load: number) => {
    if (load < 0.5) return 'Low';
    if (load < 0.8) return 'Moderate';
    return 'High';
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          System Performance
        </Typography>
        
        <Box mb={3}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body2">System Load</Typography>
            <Chip
              label={getLoadStatus(systemStatus.systemLoad)}
              color={getLoadColor(systemStatus.systemLoad)}
              size="small"
              variant="outlined"
            />
          </Box>
          <LinearProgress
            variant="determinate"
            value={systemStatus.systemLoad * 100}
            color={getLoadColor(systemStatus.systemLoad)}
            sx={{ height: 8, borderRadius: 4 }}
          />
          <Typography variant="caption" color="text.secondary">
            {(systemStatus.systemLoad * 100).toFixed(1)}% utilization
          </Typography>
        </Box>

        <Grid container spacing={2}>
          <Grid size={6}>
            <Box textAlign="center" p={2} bgcolor="background.paper" borderRadius={2}>
              <QueueIcon sx={{ fontSize: 32, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6">{systemStatus.queueLength}</Typography>
              <Typography variant="caption" color="text.secondary">
                Queue Length
              </Typography>
            </Box>
          </Grid>
          
          <Grid size={6}>
            <Box textAlign="center" p={2} bgcolor="background.paper" borderRadius={2}>
              <SpeedIcon sx={{ fontSize: 32, color: 'secondary.main', mb: 1 }} />
              <Typography variant="h6">
                {systemStatus.averageProcessingTime.toFixed(1)}s
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Avg Processing Time
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

/**
 * System Info Component
 */
const SystemInfo: React.FC = () => (
  <Card>
    <CardContent>
      <Typography variant="h6" gutterBottom>
        System Information
      </Typography>
      
      <List dense>
        <StatusIndicator
          status="healthy"
          label="API Server"
          details="Responding normally"
        />
        <Divider />
        <StatusIndicator
          status="healthy"
          label="Database Connection"
          details="Connected and operational"
        />
        <Divider />
        <StatusIndicator
          status="healthy"
          label="Cache System"
          details="Redis cache operational"
        />
        <Divider />
        <StatusIndicator
          status="healthy"
          label="File Storage"
          details="Storage system healthy"
        />
      </List>
    </CardContent>
  </Card>
);

/**
 * System Status Panel Props
 */
interface SystemStatusPanelProps {
  systemStatus: SystemStatus | null;
  isLoading: boolean;
}

/**
 * System Status Panel Component
 */
const SystemStatusPanel: React.FC<SystemStatusPanelProps> = ({
  systemStatus,
  isLoading,
}) => {
  const { loadSystemStatus } = useSettings();

  // Auto-refresh system status every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isLoading) {
        loadSystemStatus();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [loadSystemStatus, isLoading]);

  const handleRefresh = () => {
    loadSystemStatus();
  };

  // Loading state
  if (isLoading || !systemStatus) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" py={8}>
        <Box textAlign="center">
          <CircularProgress size={48} sx={{ mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            Loading system status...
          </Typography>
        </Box>
      </Box>
    );
  }

  // Calculate overall system health
  const modelHealthCount = Object.values(systemStatus.modelHealth).filter(Boolean).length;
  const totalModels = Object.keys(systemStatus.modelHealth).length;
  const systemHealthy = modelHealthCount === totalModels && systemStatus.systemLoad < 0.8;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2">
          System Status
        </Typography>
        
        <Tooltip title="Refresh status">
          <IconButton onClick={handleRefresh} disabled={isLoading}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Overall Status Alert */}
      <Alert 
        severity={systemHealthy ? 'success' : 'warning'} 
        sx={{ mb: 3 }}
        icon={systemHealthy ? <CheckIcon /> : <WarningIcon />}
      >
        <Typography variant="body2">
          <strong>System Status: {systemHealthy ? 'All Systems Operational' : 'Some Issues Detected'}</strong>
          <br />
          {systemHealthy 
            ? 'All AI models are healthy and ready for processing.'
            : `${modelHealthCount}/${totalModels} models healthy. ${systemStatus.systemLoad > 0.8 ? 'High system load detected.' : ''}`
          }
        </Typography>
      </Alert>

      {/* Status Overview */}
      <Grid container spacing={3}>
        {/* Model Health */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <ModelHealth
            modelHealth={systemStatus.modelHealth}
            availableModels={systemStatus.availableModels}
          />
        </Grid>

        {/* System Performance */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <SystemPerformance systemStatus={systemStatus} />
        </Grid>

        {/* System Information */}
        <Grid size={12}>
          <SystemInfo />
        </Grid>
      </Grid>

      {/* Status Details */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Status Details
          </Typography>
          
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Box textAlign="center" p={2}>
                <Typography variant="h6" color="primary">
                  {systemStatus.availableModels.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Available Models
                </Typography>
              </Box>
            </Grid>
            
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Box textAlign="center" p={2}>
                <Typography variant="h6" color="secondary">
                  {modelHealthCount}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Healthy Models
                </Typography>
              </Box>
            </Grid>
            
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Box textAlign="center" p={2}>
                <Typography variant="h6" color="warning.main">
                  {systemStatus.queueLength}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Processing Queue
                </Typography>
              </Box>
            </Grid>
            
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Box textAlign="center" p={2}>
                <Typography variant="h6" color="success.main">
                  {systemStatus.averageProcessingTime.toFixed(1)}s
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Avg Response Time
                </Typography>
              </Box>
            </Grid>
          </Grid>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="caption" color="text.secondary" textAlign="center" display="block">
            Last updated: {new Date(systemStatus.lastUpdated).toLocaleString()}
            <br />
            Status refreshes automatically every 30 seconds
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SystemStatusPanel;