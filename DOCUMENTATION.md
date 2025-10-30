# Inventory Demand Generator - Documentation

## Overview
This tool generates projected visit schedules and drug inventory demand for clinical trial patients based on their current status and treatment plans.

## Key Features

### ✅ Handles Multiple Treatment Scenarios
- **Regular randomized patients**: Patients assigned to initial treatment
- **Crossover patients**: Patients who switched from TPC to experimental drug
- **Multi-drug treatments**: Patients receiving combination therapy (e.g., Sacituzumab + Pembrolizumab)
- **Different visit schedules**: Supports various visit day patterns and cycle frequencies

### ✅ Smart Matching Logic
The tool matches patients to treatment plans using:
1. Study Protocol (exact match)
2. Randomized Treatment (exact match)
3. Subject Status (exact match)
4. TPC - Treatment of Physician's Choice (when applicable)

For crossover patients, the tool correctly identifies they should receive the crossover drug (Sacituzumab Govitecan) instead of their original TPC drug.

### ✅ Accurate Date Calculations
- Extracts last visit cycle and day from patient records
- Generates future visits based on visit days (e.g., Days 1, 8, 15)
- Respects dispensing frequency (e.g., 21-day or 28-day cycles)
- Projects visits up to 12 months ahead (configurable)

### ✅ Handles Inactive Patients
Automatically filters out patients with status:
- Discontinued
- Completed
- Withdrawn
- Terminated
- Death/Died
- Screen Failure

## Data Structure Requirements

### Input 1: Subject Summary (Patient-Level Data)
Required columns:
- `Study Protocol`: Study identifier (e.g., "GS-US-592-6173")
- `Site ID`: Site identifier
- `Country`: Patient's country
- `Depot`: Depot location (optional)
- `Subject Number`: Unique patient identifier
- `Date Randomized`: Date patient was randomized
- `Subject Status`: Current patient status (e.g., "Randomized", "Crossover Approved", "Discontinued")
- `Randomized Treatment`: Treatment arm assigned at randomization
- `TPC`: Treatment of Physician's Choice (drug selected by physician, or "n/a")
- `Last Study Visit Recorded`: Last visit description (e.g., "Crossover Cycle 2 Day 1")
- `Last Study Visit Date`: Date of last visit (YYYY-MM-DD format)

### Input 2: Drug Dispensation Quantities (Treatment Plan Mapping)
Required columns:
- `Study Protocol`: Study identifier
- `Randomized Treatment`: Treatment arm
- `Subject Status`: Patient status (should match subject summary)
- `TPC`: Treatment of Physician's Choice (or "n/a")
- `Study Drug Dispensed`: Drug to be dispensed
- `Additional Study Drug Dispensed`: Second drug if applicable (optional, can be blank)
- `Visit Days`: Comma-separated visit days within cycle (e.g., "1,8" or "1,8,15")
- `Dispensing Quantity`: Units/vials dispensed per visit
- `Dispensing Frequency (Days)`: Cycle length in days (e.g., 21 or 28)

**IMPORTANT**: For combination therapies (e.g., Drug A + Drug B), create **separate rows** for each drug with the same matching criteria but different `Study Drug Dispensed` values.

Example:
```
Row 1: Study Protocol, Randomized Treatment, Subject Status, TPC, Study Drug Dispensed=Sacituzumab Govitecan, Visit Days=1,8, Quantity=4
Row 2: Study Protocol, Randomized Treatment, Subject Status, TPC, Study Drug Dispensed=Pembrolizumab, Visit Days=1,8, Quantity=1
```

### Output: Inventory Demand
Generated columns:
- `Study Protocol`: From patient record
- `Subject Number`: From patient record
- `Site ID`: From patient record
- `Depot`: From patient record
- `Country`: From patient record
- `Subject Status`: From patient record
- `Randomized Treatment`: From patient record
- `TPC`: From patient record
- `Dispensing Drug`: Drug to be dispensed (from treatment plan)
- `Dispensing Quantity`: Quantity needed (from treatment plan)
- `Projected Visit Date`: Calculated future visit date
- `Projected Visit Number`: Visit identifier (e.g., "Cycle 3 Day 1")
- `Projected Study Cycle`: Cycle number
- `Projected Study Cycle Day`: Day within cycle

