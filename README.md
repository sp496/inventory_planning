# Clinical Trial Inventory Demand Generator

## 🎯 Purpose
Generate 12-month drug inventory forecasts for clinical trial patients based on their current treatment status and visit schedules.

## 📦 What's Included

| File | Description |
|------|-------------|
| `inventory_demand_generator_v2.py` | Main Python script (latest version) |
| `QUICK_START.md` | 5-minute setup guide |
| `DOCUMENTATION.md` | Comprehensive documentation |
| `DATA_TEMPLATES.xlsx` | Excel templates with sample data |
| `sample_inventory_demand_forecast.xlsx` | Example output |

## 🚀 Quick Start

### 1. Prepare Your Data
Use the templates in `DATA_TEMPLATES.xlsx`:
- **Sheet 1**: Subject Summary (patient data)
- **Sheet 2**: Drug Dispensation (treatment plans)

### 2. Run the Code
```python
import pandas as pd
from inventory_demand_generator_v2 import InventoryDemandGenerator

# Load your data
subjects = pd.read_excel('your_subject_summary.xlsx')
treatments = pd.read_excel('your_drug_dispensation.xlsx')

# Generate forecast
generator = InventoryDemandGenerator(subjects, treatments)
forecast = generator.generate_inventory_demand(months_ahead=12)

# Save
generator.save_to_excel('forecast_output.xlsx')
```

### 3. Review Output
Open the generated Excel file with three sheets:
1. **Inventory Demand** - Full visit schedule
2. **Summary by Drug** - Aggregated quantities
3. **Summary by Month** - Monthly breakdown

## ✨ Key Features

### ✅ Handles Complex Scenarios
- **Regular patients**: Standard randomized treatment
- **Crossover patients**: Switched from TPC to experimental drug
- **Combination therapy**: Multiple drugs per patient (e.g., Drug A + Drug B)
- **Variable schedules**: Different visit patterns (Day 1,8 vs Day 1,8,15)

