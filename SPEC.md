# Implementation Spec: UI Color Theme Change (Red to Blue)

## Overview
Change the Chainlit UI color theme from the default red accent colors to a blue color scheme for the DBS Banking Assistant application.

## Background
The current application uses Chainlit's default theme which features red accent colors. Chainlit v2.x supports custom theming through CSS overrides and configuration files. The default red colors appear in buttons, action elements, borders, and other UI components.

## Files to Modify

### 1. CREATE: `/workspace/ui/custom_theme.css`
**Purpose**: New CSS file containing blue theme color overrides for Chainlit UI elements.

**Content to Add**:
```css
/* Custom Blue Theme for DBS Banking Assistant */
/* Overrides Chainlit's default red color scheme */

/* Primary Action Buttons */
.cl-action-button {
    background-color: #0066CC !important;
    border-color: #0066CC !important;
    color: white !important;
}

.cl-action-button:hover {
    background-color: #0052A3 !important;
    border-color: #0052A3 !important;
}

.cl-action-button:active {
    background-color: #004488 !important;
}

/* Secondary/Alt Buttons */
.cl-button {
    background-color: #E6F0FF !important;
    border-color: #0066CC !important;
    color: #0066CC !important;
}

.cl-button:hover {
    background-color: #CCE0FF !important;
    border-color: #0052A3 !important;
}

/* Success/Primary State Colors */
.cl-success {
    background-color: #0066CC !important;
    color: white !important;
}

/* Error State - Keep red for errors but use blue-ish red */
.cl-error {
    background-color: #CC0033 !important;
    border-color: #CC0033 !important;
}

/* Info/Accent Colors */
.cl-info {
    background-color: #0066CC !important;
    color: white !important;
}

/* Border Colors */
.cl-border {
    border-color: #0066CC !important;
}

/* Input Focus States */
.cl-input:focus {
    border-color: #0066CC !important;
    box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.2) !important;
}

/* Scrollbar Styling */
::-webkit-scrollbar-thumb {
    background-color: #0066CC !important;
}

::-webkit-scrollbar-thumb:hover {
    background-color: #0052A3 !important;
}

/* Message Bubble Colors - User */
.cl-user-message {
    background-color: #E6F0FF !important;
    border-left-color: #0066CC !important;
}

/* Message Bubble Colors - Assistant */
.cl-assistant-message {
    background-color: #F0F4FF !important;
    border-left-color: #0066CC !important;
}

/* Sidebar/Navigation Colors */
.cl-sidebar {
    background-color: #F8F9FF !important;
}

.cl-sidebar-item:hover {
    background-color: #E6F0FF !important;
    color: #0066CC !important;
}

.cl-sidebar-item.active {
    background-color: #0066CC !important;
    color: white !important;
}

/* Chat Input Area */
.cl-chat-input {
    border-color: #0066CC !important;
}

.cl-chat-input:focus-within {
    border-color: #0066CC !important;
    box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1) !important;
}

/* Send Button */
.cl-send-button {
    background-color: #0066CC !important;
    color: white !important;
}

.cl-send-button:hover {
    background-color: #0052A3 !important;
}

/* Loaders/Spinners */
.cl-loader {
    color: #0066CC !important;
}

.cl-spinner {
    border-top-color: #0066CC !important;
}

/* Tooltip Colors */
.cl-tooltip {
    background-color: #0066CC !important;
    color: white !important;
}

/* Card/Container Borders */
.cl-card {
    border-color: #0066CC20 !important;
}

/* Link Colors */
a {
    color: #0066CC !important;
}

a:hover {
    color: #0052A3 !important;
    text-decoration: underline !important;
}

/* Code Block Accents */
pre {
    border-left-color: #0066CC !important;
    background-color: #F8F9FF !important;
}

/* File Upload Zone */
.cl-upload-zone {
    border-color: #0066CC !important;
    background-color: #F8F9FF !important;
}

.cl-upload-zone:hover {
    border-color: #0052A3 !important;
    background-color: #E6F0FF !important;
}

/* Modal/Dialog Colors */
.cl-modal {
    border-color: #0066CC !important;
}

.cl-modal-header {
    background-color: #0066CC !important;
    color: white !important;
}

/* Toggle/Switch Components */
.cl-toggle {
    background-color: #0066CC !important;
}

.cl-toggle:disabled {
    background-color: #99CCFF !important;
}

/* Progress Bar */
.cl-progress-bar {
    background-color: #0066CC !important;
}

/* Notification Badges */
.cl-badge {
    background-color: #0066CC !important;
    color: white !important;
}

/* DBS Branding - Blue Accent */
.dbs-brand {
    color: #0066CC !important;
}

/* DBS Primary Blue: #0066CC (DBS Brand Blue) */
/* DBS Secondary Blue: #0052A3 (Darker for hover) */
/* DBS Light Blue: #E6F0FF (Light background) */
/* DBS Ultra Light Blue: #F8F9FF (Subtle background) */
```

