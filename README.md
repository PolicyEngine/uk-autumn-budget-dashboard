# UK Autumn Budget 2025 Dashboard

A web application for analysing the impact of UK Autumn Budget 2025 policies on households and public finances, powered by [PolicyEngine UK](https://policyengine.org/uk).

## Features

- **Interactive policy selection**: Choose from various budget policy options
- **Configurable parameters**: Adjust policy parameters (rates, thresholds, years)
- **Real-time analysis**: Automatic calculations when policies are selected or modified
- **Rich visualisations**: Charts showing budgetary impact, poverty effects, and distributional analysis
- **URL sharing**: Share specific policy configurations via URL parameters
- **Data export**: Download analysis results in TXT format

## Getting started

### Prerequisites

- Node.js 20.x or higher
- npm 11.x or higher

### Installation

```bash
npm install
```

### Development

Run the development server:

```bash
npm run dev
```

The dashboard will be available at `http://localhost:5173`

### Building for production

```bash
npm run build
```

Preview the production build:

```bash
npm preview
```

## Project structure

```
src/
├── App.jsx              # Main application controller
├── App.css              # App-level styles
├── main.jsx             # Entry point
├── index.css            # Global styles
└── components/
    ├── Sidebar.jsx      # Policy selection & parameter controls
    ├── Sidebar.css
    ├── Results.jsx      # Charts & analysis display
    └── Results.css

.claude/
└── CLAUDE.md            # Comprehensive style & architecture guide
```

## Default policies

The dashboard includes these placeholder policy options:

1. **Personal allowance freeze extension** - Extend income tax threshold freeze
2. **National Insurance rate changes** - Adjust NI contribution rates
3. **VAT rate adjustment** - Change standard VAT rate
4. **Corporation tax changes** - Adjust main corporation tax rate
5. **Fuel duty changes** - End or modify fuel duty freeze
6. **Pension tax relief reform** - Modify pension contribution tax relief

## PolicyEngine integration

The dashboard is ready to integrate with PolicyEngine UK API. Once the Autumn Budget 2025 is announced:

1. Replace mock data in `App.jsx` with actual PolicyEngine API calls
2. Update policy definitions to match announced budget measures
3. Add CSV data files to `/public/data/` for detailed results

## Technology stack

- **Framework**: React 18.3 with Vite
- **Charts**: Recharts 2.15 (built on D3)
- **State management**: React hooks (useState, useEffect, useMemo)
- **Styling**: Custom CSS inspired by PolicyEngine UK two-child limit app
- **Typography**: Roboto font family (400, 500, 600, 700 weights)
- **Build tool**: Vite 5.4

## Design system

The dashboard uses PolicyEngine UK's design system:

- **Colour palette**:
  - Primary teal: `#319795`
  - Teal light: `#4db3b1`
  - Teal dark: `#277674`
  - Grey scale: `#f9fafb` to `#111827`

- **Typography**: Roboto font with multiple weights for clear hierarchy

- **Sidebar**: Beautiful gradient background (teal-dark to grey) with semi-transparent white policy cards

- **Charts**: Consistent teal colour scheme with proper tooltips and legends

- **Responsive**: Mobile-friendly design with breakpoints at 768px

## Style guide

See `.claude/CLAUDE.md` for comprehensive style and architecture guidelines including:

- Colour palette and typography
- Component patterns and React conventions
- Chart configuration best practices
- British English formatting rules
- Accessibility requirements

## Contributing

When contributing to this project, please follow the guidelines in `.claude/CLAUDE.md` to ensure consistency with the established design system and coding standards.

## Licence

This project is for policy analysis purposes. Data and analysis powered by PolicyEngine UK.
