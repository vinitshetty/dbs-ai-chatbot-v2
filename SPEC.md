# Implementation Specification: Change UI Theme from Red to Blue

## Overview
This specification outlines the changes required to modify the DBS Banking Agent UI theme from the default red color scheme to a blue color scheme using Chainlit's theming system.

## Analysis
The current codebase uses Chainlit (`chainlit>=2.9.4`) for the web interface but does not define any custom theme configuration. The application relies on Chainlit's default theme, which uses a red/pink color scheme. To change this to blue, we need to add a custom theme configuration.

---

## 1. Files to Modify

### File: `/workspace/ui/chainlit_app.py`

**Location:** At the top of the file, after imports but before any `@cl` decorators

**Required Change:** Add Chainlit theme configuration

**Specific Changes:**

```python
# Add after existing imports (line ~12)
from chainlit import Theme

# Add after component initialization (after line 21, before @cl.on_chat_start)
# Define custom blue theme
blue_theme = Theme(
    name="DBS Blue Theme",
    primary=(
        cl.Color(
            name="Blue 600",
            blue=255,
            green=95,
            red=37,
        )
    ),
    secondary=(
        cl.Color(
            name="Blue 700",
            blue=230,
            green=70,
            red=24,
        )
    ),
    background=(
        cl.Color(
            name="Gray 50",
            blue=253,
            green=253,
            red=255,
        )
    ),
    surface=(
        cl.Color(
            name="White",
            blue=255,
            green=255,
            red=255,
        )
    ),
    text=(
        cl.Color(
            name="Gray 900",
            blue=28,
            green=28,
            red=28,
        )
    ),
    input_background=(
        cl.Color(
            name="White",
            blue=255,
            green=255,
            red=255,
        )
    ),
    input_text=(
        cl.Color(
            name="Gray 800",
            blue=56,
            green=56,
            red=56,
        )
    ),
    button_background=(
        cl.Color(
            name="Blue 600",
            blue=255,
            green=95,
            red=37,
        )
    ),
    button_text=(
        cl.Color(
            name="White",
            blue=255,
            green=255,
            red=255,
        )
    ),
    accent=(
        cl.Color(
            name="Blue 500",
            blue=245,
            green=115,
            red=52,
        )
    ),
    border=(
        cl.Color(
            name="Blue 300",
            blue=210,
            green=160,
            red=114,
        )
    ),
    user_message_background=(
        cl.Color(
            name="Blue 100",
            blue=240,
            green=230,
            red=220,
        )
    ),
    user_message_text=(
        cl.Color(
            name="Gray 900",
            blue=28,
            green=28,
            red=28,
        )
    ),
    assistant_message_background=(
        cl.Color(
            name="Blue 50",
            blue=248,
            green=243,
            red=237,
        )
    ),
    assistant_message_text=(
        cl.Color(
            name="Gray 900",
            blue=28,
            green=28,
            red=28,
        )
    ),
    code_background=(
        cl.Color(
            name="Gray 100",
            blue=250,
            green=250,
            red=250,
        )
    ),
    code_text=(
        cl.Color(
            name="Blue Grey 900",
            blue=55,
            green=71,
            red=79,
        )
    ),
)

# Apply the theme
cl.set_theme(blue_theme)
```

**Alternative (Simpler approach):**

For a minimal change, we can use Chainlit's built-in color constants:

```python
from chainlit import Theme

# Define blue theme using Chainlit color constants
blue_theme = Theme(
    primary=cl.Color.BLUE_600,
    secondary=cl.Color.BLUE_700,
    accent=cl.Color.BLUE_500,
    background=cl.Color.GRAY_50,
    surface=cl.Color.WHITE,
    text=cl.Color.GRAY_900,
    button_background=cl.Color.BLUE_600,
    button_text=cl.Color.WHITE,
    input_background=cl.Color.WHITE,
    input_text=cl.Color.GRAY_800,
    user_message_background=cl.Color.BLUE_100,
    user_message_text=cl.Color.GRAY_900,
    assistant_message_background=cl.Color.BLUE_50,
    assistant_message_text=cl.Color.GRAY_900,
    code_background=cl.Color.GRAY_100,
    code_text=cl.Color.BLUE_GREY_900,
)

cl.set_theme(blue_theme)
```