### ✅ Smart Matching
Automatically matches patients to correct treatment plans based on:
- Study Protocol
- Randomized Treatment
- Subject Status (Randomized vs Crossover)
- TPC (Treatment of Physician's Choice)

### ✅ Accurate Calculations
- Projects visits up to 12 months (configurable)
- Respects cycle frequencies (21-day, 28-day cycles, etc.)
- Handles multiple visit days per cycle
- Filters out inactive/discontinued patients

## 📊 Example Scenarios

### Scenario 1: Combination Therapy Patient
**Patient on Sacituzumab Govitecan + Pembrolizumab**
```
Input (Treatment Plan - 2 rows):
Row 1: Sacituzumab Govitecan | Visit Days: 1,8 | Qty: 4 | Freq: 21 days
Row 2: Pembrolizumab | Visit Days: 1,8 | Qty: 1 | Freq: 21 days

Output (Generated Visits):
2024-01-15 | Cycle 3 Day 1 | Sacituzumab Govitecan | 4 units
2024-01-15 | Cycle 3 Day 1 | Pembrolizumab | 1 unit
2024-01-22 | Cycle 3 Day 8 | Sacituzumab Govitecan | 4 units
2024-01-22 | Cycle 3 Day 8 | Pembrolizumab | 1 unit
... (continues for 12 months)
```

### Scenario 2: Crossover Patient
**Patient switched from Nab-Paclitaxel to Sacituzumab Govitecan**
```
Input (Patient Data):
Subject Status: Crossover Approved
TPC: Nab-Paclitaxel 100 mg/m2 (original)
Last Visit: Crossover Cycle 2 Day 1

Input (Treatment Plan):
Study Drug Dispensed: Sacituzumab Govitecan (current)
Visit Days: 1,8 | Qty: 4 | Freq: 21 days

Output (Generated Visits):
2024-01-10 | Crossover Cycle 2 Day 8 | Sacituzumab Govitecan | 4 units
2024-01-31 | Crossover Cycle 3 Day 1 | Sacituzumab Govitecan | 4 units
... (continues for 12 months)
```

## 🔍 Understanding the Data Flow

```
┌─────────────────────┐
│  Subject Summary    │  ← Patient current status
│  (Patient Data)     │
└──────────┬──────────┘
           │
           │ Matching Logic:
           │ - Study Protocol
           │ - Randomized Treatment  
           │ - Subject Status
           │ - TPC
           │
           ▼
┌─────────────────────┐
│ Drug Dispensation   │  ← Treatment schedules
│ (Treatment Plans)   │
└──────────┬──────────┘
           │
           │ Generation Logic:
           │ - Extract last visit info
           │ - Apply visit schedule
           │ - Project 12 months
           │
           ▼
┌─────────────────────┐
│ Inventory Demand    │  ← Forecasted visits
│    (Output)         │
└─────────────────────┘
```

## 📝 Important Notes

### Multiple Drugs (Combination Therapy)
For patients on Drug A + Drug B, create **separate rows** in the treatment plan:
```
✅ CORRECT:
Row 1: ... | Drug A | 1,8 | 4 | 21
Row 2: ... | Drug B | 1,8 | 1 | 21

❌ INCORRECT:
Row 1: ... | Drug A | 1,8 | 4 | 21
(missing Drug B row)
```

### Crossover Patients
- **Subject Status** changes to "Crossover Approved"
- **TPC** column keeps original drug for reference
- **Study Drug Dispensed** in treatment plan shows new drug (Sacituzumab Govitecan)

### Visit Days Format
Always use comma-separated format without spaces:
- ✅ `"1,8"`
- ✅ `"1,8,15"`
- ❌ `"1, 8"` (extra space)
- ❌ `"1 8"` (no comma)

## 🛠️ Customization Options

### Change Projection Period
```python
# 6 months
forecast = generator.generate_inventory_demand(months_ahead=6)

# 18 months
forecast = generator.generate_inventory_demand(months_ahead=18)
```

### Filter Results
```python
# Specific drug
saci_only = forecast[forecast['Dispensing Drug'] == 'Sacituzumab Govitecan']

# Specific country
japan_only = forecast[forecast['Country'] == 'Japan']

# Date range
q1_2024 = forecast[(forecast['Projected Visit Date'] >= '2024-01-01') & 
                    (forecast['Projected Visit Date'] <= '2024-03-31')]
```

### Get Statistics
```python
stats = generator.get_summary_statistics()
print(f"Total visits: {stats['total_visits']}")
print(f"Total patients: {stats['unique_patients']}")
print(f"Visits per drug: {stats['visits_by_drug']}")
```

## 📚 Additional Resources

- **[QUICK_START.md](QUICK_START.md)** - Get started in 5 minutes
- **[DOCUMENTATION.md](DOCUMENTATION.md)** - Detailed technical documentation
- **[DATA_TEMPLATES.xlsx](DATA_TEMPLATES.xlsx)** - Copy and fill with your data
- **[sample_inventory_demand_forecast.xlsx](sample_inventory_demand_forecast.xlsx)** - See example output

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| No visits generated | Check if patients are active (not discontinued) |
| Missing drug in output | Add separate row for each drug in treatment plan |
| Wrong dates | Verify Visit Days format: "1,8" not "1, 8" |
| Patient not matched | Ensure Study Protocol, Randomized Treatment, Subject Status, TPC all match |

See **QUICK_START.md** for full troubleshooting matrix.

## ✅ Verification Checklist

Before running on production data:

- [ ] Test with sample data (`python inventory_demand_generator_v2.py`)
- [ ] Verify data format matches templates
- [ ] Check Visit Days format (comma-separated, no spaces)
- [ ] Confirm combination therapies have separate rows
- [ ] Review crossover patient treatment plans
- [ ] Validate date formats (YYYY-MM-DD)
- [ ] Test with 2-3 patients first
- [ ] Review output for reasonableness

## 🎓 Key Concepts Explained

### TPC (Treatment of Physician's Choice)
The chemotherapy drug selected by the physician for control arm patients.
- Experimental arm: TPC = "n/a"
- Control arm: TPC = drug name (e.g., "Nab-Paclitaxel 100 mg/m2")

### Crossover
When a patient switches from control arm (TPC) to experimental arm (Sacituzumab Govitecan).
- Happens when TPC treatment fails/doesn't work
- Patient gets access to experimental drug
- Tracked as "Crossover Cycle X" instead of "Cycle X"

### Visit Days
Days within a treatment cycle when patient comes for drug administration.
- "1,8" = Visit on Day 1 and Day 8 of each cycle
- "1,8,15" = Three visits per cycle

### Dispensing Frequency
Length of one complete treatment cycle in days.
- 21 = 3-week cycle
- 28 = 4-week cycle
- After cycle completes, new cycle starts

## 💡 Tips for Success

1. **Start Small**: Test with 5-10 patients before full dataset
2. **Clean Data**: Remove extra spaces, standardize formats
3. **Document Changes**: Track when treatment plans are updated
4. **Regular Updates**: Run forecasts weekly or monthly
5. **Version Control**: Save dated copies of forecasts

## 🔄 Updates and Maintenance

### Current Version: 2.0
- Handles multiple drug rows per treatment plan
- Improved crossover patient logic
- Automatic duplicate removal
- Enhanced error messages

### Version History
- **v2.0**: Multiple drugs per treatment (current)
- **v1.0**: Initial release

## 📧 Support

For issues or questions:
1. Check **QUICK_START.md** troubleshooting section
2. Review **DOCUMENTATION.md** examples
3. Verify sample data runs successfully
4. Check summary statistics for anomalies

---

**Ready to start?** → Open **QUICK_START.md** for 5-minute setup guide!
