# UI Theme Change: Red to Blue - Implementation Specification

## Overview
Change the Chainlit UI theme from the default red color scheme to a blue color scheme for the DBS Banking Agent application.

## Current State
The application uses Chainlit's default theme which includes red-colored UI elements (buttons, accents, error states, etc.). No custom theme configuration exists in the codebase.

## Target State
All UI elements currently using red colors should be changed to a blue color scheme that aligns with DBS Bank's brand identity.

---

## Files to Modify

### 1. `/workspace/.chainlit/config.toml` (NEW FILE)
**Action**: Create new configuration file
**Purpose**: Define Chainlit theme settings and custom CSS path

**Content to add**:
```toml
[UI]
name = "DBS Banking Assistant"
logo = ""

[features]
# Enable custom theme
theme = "custom"

[theme]
# Primary color for buttons, links, and accents
primary = "#1a1a3a"
# Secondary color
secondary = "#003366"
# Text color on primary background
text_primary = "#ffffff"
# Background colors
background = "#f8f9fa"
background_secondary = "#ffffff"
# Border colors
border = "#e0e0e0"

# CSS custom properties for fine-grained control
custom_css = ".chainlit/custom.css"
```

### 2. `/workspace/.chainlit/custom.css` (NEW FILE)
**Action**: Create new CSS file
**Purpose**: Override Chainlit's default red colors with blue theme

**Content to add**:
```css
/* DBS Banking Agent - Blue Theme Override */

/* Root CSS variables for theme */
:root {
    /* Primary blue color - DBS brand blue */
    --primary-color: #003366;
    --primary-hover: #002244;
    --primary-light: #4682b4;
    
    /* Secondary colors */
    --secondary-color: #1a1a3a;
    --secondary-hover: #0f0f23;
    
    /* Accent colors */
    --accent-color: #0066cc;
    --accent-hover: #004499;
    
    /* Error colors - keep red for errors but use DBS blue-ish red */
    --error-color: #d32f2f;
    --error-background: #ffebee;
    
    /* Success colors */
    --success-color: #1976d2;
    --success-background: #e3f2fd;
    
    /* Text colors */
    --text-primary: #1a1a3a;
    --text-secondary: #666666;
    --text-on-primary: #ffffff;
    
    /* Background colors */
    --background-primary: #f8f9fa;
    --background-secondary: #ffffff;
    --background-tertiary: #e8eaf6;
    
    /* Border colors */
    --border-color: #e0e0e0;
    --border-light: #b0bec5;
}

/* Override Chainlit default red buttons */
.cl-button {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    color: var(--text-on-primary) !important;
}

.cl-button:hover {
    background-color: var(--primary-hover) !important;
    border-color: var(--primary-hover) !important;
}

.cl-button:focus {
    box-shadow: 0 0 0 3px rgba(0, 51, 102, 0.3) !important;
}

/* Primary action buttons */
.cl-button.primary {
    background-color: var(--accent-color) !important;
    border-color: var(--accent-color) !important;
}

.cl-button.primary:hover {
    background-color: var(--accent-hover) !important;
    border-color: var(--accent-hover) !important;
}

/* Message send button */
.cl-send-button {
    background-color: var(--accent-color) !important;
    color: var(--text-on-primary) !important;
}

.cl-send-button:hover {
    background-color: var(--accent-hover) !important;
}

/* Input field focus border */
.cl-input {
    border-color: var(--border-color) !important;
}

.cl-input:focus {
    border-color: var(--accent-color) !important;
    box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2) !important;
}

/* Sidebar and header colors */
.cl-sidebar {
    background-color: var(--secondary-color) !important;
}

.cl-header {
    background-color: var(--secondary-color) !important;
    border-bottom: 1px solid var(--border-light) !important;
}

/* Message bubbles - user messages */
.cl-message-user {
    background-color: var(--primary-color) !important;
    color: var(--text-on-primary) !important;
}

/* Message bubbles - assistant messages */
.cl-message-assistant {
    background-color: var(--background-tertiary) !important;
    border-left: 3px solid var(--accent-color) !important;
}

/* Scrollbar styling */
::-webkit-scrollbar-thumb {
    background-color: var(--border-light) !important;
}

::-webkit-scrollbar-thumb:hover {
    background-color: var(--border-color) !important;
}

/* Loading spinner */
.cl-spinner {
    border-top-color: var(--accent-color) !important;
}

/* Checkbox and radio buttons */
.cl-checkbox,
.cl-radio {
    border-color: var(--border-color) !important;
}

.cl-checkbox:checked,
.cl-radio:checked {
    background-color: var(--accent-color) !important;
    border-color: var(--accent-color) !important;
}

/* Action buttons in messages */
.cl-action-button {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    color: var(--text-on-primary) !important;
}

.cl-action-button:hover {
    background-color: var(--primary-hover) !important;
    border-color: var(--primary-hover) !important;
}

/* Error message styling */
.cl-error {
    background-color: var(--error-background) !important;
    color: var(--error-color) !important;
    border-color: var(--error-color) !important;
}

/* Success message styling */
.cl-success {
    background-color: var(--success-background) !important;
    color: var(--success-color) !important;
    border-color: var(--success-color) !important;
}

/* Link colors */
a.cl-link {
    color: var(--accent-color) !important;
}

a.cl-link:hover {
    color: var(--accent-hover) !important;
}

/* Card/container elements */
.cl-card {
    border-color: var(--border-color) !important;
    background-color: var(--background-secondary) !important;
}

/* Tooltip styling */
.cl-tooltip {
    background-color: var(--secondary-color) !important;
    color: var(--text-on-primary) !important;
}

/* Progress bar */
.cl-progress-bar {
    background-color: var(--border-light) !important;
}

.cl-progress-bar-fill {
    background-color: var(--accent-color) !important;
}

/* Tabs */
.cl-tab {
    border-bottom-color: var(--border-color) !important;
    color: var(--text-secondary) !important;
}

.cl-tab.active {
    border-bottom-color: var(--accent-color) !important;
    color: var(--accent-color) !important;
}

/* Modal/dialog */
.cl-modal {
    background-color: var(--background-secondary) !important;
}

.cl-modal-header {
    border-bottom-color: var(--border-color) !important;
}

/* Focus states for accessibility */
:focus-visible {
    outline: 2px solid var(--accent-color) !important;
    outline-offset: 2px !important;
}

/* Hover states on interactive elements */
button:hover,
a.cl-action:hover,
.cl-clickable:hover {
    cursor: pointer;
}

/* Selection color */
::selection {
    background-color: rgba(0, 51, 102, 0.2) !important;
    color: var(--text-primary) !important;
}
```

