---
name: Corporate Intelligence System
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#434655'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0053db'
  primary: '#004ac6'
  on-primary: '#ffffff'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#b4c5ff'
  secondary: '#565e74'
  on-secondary: '#ffffff'
  secondary-container: '#dae2fd'
  on-secondary-container: '#5c647a'
  tertiary: '#46566c'
  on-tertiary: '#ffffff'
  tertiary-container: '#5e6e85'
  on-tertiary-container: '#e9f0ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#dae2fd'
  secondary-fixed-dim: '#bec6e0'
  on-secondary-fixed: '#131b2e'
  on-secondary-fixed-variant: '#3f465c'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: '1.5'
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.05em
  mono-data:
    fontFamily: monospace
    fontSize: 13px
    fontWeight: '400'
    lineHeight: '1.5'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-max: 1440px
  gutter: 24px
  margin-page: 40px
  space-xs: 4px
  space-sm: 8px
  space-md: 16px
  space-lg: 24px
  space-xl: 48px
---

## Brand & Style
The brand personality of this design system is rooted in **Precision, Efficiency, and Authority**. Designed for business professionals who navigate vast quantities of corporate data, the UI must evoke a sense of absolute reliability. 

The aesthetic follows a **Modern Corporate** approach blended with **Minimalism**. It prioritizes high signal-to-noise ratios, utilizing generous whitespace to prevent cognitive overload. The visual language avoids decorative elements in favor of functional clarity, ensuring that the data—not the interface—remains the focus. The emotional response should be one of "effortless speed," where complex search queries feel light and instantaneous.

## Colors
The color strategy employs a "Data-First" philosophy. The palette is dominated by **Neutral Slates** and **Whites** to create a clean, institutional backdrop. 

- **Primary Action:** A vibrant Indigo-Blue (#2563EB) is used exclusively for primary actions, progress indicators, and active states to draw the eye without being distracting.
- **Surface Neutrals:** We use a tiered system of grays (Slate 50 to Slate 900). Backgrounds are kept at the lightest end of the spectrum to maximize contrast with text.
- **Deep Slate:** Used for primary navigation and high-level headers to provide a structural anchor to the interface.
- **Semantic Colors:** Success, Warning, and Error tones are used sparingly and with high saturation to ensure critical data states are immediately recognizable.

## Typography
This design system utilizes **Inter** for its exceptional legibility in data-heavy environments and its neutral, systematic character. 

- **Hierarchy:** We use a strict typographic scale. Headlines utilize tighter letter-spacing and heavier weights to feel "locked-in" and professional.
- **Labels:** To distinguish metadata from primary content, use the `label-caps` style. This adds a layer of professionalism and helps users scan tables quickly.
- **Readability:** Body text is set with a generous line height (1.5x - 1.6x) to ensure that long rows of corporate data remain easy to parse. For numerical data or IDs, a monospaced alternative can be used to ensure tabular alignment.

## Layout & Spacing
The layout philosophy centers on a **12-column fluid grid** that adapts to the user's screen but caps at a maximum width of 1440px for search result clarity.

- **Rhythm:** An 8px baseline grid governs all spatial relationships. Every margin and padding value must be a multiple of 8 (or 4 for micro-adjustments).
- **Density:** While the system is minimalist, it supports high-density views for data tables. Use `space-sm` for internal table padding and `space-lg` for card-to-card spacing.
- **Margins:** Page-level margins are generous (40px+) to frame the content and provide the "clean" corporate feel requested.

## Elevation & Depth
In this design system, depth is used to indicate interactivity and information priority. We move away from flat design toward a **Tonal Layering** approach.

- **Surface Levels:** The background is the lowest level (Slate 50). Primary content sits on white cards.
- **Ambient Shadows:** We use ultra-diffused, low-opacity shadows (e.g., `0 4px 20px rgba(15, 23, 42, 0.05)`). These shadows should feel like they are barely there, providing just enough lift to separate a card from the background.
- **Interactive Depth:** On hover, large action cards should subtly "lift" by increasing the shadow spread and reducing the Y-offset, creating a tactile response to user presence.
- **Borders:** Subtle 1px borders in Slate 200 are used to define boundaries where shadows might be too heavy, particularly in complex data tables.

## Shapes
The shape language is defined by **Roundedness Level 2**. This provides a modern, approachable feel while maintaining a professional corporate edge.

- **Standard Elements:** Buttons, input fields, and small chips use a 0.5rem (8px) radius.
- **Large Components:** Action cards and modal containers use a 1rem (16px) radius to soften the visual impact of large blocks of data.
- **Search Bars:** The primary fluid search input uses a 0.75rem (12px) radius to differentiate it from standard form fields.

## Components
Consistent implementation of components is critical for the "Speed and Clarity" focus of this design system.

- **Fluid Autocomplete Inputs:** The search bar should span the container width. The autocomplete dropdown uses a "Glassmorphism" hint with a heavy backdrop blur (20px) and a white semi-transparent fill to overlay existing data without losing context.
- **High-Contrast Tables:** Table headers should have a Slate 50 background with `label-caps` text. Alternate row striping is not used; instead, use subtle Slate 100 dividers and a strong Blue 600 vertical highlight on the "Active" or "Selected" row.
- **Large Action Cards:** These cards serve as entry points to deep data modules. They feature a large `headline-sm` title, a brief body description, and a primary indigo icon in the top right. They utilize the 1rem corner radius and ambient shadow.
- **Buttons:** 
  - *Primary:* Solid Indigo with white text. 
  - *Secondary:* White background with Slate 200 border and Slate 900 text.
  - *Ghost:* No background or border, Indigo text; used for secondary actions within tables.
- **Status Chips:** Small, pill-shaped indicators with low-opacity background tints (e.g., 10% opacity of the semantic color) and high-contrast text for status tracking.