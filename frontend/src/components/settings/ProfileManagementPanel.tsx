/**
 * Profile Management Panel Component
 * 
 * UI for creating, selecting, and managing user settings profiles
 */

import React, { useState, useCallback } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Alert,
  Avatar,
  Divider,
  Badge,
} from '@mui/material';
import {
  AddRounded as AddIcon,
  MoreVertRounded as MoreVertIcon,
  EditRounded as EditIcon,
  DeleteRounded as DeleteIcon,
  RadioButtonCheckedRounded as ActiveIcon,
  RadioButtonUncheckedRounded as InactiveIcon,
  SaveRounded as SaveIcon,
  ContentCopyRounded as CopyIcon,
  SettingsRounded as SettingsIcon,
} from '@mui/icons-material';
import { useProfileManagement, useSettings } from '@/hooks/useSettings';
import type { 
  UserSettingsProfile, 
  ModelPreferences 
} from '@/types/settings';
import { 
  MODEL_DISPLAY_NAMES, 
  DEFAULT_PREFERENCES 
} from '@/types/settings';

/**
 * Profile Card Component
 */
interface ProfileCardProps {
  profile: UserSettingsProfile;
  isActive: boolean;
  onSelect: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onDuplicate: () => void;
  disabled?: boolean;
}

const ProfileCard: React.FC<ProfileCardProps> = ({
  profile,
  isActive,
  onSelect,
  onEdit,
  onDelete,
  onDuplicate,
  disabled = false,
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const menuOpen = Boolean(anchorEl);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const getProfileColor = (profile: UserSettingsProfile) => {
    const ensembleWeights = profile.ensemble_weights;
    const primaryModel = Object.keys(ensembleWeights)[0] || 'default';
    switch (primaryModel) {
      case 'huggingface':
        return '#1976d2'; // Blue
      case 'distilhubert':
        return '#9c27b0'; // Purple
      case 'wav2vec2':
        return '#f57c00'; // Orange
      case 'ast':
        return '#388e3c'; // Green
      default:
        return '#616161'; // Grey
    }
  };

  const formatModelsList = (ensembleWeights: Record<string, number>) => {
    const models = Object.keys(ensembleWeights);
    return models.map(model => MODEL_DISPLAY_NAMES[model] || model).join(', ');
  };

  return (
    <Card 
      variant={isActive ? "elevation" : "outlined"}
      sx={{ 
        height: '100%',
        border: isActive ? 2 : 1,
        borderColor: isActive ? 'primary.main' : 'divider',
        position: 'relative',
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          boxShadow: isActive ? 8 : 4,
        },
      }}
    >
      {/* Active Badge */}
      {isActive && (
        <Box
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            zIndex: 1,
          }}
        >
          <Badge
            badgeContent="Active"
            color="primary"
            sx={{
              '& .MuiBadge-badge': {
                fontSize: '0.7rem',
                height: 18,
                minWidth: 18,
              },
            }}
          />
        </Box>
      )}

      <CardContent sx={{ pb: 1 }}>
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <Avatar
            sx={{
              bgcolor: getProfileColor(profile),
              width: 48,
              height: 48,
            }}
          >
            <SettingsIcon />
          </Avatar>
          
          <Box flex={1}>
            <Typography variant="h6" component="h3" noWrap>
              {profile.name}
            </Typography>
            <Typography variant="body2" color="text.secondary" noWrap>
              {profile.description}
            </Typography>
          </Box>
        </Box>

        {/* Profile Details */}
        <Box mb={2}>
          <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
            Models ({Object.keys(profile.ensemble_weights).length})
          </Typography>
          <Typography variant="body2" noWrap title={formatModelsList(profile.ensemble_weights)}>
            {formatModelsList(profile.ensemble_weights)}
          </Typography>
        </Box>

        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
          <Typography variant="caption" color="text.secondary">
            Confidence Threshold
          </Typography>
          <Chip
            label={`${(profile.confidence_threshold * 100).toFixed(0)}%`}
            size="small"
            variant="outlined"
          />
        </Box>

        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="caption" color="text.secondary">
            Max Processing Time
          </Typography>
          <Typography variant="caption">
            {(profile.max_processing_time / 1000).toFixed(1)}s
          </Typography>
        </Box>
      </CardContent>

      <CardActions sx={{ justifyContent: 'space-between', pt: 0 }}>
        <Button
          variant={isActive ? "outlined" : "contained"}
          size="small"
          onClick={onSelect}
          disabled={disabled || isActive}
          startIcon={isActive ? <ActiveIcon /> : <InactiveIcon />}
        >
          {isActive ? 'Active' : 'Select'}
        </Button>

        <IconButton
          size="small"
          onClick={handleMenuClick}
          disabled={disabled}
        >
          <MoreVertIcon />
        </IconButton>

        <Menu
          anchorEl={anchorEl}
          open={menuOpen}
          onClose={handleMenuClose}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <MenuItem onClick={() => { onEdit(); handleMenuClose(); }}>
            <EditIcon sx={{ mr: 1 }} />
            Edit
          </MenuItem>
          <MenuItem onClick={() => { onDuplicate(); handleMenuClose(); }}>
            <CopyIcon sx={{ mr: 1 }} />
            Duplicate
          </MenuItem>
          <Divider />
          <MenuItem 
            onClick={() => { onDelete(); handleMenuClose(); }}
            sx={{ color: 'error.main' }}
          >
            <DeleteIcon sx={{ mr: 1 }} />
            Delete
          </MenuItem>
        </Menu>
      </CardActions>
    </Card>
  );
};