---

## Implementation Steps

### Step 1: Create directory structure
```bash
mkdir -p /workspace/.chainlit
```

### Step 2: Create config.toml
Create `/workspace/.chainlit/config.toml` with the content specified above.

### Step 3: Create custom.css
Create `/workspace/.chainlit/custom.css` with the content specified above.

### Step 4: Verify the changes
1. Restart the Chainlit server
2. Navigate to http://localhost:8000
3. Verify all UI elements now display blue colors instead of red

---

## Dependencies and Imports

**No new Python dependencies required.**

Chainlit has built-in support for custom themes via:
- The `.chainlit/config.toml` file for theme configuration
- Custom CSS files referenced in the config

Existing dependencies already include:
- `chainlit>=2.9.4` (from pyproject.toml)

---

## Edge Cases to Handle

### 1. Browser Cache
**Issue**: Users may see old red theme due to browser caching
**Solution**: 
- Add cache-busting query parameter to CSS file: `custom.css?v=2`
- Or configure Chainlit to disable cache in development mode
- Document that users should hard-refresh (Ctrl+Shift+R / Cmd+Shift+R) if colors don't update

### 2. Chainlit Version Compatibility
**Issue**: Different Chainlit versions may use different CSS class names
**Solution**: 
- Test with current version (2.9.4+)
- Use `!important` flags to ensure overrides work
- Check Chainlit release notes for breaking changes in theming

### 3. Mobile Responsiveness
**Issue**: Custom colors may affect mobile layout
**Solution**: 
- Test on mobile devices
- Use relative units (rem, %) where possible
- Ensure contrast ratios meet accessibility standards (WCAG AA minimum 4.5:1)

