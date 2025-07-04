import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box, IconButton, Chip } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import HomeIcon from '@mui/icons-material/Home';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import CompareIcon from '@mui/icons-material/Compare';
import SettingsIcon from '@mui/icons-material/Settings';
import GraphicEqIcon from '@mui/icons-material/GraphicEq';
import GitHubIcon from '@mui/icons-material/GitHub';

const Header = (): React.ReactElement => {
  const location = useLocation();

  const navItems = [
    { label: 'Home', path: '/', icon: <HomeIcon /> },
    { label: 'AI Auto-Master', path: '/auto-master', icon: <AutoFixHighIcon /> },
    { label: 'Reference Master', path: '/reference-master', icon: <CompareIcon /> },
    { label: 'Settings', path: '/settings', icon: <SettingsIcon /> },
  ] as const;

  return (
    <AppBar 
      position="sticky" 
      elevation={0}
      sx={{ 
        backgroundColor: 'rgba(26, 27, 30, 0.8)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        width: '100%',
        left: 0,
        right: 0,
      }}
    >
      <Toolbar sx={{ py: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <GraphicEqIcon sx={{ color: '#fed535', fontSize: 32, mr: 2 }} />
          <Box>
            <Typography 
              variant="h5" 
              component="div" 
              sx={{ 
                fontWeight: 800,
                letterSpacing: '-0.02em',
                lineHeight: 1,
              }}
            >
              Matchering
            </Typography>
            <Typography 
              variant="caption" 
              sx={{ 
                color: '#fed535',
                fontWeight: 600,
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
              }}
            >
              AI-Powered Mastering
            </Typography>
          </Box>
          <Chip 
            label="BETA" 
            size="small" 
            sx={{ 
              ml: 2,
              backgroundColor: '#fed535',
              color: '#0a0b0d',
              fontWeight: 700,
              fontSize: '0.75rem',
            }} 
          />
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1, mr: 2 }}>
          {navItems.map((item) => (
            <Button
              key={item.path}
              color="inherit"
              component={Link}
              to={item.path}
              startIcon={item.icon}
              sx={{
                px: 2,
                py: 1,
                borderRadius: '8px',
                backgroundColor: location.pathname === item.path ? 'rgba(254, 213, 53, 0.1)' : 'transparent',
                color: location.pathname === item.path ? '#fed535' : '#ffffff',
                border: location.pathname === item.path ? '1px solid #fed535' : '1px solid transparent',
                '&:hover': {
                  backgroundColor: 'rgba(254, 213, 53, 0.1)',
                  borderColor: '#fed535',
                },
                transition: 'all 0.2s ease',
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>

        <IconButton
          color="inherit"
          href="https://github.com/sergree/matchering"
          target="_blank"
          rel="noopener noreferrer"
          sx={{ 
            color: '#b3b3b3',
            '&:hover': { color: '#ffffff' }
          }}
        >
          <GitHubIcon />
        </IconButton>
      </Toolbar>
    </AppBar>
  );
};

export default Header;