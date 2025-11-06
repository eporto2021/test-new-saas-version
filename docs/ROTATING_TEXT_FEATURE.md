# Rotating Text Feature

## Overview

The CTA (Call-to-Action) section now has a rotating text animation that cycles through different words.

## Location

**Template:** `templates/web/components/cta.html`  
**Configuration:** `test/settings.py` → `PROJECT_METADATA['ROTATING_WORDS']`

## Current Text

```
Ready to implement software for your business?
Save [money/time/headaches/resources/effort/stress], time and headaches.
       ↑ This word rotates every 2 seconds
```

## How to Edit the Rotating Words

### 1. Edit the Words List

Open `test/settings.py` and modify the `ROTATING_WORDS` list:

```python
PROJECT_METADATA = {
    "NAME": gettext_lazy("Eporto"),
    "URL": "http://localhost:8000",
    "DESCRIPTION": gettext_lazy("Software solutions for your business"),
    "IMAGE": "https://upload.wikimedia.org/wikipedia/commons/2/20/PEO-pegasus_black.svg",
    "KEYWORDS": "SaaS, django",
    "CONTACT_EMAIL": "maxdavenport96@gmail.com",
    "ROTATING_WORDS": ["money", "time", "headaches", "resources", "effort", "stress"],
    #                  ↑ Add, remove, or reorder words here
}
```

### 2. Examples of Custom Word Lists

**For a productivity app:**
```python
"ROTATING_WORDS": ["time", "effort", "money", "stress", "hassle"]
```

**For a data/analytics app:**
```python
"ROTATING_WORDS": ["data", "insights", "reports", "analytics", "complexity"]
```

**For a business automation app:**
```python
"ROTATING_WORDS": ["manual work", "errors", "delays", "overhead", "inefficiency"]
```

**For your logistics business:**
```python
"ROTATING_WORDS": ["scheduling time", "route planning", "manual errors", "delivery delays", "operational costs"]
```

## How It Works

### Animation Details

- **Rotation Speed**: Changes every 2 seconds (2000ms)
- **Transition Effect**: 
  - Fades out (opacity to 0)
  - Moves up slightly (translateY -10px)
  - Changes word
  - Fades back in
  - Returns to position
- **Transition Duration**: 300ms

### Customizing Animation Speed

Edit line 36 in `templates/web/components/cta.html`:

```javascript
}, 2000); // Change word every 2 seconds
   ↑ Change this number (in milliseconds)
```

Examples:
- `1000` = 1 second (fast)
- `2000` = 2 seconds (default)
- `3000` = 3 seconds (slower)
- `5000` = 5 seconds (very slow)

### Customizing Transition Effect

Edit line 25 in `templates/web/components/cta.html`:

```javascript
rotatingElement.style.transform = 'translateY(-10px)';
//                                           ↑ Change distance
```

Options:
- `translateY(-10px)` - Moves up
- `translateY(10px)` - Moves down
- `translateX(10px)` - Slides right
- `scale(0.9)` - Shrinks
- `rotate(10deg)` - Rotates

## Technical Implementation

### HTML Structure

```html
<span id="rotating-word" class="inline-block min-w-[120px]">money</span>
```

- `id="rotating-word"` - JavaScript targets this element
- `inline-block` - Allows transformations
- `min-w-[120px]` - Prevents layout shift when words change length

### JavaScript Logic

1. Loads words from `PROJECT_METADATA['ROTATING_WORDS']`
2. Sets up interval timer
3. Fades out current word
4. Changes to next word in array
5. Fades in new word
6. Loops back to first word after reaching the end

### CSS Transitions

```css
#rotating-word {
  transition: opacity 0.3s ease-in-out, transform 0.3s ease-in-out;
  display: inline-block;
}
```

## Where This Appears

The CTA section appears on:
- Landing page (for non-logged-in users)
- Various marketing pages

## Troubleshooting

### Words not rotating?

1. Check browser console for JavaScript errors
2. Verify `PROJECT_METADATA['ROTATING_WORDS']` exists in settings
3. Make sure the CTA component is included in your page
4. Clear browser cache and refresh

### Layout jumping when words change?

Adjust the `min-w-[120px]` value to accommodate your longest word:

```html
<span id="rotating-word" class="inline-block min-w-[200px]">money</span>
<!--                                            ↑ Increase this -->
```

### Animation too fast/slow?

Change the interval value (currently 2000ms = 2 seconds)

## Future Enhancements

Possible improvements:
- Add different animations (slide, bounce, flip)
- Make animation speed configurable via settings
- Add pause on hover
- Random word order instead of sequential
- Different word lists for different pages

## File Locations

**Settings:**
- `test/settings.py` (line 461)
- `test/settings_production.py` (add override here for production)

**Template:**
- `templates/web/components/cta.html` (lines 5, 15-46)

## Example: Production Override

In `test/settings_production.py`, add:

```python
PROJECT_METADATA = {
    # ... other metadata ...
    "ROTATING_WORDS": ["costs", "complexity", "inefficiency", "manual work", "overhead"],
}
```

This will merge with or override the development settings when in production mode.
