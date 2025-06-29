import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  Paper,
  LinearProgress,
  Alert,
  Chip,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  CloudUpload,
  Delete,
  AudioFile,
  CheckCircle,
  Error as ErrorIcon,
} from '@mui/icons-material';
import type { AudioFormat, AudioFileMetadata } from '@/types';

interface AudioUploadProps {
  readonly maxFileSize?: number; // bytes
  readonly allowedFormats?: readonly AudioFormat[];
  readonly multiple?: boolean;
  readonly onFilesSelected?: (files: File[]) => void;
  readonly onFileRemove?: (index: number) => void;
  readonly disabled?: boolean;
}

interface UploadedFile {
  readonly file: File;
  readonly id: string;
  readonly status: 'uploading' | 'completed' | 'error';
  readonly progress: number;
  readonly error?: string;
  readonly metadata?: Partial<AudioFileMetadata>;
}

const ALLOWED_FORMATS: readonly AudioFormat[] = ['wav', 'mp3', 'flac', 'aiff'];
const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

const AudioUpload = ({
  maxFileSize = MAX_FILE_SIZE,
  allowedFormats = ALLOWED_FORMATS,
  multiple = true,
  onFilesSelected,
  onFileRemove,
  disabled = false,
}: AudioUploadProps): JSX.Element => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [globalError, setGlobalError] = useState<string | null>(null);

  const validateFile = useCallback(
    (file: File): { valid: boolean; error?: string } => {
      // Check file size
      if (file.size > maxFileSize) {
        return {
          valid: false,
          error: `File size (${(file.size / 1024 / 1024).toFixed(1)}MB) exceeds maximum allowed size (${(maxFileSize / 1024 / 1024).toFixed(1)}MB)`,
        };
      }

      // Check file format
      const extension = file.name.split('.').pop()?.toLowerCase() as AudioFormat;
      if (!allowedFormats.includes(extension)) {
        return {
          valid: false,
          error: `File format .${extension} is not supported. Allowed formats: ${allowedFormats.join(', ')}`,
        };
      }

      return { valid: true };
    },
    [maxFileSize, allowedFormats]
  );

  const analyzeAudioFile = useCallback(async (file: File): Promise<Partial<AudioFileMetadata>> => {
    // This is a placeholder for actual audio analysis
    // In a real implementation, this would analyze the audio file
    const extension = file.name.split('.').pop()?.toLowerCase() as AudioFormat;
    
    return {
      filename: file.name,
      format: extension,
      fileSize: file.size,
      // These would come from actual audio analysis
      duration: 0,
      sampleRate: 44100,
      channels: 2,
      bitDepth: 16,
    };
  }, []);

  const simulateUpload = useCallback(async (fileData: UploadedFile): Promise<void> => {
    const updateProgress = (progress: number): void => {
      setUploadedFiles(prev =>
        prev.map(f =>
          f.id === fileData.id
            ? { ...f, progress }
            : f
        )
      );
    };

    try {
      // Simulate upload progress
      for (let progress = 0; progress <= 100; progress += 10) {
        await new Promise(resolve => setTimeout(resolve, 100));
        updateProgress(progress);
      }

      // Analyze the audio file
      const metadata = await analyzeAudioFile(fileData.file);

      // Mark as completed
      setUploadedFiles(prev =>
        prev.map(f =>
          f.id === fileData.id
            ? { ...f, status: 'completed', metadata }
            : f
        )
      );
    } catch (uploadError) {
      const errorMessage = uploadError instanceof Error ? uploadError.message : 'Upload failed';
      // Mark as error
      setUploadedFiles(prev =>
        prev.map(f =>
          f.id === fileData.id
            ? { ...f, status: 'error', error: errorMessage }
            : f
        )
      );
    }
  }, [analyzeAudioFile]);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      setGlobalError(null);
      const validFiles: File[] = [];
      const errors: string[] = [];

      for (const file of acceptedFiles) {
        const validation = validateFile(file);
        if (validation.valid) {
          validFiles.push(file);
        } else {
          errors.push(`${file.name}: ${validation.error}`);
        }
      }

      if (errors.length > 0) {
        setGlobalError(errors.join('; '));
      }

      if (validFiles.length > 0) {
        const newFiles: UploadedFile[] = validFiles.map(file => ({
          file,
          id: `${Date.now()}-${Math.random()}`,
          status: 'uploading',
          progress: 0,
        }));

        setUploadedFiles(prev => [...prev, ...newFiles]);

        // Start upload simulation for each file
        newFiles.forEach(fileData => {
          simulateUpload(fileData);
        });

        // Notify parent component
        onFilesSelected?.(validFiles);
      }
    },
    [validateFile, onFilesSelected, simulateUpload]
  );

  const removeFile = useCallback(
    (index: number): void => {
      setUploadedFiles(prev => prev.filter((_, i) => i !== index));
      onFileRemove?.(index);
    },
    [onFileRemove]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': allowedFormats.map(format => `.${format}`),
    },
    multiple,
    disabled,
    maxSize: maxFileSize,
  });

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: UploadedFile['status']): JSX.Element => {
    switch (status) {
      case 'completed':
        return <CheckCircle color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <AudioFile />;
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Dropzone */}
      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.500',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: disabled ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease-in-out',
          textAlign: 'center',
          opacity: disabled ? 0.5 : 1,
          '&:hover': {
            borderColor: disabled ? 'grey.500' : 'primary.main',
            backgroundColor: disabled ? 'background.paper' : 'action.hover',
          },
        }}
      >
        <input {...getInputProps()} />
        <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop the audio files here...' : 'Drag & drop audio files here'}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          or click to select files
        </Typography>
        
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, flexWrap: 'wrap' }}>
          {allowedFormats.map(format => (
            <Chip key={format} label={format.toUpperCase()} size="small" />
          ))}
        </Box>
        
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Max file size: {formatFileSize(maxFileSize)}
        </Typography>
      </Paper>

      {/* Global Error */}
      {globalError && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setGlobalError(null)}>
          {globalError}
        </Alert>
      )}

      {/* Uploaded Files List */}
      {uploadedFiles.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Uploaded Files ({uploadedFiles.length})
          </Typography>
          
          <List>
            {uploadedFiles.map((fileData, index) => (
              <ListItem key={fileData.id}>
                <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
                  {getStatusIcon(fileData.status)}
                </Box>
                
                <ListItemText
                  primary={fileData.file.name}
                  secondary={
                    <span>
                      <Typography variant="caption" color="text.secondary" component="span">
                        {formatFileSize(fileData.file.size)}
                        {fileData.metadata?.duration ? ` • ${fileData.metadata.duration.toFixed(1)}s` : ''}
                        {fileData.metadata?.sampleRate ? ` • ${fileData.metadata.sampleRate}Hz` : ''}
                      </Typography>
                      
                      {fileData.status === 'uploading' && (
                        <LinearProgress
                          variant="determinate"
                          value={fileData.progress}
                          sx={{ mt: 1, display: 'block' }}
                        />
                      )}
                      
                      {fileData.status === 'error' && fileData.error && (
                        <Typography variant="caption" color="error" component="span" sx={{ display: 'block' }}>
                          {fileData.error}
                        </Typography>
                      )}
                    </span>
                  }
                />
                
                <ListItemSecondaryAction>
                  <IconButton
                    edge="end"
                    onClick={() => removeFile(index)}
                    size="small"
                  >
                    <Delete />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </Box>
      )}
    </Box>
  );
};

export default AudioUpload;