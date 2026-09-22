---
name: Autonomous Governance & Telemetry
colors:
  surface: '#0f131d'
  surface-dim: '#0f131d'
  surface-bright: '#353944'
  surface-container-lowest: '#0a0e18'
  surface-container-low: '#171b26'
  surface-container: '#1c1f2a'
  surface-container-high: '#262a35'
  surface-container-highest: '#313540'
  on-surface: '#dfe2f1'
  on-surface-variant: '#bbcabf'
  inverse-surface: '#dfe2f1'
  inverse-on-surface: '#2c303b'
  outline: '#86948a'
  outline-variant: '#3c4a42'
  surface-tint: '#4edea3'
  primary: '#4edea3'
  on-primary: '#003824'
  primary-container: '#10b981'
  on-primary-container: '#00422b'
  inverse-primary: '#006c49'
  secondary: '#ffb2b7'
  on-secondary: '#67001b'
  secondary-container: '#b50036'
  on-secondary-container: '#ffc2c4'
  tertiary: '#ffb95f'
  on-tertiary: '#472a00'
  tertiary-container: '#e29100'
  on-tertiary-container: '#523200'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#6ffbbe'
  primary-fixed-dim: '#4edea3'
  on-primary-fixed: '#002113'
  on-primary-fixed-variant: '#005236'
  secondary-fixed: '#ffdadb'
  secondary-fixed-dim: '#ffb2b7'
  on-secondary-fixed: '#40000d'
  on-secondary-fixed-variant: '#92002a'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#0f131d'
  on-background: '#dfe2f1'
  surface-variant: '#313540'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-mono-lg:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-mono-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-mono-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style
The design system articulates an authoritative, mission-critical operational cockpit for high-throughput Agent-to-Agent (A2A) interactions. Targeting Enterprise Security Architects, Data Protection Officers, and AI Systems Engineers, the aesthetic projects unyielding technical precision, immediate compliance legibility, and zero visual ambiguity. 

The design narrative merges **Technical Minimalist Instrumentation** with high-density data visualization. Structural hierarchy is strictly defined by deep slate surfaces, subtle hairline borders, and semantically loaded high-contrast accents. Visual friction is eliminated to ensure cognitive focus remains on cross-border data movements, synthetic payload traces, and instant policy breach discovery.

## Colors
The palette is engineered for low-fatigue, continuous-monitoring environments in high-density enterprise operations centers.

- **Canvas & Background (`#0B0F19`)**: Deepest indigo-slate base providing infinite-contrast depth for data streams.
- **Surface Elevation (`#0F172A`)**: Layered container slate for cards, trace logs, and inspector panes.
- **Structural Lines (`#1E293B`)**: Crisp, hairline boundaries separating multi-agent runtime sessions.
- **Primary / Compliant EU Agent (`#10B981`)**: Emerald green signaling fully attested, GDPR/EDPB-cleared transactions and sovereign telemetry pipelines.
- **Secondary / Policy Violation (`#F43F5E`)**: High-saturation rose crimson reserved exclusively for policy breaches, cross-border leakage, unauthorized exfiltration, and immediate operational halts.
- **Tertiary / Non-Compliant Agent & Warning (`#F59E0B`)**: Amber gold signifying non-compliant or untrusted execution zones (e.g., untrusted nodes, synthetic fallback alerts, or missing cryptographic proofs).
- **Subdued Text / Inactive Borders (`#64748B`)**: Balanced cool gray for labels, payload structures, and trace metadata.
- **High-Readability Foreground (`#F8FAFC`)**: Ultra-bright slate for primary telemetry figures, status heads, and active node identifiers.

## Typography
Typographic discipline pairs the Swiss corporate clarity of **Inter** for user orchestration with the clinical, fixed-width precision of **JetBrains Mono** for payload traces, cryptographic hashes, model identifiers, and audit payloads.

- **Hierarchy Rules**: Primary labels, system stats, and metric units are set in tabular formatting with optical tracking pulled tight (`-0.01em` to `-0.02em`) on headings to optimize density.
- **Trace Typography**: Every machine-generated attribute—payload fragments, JSON keys, IP ranges, hash verifications, and compliance rule IDs—must use `JetBrains Mono` without exception.

