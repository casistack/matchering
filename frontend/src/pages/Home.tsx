import { Container, Typography, Box, Card, CardContent, Grid2 as Grid } from '@mui/material';

const Home = (): JSX.Element => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 8 }}>
        <Typography variant="h2" component="h1" gutterBottom align="center">
          Enhanced Matchering
        </Typography>
        <Typography variant="h5" component="h2" gutterBottom align="center" color="text.secondary">
          AI-Powered Audio Mastering
        </Typography>
        
        <Grid container spacing={4} sx={{ mt: 4 }}>
          <Grid xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" component="h3" gutterBottom>
                  AI Auto-Mastering
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Upload your track and let our AI automatically master it to professional standards.
                  No reference track needed.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" component="h3" gutterBottom>
                  Reference-Based Mastering
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Traditional Matchering approach - upload your track and a reference to match its characteristics.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" component="h3" gutterBottom>
                  Hybrid Mode
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Let AI suggest the best reference tracks, then fine-tune with traditional Matchering.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default Home;