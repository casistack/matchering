import { useState, useCallback } from 'react';
import { Container, Typography, Box, Grid, Alert } from '@mui/material';
import AudioUpload from '@/components/audio/AudioUpload';
import ProcessingControls from '@/components/audio/ProcessingControls';
import ProcessingProgress from '@/components/audio/ProcessingProgress';
import WaveformVisualizationV2 from '@/components/audio/WaveformVisualizationV2';
import AudioAnalyzer from '@/components/audio/AudioAnalyzer';
import MasteringComparison from '@/components/audio/MasteringComparison';
import useAudioUpload from '@/hooks/useAudioUpload';
// Removed useAudioPlayback to avoid conflict with WaveSurfer.js playback
import useProcessingJob from '@/hooks/useProcessingJob';
import type { ProcessingMode, ProcessingSettings, AudioTrack } from '@/types';

const AutoMaster = (): JSX.Element => {
  const [processingMode, setProcessingMode] = useState<ProcessingMode>('auto');
  const [processingSettings, setProcessingSettings] = useState<ProcessingSettings>({
    intensity: 'medium',
    eqStyle: 'balanced',
    preserveDynamics: true,
    targetLoudness: -16,
  });
  const [currentTrack, setCurrentTrack] = useState<AudioTrack | null>(null);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [uploadedFileId, setUploadedFileId] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [processingResult, setProcessingResult] = useState<any | null>(null);

  const audioUpload = useAudioUpload({
    maxFileSize: 100 * 1024 * 1024, // 100MB
    allowedFormats: ['wav', 'mp3', 'flac', 'aiff'],
    autoProcess: false,
    onUploadComplete: (metadata) => {
      console.log('File uploaded successfully:', metadata);
    },
    onUploadError: (error) => {
      console.error('Upload error:', error);
    },
  });

  const processingJob = useProcessingJob({
    onJobStarted: (jobId, response) => {
      console.log('Processing job started:', jobId, response);
    },
    onProgressUpdate: (progress, stage) => {
      console.log('Processing progress:', progress, stage);
    },
    onJobCompleted: (jobId, outputUrl) => {
      console.log('Processing completed:', jobId, outputUrl);
      
      // Create mock processing result for comparison (in production, this would come from the API)
      if (uploadedFile && outputUrl) {
        const mockResult = {
          jobId,
          originalFile: {
            name: uploadedFile.name,
            url: URL.createObjectURL(uploadedFile),
            metrics: {
              rms: -18.5,
              peak: -3.2,
              lufs: -23.1,
              truePeak: -2.8,
              dynamicRange: 12.3,
              stereoWidth: 85,
              spectralCentroid: 2800,
              fileSize: uploadedFile.size,
              duration: 180.5,
            },
          },
          processedFile: {
            name: uploadedFile.name.replace(/\.(wav|mp3|flac|aiff)$/i, '_mastered.$1'),
            url: outputUrl,
            metrics: {
              rms: -14.2,
              peak: -0.1,
              lufs: -16.0,
              truePeak: -0.05,
              dynamicRange: 10.8,
              stereoWidth: 92,
              spectralCentroid: 2650,
              fileSize: uploadedFile.size * 1.1, // Slightly larger
              duration: 180.5,
            },
          },
          processingSettings: {
            mode: processingMode,
            intensity: processingSettings.intensity,
            eqStyle: processingSettings.eqStyle,
            targetLoudness: processingSettings.targetLoudness,
            preserveDynamics: processingSettings.preserveDynamics,
          },
          aiPredictions: processingMode === 'hybrid' ? {
            modelUsed: 'Hybrid AI (AST + Custom)',
            confidence: 0.87,
            predictedGenre: 'Pop/Electronic',
            audioCharacteristics: {},
          } : undefined,
          processingTime: 8.4,
        };
        
        setProcessingResult(mockResult);
      }
    },
    onJobFailed: (jobId, error) => {
      console.error('Processing failed:', jobId, error);
    },
    autoConnectWebSocket: true,
  });

  // Removed audioPlayback hook - using WaveSurfer.js for playback instead

  const handleFilesSelected = useCallback((files: File[]): void => {
    console.log('Files selected for processing:', files);
    if (files.length > 0) {
      const file = files[0];
      
      // Clean up previous blob URL if it exists
      if (currentTrack?.url.startsWith('blob:')) {
        console.log('AutoMaster: Cleaning up previous blob URL');
        URL.revokeObjectURL(currentTrack.url);
      }
      
      // Create object URL for immediate playback
      const audioUrl = URL.createObjectURL(file);
      console.log('AutoMaster: Created new blob URL:', audioUrl);
      
      // Upload file and create track
      audioUpload.upload(file).then((response) => {
        const track: AudioTrack = {
          id: response.fileId,
          name: response.metadata.filename,
          url: audioUrl,
          metadata: response.metadata,
        };
        setCurrentTrack(track);
        setUploadedFileId(response.fileId);
        setUploadedFile(file); // Store the file for hybrid processing
        
        // Track will be loaded by WaveformVisualization component
        console.log('AutoMaster: Track created for WaveformVisualization:', track);
      }).catch(console.error);
    }
  }, [audioUpload, currentTrack]);

  const handleStartProcessing = useCallback(async (): Promise<void> => {
    if (!uploadedFileId && !uploadedFile) {
      console.error('No file uploaded yet');
      return;
    }

    try {
      console.log('Starting processing with settings:', processingSettings);
      console.log('Processing mode:', processingMode);
      
      // Use file for hybrid mode, fileId for other modes
      const fileInput = processingMode === 'hybrid' ? uploadedFile! : uploadedFileId!;
      await processingJob.startJob(fileInput, processingMode, processingSettings);
    } catch (error) {
      console.error('Failed to start processing:', error);
    }
  }, [uploadedFileId, uploadedFile, processingMode, processingSettings, processingJob]);

  const handleStopProcessing = useCallback(async (): Promise<void> => {
    try {
      console.log('Cancelling processing job');
      await processingJob.cancelJob();
    } catch (error) {
      console.error('Failed to cancel processing:', error);
    }
  }, [processingJob]);

  const handleDownloadResult = useCallback((url: string): void => {
    console.log('Downloading result from:', url);
    // Create a temporary link to trigger download
    const link = document.createElement('a');
    link.href = url;
    link.download = 'processed_audio.wav';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, []);

  const handleRetryProcessing = useCallback((): void => {
    processingJob.reset();
    setProcessingResult(null);
  }, [processingJob]);

  const handleNewProcessing = useCallback((): void => {
    // Reset all state for new processing
    setProcessingResult(null);
    setUploadedFile(null);
    setUploadedFileId(null);
    setCurrentTrack(null);
    processingJob.reset();
    audioUpload.clearFiles();
  }, [processingJob, audioUpload]);

  const handleDownloadComparison = useCallback((fileType: 'original' | 'processed'): void => {
    if (!processingResult) return;
    
    const file = fileType === 'original' ? processingResult.originalFile : processingResult.processedFile;
    const link = document.createElement('a');
    link.href = file.url;
    link.download = file.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [processingResult]);

  const handleAudioElementReady = useCallback((element: HTMLAudioElement): void => {
    setAudioElement(element);
    
    // Track play/pause state for analyzer
    const handlePlay = (): void => setIsPlayingAudio(true);
    const handlePause = (): void => setIsPlayingAudio(false);
    const handleEnded = (): void => setIsPlayingAudio(false);
    
    element.addEventListener('play', handlePlay);
    element.addEventListener('pause', handlePause);
    element.addEventListener('ended', handleEnded);
    
    // Cleanup function
    return () => {
      element.removeEventListener('play', handlePlay);
      element.removeEventListener('pause', handlePause);
      element.removeEventListener('ended', handleEnded);
    };
  }, []);

  const hasUploadedFiles = audioUpload.uploadedFiles.length > 0;

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          AI-Powered Mastering
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Upload your audio file and choose your processing mode: AI Auto-Mastering, Reference-Based, or Hybrid AI approach.
          Our advanced AI analyzes your music and applies optimal processing for professional results.
        </Typography>

        <Grid container spacing={4}>
          {/* Upload Section */}
          <Grid item xs={12} md={8}>
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" gutterBottom>
                1. Upload Your Audio
              </Typography>
              <AudioUpload
                maxFileSize={100 * 1024 * 1024}
                allowedFormats={['wav', 'mp3', 'flac', 'aiff']}
                multiple={false}
                onFilesSelected={handleFilesSelected}
                disabled={processingJob.state.isProcessing}
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
                <WaveformVisualizationV2
                  audioUrl={currentTrack.url}
                  title={currentTrack.name}
                  height={120}
                  disabled={processingJob.state.isProcessing}
                  onTimeUpdate={(time) => console.log('Waveform time:', time)}
                  onDurationChange={(duration) => console.log('Duration:', duration)}
                  onAudioElementReady={handleAudioElementReady}
                />
              </Box>
            )}

            {/* Audio Analysis */}
            {currentTrack && (
              <Box sx={{ mb: 4 }}>
                <AudioAnalyzer
                  audioElement={audioElement}
                  isPlaying={isPlayingAudio}
                  onAnalysisUpdate={(analysis) => {
                    console.log('Audio analysis:', {
                      rms: analysis.rms,
                      peak: analysis.peak,
                      centroid: analysis.centroid,
                      rolloff: analysis.rolloff,
                    });
                  }}
                />
              </Box>
            )}

            {/* Processing Controls */}
            {hasUploadedFiles && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  4. Configure AI Processing
                </Typography>
                <ProcessingControls
                  mode={processingMode}
                  settings={processingSettings}
                  onModeChange={setProcessingMode}
                  onSettingsChange={setProcessingSettings}
                  onStartProcessing={handleStartProcessing}
                  onStopProcessing={handleStopProcessing}
                  isProcessing={processingJob.state.isProcessing}
                  disabled={audioUpload.isUploading || (!uploadedFileId && !uploadedFile)}
                />

                {/* Processing Progress */}
                <ProcessingProgress
                  state={processingJob.state}
                  connectionState={processingJob.connectionState}
                  isConnected={processingJob.isConnected}
                  onCancel={handleStopProcessing}
                  onDownload={handleDownloadResult}
                  onRetry={handleRetryProcessing}
                  formatProgress={processingJob.formatProgress}
                  formatTimeRemaining={processingJob.formatTimeRemaining}
                  formatElapsedTime={processingJob.formatElapsedTime}
                />
              </Box>
            )}
          </Grid>

          {/* Info Panel */}
          <Grid item xs={12} md={4}>
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

              {processingJob.state.isProcessing && (
                <Alert severity="info">
                  <Typography variant="body2">
                    Processing your track with AI mastering algorithms...
                  </Typography>
                </Alert>
              )}
            </Box>
          </Grid>
        </Grid>

        {/* Mastering Results Comparison */}
        {processingResult && (
          <MasteringComparison
            processingResult={processingResult}
            onDownload={handleDownloadComparison}
            onNewProcessing={handleNewProcessing}
          />
        )}
      </Box>
    </Container>
  );
};

export default AutoMaster;