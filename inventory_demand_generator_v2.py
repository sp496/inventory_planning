"""
Inventory Demand Generator for Clinical Trial Drug Dispensation
This script generates projected visit schedules and drug demand based on:
1. Subject Summary (patient-level data)
2. Drug Dispensation Quantities (treatment plan mapping)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')


class InventoryDemandGenerator:
    """
    Generates inventory demand forecasts for clinical trial patients
    """
    
    def __init__(self, subject_summary_df: pd.DataFrame, drug_dispensation_df: pd.DataFrame):
        """
        Initialize with patient and treatment plan data
        
        Args:
            subject_summary_df: Patient-level data with current status
            drug_dispensation_df: Treatment plan mapping with visit schedules
        """
        self.subject_summary = subject_summary_df.copy()
        self.drug_dispensation = drug_dispensation_df.copy()
        self.inventory_demand = pd.DataFrame()
        
    def parse_visit_days(self, visit_days_str: str) -> List[int]:
        """
        Parse visit days string into list of integers
        
        Args:
            visit_days_str: String like "1,8" or "1, 8, 15"
            
        Returns:
            List of visit days as integers
        """
        if pd.isna(visit_days_str):
            return [1]  # Default to Day 1 if not specified
        
        try:
            days = [int(d.strip()) for d in str(visit_days_str).split(',')]
            return sorted(days)
        except:
            return [1]
    
    def extract_cycle_info(self, last_visit_recorded: str) -> Tuple[int, int]:
        """
        Extract cycle number and day from last visit string
        
        Args:
            last_visit_recorded: String like "Crossover Cycle 2 Day 1" or "Cycle 18 Day 8"
            
        Returns:
            Tuple of (cycle_number, day_number)
        """
        if pd.isna(last_visit_recorded):
            return (0, 0)
        
        try:
            # Handle different formats: "Cycle X Day Y" or "Crossover Cycle X Day Y"
            import re
            
            # Look for "Cycle X Day Y" pattern
            cycle_match = re.search(r'Cycle\s+(\d+)', str(last_visit_recorded))
            day_match = re.search(r'Day\s+(\d+)', str(last_visit_recorded))
            
            cycle_num = int(cycle_match.group(1)) if cycle_match else 0
            day_num = int(day_match.group(1)) if day_match else 0
            
            return (cycle_num, day_num)
        except:
            return (0, 0)
    
    def match_treatment_plan(self, patient_row: pd.Series) -> pd.DataFrame:
        """
        Match patient to their treatment plan(s)
        
        Args:
            patient_row: Single row from subject_summary
            
        Returns:
            DataFrame with all matched treatment plan rows (can be multiple drugs)
        """
        # Start with matching on Study Protocol
        mask = self.drug_dispensation['Study Protocol'] == patient_row['Study Protocol']
        
        # Match on Randomized Treatment
        mask &= self.drug_dispensation['Randomized Treatment'] == patient_row['Randomized Treatment']
        
        # Match on Subject Status
        mask &= self.drug_dispensation['Subject Status'] == patient_row['Subject Status']
        
        # Match on TPC if applicable (not n/a)
        if pd.notna(patient_row['TPC']) and str(patient_row['TPC']).lower() != 'n/a':
            mask &= self.drug_dispensation['TPC'] == patient_row['TPC']
        
        matched_plans = self.drug_dispensation[mask]
        
        if len(matched_plans) == 0:
            # Try relaxed matching without Subject Status for edge cases
            mask = self.drug_dispensation['Study Protocol'] == patient_row['Study Protocol']
            mask &= self.drug_dispensation['Randomized Treatment'] == patient_row['Randomized Treatment']
            
            if pd.notna(patient_row['TPC']) and str(patient_row['TPC']).lower() != 'n/a':
                mask &= self.drug_dispensation['TPC'] == patient_row['TPC']
            
            matched_plans = self.drug_dispensation[mask]
        
        return matched_plans if len(matched_plans) > 0 else None
    
    def is_patient_active(self, subject_status: str) -> bool:
        """
        Check if patient is active and should have future visits generated
        
        Args:
            subject_status: Patient's subject status
            
        Returns:
            True if patient is active, False otherwise
        """
        if pd.isna(subject_status):
            return False
        
        status_lower = str(subject_status).lower()
        
        # Inactive statuses
        inactive_keywords = [
            'discontinued',
            'completed',
            'withdrawn',
            'terminated',
            'death',
            'died',
            'screen failure'
        ]
        
        for keyword in inactive_keywords:
            if keyword in status_lower:
                return False
        
        return True
    
    def generate_future_visits(self, 
                              patient_row: pd.Series, 
                              treatment_plan: pd.Series,
                              months_ahead: int = 12) -> List[Dict]:
        """
        Generate future visit schedule for a patient and specific drug
        
        Args:
            patient_row: Patient data
            treatment_plan: Matched treatment plan for one specific drug
            months_ahead: Number of months to project ahead
            
        Returns:
            List of dictionaries containing visit information
        """
        visits = []
        
        # Check if patient is active
        if not self.is_patient_active(patient_row['Subject Status']):
            return visits
        
        # Get treatment plan details for this specific drug
        visit_days = self.parse_visit_days(treatment_plan['Visit Days'])
        dispensing_freq = int(treatment_plan['Dispensing Frequency (Days)'])
        dispensing_qty = treatment_plan['Dispensing Quantity']

        # Check both Study Drug Dispensed and Additional Study Drug Dispensed columns
        study_drug = treatment_plan['Study Drug Dispensed']
        if pd.isna(study_drug) or str(study_drug).strip() == '':
            study_drug = treatment_plan.get('Additional Study Drug Dispensed', '')
        
        # Get last visit info
        last_visit_date = pd.to_datetime(patient_row['Last Study Visit Date'])
        last_cycle, last_day = self.extract_cycle_info(patient_row['Last Study Visit Recorded'])
        
        # Calculate projection end date
        end_date = datetime.now() + timedelta(days=months_ahead * 30)
        
        # Determine if this is a crossover patient
        is_crossover = 'crossover' in str(patient_row['Subject Status']).lower()
        cycle_prefix = "Crossover Cycle" if is_crossover else "Cycle"
        
        # Start from next visit after last recorded visit
        current_cycle = last_cycle
        current_date = last_visit_date
        
        # Find next visit to schedule
        if last_day in visit_days:
            # Get next day in the cycle
            day_index = visit_days.index(last_day)
            if day_index < len(visit_days) - 1:
                # More visits in current cycle
                next_day = visit_days[day_index + 1]
                days_to_add = next_day - last_day
                current_date = last_visit_date + timedelta(days=days_to_add)
            else:
                # Move to next cycle
                current_cycle += 1
                next_day = visit_days[0]
                current_date = last_visit_date + timedelta(days=dispensing_freq)
        else:
            # Last day not in visit_days, start from next cycle
            current_cycle += 1
            next_day = visit_days[0]
            current_date = last_visit_date + timedelta(days=dispensing_freq)
        
        # Generate visits for each cycle
        while current_date <= end_date:
            for day in visit_days:
                if current_date > last_visit_date and current_date <= end_date:
                    # Create visit record for this drug
                    visit = {
                        'Study Protocol': patient_row['Study Protocol'],
                        'Subject Number': patient_row['Subject Number'],
                        'Site ID': patient_row['Site ID'],
                        'Depot': patient_row.get('Depot', ''),
                        'Country': patient_row.get('Country', ''),
                        'Subject Status': patient_row['Subject Status'],
                        'Randomized Treatment': patient_row['Randomized Treatment'],
                        'TPC': patient_row['TPC'],
                        'Dispensing Drug': study_drug,
                        'Dispensing Quantity': dispensing_qty,
                        'Projected Visit Date': current_date.strftime('%Y-%m-%d'),
                        'Projected Visit Number': f"{cycle_prefix} {current_cycle} Day {day}",
                        'Projected Study Cycle': current_cycle,
                        'Projected Study Cycle Day': day
                    }
                    visits.append(visit)
                
                # Move to next visit day in cycle
                if day != visit_days[-1]:
                    next_day_index = visit_days.index(day) + 1
                    days_diff = visit_days[next_day_index] - day
                    current_date += timedelta(days=days_diff)
            
            # Move to next cycle
            current_cycle += 1
            # Reset to first day of next cycle (add remaining days to complete the cycle)
            last_day_of_cycle = visit_days[-1]
            days_remaining = dispensing_freq - last_day_of_cycle
            current_date += timedelta(days=days_remaining)
        
        return visits
    
    def generate_inventory_demand(self, months_ahead: int = 12) -> pd.DataFrame:
        """
        Generate complete inventory demand forecast
        
        Args:
            months_ahead: Number of months to project ahead
            
        Returns:
            DataFrame with projected inventory demand
        """
        all_visits = []
        
        print(f"Processing {len(self.subject_summary)} patients...")
        
        for idx, patient in self.subject_summary.iterrows():
            # Match patient to treatment plan(s) - can be multiple drugs
            treatment_plans = self.match_treatment_plan(patient)
            
            if treatment_plans is None:
                print(f"Warning: No treatment plan found for patient {patient.get('Subject Number', idx)}")
                continue
            
            # Generate future visits for each drug in the treatment plan
            for plan_idx, treatment_plan in treatment_plans.iterrows():
                patient_visits = self.generate_future_visits(patient, treatment_plan, months_ahead)
                all_visits.extend(patient_visits)
            
            if (idx + 1) % 10 == 0:
                print(f"Processed {idx + 1} patients...")
        
        # Create DataFrame
        if len(all_visits) > 0:
            self.inventory_demand = pd.DataFrame(all_visits)
            
            # Remove duplicates if any (same visit for same drug)
            self.inventory_demand = self.inventory_demand.drop_duplicates(
                subset=['Subject Number', 'Projected Visit Date', 'Dispensing Drug'],
                keep='first'
            )
            
            print(f"\nGenerated {len(self.inventory_demand)} projected visits")
        else:
            print("\nNo visits generated - check if patients are active")
            self.inventory_demand = pd.DataFrame()
        
        return self.inventory_demand
    
    def get_summary_statistics(self) -> Dict:
        """
        Get summary statistics of the inventory demand
        
        Returns:
            Dictionary with summary statistics
        """
        if len(self.inventory_demand) == 0:
            return {}
        
        stats = {
            'total_visits': len(self.inventory_demand),
            'unique_patients': self.inventory_demand['Subject Number'].nunique(),
            'visits_by_drug': self.inventory_demand.groupby('Dispensing Drug').size().to_dict(),
            'visits_by_country': self.inventory_demand.groupby('Country').size().to_dict(),
            'total_quantity_by_drug': self.inventory_demand.groupby('Dispensing Drug')['Dispensing Quantity'].sum().to_dict(),
            'date_range': {
                'start': self.inventory_demand['Projected Visit Date'].min(),
                'end': self.inventory_demand['Projected Visit Date'].max()
            }
        }
        
        return stats
    
    def save_to_excel(self, filename: str = 'inventory_demand_forecast.xlsx'):
        """
        Save inventory demand to Excel file
        
        Args:
            filename: Output filename
        """
        if len(self.inventory_demand) == 0:
            print("No data to save")
            return
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Main forecast
            self.inventory_demand.to_excel(writer, sheet_name='Inventory Demand', index=False)
            
            # Summary by drug
            drug_summary = self.inventory_demand.groupby('Dispensing Drug').agg({
                'Dispensing Quantity': 'sum',
                'Subject Number': 'nunique',
                'Projected Visit Date': 'count'
            }).rename(columns={
                'Dispensing Quantity': 'Total Quantity Needed',
                'Subject Number': 'Number of Patients',
                'Projected Visit Date': 'Number of Visits'
            })
            drug_summary.to_excel(writer, sheet_name='Summary by Drug')
            
            # Summary by month
            self.inventory_demand['Month'] = pd.to_datetime(self.inventory_demand['Projected Visit Date']).dt.to_period('M')
            monthly_summary = self.inventory_demand.groupby(['Month', 'Dispensing Drug']).agg({
                'Dispensing Quantity': 'sum',
                'Subject Number': 'nunique'
            }).rename(columns={
                'Dispensing Quantity': 'Quantity Needed',
                'Subject Number': 'Number of Patients'
            })
            monthly_summary.to_excel(writer, sheet_name='Summary by Month')
        
        print(f"Data saved to {filename}")


def main():
    """
    Example usage of the InventoryDemandGenerator
    """
    print("=" * 80)
    print("Inventory Demand Generator for Clinical Trials")
    print("=" * 80)
    print()
    
    # Example: Load your data files
    # Replace these with your actual file paths
    
    print("Loading data files...")
    print("Please provide your data files:")
    print("1. Subject Summary (patient-level data)")
    print("2. Drug Dispensation Quantities (treatment plan mapping)")
    print()
    
    # Example data loading (uncomment and modify with your actual file paths):
    """
    subject_summary = pd.read_excel('subject_summary.xlsx')
    drug_dispensation = pd.read_excel('drug_dispensation_qtys.xlsx')
    
    # Initialize generator
    generator = InventoryDemandGenerator(subject_summary, drug_dispensation)
    
    # Generate 12-month forecast
    inventory_demand = generator.generate_inventory_demand(months_ahead=12)
    
    # Display summary statistics
    stats = generator.get_summary_statistics()
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Total projected visits: {stats['total_visits']}")
    print(f"Unique patients: {stats['unique_patients']}")
    print(f"\nVisits by drug:")
    for drug, count in stats['visits_by_drug'].items():
        print(f"  {drug}: {count} visits")
    print(f"\nTotal quantity needed by drug:")
    for drug, qty in stats['total_quantity_by_drug'].items():
        print(f"  {drug}: {qty} units")
    print(f"\nProjection period: {stats['date_range']['start']} to {stats['date_range']['end']}")
    
    # Save to Excel
    generator.save_to_excel('inventory_demand_forecast.xlsx')
    
    print("\n" + "=" * 80)
    print("Processing complete!")
    print("=" * 80)
    """
    
    # Create sample data for demonstration
    print("Creating sample data for demonstration...")
    
    # Sample Subject Summary
    sample_subjects = pd.DataFrame({
        'Study Protocol': ['GS-US-592-6173', 'GS-US-592-6173', 'GS-US-592-6173'],
        'Site ID': ['10663', '20735', '23323'],
        'Country': ['Japan', 'France', 'Australia'],
        'Depot': ['Tokyo-North', '3KI Lumbres', 'Sydney-Central'],
        'Subject Number': ['10663-106', '20735-001', '23323-045'],
        'Date Randomized': ['2021-03-10', '2022-11-10', '2022-09-20'],
        'Subject Status': ['Crossover Approved', 'Randomized', 'Crossover Approved'],
        'Randomized Treatment': [
            'Treatment of Physician\'s Choice plus Pembrolizumab',
            'Sacituzumab Govitecan plus Pembrolizumab',
            'Treatment of Physician\'s Choice plus Pembrolizumab'
        ],
        'TPC': ['Nab-Paclitaxel 100 mg/m2', 'n/a', 'Paclitaxel 90 mg/m2'],
        'Last Study Visit Recorded': ['Crossover Cycle 2 Day 1', 'Cycle 18 Day 1', 'Crossover Cycle 1 Day 8'],
        'Last Study Visit Date': ['2023-10-15', '2023-12-12', '2023-10-20']
    })
    
    # Sample Drug Dispensation
    sample_dispensation = pd.DataFrame({
        'Study Protocol': ['GS-US-592-6173'] * 6,
        'Randomized Treatment': [
            'Sacituzumab Govitecan plus Pembrolizumab',
            'Sacituzumab Govitecan plus Pembrolizumab',  # Separate row for Pembrolizumab
            'Treatment of Physician\'s Choice plus Pembrolizumab',
            'Treatment of Physician\'s Choice plus Pembrolizumab',
            'Treatment of Physician\'s Choice plus Pembrolizumab',
            'Treatment of Physician\'s Choice plus Pembrolizumab'
        ],
        'Subject Status': ['Randomized', 'Randomized', 'Randomized', 'Randomized', 'Crossover Approved', 'Crossover Approved'],
        'TPC': ['n/a', 'n/a', 'Nab-Paclitaxel 100 mg/m2', 'Nab-Paclitaxel 100 mg/m2', 'Nab-Paclitaxel 100 mg/m2', 'Paclitaxel 90 mg/m2'],
        'Study Drug Dispensed': [
            'Sacituzumab Govitecan',
            '',  # Additional drug goes in Additional Study Drug Dispensed column
            'Nab-Paclitaxel',
            '',  # Additional drug goes in Additional Study Drug Dispensed column
            'Sacituzumab Govitecan',
            'Sacituzumab Govitecan'
        ],
        'Additional Study Drug Dispensed': [
            '',
            'Pembrolizumab',  # Additional drug in separate column
            '',
            'Pembrolizumab',  # Additional drug in separate column
            '',
            ''
        ],
        'Visit Days': ['1,8', '1,8', '1,8,15', '1,8,15', '1,8', '1,8'],
        'Dispensing Quantity': [4, 1, 1, 1, 4, 4],
        'Dispensing Frequency (Days)': [21, 21, 28, 28, 21, 21]
    })
    
    print("\nSample data created. Running generator...")
    
    # Initialize and run generator
    generator = InventoryDemandGenerator(sample_subjects, sample_dispensation)
    inventory_demand = generator.generate_inventory_demand(months_ahead=12)
    
    # Display results
    if len(inventory_demand) > 0:
        print("\nFirst 10 projected visits:")
        print(inventory_demand.head(10).to_string())
        
        stats = generator.get_summary_statistics()
        print("\n" + "=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        print(f"Total projected visits: {stats['total_visits']}")
        print(f"Unique patients: {stats['unique_patients']}")
        print(f"\nVisits by drug:")
        for drug, count in stats['visits_by_drug'].items():
            print(f"  {drug}: {count} visits")
        print(f"\nTotal quantity needed by drug:")
        for drug, qty in stats['total_quantity_by_drug'].items():
            print(f"  {drug}: {qty} units")
        
        # Save sample output
        generator.save_to_excel('/mnt/user-data/outputs/sample_inventory_demand_forecast.xlsx')
    
    print("\n" + "=" * 80)
    print("USAGE INSTRUCTIONS")
    print("=" * 80)
    print("""
To use with your actual data:

1. Load your data files:
   subject_summary = pd.read_excel('your_subject_summary.xlsx')
   drug_dispensation = pd.read_excel('your_drug_dispensation.xlsx')

2. Initialize the generator:
   generator = InventoryDemandGenerator(subject_summary, drug_dispensation)

3. Generate forecast (default 12 months):
   inventory_demand = generator.generate_inventory_demand(months_ahead=12)

4. Save results:
   generator.save_to_excel('output_filename.xlsx')

5. Get summary statistics:
   stats = generator.get_summary_statistics()
    """)


if __name__ == "__main__":
    main()
