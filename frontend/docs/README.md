# Backend API Documentation

This directory contains **auto-generated documentation** for the Matchering backend API schemas. The documentation is generated directly from the actual Pydantic models to ensure 100% accuracy.

## Files

- **`backend-api-schema.md`** - Comprehensive API documentation with all endpoints and schemas
- **`validation-rules.md`** - Quick reference for validation rules and common errors  
- **`backend-schemas.json`** - Machine-readable JSON schema export

## How to Update Documentation

### Automatic Generation (Recommended)

Run the schema documentation generator from the backend directory:

```bash
cd backend
python generate_schema_docs.py
```

This will:
1. ✅ Read current Pydantic schemas from `app/schemas/settings.py`
2. ✅ Extract all field information, types, and validation rules
3. ✅ Generate comprehensive markdown documentation
4. ✅ Create JSON schema export for tooling
5. ✅ Update validation reference guide

### When to Regenerate

**Always regenerate after:**
- Adding new API endpoints
- Modifying Pydantic schemas in `app/schemas/settings.py`
- Changing validation rules or constraints
- Adding new enum values
- Updating field descriptions

### Integration with Development Workflow

**Option 1: Manual Updates**
- Run `python generate_schema_docs.py` after backend schema changes
- Commit the updated documentation files

**Option 2: Git Pre-commit Hook** (Future Enhancement)
```bash
# Add to .git/hooks/pre-commit
cd backend && python generate_schema_docs.py
git add frontend/docs/
```

**Option 3: CI/CD Integration** (Future Enhancement)
- Auto-generate docs on backend changes
- Create PR with documentation updates

## Usage for Frontend Engineers

### 1. Reference Documentation
- **Quick lookup**: Use `validation-rules.md` for common validation checks
- **Complete reference**: Use `backend-api-schema.md` for full API documentation
- **Machine processing**: Use `backend-schemas.json` for automated tooling

### 2. Validation Helpers
Copy validation functions from `validation-rules.md`:

```typescript
import { validatePreferences } from './validation-helpers';

const errors = validatePreferences(preferences);
if (errors.length > 0) {
  console.error('Validation errors:', errors);
}
```

### 3. Schema Enforcement
Use the documented constraints to prevent 422 errors:

```typescript
// ✅ Valid ensemble weights (sum to ~1.0)
const ensembleWeights = {
  'huggingface_ensemble': 0.7,
  'ast_model': 0.25, 
  'fallback_classifier': 0.05
}; // Total: 1.0

// ✅ Valid confidence threshold (0.5-0.95)
const confidenceThreshold = 0.6;

// ✅ Valid processing time (1000-10000ms)
const maxProcessingTime = 5000;
```

## Documentation Features

### Complete Coverage
- ✅ All 11 API endpoints documented
- ✅ All 12 Pydantic schemas included
- ✅ All 4 enumerations with valid values
- ✅ Validation constraints for every field
- ✅ JSON schema export for tooling

### Accuracy Guaranteed
- ✅ Generated from actual backend code
- ✅ No manual transcription errors
- ✅ Always reflects current implementation
- ✅ Includes validation rules and constraints

### Engineer-Friendly
- ✅ Quick reference sections
- ✅ Copy-paste validation code
- ✅ Common error examples
- ✅ Troubleshooting guidance

## Troubleshooting

### Common Issues

**Q: Documentation is outdated**
A: Run `python generate_schema_docs.py` from backend directory

**Q: 422 validation errors despite following docs**
A: Check if you regenerated docs after recent backend changes

**Q: Missing new endpoints**
A: Add endpoint info to `generate_schema_docs.py` and regenerate

**Q: TypeScript types don't match**
A: Consider generating TypeScript types from JSON schema

### Getting Help

1. Check `validation-rules.md` for common validation issues
2. Review `backend-api-schema.md` for complete field documentation  
3. Inspect `backend-schemas.json` for exact type definitions
4. Run the generator script to get latest documentation

---

**Note:** This documentation is automatically generated and should not be manually edited. All changes should be made to the backend schemas and then regenerated using the provided script.