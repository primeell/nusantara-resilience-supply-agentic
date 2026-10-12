# NSRA Control Tower Design System

## Product posture

NSRA is an internal decision-support workspace for supply planners and operations
managers. It must feel like durable line-of-business software, not a marketing
site, pitch deck, or competition prototype.

## Visual direction

- Style: data-dense dashboard + restrained Swiss minimalism.
- Mode: light-first, with high-contrast graphite navigation and neutral surfaces.
- Density: 8/10. Motion: 2/10. Variance: 3/10.
- No gradients, glass effects, glow, decorative charts, oversized KPI cards, or
  floating bento tiles.
- Structure: 240 px adaptive sidebar, 56 px top bar, 12-column content grid,
  compact 36-44 px data rows, and 8 px spacing rhythm.

## Semantic tokens

| Role | Token | Value |
|---|---|---|
| Canvas | `--canvas` | `#F4F5F7` |
| Surface | `--surface` | `#FFFFFF` |
| Raised surface | `--surface-raised` | `#FFFFFF` |
| Subtle surface | `--surface-subtle` | `#F8F9FB` |
| Sidebar | `--sidebar` | `#17191E` |
| Primary text | `--text` | `#171A21` |
| Secondary text | `--text-muted` | `#5F6673` |
| Muted on dark | `--sidebar-muted` | `#A4A9B3` |
| Border | `--border` | `#E1E4E8` |
| Strong border | `--border-strong` | `#C9CED6` |
| Primary action | `--accent` | `#2457D6` |
| Accent soft | `--accent-soft` | `#EDF2FF` |
| Critical | `--critical` | `#B42318` |
| Warning | `--warning` | `#9A6700` |
| Success | `--success` | `#18794E` |
| Info | `--info` | `#3B5CCC` |

Status color is always paired with a visible text label or icon. It never carries
meaning alone.

## Typography

- Font stack: `Inter`, `Segoe UI`, `system-ui`, sans-serif. No network font
  dependency.
- Type scale: 12 / 14 / 16 / 18 / 24 / 32 px.
- Body: 14 px desktop, 16 px form controls on mobile.
- Numeric values and IDs use tabular figures; IDs may use the system monospace
  stack where scanning benefits.
- Heading hierarchy stays sequential and prose measures stay below 75 characters.

## Components

- Buttons use 8 px radius and a minimum 40 px desktop / 44 px mobile target.
- Cards use 10-12 px radius, a visible 1 px border, and at most one subtle shadow
  elevation. No hover lift or scale.
- The selected incident uses a left accent rail plus a stronger background; it is
  not indicated by color alone.
- KPI summaries use dividers within one strip instead of separate oversized cards.
- Scenario comparison defaults to a precise table. The recommended row has an
  explicit `Recommended` label and does not rely on green fill alone.
- Dialogs use native `<dialog>`, visible labels, inline error feedback, explicit
  close actions, and focus restoration.
- Loading uses stable skeleton geometry and busy button labels to avoid layout
  shift.

## Information architecture

1. Incident queue and filters.
2. Selected incident context.
3. Recommended response and operational impact.
4. Scenario comparison and supporting evidence.
5. Response package and human approval.
6. Audit history.

Development metadata is secondary and lives in Environment details. Synthetic
fixtures and disabled ERP writeback must remain honest, but they must not become
the product's primary visual identity.

## Responsive behavior

- `>= 1200 px`: fixed 240 px sidebar; incident queue and detail workspace share
  the primary grid.
- `768-1199 px`: 208 px sidebar; queue stacks above detail when necessary.
- `< 768 px`: sidebar becomes a modal drawer; content is single-column; wide data
  tables become labeled scenario cards rather than forcing horizontal scroll.
- Verify at 375, 768, 1024, and 1440 px, plus reduced-motion mode.

## Accessibility and motion

- Text contrast is at least 4.5:1; meaningful boundaries/icons at least 3:1.
- All controls have visible `:focus-visible` rings and full keyboard operation.
- Include a skip link, logical headings, native buttons/links/forms, and live
  regions for async status.
- Use a single outline SVG icon language with 1.75 px stroke. Decorative icons are
  `aria-hidden`.
- Motion only explains state changes, uses opacity/transform, and is disabled by
  `prefers-reduced-motion`.
