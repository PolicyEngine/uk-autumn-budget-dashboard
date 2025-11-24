# UK Autumn Budget Dashboard - Analysis Scripts

This directory contains Python scripts for analyzing policy reforms using PolicyEngine UK.

## Setup

### Requirements
- Python 3.10+
- PolicyEngine UK (development version from `/Users/janansadeqian/policyengine-uk`)
- PolicyEngine UK data (`/Users/janansadeqian/policyengine-uk-data`)
- pandas, numpy

### Data Flow

```
Python Analysis Script → CSV Results → Dashboard
```

1. Run Python script to analyze a reform
2. Results are saved to `/public/data/reform-results.csv`
3. Dashboard reads CSV and displays results

## Available Scripts

### Two-Child Limit Reform
**File**: `two_child_limit_reform.py`

**Reform**: Removes the two-child benefit limit by setting child count to infinity

**Parameters**:
- `gov.dwp.tax_credits.child_tax_credit.limit.child_count`: ∞
- `gov.dwp.universal_credit.elements.child.limit.child_count`: ∞

**Metrics calculated**:
- ✅ Budgetary impact (2026-2029)
- ⏳ Distributional analysis (pending)
- ⏳ Household-level impacts (pending)
- ⏳ Geographic breakdown (pending)

**To run**:
```bash
cd /Users/janansadeqian/uk-autumn-budget-dashbaord/analysis
python two_child_limit_reform.py
```

**Results** (as of latest run):
- 2026: £2.82bn cost
- 2027: £3.02bn cost
- 2028: £3.27bn cost
- 2029: £3.37bn cost
- **Total**: £12.47bn cost (2026-2029)

## CSV Output Format

The unified results file (`/public/data/reform-results.csv`) has this structure:

```csv
reform_id,reform_name,metric_type,year,value,unit
two_child_limit,2 child limit reforms,budgetary_impact,2026,-2.816,GBP_billions
```

### Columns:
- `reform_id`: Policy ID (must match dashboard policy IDs)
- `reform_name`: Human-readable policy name
- `metric_type`: Type of metric (budgetary_impact, distributional_analysis, etc.)
- `year`: Year of the metric
- `value`: Numeric value
- `unit`: Unit of measurement

## Creating New Reform Analysis Scripts

### Template

```python
import os
import sys
sys.path.insert(0, '/Users/janansadeqian/policyengine-uk')

import numpy as np
import pandas as pd
from policyengine_uk import Microsimulation, Scenario
from policyengine_uk.data import UKSingleYearDataset

# Configuration
DATASET_PATH = "/Users/janansadeqian/policyengine-uk-data/policyengine_uk_data/storage/enhanced_frs_2023_24.h5"
OUTPUT_CSV = "/Users/janansadeqian/uk-autumn-budget-dashbaord/public/data/reform-results.csv"
REFORM_ID = "your_reform_id"  # Must match dashboard
REFORM_NAME = "Your Reform Name"
YEARS = [2026, 2027, 2028, 2029]

# Define reform scenario
scenario = Scenario(
    parameter_changes={
        "your.parameter.path": {
            "2026": new_value,
            "2027": new_value,
            "2028": new_value,
            "2029": new_value
        }
    }
)

# Create simulations
baseline = Microsimulation(dataset=dataset)
reformed = Microsimulation(dataset=dataset, scenario=scenario)

# Calculate and save results
# ... (see two_child_limit_reform.py for full example)
```

### Key Points:
1. Use the same `REFORM_ID` as defined in the dashboard (`DEFAULT_POLICIES` in App.jsx)
2. Set parameters for each year (2026-2029) explicitly
3. Load existing CSV and append new results (don't overwrite)
4. Use negative values for costs (reduces government balance)

## Dashboard Integration

The dashboard (`/src/App.jsx`):
- Reads `/data/reform-results.csv` on policy selection
- Shows real data when available
- Shows "No data available" for missing metrics
- Displays budgetary impact chart with real values

## Next Steps

To complete the dashboard, run analyses for:

1. **Two-child limit reform** ✅ (Done - budgetary impact only)
   - ⏳ Add distributional analysis
   - ⏳ Add household-level impacts

2. **VAT changes** (TBD)
   - Define reform parameters
   - Run analysis

3. **Freezing thresholds** (TBD)
   - Define reform parameters
   - Run analysis

4. **Fuel duty** (TBD)
   - Define reform parameters
   - Run analysis

5. **NI rates** (TBD)
   - Define reform parameters
   - Run analysis

6. **Income tax rates** (TBD)
   - Define reform parameters
   - Run analysis

## Troubleshooting

### Reform shows £0.00 impact
- Check parameter names are correct (use PolicyEngine UK parameter files)
- Ensure parameters are set for all years (2026-2029)
- Use `np.inf` for removing limits
- Run `test_two_child_limit.py` to verify reform is working

### CSV not loading in dashboard
- Check file path: `/public/data/reform-results.csv`
- Verify CSV format matches expected structure
- Check browser console for errors

### PolicyEngine errors
- Ensure local PolicyEngine UK installation is up to date
- Check dataset path is correct
- Verify Python environment has required packages

## Testing

Before running full analysis:
1. Use `test_two_child_limit.py` as a template
2. Verify parameter values changed in reformed simulation
3. Check benefit spending changes
4. Validate government balance impact

## Performance

- Full analysis takes 2-3 minutes per reform
- CSV file grows with each reform (append-only)
- Dashboard loads instantly (static CSV)