---

### 2. MODIFY: `/workspace/ui/chainlit_app.py`
**Purpose**: Configure Chainlit to use the custom CSS theme file.

**Changes Required**:

1. **Add CSS import at the top of the file** (after existing imports, before component initialization):
```python
# Add custom theme CSS
import chainlit as cl

# Configure custom theme
cl.set_theme(
    name="DBS Blue Theme",
    primary_hue="blue",
    primary_color="#0066CC",
    background_color="#FFFFFF",
    secondary_background_color="#F8F9FF",
    text_color="#1A1A1A",
    secondary_text_color="#4A4A4A",
    border_color="#0066CC",
    button_primary_background="#0066CC",
    button_primary_text="#FFFFFF",
    button_secondary_background="#E6F0FF",
    button_secondary_text="#0066CC",
    accent_color="#0066CC",
    success_color="#0066CC",
    error_color="#CC0033",
    info_color="#0066CC",
    warning_color="#FF9900"
)

# OR Alternatively, load custom CSS
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Existing auth logic
    pass
```

2. **Add CSS file reference in the `start()` function**:
```python
@cl.on_chat_start
async def start():
    """Initialize chat session"""
    # Load custom theme CSS
    with open("custom_theme.css", "r") as f:
        clCSS = f.read()
    await cl.StaticFile(path="custom_theme.css", content=clCSS).send()
    
    # Rest of existing code...
```

---

### 3. MODIFY: `/workspace/ui/chainlit.md`
**Purpose**: Add theme configuration metadata to the Chainlit markdown file.

**Changes Required**:

Add theme configuration at the top of the file:
```markdown
---
theme:
  name: DBS Blue Theme
  primary_hue: blue
  primary_color: "#0066CC"
  background_color: "#FFFFFF"
  secondary_background_color: "#F8F9FF"
  text_color: "#1A1A1A"
  border_color: "#0066CC"
---

# Welcome to DBS Banking Assistant! 🚀💙

... (rest of existing content)
```

---

## New Dependencies
None required. Uses existing Chainlit framework capabilities.

## Implementation Notes

### Color Palette Definition
The blue theme uses the following color palette:

| Color | Hex Code | Usage |
|-------|----------|-------|
| DBS Blue (Primary) | `#0066CC` | Primary actions, buttons, accents |
| DBS Dark Blue | `#0052A3` | Hover states |
| DBS Ultra Dark Blue | `#004488` | Active/pressed states |
| DBS Light Blue | `#E6F0FF` | Light backgrounds, secondary buttons |
| DBS Ultra Light Blue | `#F8F9FF` | Subtle backgrounds |
| DBS Brand Blue | `#0066CC` | Brand identity |
| Error Red | `#CC0033` | Error states (kept red for visibility) |

### Chainlit Theme Configuration Methods

**Method 1: Programmatic Configuration (Recommended)**
```python
cl.set_theme(...)  # In chainlit_app.py
```