## Usage Examples

### Basic Usage
```python
import pandas as pd
from inventory_demand_generator import InventoryDemandGenerator

# Load your data
subject_summary = pd.read_excel('subject_summary.xlsx')
drug_dispensation = pd.read_excel('drug_dispensation_qtys.xlsx')

# Initialize generator
generator = InventoryDemandGenerator(subject_summary, drug_dispensation)

# Generate 12-month forecast
inventory_demand = generator.generate_inventory_demand(months_ahead=12)

# Save results
generator.save_to_excel('inventory_forecast_2024.xlsx')

# Get statistics
stats = generator.get_summary_statistics()
print(f"Total visits: {stats['total_visits']}")
print(f"Unique patients: {stats['unique_patients']}")
```

### Custom Projection Period
```python
# Generate 6-month forecast
inventory_demand = generator.generate_inventory_demand(months_ahead=6)

# Generate 18-month forecast
inventory_demand = generator.generate_inventory_demand(months_ahead=18)
```

### Accessing Results
```python
# View first 10 visits
print(inventory_demand.head(10))

# Filter by drug
saci_visits = inventory_demand[inventory_demand['Dispensing Drug'] == 'Sacituzumab Govitecan']

# Filter by patient
patient_visits = inventory_demand[inventory_demand['Subject Number'] == '10663-106']

# Filter by date range
import pandas as pd
inventory_demand['Visit Date'] = pd.to_datetime(inventory_demand['Projected Visit Date'])
q1_visits = inventory_demand[(inventory_demand['Visit Date'] >= '2024-01-01') & 
                              (inventory_demand['Visit Date'] <= '2024-03-31')]
```

### Summary Statistics
```python
stats = generator.get_summary_statistics()

# Available statistics:
# - stats['total_visits']: Total number of projected visits
# - stats['unique_patients']: Number of unique patients
# - stats['visits_by_drug']: Dictionary of visits per drug
# - stats['visits_by_country']: Dictionary of visits per country
# - stats['total_quantity_by_drug']: Dictionary of total quantities per drug
# - stats['date_range']: Dictionary with 'start' and 'end' dates
```

## Treatment Scenario Examples

### Example 1: Regular Patient on Single Drug
**Patient Data:**
- Status: Randomized
- Randomized Treatment: Sacituzumab Govitecan plus Pembrolizumab
- TPC: n/a
- Last Visit: Cycle 18 Day 1 on 2023-12-12

**Treatment Plan Matches (2 rows):**
- Row 1: Sacituzumab Govitecan, Visit Days: 1,8, Quantity: 4, Frequency: 21 days
- Row 2: Pembrolizumab, Visit Days: 1,8, Quantity: 1, Frequency: 21 days

**Generated Visits:**
- 2023-12-19: Cycle 18 Day 8 - Sacituzumab Govitecan (4 units)
- 2023-12-19: Cycle 18 Day 8 - Pembrolizumab (1 unit)
- 2024-01-08: Cycle 19 Day 1 - Sacituzumab Govitecan (4 units)
- 2024-01-08: Cycle 19 Day 1 - Pembrolizumab (1 unit)
- ... continues for 12 months

### Example 2: Crossover Patient
**Patient Data:**
- Status: Crossover Approved
- Randomized Treatment: Treatment of Physician's Choice plus Pembrolizumab
- TPC: Nab-Paclitaxel 100 mg/m2 (original drug)
- Last Visit: Crossover Cycle 2 Day 1 on 2023-10-15

**Treatment Plan Matches:**
- Matches to: Subject Status="Crossover Approved", TPC="Nab-Paclitaxel 100 mg/m2"
- Study Drug Dispensed: **Sacituzumab Govitecan** (NOT Nab-Paclitaxel)
- Visit Days: 1,8
- Quantity: 4
- Frequency: 21 days

**Generated Visits:**
- 2023-10-22: Crossover Cycle 2 Day 8 - Sacituzumab Govitecan (4 units)
- 2023-11-11: Crossover Cycle 3 Day 1 - Sacituzumab Govitecan (4 units)
- 2023-11-18: Crossover Cycle 3 Day 8 - Sacituzumab Govitecan (4 units)
- ... continues for 12 months