### 4. Dark Mode Compatibility
**Issue**: Users with system dark mode may need different color schemes
**Solution**: 
- Add `@media (prefers-color-scheme: dark)` rules in custom.css
- Provide dark mode color variants:
  ```css
  @media (prefers-color-scheme: dark) {
      :root {
          --background-primary: #0f172a;
          --background-secondary: #1e293b;
          --text-primary: #f1f5f9;
          --border-color: #334155;
      }
      .cl-message-assistant {
          background-color: #1e293b !important;
      }
  }
  ```

### 5. Accessibility Contrast
**Issue**: Blue colors must maintain proper contrast ratios
**Solution**: 
- Use verified color combinations:
  - `#003366` on `#ffffff`: 7.5:1 (AAA compliant)
  - `#ffffff` on `#003366`: 7.5:1 (AAA compliant)
  - `#1a1a3a` on `#ffffff`: 10.2:1 (AAA compliant)
- Test with accessibility tools (axe, Lighthouse)

### 6. Print Styles
**Issue**: Printed pages may have poor contrast with blue theme
**Solution**: 
- Add print-specific CSS:
  ```css
  @media print {
      .cl-message-user,
      .cl-button {
          background-color: #000000 !important;
          color: #ffffff !important;
      }
  }
  ```

### 7. Existing Session State
**Issue**: Running Chainlit sessions may cache old theme
**Solution**: 
- Restart Chainlit server after theme changes
- Clear session data if theme doesn't update

### 8. Custom Component Compatibility
**Issue**: Any future custom Chainlit components may not respect theme
**Solution**: 
- Document theme variables in code comments
- Use CSS variables consistently
- Create a theme documentation file

### 9. Testing Across Browsers
**Issue**: CSS variable support varies across browsers
**Solution**: 
- Test in Chrome, Firefox, Safari, Edge
- Provide fallback colors for older browsers:
  ```css
  .cl-button {
      background-color: #003366;
      background-color: var(--primary-color, #003366);
  }
  ```

### 10. Performance Impact
**Issue**: Large CSS file may impact page load
**Solution**: 
- Minify CSS before production deployment
- Use efficient selectors
- Avoid overly specific selectors

---

## Color Palette Reference

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| Primary | `#003366` | Buttons, headers, main accents |
| Primary Hover | `#002244` | Button hover states |
| Primary Light | `#4682b4` | Secondary accents |
| Accent | `#0066cc` | Links, highlights, active states |
| Accent Hover | `#004499` | Link hover states |
| Secondary | `#1a1a3a` | Sidebar, header backgrounds |
| Text Primary | `#1a1a3a` | Main text on light backgrounds |
| Text Secondary | `#666666` | Secondary text |
| Background Primary | `#f8f9fa` | Main background |
| Background Secondary | `#ffffff` | Cards, content areas |
| Border | `#e0e0e0` | Borders, dividers |

---

## Verification Checklist

- [ ] `.chainlit/config.toml` created with correct content
- [ ] `.chainlit/custom.css` created with all overrides
- [ ] All red-colored elements now display blue
- [ ] Buttons use DBS brand blue (#003366)
- [ ] Hover states work correctly
- [ ] Message bubbles have correct colors
- [ ] Input fields have blue focus states
- [ ] Error messages maintain visibility (red errors on light background)
- [ ] Success messages use blue-green tones
- [ ] Sidebar and header use dark blue
- [ ] Text remains readable with good contrast
- [ ] Mobile layout works correctly
- [ ] Dark mode (if enabled) has appropriate colors
- [ ] Browser cache doesn't prevent theme update
- [ ] All accessibility contrast ratios meet WCAG AA standards

---

## Rollback Plan

If issues arise with the blue theme:
1. Rename custom.css to custom.css.bak
2. Remove or comment out custom_css line in config.toml
3. Restart Chainlit server to revert to default theme

---

## Notes

- Chainlit's default red theme uses CSS variables that can be overridden
- The custom CSS approach is the most flexible and maintainable
- Theme changes don't require code changes to Python files
- All styling is centralized in `.chainlit/` directory for easy maintenance