**Method 2: YAML Front Matter**
```markdown
---
theme: {...}
---
```

**Method 3: Custom CSS File (Fallback)**
Create `custom_theme.css` and reference it in the application.

---

## Edge Cases to Handle

### 1. **CSS Specificity Conflicts**
- Chainlit's default styles may have high specificity
- Solution: Use `!important` flag on custom styles and specific selectors
- Test all UI components after implementation

### 2. **Dark Mode Compatibility**
- Chainlit may have dark mode support
- Solution: Include dark mode variants in CSS:
  ```css
  @media (prefers-color-scheme: dark) {
      .cl-user-message { background-color: #004488 !important; }
      /* Other dark mode adjustments */
  }
  ```

### 3. **Browser Compatibility**
- Ensure CSS works across modern browsers
- Solution: Use standard CSS properties with vendor prefixes where needed
- Test on Chrome, Firefox, Safari, Edge

### 4. **Mobile Responsiveness**
- Theme colors should work well on mobile devices
- Solution: Test on mobile viewports and ensure readability
- Blue theme should maintain contrast ratios for accessibility

### 5. **Existing Custom Styles**
- Check if any existing custom styles need updating
- Solution: Audit all CSS and ensure blue theme overrides are comprehensive

### 6. **Third-party Component Colors**
- LangWatch and other integrations may have their own styling
- Solution: Add specific overrides for third-party component classes if needed

### 7. **Color Blindness Accessibility**
- Ensure blue theme is accessible to color-blind users
- Solution: 
  - Use color AND non-color indicators (icons, text)
  - Maintain minimum contrast ratio of 4.5:1 for normal text
  - Test with color blindness simulators
  - DBS Blue (#0066CC) has good contrast with white (#FFFFFF): 7.5:1

### 8. **Caching Issues**
- Browser may cache old CSS
- Solution: Add version query parameter or use cache-busting technique:
  ```css
  /* custom_theme.css?v=1.0 */
  ```

### 9. **Chainlit Version Compatibility**
- Current project uses chainlit>=2.9.4
- Solution: Verify theme API compatibility with version 2.9.4+
- If `cl.set_theme()` not available, use CSS override approach

### 10. **Fallback for Missing CSS**
- If CSS file not found, app should still work
- Solution: Wrap CSS loading in try-except block:
  ```python
  try:
      with open("custom_theme.css", "r") as f:
          clCSS = f.read()
      await cl.StaticFile(path="custom_theme.css", content=clCSS).send()
  except FileNotFoundError:
      print("Custom theme CSS not found, using default theme")
  ```

---

## Testing Checklist

- [ ] All buttons show blue color (#0066CC) instead of red
- [ ] Hover states work correctly with darker blue
- [ ] Message bubbles use blue accent borders
- [ ] Input focus states show blue border/glow
- [ ] Scrollbars use blue color
- [ ] Sidebar navigation uses blue highlight
- [ ] Error messages remain visible (red error color preserved)
- [ ] Links use blue color
- [ ] Loading spinners use blue color
- [ ] Theme works in both light and dark modes
- [ ] Theme is responsive on mobile devices
- [ ] Accessibility contrast ratios meet WCAG standards
- [ ] All existing functionality still works
- [ ] No JavaScript errors in console
- [ ] No CSS conflicts causing layout issues

---

## Rollback Plan

If issues are discovered:
1. Remove or comment out `cl.set_theme()` call
2. Remove or rename `custom_theme.css`
3. Revert `chainlit.md` to original state
4. Restart Chainlit server

---

## References

- Chainlit Documentation: https://docs.chainlit.io
- DBS Brand Colors: https://www.dbs.com/about-us/brand.html
- WCAG Contrast Guidelines: https://www.w3.org/WAI/WCAG21/quickref/#contrast
- CSS Color Accessibility: https://webaim.org/resources/contrastchecker/