**Note**: The TPC column preserves the original drug (Nab-Paclitaxel) for reference, but the Dispensing Drug is correctly set to Sacituzumab Govitecan.

### Example 3: Patient with Different Visit Schedule
**Patient Data:**
- Status: Randomized
- Randomized Treatment: Treatment of Physician's Choice plus Pembrolizumab
- TPC: Nab-Paclitaxel 100 mg/m2
- Last Visit: Cycle 5 Day 15 on 2023-11-15

**Treatment Plan:**
- Study Drug Dispensed: Nab-Paclitaxel
- Visit Days: 1,8,15 (three visits per cycle)
- Quantity: 1
- Frequency: 28 days

**Generated Visits:**
- 2023-12-13: Cycle 6 Day 1 - Nab-Paclitaxel (1 unit)
- 2023-12-20: Cycle 6 Day 8 - Nab-Paclitaxel (1 unit)
- 2023-12-28: Cycle 6 Day 15 - Nab-Paclitaxel (1 unit)
- 2024-01-10: Cycle 7 Day 1 - Nab-Paclitaxel (1 unit)
- ... continues for 12 months

## Output Files

When you save results using `generator.save_to_excel()`, three sheets are created:

### Sheet 1: Inventory Demand
Complete list of all projected visits with all columns.

### Sheet 2: Summary by Drug
Aggregated statistics per drug:
- Total Quantity Needed
- Number of Patients
- Number of Visits

### Sheet 3: Summary by Month
Monthly breakdown by drug:
- Quantity Needed per month
- Number of Patients per month

## Troubleshooting

### No visits generated
**Possible causes:**
1. All patients have discontinued/completed status
2. Last visit dates are in the future
3. No matching treatment plans found

**Solutions:**
- Check patient statuses in Subject Summary
- Verify Last Study Visit Date format
- Verify treatment plan matching criteria

### Incorrect drug dispensed
**Possible causes:**
1. Treatment plan not properly defined for crossover patients
2. Multiple matching rows in treatment plan

**Solutions:**
- Ensure crossover treatment plans have Subject Status = "Crossover Approved"
- Verify TPC values match between patient and treatment plan
- Check that Study Drug Dispensed is correct for crossover (should be Sacituzumab Govitecan)

### Missing combination drug
**Possible causes:**
1. Only one row in treatment plan for combination therapy
2. Additional Study Drug Dispensed not used

**Solutions:**
- Create **separate rows** for each drug in combination therapy
- Each row should have identical matching criteria but different Study Drug Dispensed

### Wrong visit dates
**Possible causes:**
1. Visit Days not properly formatted
2. Dispensing Frequency incorrect
3. Last visit info not correctly parsed

**Solutions:**
- Ensure Visit Days is comma-separated (e.g., "1,8,15")
- Verify Dispensing Frequency is a number (days)
- Check Last Study Visit Recorded format (e.g., "Cycle 2 Day 1")

## Technical Details

### Date Calculation Algorithm
1. Parse last visit cycle and day from patient record
2. Determine next visit in current cycle or move to next cycle
3. For each visit day in the cycle:
   - Calculate date based on last visit + days elapsed
   - Create visit record
4. Move to next cycle by adding Dispensing Frequency days
5. Repeat until projection end date reached

### Crossover Handling
The code identifies crossover patients by:
1. Checking if "crossover" appears in Subject Status (case-insensitive)
2. Matching to treatment plan where Subject Status = "Crossover Approved"
3. Using Study Drug Dispensed from matched treatment plan (typically Sacituzumab Govitecan)
4. Labeling future visits as "Crossover Cycle X Day Y"

### Duplicate Prevention
The code automatically removes duplicates based on:
- Subject Number
- Projected Visit Date
- Dispensing Drug

This prevents double-counting if a visit is generated by multiple logic paths.

## Version History

### Version 2.0 (Current)
- Added support for multiple drug rows per treatment plan
- Improved handling of combination therapies
- Added duplicate removal logic
- Enhanced documentation

### Version 1.0
- Initial release
- Basic visit projection
- Crossover patient support
- Single drug per treatment plan row

## Support

For questions or issues:
1. Check that input data matches required format
2. Review troubleshooting section
3. Verify sample data runs successfully
4. Check generated summary statistics for anomalies

## License

This tool is provided as-is for clinical trial inventory management purposes.