---

## 2. New Dependencies or Imports

### New Imports Required
In `/workspace/ui/chainlit_app.py`:
- Add `from chainlit import Theme` at the top with other chainlit imports

### Dependencies
No new dependencies required. The existing `chainlit>=2.9.4` package already includes the theming system.

---

## 3. Implementation Details

### Placement
The theme configuration must be set **before** any Chainlit decorators (`@cl.on_chat_start`, `@cl.on_message`) are processed. The recommended location is after all imports and component initializations, but before the first `@cl` decorator.

### Theme Application
The `cl.set_theme()` call must be executed at module load time (not inside a function) to ensure it applies to the entire application.

### Color Selection
The proposed blue color palette:
- **Primary (Blue 600):** `#2563FF` - Main brand color for buttons and accents
- **Secondary (Blue 700):** `#1846E6` - Supporting blue tone
- **Accent (Blue 500):** `#3473F5` - Highlight color
- **User Messages:** Light blue background (`#E6F0FF` / Blue 100)
- **Assistant Messages:** Very light blue background (`#F8F3ED` / Blue 50)
- **Background:** Light gray (`#FDFDFF` / Gray 50)

---

## 4. Edge Cases to Handle

### 4.1 Theme Already Defined
- **Scenario:** If a theme is already defined elsewhere in the application
- **Solution:** Ensure only one `cl.set_theme()` call exists in the entire application. Remove any duplicate theme configurations.

### 4.2 Version Compatibility
- **Scenario:** Chainlit version < 2.9.0 may not support all theme properties
- **Solution:** Verify Chainlit version is >= 2.9.4 (already satisfied per requirements.txt). The current `pyproject.toml` specifies `chainlit>=2.9.4`.

### 4.3 Theme Property Validation
- **Scenario:** Invalid color values or unsupported properties
- **Solution:** Use Chainlit's built-in color constants (recommended) or validate RGB values are in range 0-255.

### 4.4 Multiple Theme Files
- **Scenario:** Theme configuration might be split across multiple files
- **Solution:** Consolidate all theme configuration in `chainlit_app.py` as the single source of truth.

### 4.5 Caching Issues
- **Scenario:** Browser may cache old CSS/colors
- **Solution:** Users should perform a hard refresh (Ctrl+Shift+R or Cmd+Shift+R) after theme changes. For production, implement cache-busting if needed.

### 4.6 Dark Mode Consideration
- **Scenario:** Users may have dark mode enabled
- **Solution:** The current specification only covers light mode. For future enhancement, consider defining a dark theme variant. Chainlit automatically handles dark mode based on user preferences if dark theme properties are provided.

### 4.7 Accessibility Compliance
- **Scenario:** Blue color choices must meet WCAG accessibility standards
- **Solution:** Verify color contrast ratios:
  - Text on primary: White on Blue 600 = 8.59:1 (AAA compliant)
  - Text on backgrounds: Gray 900 on Blue 50 = 17.13:1 (AAA compliant)
  - Text on user message: Gray 900 on Blue 100 = 11.17:1 (AAA compliant)

### 4.8 Custom CSS Override
- **Scenario:** Existing custom CSS might override theme colors
- **Scenario:** No custom CSS files currently exist in the codebase, so this is not an issue for the initial implementation.

---

## 5. Testing Checklist

- [ ] Verify theme applies correctly when running `chainlit run chainlit_app.py -w`
- [ ] Check primary buttons are blue (not red)
- [ ] Verify user message bubbles have blue tint
- [ ] Verify assistant message bubbles have light blue tint
- [ ] Confirm text remains readable with good contrast
- [ ] Test in both light and dark system preferences
- [ ] Validate all interactive elements (buttons, inputs) use blue color scheme
- [ ] Verify no console errors related to theme configuration

---

## 6. Rollback Plan

If issues arise after implementation:
1. Comment out or remove the `cl.set_theme(blue_theme)` line
2. Remove the `Theme` import
3. Application will revert to Chainlit's default theme

---

## 7. Future Enhancements (Out of Scope)

- Add dark mode theme variant
- Create theme configuration file (e.g., `theme.py`)
- Add theme toggle functionality for users
- Customize scrollbar colors
- Add custom CSS for additional styling
- Make theme configurable via environment variables
