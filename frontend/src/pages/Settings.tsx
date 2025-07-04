/**
 * Settings Page Component
 * 
 * Main page for user model selection and profile management
 */

import React, { useState } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Fade,
} from '@mui/material';
import {
  TuneRounded as TuneIcon,
  AccountBoxRounded as ProfileIcon,
  AnalyticsRounded as AnalyticsIcon,
  InfoRounded as InfoIcon,
} from '@mui/icons-material';
import { useSettings } from '@/hooks/useSettings';
import ModelPreferencesPanel from '@/components/settings/ModelPreferencesPanel';
import ProfileManagementPanel from '@/components/settings/ProfileManagementPanel';
import AnalyticsDashboard from '@/components/settings/AnalyticsDashboard';
import SystemStatusPanel from '@/components/settings/SystemStatusPanel';

/**
 * Tab Panel Component
 */
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Fade in={true} timeout={300}>
          <Box sx={{ pt: 3 }}>
            {children}
          </Box>
        </Fade>
      )}
    </div>
  );
};

/**
 * Tab Props Helper
 */
const a11yProps = (index: number) => {
  return {
    id: `settings-tab-${index}`,
    'aria-controls': `settings-tabpanel-${index}`,
  };
};

/**
 * Settings Page Component
 */
const SettingsPage: React.FC = () => {
  const { config, analytics, systemStatus, isLoading, error } = useSettings();
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Loading state
  if (isLoading && !config) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          minHeight="60vh"
        >
          <CircularProgress size={48} sx={{ mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            Loading settings...
          </Typography>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography 
          variant="h3" 
          component="h1" 
          gutterBottom
          sx={{ 
            fontWeight: 600,
            background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          AI Model Settings
        </Typography>
        <Typography variant="h6" color="text.secondary" paragraph>
          Configure your AI model preferences, manage processing profiles, and monitor performance analytics.
        </Typography>
        
        {/* Active Profile Indicator */}
        {config?.activeProfile && (
          <Alert 
            severity="info" 
            sx={{ mt: 2 }}
            icon={<ProfileIcon />}
          >
            Active Profile: <strong>{config.activeProfile.name}</strong> - {config.activeProfile.description}
          </Alert>
        )}
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => {}}>
          {error}
        </Alert>
      )}

      {/* Settings Tabs */}
      <Paper elevation={2} sx={{ borderRadius: 2 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            aria-label="settings navigation"
            variant="fullWidth"
            sx={{
              '& .MuiTabs-indicator': {
                height: 3,
                borderRadius: '3px 3px 0 0',
              },
            }}
          >
            <Tab
              icon={<TuneIcon />}
              label="Model Preferences"
              {...a11yProps(0)}
              sx={{ 
                minHeight: 72,
                textTransform: 'none',
                fontSize: '1rem',
                fontWeight: 500,
              }}
            />
            <Tab
              icon={<ProfileIcon />}
              label="Profiles"
              {...a11yProps(1)}
              sx={{ 
                minHeight: 72,
                textTransform: 'none',
                fontSize: '1rem',
                fontWeight: 500,
              }}
            />
            <Tab
              icon={<AnalyticsIcon />}
              label="Analytics"
              {...a11yProps(2)}
              sx={{ 
                minHeight: 72,
                textTransform: 'none',
                fontSize: '1rem',
                fontWeight: 500,
              }}
            />
            <Tab
              icon={<InfoIcon />}
              label="System Status"
              {...a11yProps(3)}
              sx={{ 
                minHeight: 72,
                textTransform: 'none',
                fontSize: '1rem',
                fontWeight: 500,
              }}
            />
          </Tabs>
        </Box>

        {/* Tab Panels */}
        <Box sx={{ p: 3 }}>
          {/* Model Preferences Panel */}
          <TabPanel value={activeTab} index={0}>
            <ModelPreferencesPanel />
          </TabPanel>

          {/* Profile Management Panel */}
          <TabPanel value={activeTab} index={1}>
            <ProfileManagementPanel />
          </TabPanel>

          {/* Analytics Dashboard */}
          <TabPanel value={activeTab} index={2}>
            <AnalyticsDashboard analytics={analytics} systemStatus={systemStatus} isLoading={isLoading} />
          </TabPanel>

          {/* System Status Panel */}
          <TabPanel value={activeTab} index={3}>
            <SystemStatusPanel systemStatus={systemStatus} isLoading={isLoading} />
          </TabPanel>
        </Box>
      </Paper>

      {/* Footer Info */}
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Settings are automatically saved and synced across your devices.
          {config?.anonymousId && (
            <>
              <br />
              Session ID: <code>{config.anonymousId}</code>
            </>
          )}
        </Typography>
      </Box>
    </Container>
  );
};

export default SettingsPage;