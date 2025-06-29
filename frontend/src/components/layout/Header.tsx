import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';

const Header = (): JSX.Element => {
  const location = useLocation();

  const navItems = [
    { label: 'Home', path: '/' },
    { label: 'AI Auto-Master', path: '/auto-master' },
    { label: 'Reference Master', path: '/reference-master' },
  ] as const;

  return (
    <AppBar position="static" sx={{ backgroundColor: '#1c1d1f' }}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1, color: '#fed535' }}>
          <span style={{ color: '#fed535', fontWeight: 'bold' }}>Match</span>ering{' '}
          <span style={{ color: '#fed535', fontWeight: 'bold' }}>AI</span>
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          {navItems.map((item) => (
            <Button
              key={item.path}
              color="inherit"
              component={Link}
              to={item.path}
              sx={{
                backgroundColor: location.pathname === item.path ? '#fed535' : 'transparent',
                color: location.pathname === item.path ? '#1c1d1f' : '#e4e3df',
                '&:hover': {
                  backgroundColor: '#fed535',
                  color: '#1c1d1f',
                },
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;