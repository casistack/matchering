# Frontend Debugging Commands

## Type Checking

```bash
# Check TypeScript errors
npm run type-check

# Check with detailed output
npx tsc --noEmit --pretty

# Check specific file
npx tsc --noEmit src/components/settings/AnalyticsDashboard.tsx
```

## Linting

```bash
# Check ESLint errors
npm run lint

# Auto-fix ESLint issues
npm run lint:fix

# Check specific file
npx eslint src/components/settings/AnalyticsDashboard.tsx
```

## Build Testing

```bash
# Full build (catches most issues)
npm run build

# Development build
npm run dev
```

## Dependencies

```bash
# Check for dependency issues
npm ls

# Check for outdated packages
npm outdated

# Check for security issues
npm audit
```

## VS Code Debugging

- **Ctrl+Shift+P** → "TypeScript: Reload Projects"
- **Ctrl+Shift+P** → "Developer: Reload Window"
- Check the "Problems" panel (Ctrl+Shift+M)
