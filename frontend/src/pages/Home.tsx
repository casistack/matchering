import { Container, Typography, Box, Card, CardContent, Grid, Button, Chip } from '@mui/material';
import { Link } from 'react-router-dom';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import CompareIcon from '@mui/icons-material/Compare';
import BlendIcon from '@mui/icons-material/Blender';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import SpeedIcon from '@mui/icons-material/Speed';
import SecurityIcon from '@mui/icons-material/Security';

const Home = (): JSX.Element => {
  const features = [
    {
      icon: <AutoFixHighIcon sx={{ fontSize: 48 }} />,
      title: 'AI Auto-Mastering',
      description: 'Upload your track and let our AI automatically master it to professional standards. No reference track needed.',
      path: '/auto-master',
      color: '#fed535',
      badge: 'NEW',
    },
    {
      icon: <CompareIcon sx={{ fontSize: 48 }} />,
      title: 'Reference-Based Mastering',
      description: 'Traditional Matchering approach - upload your track and a reference to match its characteristics.',
      path: '/reference-master',
      color: '#51cf66',
    },
    {
      icon: <BlendIcon sx={{ fontSize: 48 }} />,
      title: 'Hybrid Mode',
      description: 'Let AI suggest the best reference tracks, then fine-tune with traditional Matchering.',
      path: '/auto-master',
      color: '#ff6b6b',
      badge: 'COMING SOON',
      disabled: true,
    },
  ];

  const benefits = [
    { icon: <RocketLaunchIcon />, text: 'Professional results in seconds' },
    { icon: <SpeedIcon />, text: 'GPU-accelerated processing' },
    { icon: <SecurityIcon />, text: 'Privacy-first, local processing' },
  ];

  return (
    <Box>
      {/* Hero Section */}
      <Box
        sx={{
          background: 'linear-gradient(180deg, rgba(254, 213, 53, 0.1) 0%, rgba(10, 11, 13, 0) 100%)',
          pt: 8,
          pb: 12,
        }}
      >
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Typography 
              variant="h1" 
              component="h1" 
              gutterBottom
              sx={{
                background: 'linear-gradient(135deg, #ffffff 0%, #fed535 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 3,
              }}
            >
              Master Your Music
            </Typography>
            <Typography 
              variant="h5" 
              component="h2" 
              color="text.secondary"
              sx={{ mb: 4, fontWeight: 400 }}
            >
              Professional audio mastering powered by AI and traditional algorithms
            </Typography>
            
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap', mb: 4 }}>
              {benefits.map((benefit, index) => (
                <Chip
                  key={index}
                  icon={benefit.icon}
                  label={benefit.text}
                  sx={{
                    py: 2.5,
                    px: 2,
                    fontSize: '0.9rem',
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                />
              ))}
            </Box>

            <Button
              component={Link}
              to="/auto-master"
              variant="contained"
              size="large"
              startIcon={<AutoFixHighIcon />}
              sx={{
                py: 1.5,
                px: 4,
                fontSize: '1.125rem',
              }}
            >
              Try AI Mastering Now
            </Button>
          </Box>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Typography 
          variant="h3" 
          component="h2" 
          align="center" 
          gutterBottom
          sx={{ mb: 6 }}
        >
          Choose Your Mastering Workflow
        </Typography>
        
        <Grid container spacing={4}>
          {features.map((feature) => (
            <Grid item xs={12} md={4} key={feature.title}>
              <Card
                sx={{
                  height: '100%',
                  position: 'relative',
                  transition: 'all 0.3s ease',
                  cursor: feature.disabled ? 'default' : 'pointer',
                  opacity: feature.disabled ? 0.6 : 1,
                  '&:hover': feature.disabled ? {} : {
                    transform: 'translateY(-4px)',
                    boxShadow: `0 12px 24px rgba(254, 213, 53, 0.2)`,
                    borderColor: feature.color,
                  },
                }}
                component={feature.disabled ? 'div' : Link}
                to={feature.disabled ? '' : feature.path}
              >
                <CardContent sx={{ p: 4, textAlign: 'center' }}>
                  {feature.badge && (
                    <Chip
                      label={feature.badge}
                      size="small"
                      sx={{
                        position: 'absolute',
                        top: 16,
                        right: 16,
                        backgroundColor: feature.badge === 'NEW' ? '#fed535' : '#666',
                        color: feature.badge === 'NEW' ? '#0a0b0d' : '#fff',
                        fontWeight: 700,
                      }}
                    />
                  )}
                  
                  <Box sx={{ color: feature.color, mb: 2 }}>
                    {feature.icon}
                  </Box>
                  
                  <Typography variant="h5" component="h3" gutterBottom sx={{ fontWeight: 700 }}>
                    {feature.title}
                  </Typography>
                  
                  <Typography variant="body1" color="text.secondary">
                    {feature.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
};

export default Home;