## Layout & Spacing
The layout adheres to a flexible, 12-column modular grid on desktop and a vertical 4-column flow on mobile viewports.

- **Desktop (1280px+)**: A split-screen topology featuring a 320px persistent system inspector, an expandable central node-graph/flow area, and a 380px collapsible JSON audit trace inspector.
- **Tablet (768px - 1279px)**: Side-by-side agent cards with bottom-docked trace logs.
- **Mobile (320px - 767px)**: Linear stack layout. Complex flow diagrams collapse into sequential, card-based "Hop" steps with clear directional arrow badges (`Hop 1 (Agent 1) -> Hop 2 (Agent 2)`).
- **Rhythm**: Spacing follows a rigorous 4px baseline rhythm (`space-xs` = 4px, `space-sm` = 8px, `space-md` = 16px, `space-lg` = 24px, `space-xl` = 32px).

## Elevation & Depth
Elevation is rendered strictly via tonal surface shifts and hairline luminance boundaries rather than heavy drop shadows, preserving an authentic high-tech terminal feel.

- **Ground Tier**: Canvas background `#0B0F19` with a subtle 24px isometric dot grid overlay at 4% opacity.
- **Surface Tier (Cards, Pods)**: Solid `#0F172A` bound by a 1px solid border of `#1E293B`.
- **Raised Tier (Drawers, Tooltips, Context Modals)**: Solid `#1E293B` surrounded by a 1px border of `#334155` and a crisp, diffused ambient shadow (`0 12px 32px -4px rgba(0, 0, 0, 0.65)`).
- **Active / Alert Edge Highlights**: When an agent breaches policy, its container maintains a 1px perimeter glow (`box-shadow: 0 0 16px -2px rgba(244, 63, 94, 0.3)`) paired with a `#F43F5E` outline.

## Shapes
A controlled, soft border radius of `0.25rem` (4px) to `0.5rem` (8px) ensures modules and inputs feel engineered and structural. Status pills, flow indicator tags, and compliance badges utilize full capsule rounding (9999px) to establish immediate visual differentiation between structural layout containers and temporal status items.

## Components

### Buttons & Action Controls
- **Primary / Remediate**: `#10B981` background, `#0B0F19` bold typography, 6px border radius, subtle hover brighten.
- **Destructive / Block Agent**: `#F43F5E` background, `#FFFFFF` text, high-urgency states.
- **Secondary / Telemetry Action**: `#0F172A` background, 1px solid `#1E293B`, `#F8FAFC` text; transitions to `#1E293B` background on hover.

### Badges & Pill Indicators
- **Agent 1 Compliance Pill (EU)**: Capsule radius, emerald background at 10% opacity (`rgba(16, 185, 129, 0.1)`), 1px solid `#10B981`, `#10B981` monospace text with a pulsing 6px green status dot.
- **Agent 2 Risk Pill (South Asia/Non-Compliant)**: Capsule radius, amber background at 10% opacity (`rgba(245, 158, 11, 0.1)`), 1px solid `#F59E0B`, `#F59E0B` monospace text with a warning indicator.
- **Breach Tag**: Rose background at 15% opacity (`rgba(244, 63, 94, 0.15)`), 1px solid `#F43F5E`, `#F43F5E` bold monospace tag.

### Agent Flow Cards & Connectors
- **Cards**: Contain agent ID, host zone, cryptographic attestation status, and live output speed (tokens/sec).
- **Flow Connectors**: Thin lines (`#1E293B`) with directional SVG chevrons indicating transmission vector. When payloads transit between compliant and non-compliant contexts, the connector stroke alternates dynamically to animated dashed amber/rose gradients.

### Monospace Audit & Payload Inspector
- High-contrast syntax-highlighted block; background `#070A10`, border `#1E293B`. Key-value traces formatted with soft blue/slate properties and bright green/rose string assertions to highlight PII/GDPR anomalies instantly.

### Form Inputs & Search Filters
- Input fields leverage `#0B0F19` background, `#1E293B` hairline borders, and `JetBrains Mono` placeholder text with emerald active focus rings (`0 0 0 1px #10B981`).