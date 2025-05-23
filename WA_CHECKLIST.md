# Web Assistant (WA) Task Checklist

## Pre-Development Checklist

### Branch Management
- [ ] Create branch with format: `feat/TASK-XXX-description` or `fix/TASK-XXX-description`
- [ ] Ensure branch is based on latest main
- [ ] Verify branch name matches task ID and description

### Task Analysis
- [ ] Review task description and requirements
- [ ] Identify all files that need modification
- [ ] Document any dependencies or assumptions
- [ ] Plan component structure and data flow

## Development Checklist

### Code Organization
- [ ] Follow established folder structure:
  - `/apps/web/src/components/` for reusable components
  - `/apps/web/src/app/` for pages and routes
  - `/apps/web/src/hooks/` for custom React hooks
  - `/apps/web/src/api/` for API client code
- [ ] Use TypeScript for all new files
- [ ] Follow naming conventions:
  - PascalCase for components
  - camelCase for functions and variables
  - kebab-case for CSS classes

### Component Development
- [ ] Create components with proper TypeScript interfaces
- [ ] Implement error boundaries where appropriate
- [ ] Add loading states for async operations
- [ ] Include proper prop validation
- [ ] Write component documentation (JSDoc)

### Styling
- [ ] Use Tailwind CSS for styling
- [ ] Ensure responsive design (mobile-first)
- [ ] Follow design system color palette
- [ ] Add hover/focus states for interactive elements
- [ ] Test dark mode compatibility

### Testing
- [ ] Test all routes render correctly
- [ ] Verify responsive behavior on different screen sizes
- [ ] Test error states and loading states
- [ ] Validate form inputs and error messages
- [ ] Check accessibility (keyboard navigation, ARIA labels)

## Documentation & Reporting

### Screenshots
- [ ] Take at least one screenshot of the working UI
- [ ] Include screenshots in PR description
- [ ] Document any visual changes or improvements

### Task Updates
- [ ] Update `/TASK_CARDS.md` with:
  - [ ] Task status (✅ Done)
  - [ ] Implementation summary
  - [ ] Files modified
  - [ ] Testing notes

### Agent Communication
- [ ] Update `/postbox/WA/outbox.json` with:
  - [ ] Task completion status
  - [ ] Implementation details
  - [ ] Screenshots or visual evidence
  - [ ] Any issues or concerns

## Code Review Preparation

### Final Checks
- [ ] Run `npm run lint` and fix any issues
- [ ] Run `npm run build` to verify production build
- [ ] Test all routes in development mode
- [ ] Verify no console errors or warnings
- [ ] Check for any unused imports or code

### PR Description
- [ ] Include task ID and description
- [ ] List all modified files
- [ ] Add screenshots or GIFs
- [ ] Document testing performed
- [ ] Note any dependencies or setup requirements

## Restrictions

### Do Not Modify
- [ ] CLI tools or scripts
- [ ] Plan execution logic
- [ ] Backend infrastructure
- [ ] API endpoints or schemas
- [ ] Database or storage systems

### File Management
- [ ] Do not commit placeholder files
- [ ] Do not commit experimental code without review
- [ ] Do not commit large binary files
- [ ] Do not commit sensitive information
- [ ] Do not commit node_modules or build artifacts

## Completion

### Final Steps
- [ ] Create PR with proper title format: `TASK-XXX: Description`
- [ ] Request review from CC or ARCH
- [ ] Address any review comments
- [ ] Merge only after approval
- [ ] Delete feature branch after merge

### Post-Merge
- [ ] Verify changes are live in main
- [ ] Test deployed changes if applicable
- [ ] Update any related documentation
- [ ] Notify team of completion 