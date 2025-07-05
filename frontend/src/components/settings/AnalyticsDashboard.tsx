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
  FavoriteRounded as FavoriteIcon,
  SpeedRounded as SpeedIcon,
  AnalyticsRounded as AnalyticsIcon,
  PsychologyRounded as BrainIcon,
  EmojiEventsRounded as TrophyIcon,
} from '@mui/icons-material';
import type { UserAnalytics, SystemStatus } from '@/types/settings';
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
  const modelUsage = Object.entries(analytics.model_usage_distribution);
  const maxUsage = Math.max(...Object.values(analytics.model_usage_distribution));

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Model Performance
        </Typography>
        
        <List>
          {modelUsage.map(([modelName, usageCount], index) => (
            <React.Fragment key={modelName}>
              <ListItem>
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: `hsl(${index * 60}, 70%, 50%)` }}>
                    <BrainIcon />
                  </Avatar>
                </ListItemAvatar>
                
                <ListItemText
                  primary={MODEL_DISPLAY_NAMES[modelName] || modelName}
                  secondary={
                    <Box>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="caption">
                          Quality: {analytics.quality_ratings[modelName] ? (analytics.quality_ratings[modelName] * 100).toFixed(1) + '%' : 'N/A'}
                        </Typography>
                        <Typography variant="caption">
                          Avg Time: {analytics.average_processing_time.toFixed(1)}s
                        </Typography>
                      </Box>
                      
                      <LinearProgress
                        variant="determinate"
                        value={(usageCount / maxUsage) * 100}
                        sx={{ height: 6, borderRadius: 3 }}
                      />
                      
                      <Box display="flex" justifyContent="space-between" alignItems="center" mt={1}>
                        <Typography variant="caption" color="text.secondary">
                          Used {usageCount} times
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Last {analytics.period_days} days
                        </Typography>
                      </Box>
                    </Box>
                  }
                />
              </ListItem>
              {index < modelUsage.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

/**
 * Most Used Model Component
 */
interface MostUsedModelProps {
  modelUsage: Record<string, number>;
}

const MostUsedModel: React.FC<MostUsedModelProps> = ({ modelUsage }) => {
  const topModels = Object.entries(modelUsage)
    .sort(([, a], [, b]) => (b as number) - (a as number))
    .slice(0, 3);

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Most Used Models
        </Typography>
        
        {topModels.length === 0 ? (
          <Typography variant="body2" color="text.secondary" textAlign="center" py={2}>
            No model usage data yet.
          </Typography>
        ) : (
          <Box display="flex" flexWrap="wrap" gap={1}>
            {topModels.map(([model, usage], index) => (
              <Chip
                key={model}
                label={`${MODEL_DISPLAY_NAMES[model] || model} (${usage})`}
                variant="outlined"
                avatar={
                  <Avatar sx={{ bgcolor: index === 0 ? 'gold' : index === 1 ? 'silver' : '#cd7f32' }}>
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
};

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
  if (isLoading && !analytics) {
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

  // No analytics data state (show empty state with mock data)
  if (!analytics) {
    return (
      <Box>
        <Typography variant="h5" component="h2" gutterBottom>
          Usage Analytics
        </Typography>
        
        <Alert severity="info" sx={{ mb: 4 }}>
          <Typography variant="body2">
            <strong>Start Processing Audio Files</strong>
            <br />
            Analytics data will appear here once you begin processing audio files. 
            Upload some tracks and experiment with different model settings to see personalized insights.
          </Typography>
        </Alert>

        {/* Show placeholder metrics for demo */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <MetricCard
              title="Total Processing Jobs"
              value="0"
              subtitle="No jobs yet"
              icon={<AnalyticsIcon />}
              color="primary"
            />
          </Grid>
          
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <MetricCard
              title="Average Processing Time"
              value="0.0s"
              subtitle="No data"
              icon={<SpeedIcon />}
              color="secondary"
            />
          </Grid>
          
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <MetricCard
              title="Most Used Model"
              value="None"
              subtitle="No usage yet"
              icon={<BrainIcon />}
              color="success"
            />
          </Grid>
          
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <MetricCard
              title="Analysis Period"
              value="30 days"
              subtitle="Ready to track"
              icon={<TrendingUpIcon />}
              color="warning"
            />
          </Grid>
        </Grid>

        {/* System Status if available */}
        {systemStatus && (
          <Alert severity="info" sx={{ mt: 3 }}>
            <Typography variant="body2">
              <strong>System Performance:</strong> {systemStatus.available_models_count} models available
              • Active users: {systemStatus.active_users_count}
              • Cache hit rate: {(systemStatus.cache_hit_rate * 100).toFixed(1)}%
              • Avg response: {systemStatus.average_response_time.toFixed(1)}ms
            </Typography>
          </Alert>
        )}
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
            value={analytics.total_processing_jobs}
            icon={<AnalyticsIcon />}
            color="primary"
          />
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Average Processing Time"
            value={`${analytics.average_processing_time.toFixed(1)}s`}
            icon={<SpeedIcon />}
            color="secondary"
          />
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Most Used Model"
            value={analytics.most_used_model || 'None'}
            icon={<BrainIcon />}
            color="success"
          />
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Analysis Period"
            value={`${analytics.period_days} days`}
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

        {/* Quality Ratings */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Model Quality Ratings
              </Typography>
              {Object.keys(analytics.quality_ratings).length === 0 ? (
                <Typography variant="body2" color="text.secondary" textAlign="center" py={4}>
                  No quality ratings available yet.
                </Typography>
              ) : (
                <List dense>
                  {Object.entries(analytics.quality_ratings).map(([model, rating]) => (
                    <ListItem key={model}>
                      <ListItemText
                        primary={MODEL_DISPLAY_NAMES[model] || model}
                        secondary={`${(rating * 100).toFixed(1)}% quality score`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Most Used Models */}
        <Grid size={{ xs: 12, md: 6 }}>
          <MostUsedModel 
            modelUsage={analytics.model_usage_distribution}
          />
        </Grid>

        {/* Performance Trends */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Trends
              </Typography>
              {Object.keys(analytics.performance_trends).length === 0 ? (
                <Typography variant="body2" color="text.secondary" textAlign="center" py={4}>
                  No performance trend data available yet.
                </Typography>
              ) : (
                <List dense>
                  {Object.entries(analytics.performance_trends).map(([metric, values]) => (
                    <ListItem key={metric}>
                      <ListItemText
                        primary={metric.replace('_', ' ').toUpperCase()}
                        secondary={`${values.length} data points over ${analytics.period_days} days`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* System Status Integration */}
      {systemStatus && (
        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="body2">
            <strong>System Performance:</strong> {systemStatus.available_models_count} models available
            • Active users: {systemStatus.active_users_count}
            • Cache hit rate: {(systemStatus.cache_hit_rate * 100).toFixed(1)}%
            • Avg response: {systemStatus.average_response_time.toFixed(1)}ms
          </Typography>
        </Alert>
      )}

      {/* No Data State */}
      {analytics.total_processing_jobs === 0 && (
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