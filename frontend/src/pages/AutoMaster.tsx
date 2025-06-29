import { useState, useCallback } from 'react';
import { Container, Typography, Box, Grid2 as Grid, Alert } from '@mui/material';
import AudioUpload from '@/components/audio/AudioUpload';
import ProcessingControls from '@/components/audio/ProcessingControls';
import WaveformVisualization from '@/components/audio/WaveformVisualization';
import useAudioUpload from '@/hooks/useAudioUpload';
import useAudioPlayback from '@/hooks/useAudioPlayback';
import type { ProcessingMode, ProcessingSettings, AudioTrack } from '@/types';

const AutoMaster = (): JSX.Element => {
  const [processingMode] = useState<ProcessingMode>('auto');
  const [processingSettings, setProcessingSettings] = useState<ProcessingSettings>({
    intensity: 'medium',
    eqStyle: 'balanced',
    preserveDynamics: true,
    targetLoudness: -16,
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentTrack, setCurrentTrack] = useState<AudioTrack | null>(null);

  const audioUpload = useAudioUpload({
    maxFileSize: 100 * 1024 * 1024, // 100MB
    allowedFormats: ['wav', 'mp3', 'flac', 'aiff'],
    autoProcess: false,
    onUploadComplete: (metadata) => {
      console.log('File uploaded successfully:', metadata);
      // Create audio track for playback
      const track: AudioTrack = {
        id: `track_${Date.now()}`,
        name: metadata.filename,
        url: URL.createObjectURL(new File([], metadata.filename)), // Temporary
        metadata,
      };
      setCurrentTrack(track);
    },
    onUploadError: (error) => {
      console.error('Upload error:', error);
    },
  });

  const audioPlayback = useAudioPlayback({
    volume: 0.5,
    onTimeUpdate: (currentTime) => {
      console.log('Playback time:', currentTime);
    },
  });

  const handleFilesSelected = useCallback((files: File[]): void => {
    console.log('Files selected for processing:', files);
    if (files.length > 0) {
      const file = files[0];
      // Create object URL for immediate playback
      const audioUrl = URL.createObjectURL(file);
      
      // Upload file and create track
      audioUpload.upload(file).then((response) => {
        const track: AudioTrack = {
          id: response.fileId,
          name: response.metadata.filename,
          url: audioUrl,
          metadata: response.metadata,
        };
        setCurrentTrack(track);
        
        // Load track for playback
        audioPlayback.loadTrack(track).catch(console.error);
      }).catch(console.error);
    }
  }, [audioUpload, audioPlayback]);

  const handleStartProcessing = useCallback((): void => {
    console.log('Starting processing with settings:', processingSettings);
    setIsProcessing(true);
    
    // Simulate processing time
    setTimeout(() => {
      setIsProcessing(false);
      console.log('Processing completed');
    }, 5000);
  }, [processingSettings]);

  const handleStopProcessing = useCallback((): void => {
    console.log('Stopping processing');
    setIsProcessing(false);
  }, []);

  const hasUploadedFiles = audioUpload.uploadedFiles.length > 0;

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          AI Auto-Mastering
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Upload your audio file and let our AI automatically master it to professional standards.
          No reference track needed - our AI analyzes your music and applies optimal processing.
        </Typography>

        <Grid container spacing={4}>
          {/* Upload Section */}
          <Grid xs={12} md={8}>
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" gutterBottom>
                1. Upload Your Audio
              </Typography>
              <AudioUpload
                maxFileSize={100 * 1024 * 1024}
                allowedFormats={['wav', 'mp3', 'flac', 'aiff']}
                multiple={false}
                onFilesSelected={handleFilesSelected}
                disabled={isProcessing}
              />
              
              {audioUpload.uploadError && (
                <Alert severity="error" sx={{ mt: 2 }} onClose={audioUpload.clearError}>
                  {audioUpload.uploadError}
                </Alert>
              )}
              
              {audioUpload.isUploading && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  Uploading and analyzing your audio file...
                </Alert>
              )}
            </Box>

            {/* Waveform Visualization */}
            {currentTrack && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="h6" gutterBottom>
                  2. Audio Preview
                </Typography>
                <WaveformVisualization
                  audioUrl={currentTrack.url}
                  title={currentTrack.name}
                  height={120}
                  disabled={isProcessing}
                  onTimeUpdate={(time) => console.log('Waveform time:', time)}
                  onDurationChange={(duration) => console.log('Duration:', duration)}
                />
              </Box>
            )}

            {/* Processing Controls */}
            {hasUploadedFiles && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  3. Configure AI Processing
                </Typography>
                <ProcessingControls
                  mode={processingMode}
                  settings={processingSettings}
                  onModeChange={() => {}} // Auto mode is fixed
                  onSettingsChange={setProcessingSettings}
                  onStartProcessing={handleStartProcessing}
                  onStopProcessing={handleStopProcessing}
                  isProcessing={isProcessing}
                  disabled={audioUpload.isUploading}
                />
              </Box>
            )}
          </Grid>

          {/* Info Panel */}
          <Grid xs={12} md={4}>
            <Box sx={{ position: 'sticky', top: 20 }}>
              <Typography variant="h6" gutterBottom>
                AI Auto-Mastering Features
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" paragraph>
                  <strong>Intelligent Analysis:</strong> Our AI analyzes your track's frequency content, dynamics, and musical characteristics.
                </Typography>
                
                <Typography variant="body2" paragraph>
                  <strong>Professional Standards:</strong> Automatically applies industry-standard mastering techniques for streaming platforms.
                </Typography>
                
                <Typography variant="body2" paragraph>
                  <strong>Genre Adaptive:</strong> AI recognizes musical style and applies appropriate processing for your genre.
                </Typography>
                
                <Typography variant="body2" paragraph>
                  <strong>Real-time Preview:</strong> Listen to your mastered track instantly with A/B comparison.
                </Typography>
              </Box>

              {isProcessing && (
                <Alert severity="info">
                  <Typography variant="body2">
                    Processing your track with AI mastering algorithms...
                  </Typography>
                </Alert>
              )}
            </Box>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default AutoMaster;