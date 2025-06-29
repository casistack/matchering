import { Box, Typography, Link } from '@mui/material';

const Footer = (): JSX.Element => {
  return (
    <Box
      component="footer"
      sx={{
        backgroundColor: '#1c1d1f',
        color: '#333942',
        py: 3,
        px: 2,
        mt: 'auto',
        textAlign: 'center',
      }}
    >
      <Typography variant="body2">
        Enhanced by{' '}
        <Link href="https://github.com/sergree/matchering" target="_blank" rel="noopener" color="inherit">
          Matchering
        </Link>{' '}
        | Maintained by{' '}
        <Link href="https://github.com/sergree" target="_blank" rel="noopener" color="inherit">
          Sergree
        </Link>
      </Typography>
    </Box>
  );
};

export default Footer;