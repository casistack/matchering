import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import Layout from './components/layout/Layout';
import Home from './pages/Home';
import AutoMaster from './pages/AutoMaster';
import ReferenceMaster from './pages/ReferenceMaster';

// Create a dark theme matching Matchering's color scheme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#fed535',
    },
    secondary: {
      main: '#e4e3df',
    },
    background: {
      default: '#1c1d1f',
      paper: '#4b5665',
    },
    text: {
      primary: '#e4e3df',
      secondary: '#fed535',
    },
  },
  typography: {
    fontFamily: 'Ubuntu, sans-serif',
    h1: {
      fontWeight: 700,
    },
    h2: {
      fontWeight: 700,
    },
    h6: {
      fontWeight: 700,
    },
  },
});

const App = (): JSX.Element => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="auto-master" element={<AutoMaster />} />
            <Route path="reference-master" element={<ReferenceMaster />} />
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  );
};

export default App