/**
 * Create/Edit Profile Dialog
 */
interface ProfileDialogProps {
  open: boolean;
  profile?: UserSettingsProfile;
  onClose: () => void;
  onSave: (name: string, description: string, preferences: ModelPreferences) => void;
  isLoading?: boolean;
}

const ProfileDialog: React.FC<ProfileDialogProps> = ({
  open,
  profile,
  onClose,
  onSave,
  isLoading = false,
}) => {
  const { config } = useSettings();
  const [name, setName] = useState(profile?.name || '');
  const [description, setDescription] = useState(profile?.description || '');
  const [nameError, setNameError] = useState('');

  React.useEffect(() => {
    if (open) {
      setName(profile?.name || '');
      setDescription(profile?.description || '');
      setNameError('');
    }
  }, [open, profile]);

  const handleSave = () => {
    if (!name.trim()) {
      setNameError('Profile name is required');
      return;
    }

    if (name.trim().length < 2) {
      setNameError('Profile name must be at least 2 characters');
      return;
    }

    const preferences = (profile as unknown as ModelPreferences) || config?.current_profile || DEFAULT_PREFERENCES;
    onSave(name.trim(), description.trim(), preferences);
  };

  const isEditing = !!profile;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {isEditing ? 'Edit Profile' : 'Create New Profile'}
      </DialogTitle>
      
      <DialogContent>
        <Box display="flex" flexDirection="column" gap={3} pt={1}>
          <TextField
            label="Profile Name"
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              setNameError('');
            }}
            error={!!nameError}
            helperText={nameError || 'Enter a descriptive name for this profile'}
            fullWidth
            autoFocus
            disabled={isLoading}
          />
          
          <TextField
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            multiline
            rows={3}
            fullWidth
            placeholder="Describe when to use this profile..."
            disabled={isLoading}
          />

          {!isEditing && (
            <Alert severity="info">
              The profile will be created with your current model preferences. 
              You can modify the preferences after creating the profile.
            </Alert>
          )}
        </Box>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} disabled={isLoading}>
          Cancel
        </Button>
        <Button 
          onClick={handleSave} 
          variant="contained"
          disabled={isLoading}
          startIcon={<SaveIcon />}
        >
          {isEditing ? 'Save Changes' : 'Create Profile'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

/**
 * Profile Management Panel Component
 */
const ProfileManagementPanel: React.FC = () => {
  const { profiles, activeProfile, createProfile, selectProfile, deleteProfile, isLoading } = useProfileManagement();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingProfile, setEditingProfile] = useState<UserSettingsProfile | undefined>();
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const handleCreateProfile = useCallback(() => {
    setEditingProfile(undefined);
    setDialogOpen(true);
  }, []);

  const handleEditProfile = useCallback((profile: UserSettingsProfile) => {
    setEditingProfile(profile);
    setDialogOpen(true);
  }, []);

  const handleDuplicateProfile = useCallback((profile: UserSettingsProfile) => {
    setEditingProfile({
      ...profile,
      id: '',
      name: `${profile.name} (Copy)`,
    });
    setDialogOpen(true);
  }, []);

  const handleSaveProfile = useCallback(async (
    name: string, 
    description: string, 
    preferences: ModelPreferences
  ) => {
    try {
      await createProfile(name, description, preferences);
      setDialogOpen(false);
      setEditingProfile(undefined);
    } catch (error) {
      // Error handling is done in the context
      console.error('Failed to save profile:', error);
    }
  }, [createProfile]);

  const handleDeleteProfile = useCallback(async (profileId: string) => {
    try {
      await deleteProfile(profileId);
      setDeleteConfirmId(null);
    } catch (error) {
      console.error('Failed to delete profile:', error);
    }
  }, [deleteProfile]);

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2">
          Settings Profiles
        </Typography>
        
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateProfile}
          disabled={isLoading}
        >
          Create Profile
        </Button>
      </Box>

      {/* No Profiles State */}
      {profiles.length === 0 && (
        <Card sx={{ textAlign: 'center', py: 6 }}>
          <CardContent>
            <SettingsIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No Profiles Created
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Create profiles to save different model configurations for various use cases.
              Perfect for switching between different audio types and quality preferences.
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreateProfile}
              disabled={isLoading}
            >
              Create Your First Profile
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Profiles Grid */}
      {profiles.length > 0 && (
        <Grid container spacing={3}>
          {profiles.map((profile: UserSettingsProfile) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={profile.id}>
              <ProfileCard
                profile={profile}
                isActive={activeProfile?.id === profile.id}
                onSelect={() => selectProfile(profile.id)}
                onEdit={() => handleEditProfile(profile)}
                onDelete={() => setDeleteConfirmId(profile.id)}
                onDuplicate={() => handleDuplicateProfile(profile)}
                disabled={isLoading}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Profile Management Tips */}
      <Alert severity="info" sx={{ mt: 4 }}>
        <Typography variant="body2">
          <strong>Profile Tips:</strong>
          <br />
          • Create specialized profiles for different audio types (vocals, instruments, genres)
          <br />
          • Use descriptive names like "Hip-Hop Vocals" or "Classical Orchestra"
          <br />
          • Duplicate existing profiles to create variations quickly
          <br />
          • The active profile determines which models are used for processing
        </Typography>
      </Alert>

      {/* Create/Edit Profile Dialog */}
      <ProfileDialog
        open={dialogOpen}
        profile={editingProfile}
        onClose={() => {
          setDialogOpen(false);
          setEditingProfile(undefined);
        }}
        onSave={handleSaveProfile}
        isLoading={isLoading}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={!!deleteConfirmId}
        onClose={() => setDeleteConfirmId(null)}
        maxWidth="sm"
      >
        <DialogTitle>Delete Profile</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this profile? This action cannot be undone.
          </Typography>
          {deleteConfirmId === activeProfile?.id && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              This is your active profile. Deleting it will reset your preferences to defaults.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmId(null)}>
            Cancel
          </Button>
          <Button
            onClick={() => deleteConfirmId && handleDeleteProfile(deleteConfirmId)}
            color="error"
            variant="contained"
            disabled={isLoading}
            startIcon={<DeleteIcon />}
          >
            Delete Profile
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProfileManagementPanel;