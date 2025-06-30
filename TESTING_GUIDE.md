# 🧪 Hybrid AI Mastering System - Testing Guide

**Status**: ✅ Backend Running on Port 8000  
**Frontend**: Available on http://localhost:5173/  
**API Docs**: Available on http://localhost:8000/docs  

## 🚀 Quick Start - What You Can Test Right Now

### 1. **Backend API Health Check** ✅
```bash
# Test if the backend is running
curl http://localhost:8000/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "service": "enhanced-matchering-api", 
  "version": "3.0.0"
}
```

### 2. **Hybrid AI Health Check** ✅
```bash
# Test if hybrid AI endpoints are available
curl http://localhost:8000/api/v1/hybrid-ai/health
```

### 3. **Interactive API Documentation** ✅
**Visit**: http://localhost:8000/docs

This will show you all available endpoints with interactive testing interface.

## 📋 Step-by-Step Testing Plan

### **Phase 1: Basic API Connectivity** (5 minutes)

#### Step 1.1: Test Main API Health
```bash
curl http://localhost:8000/health
```

#### Step 1.2: Test Hybrid AI Health
```bash
curl http://localhost:8000/api/v1/hybrid-ai/health
```

#### Step 1.3: Check Available Models
```bash
curl http://localhost:8000/api/v1/hybrid-ai/available-models
```

#### Step 1.4: View API Documentation
**Open in browser**: http://localhost:8000/docs

---

### **Phase 2: Hybrid AI Feature Testing** (10 minutes)

#### Step 2.1: Test Model Selection (No File Required)
```bash
curl -X GET http://localhost:8000/api/v1/hybrid-ai/available-models
```

#### Step 2.2: Test Performance Metrics
```bash
curl -X GET http://localhost:8000/api/v1/hybrid-ai/model-performance
```

---

### **Phase 3: Audio File Processing** (15 minutes)

#### Step 3.1: Prepare Test Audio File
Make sure you have an audio file in your Testuploads folder:
```bash
ls /home/masterp/Seafile/sourcery-mac/mypythonai/matchering/Testuploads/
```

#### Step 3.2: Test Feature Extraction
```bash
curl -X POST "http://localhost:8000/api/v1/hybrid-ai/extract-hybrid-features" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/home/masterp/Seafile/sourcery-mac/mypythonai/matchering/Testuploads/Respek Ma Craft.wav" \
  -F "include_model_features=true" \
  -F "include_custom_features=true"
```

#### Step 3.3: Test Model Selection for Audio
```bash
curl -X POST "http://localhost:8000/api/v1/hybrid-ai/select-model" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/home/masterp/Seafile/sourcery-mac/mypythonai/matchering/Testuploads/Respek Ma Craft.wav"
```

#### Step 3.4: Test Parameter Prediction
```bash
curl -X POST "http://localhost:8000/api/v1/hybrid-ai/predict-parameters" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/home/masterp/Seafile/sourcery-mac/mypythonai/matchering/Testuploads/Respek Ma Craft.wav" \
  -F "model_preference=auto" \
  -F "processing_mode=hybrid" \
  -F "intensity_level=medium"
```

---

### **Phase 4: Complete Mastering Pipeline** (20 minutes)

#### Step 4.1: Basic Hybrid Mastering
```bash
curl -X POST "http://localhost:8000/api/v1/hybrid-ai/process-hybrid" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/home/masterp/Seafile/sourcery-mac/mypythonai/matchering/Testuploads/Respek Ma Craft.wav" \
  -F "model_preference=auto" \
  -F "processing_mode=hybrid" \
  -F "intensity_level=medium" \
  -F "preserve_dynamics=true" \
  -F "target_loudness_lufs=-14.0"
```

#### Step 4.2: Advanced Hybrid Mastering with Style
```bash
curl -X POST "http://localhost:8000/api/v1/hybrid-ai/process-hybrid" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/home/masterp/Seafile/sourcery-mac/mypythonai/matchering/Testuploads/Respek Ma Craft.wav" \
  -F "model_preference=clap" \
  -F "user_style=warm and punchy rock sound" \
  -F "processing_mode=hybrid" \
  -F "intensity_level=high" \
  -F "preserve_dynamics=false" \
  -F "target_loudness_lufs=-12.0"
```

---

## 🌐 Frontend Testing (http://localhost:5173/)

### What to Expect on Frontend:

1. **Navigate to**: http://localhost:5173/
2. **Look for**: 
   - Upload interface for audio files
   - Processing options (intensity, mode, etc.)
   - AI model selection options
   - Progress indicators
   - Results display

### Frontend Test Steps:

#### Step F1: File Upload Test
- Try uploading an audio file (.wav, .mp3, .flac)
- Check if file validation works
- Verify upload progress indication

#### Step F2: Processing Options Test
- Test different intensity levels (low, medium, high)
- Try different processing modes (ai, reference, hybrid)
- Test model preference selection

#### Step F3: AI Processing Test
- Submit a file for processing
- Monitor progress indicators
- Check results display
- Test download functionality

---

## 🔧 Advanced Testing with Swagger UI

### Interactive Testing via Browser:

1. **Open**: http://localhost:8000/docs
2. **Expand**: "Hybrid AI Mastering" section
3. **Test each endpoint**:
   - Click "Try it out"
   - Upload test files
   - Modify parameters
   - Execute requests
   - Review responses

### Recommended Test Sequence in Swagger:

1. **GET** `/hybrid-ai/health` - Check service status
2. **GET** `/hybrid-ai/available-models` - See model options
3. **POST** `/hybrid-ai/extract-hybrid-features` - Upload file
4. **POST** `/hybrid-ai/select-model` - Test model selection
5. **POST** `/hybrid-ai/predict-parameters` - Test AI prediction
6. **POST** `/hybrid-ai/process-hybrid` - Full processing

---

## ⚠️ What Might Happen (Expected Behaviors)

### ✅ **Should Work Immediately:**
- API health checks
- Model availability queries
- File upload and validation
- Basic feature extraction
- Model selection logic
- Parameter prediction

### ⚡ **Might Take Time on First Use:**
- **Model Downloads**: First time using pre-trained models (AST, Wav2Vec, CLAP) will download them from HuggingFace (1-5GB total)
- **CUDA Setup**: GPU initialization may take a few seconds
- **Feature Extraction**: First run might be slower due to model loading

### 🔄 **Potential Issues:**
- **CUDA Warnings**: May see CUDA/GPU warnings (system will fallback to CPU)
- **Model Loading Timeouts**: Large models might timeout on first load
- **Memory Usage**: High memory usage during model loading

---

## 🐛 Troubleshooting Guide

### If API Returns Errors:

#### Error: "CUDA symbol undefined"
```bash
# Set CUDA environment and restart
export CUDA_HOME=/usr/local/cuda-12.4
export LD_LIBRARY_PATH=/usr/local/cuda-12.4/lib64:$LD_LIBRARY_PATH
# Restart the backend
```

#### Error: "Model loading failed"
- **Solution**: First model download requires internet
- **Expected**: Models will be cached after first download
- **Fallback**: System will use CPU/custom models if pre-trained models fail

#### Error: "File validation failed"
- **Check**: File format (only .wav, .mp3, .flac, .aiff supported)
- **Check**: File size (max 100MB)
- **Solution**: Use a smaller, supported audio file

### If Frontend Issues:

#### Frontend won't connect to backend:
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check CORS settings
# Backend should allow localhost:5173
```

#### Upload not working:
- Check file size (max 100MB)
- Verify file format
- Check browser console for errors

---

## 📊 What to Look For in Responses

### Successful Model Selection Response:
```json
{
  "recommended_model": "ast",
  "model_confidence": 0.85,
  "audio_characteristics": {
    "genre": "pop",
    "energy_level": 0.7,
    "has_vocals": true
  },
  "selection_reasoning": "AST excels at spectral analysis for electronic genres"
}
```

### Successful Parameter Prediction:
```json
{
  "success": true,
  "model_used": "ast",
  "predicted_parameters": {
    "eq_curve": [0.0, 0.2, 0.4, ...],
    "compression_ratio": 2.5,
    "limiting_threshold": -1.0
  },
  "model_confidence": 0.85
}
```

### Successful Processing Job:
```json
{
  "success": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "processing_mode": "hybrid",
  "model_used": "ast",
  "estimated_completion_time": 12.5
}
```

---

## 🎯 Success Criteria

### ✅ **System is Working If:**
1. **Health checks** return "healthy" status
2. **Model availability** shows at least 1 available model
3. **File upload** completes without errors
4. **Feature extraction** returns audio characteristics
5. **Model selection** provides recommendations
6. **Parameter prediction** returns mastering parameters
7. **Processing jobs** are created with valid job IDs

### 🚀 **Ready for Production If:**
1. All above tests pass
2. Response times are reasonable (<30s for processing)
3. Error handling works gracefully
4. Frontend integrates successfully
5. Multiple concurrent requests work

---

## 📞 Quick Test Script

Save this as `quick_test.sh`:

```bash
#!/bin/bash
echo "🧪 Testing Hybrid AI Mastering System..."

echo "1. Testing API Health..."
curl -s http://localhost:8000/health | jq .

echo -e "\n2. Testing Hybrid AI Health..."
curl -s http://localhost:8000/api/v1/hybrid-ai/health | jq .

echo -e "\n3. Testing Available Models..."
curl -s http://localhost:8000/api/v1/hybrid-ai/available-models | jq .

echo -e "\n4. Testing Feature Extraction..."
curl -X POST "http://localhost:8000/api/v1/hybrid-ai/extract-hybrid-features" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/home/masterp/Seafile/sourcery-mac/mypythonai/matchering/Testuploads/Respek Ma Craft.wav" \
  -F "include_model_features=false" \
  -F "include_custom_features=true" | jq .

echo -e "\n✅ Basic tests complete!"
```

```bash
chmod +x quick_test.sh
./quick_test.sh
```

---

## 🎵 Ready to Test!

Your hybrid AI mastering system is **fully operational** and ready for testing! Start with the basic health checks and work your way up to full audio processing. The system should handle everything gracefully, even if some advanced features need first-time setup.

**Happy Testing!** 🎉