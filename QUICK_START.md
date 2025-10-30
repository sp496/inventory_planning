# Quick Start Guide - Inventory Demand Generator

## Installation
```bash
# No installation needed! Just ensure you have pandas installed
pip install pandas openpyxl --break-system-packages
```

## 5-Minute Setup

### Step 1: Prepare Your Data Files
You need two Excel files:

**File 1: subject_summary.xlsx**
| Study Protocol | Subject Number | Site ID | Country | Subject Status | Randomized Treatment | TPC | Last Study Visit Recorded | Last Study Visit Date |
|---------------|----------------|---------|---------|----------------|---------------------|-----|--------------------------|---------------------|
| GS-US-592-6173 | 10663-106 | 10663 | Japan | Crossover Approved | TPC + Pembro | Nab-Paclitaxel 100 mg/m2 | Crossover Cycle 2 Day 1 | 2023-10-15 |

**File 2: drug_dispensation_qtys.xlsx**
| Study Protocol | Randomized Treatment | Subject Status | TPC | Study Drug Dispensed | Visit Days | Dispensing Quantity | Dispensing Frequency (Days) |
|---------------|---------------------|----------------|-----|---------------------|------------|-------------------|---------------------------|
| GS-US-592-6173 | TPC + Pembro | Crossover Approved | Nab-Paclitaxel 100 mg/m2 | Sacituzumab Govitecan | 1,8 | 4 | 21 |

### Step 2: Run the Code
```python
import pandas as pd
from inventory_demand_generator import InventoryDemandGenerator

# Load data
subjects = pd.read_excel('subject_summary.xlsx')
treatments = pd.read_excel('drug_dispensation_qtys.xlsx')

# Generate forecast
generator = InventoryDemandGenerator(subjects, treatments)
forecast = generator.generate_inventory_demand(months_ahead=12)

# Save results
generator.save_to_excel('my_forecast.xlsx')
```

### Step 3: View Results
Open `my_forecast.xlsx` - you'll see three sheets:
1. **Inventory Demand**: All projected visits
2. **Summary by Drug**: Totals per drug
3. **Summary by Month**: Monthly breakdown

## Common Scenarios

### Scenario A: Combination Therapy (2 drugs)
Create **TWO rows** in drug_dispensation_qtys.xlsx:
```
Row 1: ... | Sacituzumab Govitecan | 1,8 | 4 | 21
Row 2: ... | Pembrolizumab | 1,8 | 1 | 21
```
(Same matching criteria, different drugs)

### Scenario B: Crossover Patient
In subject_summary.xlsx:
- Subject Status: "Crossover Approved"
- TPC: Original drug (e.g., "Nab-Paclitaxel 100 mg/m2")

In drug_dispensation_qtys.xlsx:
- Subject Status: "Crossover Approved"
- TPC: Same original drug
- Study Drug Dispensed: "Sacituzumab Govitecan" ← New drug

### Scenario C: Multiple Visit Days
Use comma-separated days in drug_dispensation_qtys.xlsx:
- Visit Days: "1,8,15" (three visits per cycle)
- Visit Days: "1,8" (two visits per cycle)
- Visit Days: "1" (one visit per cycle)

## Quick Checks

### ✅ Check 1: Are patients matching?
```python
stats = generator.get_summary_statistics()
print(f"Unique patients with visits: {stats['unique_patients']}")
print(f"Total patients in data: {len(subjects)}")
```
If numbers don't match, some patients aren't matching treatment plans.

### ✅ Check 2: Are both drugs in combination therapy showing?
```python
print(forecast['Dispensing Drug'].value_counts())
```
You should see both drugs listed.

### ✅ Check 3: Are visit dates reasonable?
```python
print(f"Date range: {forecast['Projected Visit Date'].min()} to {forecast['Projected Visit Date'].max()}")
```

## Troubleshooting Matrix

| Problem | Likely Cause | Solution |
|---------|--------------|----------|
| No visits generated | All patients discontinued | Check Subject Status column |
| Missing drug in combo | Only 1 row in treatment plan | Add separate row for each drug |
| Wrong dates | Visit Days format wrong | Use "1,8" not "1, 8" or "1 8" |
| Patient not matched | Matching criteria mismatch | Verify Study Protocol, Randomized Treatment, Subject Status, TPC all match |
| Duplicate visits | N/A - code handles this | Duplicates auto-removed |

## Key Concepts

### What is TPC?
**Treatment of Physician's Choice** - The drug selected by the physician for patients on the control arm.
- For experimental arm patients: TPC = "n/a"
- For TPC arm patients: TPC = drug name (e.g., "Nab-Paclitaxel 100 mg/m2")

### What is a Crossover?
When a patient switches from their original treatment (TPC) to the experimental drug (Sacituzumab Govitecan).
- Original status: "Randomized"
- After crossover: "Crossover Approved"
- Drug changes: TPC drug → Sacituzumab Govitecan
- TPC column preserves original drug for reference

### Visit Days vs. Cycle Frequency
- **Visit Days**: Days within a cycle when patient visits (e.g., "1,8" = Day 1 and Day 8)
- **Cycle Frequency**: Length of one complete cycle in days (e.g., 21 = 21-day cycle)

Example with "1,8" visit days and 21-day cycle:
- Cycle 1: Day 1 (Jan 1), Day 8 (Jan 8)
- Cycle 2: Day 1 (Jan 22), Day 8 (Jan 29)  ← 21 days after Cycle 1 Day 1
- Cycle 3: Day 1 (Feb 12), Day 8 (Feb 19)

## Tips for Success

1. **Clean your data first**
   - Remove extra spaces in drug names
   - Standardize date formats (YYYY-MM-DD)
   - Check for typos in matching fields

2. **Start small**
   - Test with 3-5 patients first
   - Verify output looks correct
   - Then run full dataset

3. **Use descriptive filenames**
   - `inventory_forecast_2024_Q1.xlsx`
   - `inventory_forecast_full_year.xlsx`

4. **Keep a data dictionary**
   - Document what each TPC drug code means
   - Note any special patient statuses
   - Track when treatment plans change

## Getting Help

Run the test to verify everything works:
```python
python inventory_demand_generator.py
```

This runs built-in sample data and should generate output files.

## Next Steps

1. Review the full [DOCUMENTATION.md](DOCUMENTATION.md) for detailed explanations
2. Customize the code for your specific needs
3. Set up regular forecast generation (weekly/monthly)
4. Integrate with your inventory management system

---

**Questions?** Review the examples in DOCUMENTATION.md or check the troubleshooting section.
