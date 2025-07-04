/**
 * Analytics Dashboard Component
 * 
 * Displays user analytics and performance metrics
 */

import React from 'react';
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
  ListItemAvatar,
  Avatar,
  LinearProgress,
  Alert,
  Divider,
} from '@mui/material';
import {
  TrendingUpRounded as TrendingUpIcon,
  AccessTimeRounded as TimeIcon,
  FavoriteRounded as FavoriteIcon,
  MusicNoteRounded as MusicIcon,
  SpeedRounded as SpeedIcon,
  AnalyticsRounded as AnalyticsIcon,
  PsychologyRounded as BrainIcon,
  EmojiEventsRounded as TrophyIcon,
} from '@mui/icons-material';
import type { UserAnalytics, SystemStatus, ModelName } from '@/types/settings';
import { MODEL_DISPLAY_NAMES } from '@/types/settings';

/**
 * Metric Card Component
 */
interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  subtitle, 
  icon, 
  color = 'primary' 
}) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Avatar sx={{ bgcolor: `${color}.main`, width: 48, height: 48 }}>
          {icon}
        </Avatar>
        <Box textAlign="right">
          <Typography variant="h4" component="div" fontWeight="bold">
            {value}
          </Typography>
          {subtitle && (
            <Typography variant="caption" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
      </Box>
      <Typography variant="body2" color="text.secondary">
        {title}
      </Typography>
    </CardContent>
  </Card>
);

/**
 * Model Performance Chart Component
 */
interface ModelPerformanceChartProps {
  analytics: UserAnalytics;
}

const ModelPerformanceChart: React.FC<ModelPerformanceChartProps> = ({ analytics }) => {
  const maxUsage = Math.max(...analytics.modelPerformance.map(m => m.usageCount));

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Model Performance
        </Typography>
        
        <List>
          {analytics.modelPerformance.map((model, index) => (
            <React.Fragment key={model.modelName}>
              <ListItem>
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: `hsl(${index * 60}, 70%, 50%)` }}>
                    <BrainIcon />
                  </Avatar>
                </ListItemAvatar>
                
                <ListItemText
                  primary={MODEL_DISPLAY_NAMES[model.modelName] || model.modelName}
                  secondary={
                    <Box>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="caption">
                          Accuracy: {(model.accuracy * 100).toFixed(1)}%
                        </Typography>
                        <Typography variant="caption">
                          Avg Time: {model.processingTime.toFixed(1)}s
                        </Typography>
                      </Box>
                      
                      <LinearProgress
                        variant="determinate"
                        value={(model.usageCount / maxUsage) * 100}
                        sx={{ height: 6, borderRadius: 3 }}
                      />
                      
                      <Box display="flex" justifyContent="space-between" alignItems="center" mt={1}>
                        <Typography variant="caption" color="text.secondary">
                          Used {model.usageCount} times
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(model.lastUsed).toLocaleDateString()}
                        </Typography>
                      </Box>
                    </Box>
                  }
                />
              </ListItem>
              {index < analytics.modelPerformance.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

/**
 * Genre Distribution Component
 */
interface GenreDistributionProps {
  genreDistribution: Record<string, number>;
}

const GenreDistribution: React.FC<GenreDistributionProps> = ({ genreDistribution }) => {
  const genres = Object.entries(genreDistribution)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5); // Top 5 genres

  const total = Object.values(genreDistribution).reduce((sum, count) => sum + count, 0);

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Genre Distribution
        </Typography>
        
        {genres.length === 0 ? (
          <Typography variant="body2" color="text.secondary" textAlign="center" py={4}>
            No genre data available yet.
            Process some audio files to see your genre preferences.
          </Typography>
        ) : (
          <List dense>
            {genres.map(([genre, count], index) => (
              <ListItem key={genre} disablePadding>
                <ListItemAvatar>
                  <Avatar 
                    sx={{ 
                      bgcolor: `hsl(${index * 45}, 60%, 50%)`,
                      width: 32,
                      height: 32,
                      fontSize: '0.8rem'
                    }}
                  >
                    <MusicIcon fontSize="small" />
                  </Avatar>
                </ListItemAvatar>
                
                <ListItemText
                  primary={
                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                        {genre}
                      </Typography>
                      <Chip
                        label={`${((count / total) * 100).toFixed(1)}%`}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                  }
                  secondary={
                    <LinearProgress
                      variant="determinate"
                      value={(count / Math.max(...Object.values(genreDistribution))) * 100}
                      sx={{ mt: 0.5, height: 4, borderRadius: 2 }}
                    />
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * Favorite Models Component
 */
interface FavoriteModelsProps {
  favoriteModels: ModelName[];
}

const FavoriteModels: React.FC<FavoriteModelsProps> = ({ favoriteModels }) => (
  <Card>
    <CardContent>
      <Typography variant="h6" gutterBottom>
        Your Favorite Models
      </Typography>
      
      {favoriteModels.length === 0 ? (
        <Typography variant="body2" color="text.secondary" textAlign="center" py={2}>
          No favorite models identified yet.
        </Typography>
      ) : (
        <Box display="flex" flexWrap="wrap" gap={1}>
          {favoriteModels.map((model, index) => (
            <Chip
              key={model}
              label={MODEL_DISPLAY_NAMES[model] || model}
              variant="outlined"
              avatar={
                <Avatar sx={{ bgcolor: index === 0 ? 'gold' : 'silver' }}>
                  {index === 0 ? <TrophyIcon /> : <FavoriteIcon />}
                </Avatar>
              }
            />
          ))}
        </Box>
      )}
    </CardContent>
  </Card>
);

/**
 * Analytics Dashboard Props
 */
interface AnalyticsDashboardProps {
  analytics: UserAnalytics | null;
  systemStatus: SystemStatus | null;
  isLoading: boolean;
}

/**
 * Analytics Dashboard Component
 */
const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  analytics,
  systemStatus,
  isLoading,
}) => {
  // Loading state
  if (isLoading || !analytics) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" py={8}>
        <Box textAlign="center">
          <CircularProgress size={48} sx={{ mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            Loading analytics...
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Typography variant="h5" component="h2" gutterBottom>
        Usage Analytics
      </Typography>
      
      <Typography variant="body2" color="text.secondary" paragraph>
        Track your processing habits, model performance, and usage patterns to optimize your settings.
      </Typography>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Total Processing Jobs"
            value={analytics.totalProcessingJobs}
            icon={<AnalyticsIcon />}
            color="primary"
          />
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Average Processing Time"
            value={`${analytics.averageProcessingTime.toFixed(1)}s`}
            icon={<SpeedIcon />}
            color="secondary"
          />
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Total Sessions"
            value={analytics.systemUsage.totalSessions}
            icon={<TimeIcon />}
            color="success"
          />
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Avg Session Duration"
            value={`${Math.round(analytics.systemUsage.averageSessionDuration / 60)}min`}
            icon={<TrendingUpIcon />}
            color="warning"
          />
        </Grid>
      </Grid>

      {/* Detailed Analytics */}
      <Grid container spacing={3}>
        {/* Model Performance */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <ModelPerformanceChart analytics={analytics} />
        </Grid>

        {/* Genre Distribution */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <GenreDistribution genreDistribution={analytics.genreDistribution} />
        </Grid>

        {/* Favorite Models */}
        <Grid size={{ xs: 12, md: 6 }}>
          <FavoriteModels favoriteModels={analytics.favoriteModels} />
        </Grid>

        {/* System Usage */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Usage
              </Typography>
              
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Last Active"
                    secondary={new Date(analytics.systemUsage.lastActive).toLocaleString()}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Total Sessions"
                    secondary={`${analytics.systemUsage.totalSessions} sessions`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Average Session Duration"
                    secondary={`${Math.round(analytics.systemUsage.averageSessionDuration / 60)} minutes`}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* System Status Integration */}
      {systemStatus && (
        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="body2">
            <strong>System Performance:</strong> {Object.values(systemStatus.modelHealth).filter(Boolean).length}/{Object.keys(systemStatus.modelHealth).length} models healthy
            • Queue: {systemStatus.queueLength} jobs 
            • Avg processing: {systemStatus.averageProcessingTime.toFixed(1)}s
          </Typography>
        </Alert>
      )}

      {/* No Data State */}
      {analytics.totalProcessingJobs === 0 && (
        <Alert severity="info" sx={{ mt: 4 }}>
          <Typography variant="body2">
            <strong>Start Processing Audio Files</strong>
            <br />
            Analytics data will appear here once you begin processing audio files. 
            Upload some tracks and experiment with different model settings to see personalized insights.
          </Typography>
        </Alert>
      )}
    </Box>
  );
};

export default AnalyticsDashboard;