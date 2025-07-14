import pandas as pd
import os
from datetime import datetime

def fix_csv_mixed_dates(file_path, expected_year=None, expected_month=None, output_suffix="_fixed"):
    """
    Fix CSV file that has mixed date formats (dd/mm/yyyy and mm/dd/yyyy)
    
    Parameters:
    - file_path: Path to the CSV file
    - expected_year: Expected year (e.g., 2024, 2025). If None, allows any year
    - expected_month: Expected month (1-12). If None, allows any month
    - output_suffix: Suffix to add to the output filename
    """
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    print(f"Reading {file_path}...")
    df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
    df.columns = df.columns.str.strip()
    
    print(f"Original file has {len(df)} rows")
    
    # Keep original for backup
    df['orderDate_original'] = df['orderDate'].copy()
    
    # Clean the orderDate column
    df['orderDate'] = df['orderDate'].astype(str).str.strip()
    
    # Function to intelligently parse mixed date formats
    def parse_mixed_date(date_str):
        """Parse date string that could be in dd/mm/yyyy or mm/dd/yyyy format"""
        if pd.isna(date_str) or date_str == '' or date_str == 'nan':
            return None
            
        try:
            # Split the date
            parts = date_str.split('/')
            if len(parts) != 3:
                print(f"Invalid date format: {date_str}")
                return None
            
            first_num, second_num, year = parts
            first_num, second_num, year = int(first_num), int(second_num), int(year)
            
            # Check expected year if specified
            if expected_year and year != expected_year:
                print(f"Skipping wrong year date: {date_str} (expected {expected_year})")
                return None
            
            # Logic to determine correct format:
            day, month = None, None
            
            # If first number > 12, it must be day (dd/mm/yyyy format)
            if first_num > 12:
                day, month = first_num, second_num
                if month > 12 or month < 1:
                    print(f"Invalid month in dd/mm/yyyy: {date_str}")
                    return None
            # If second number > 12, it must be day (mm/dd/yyyy format)
            elif second_num > 12:
                month, day = first_num, second_num
                if month > 12 or month < 1:
                    print(f"Invalid month in mm/dd/yyyy: {date_str}")
                    return None
            # If both numbers <= 12, we need to make a smart guess
            else:
                # Strategy: Try both interpretations and see which makes more sense
                # Option 1: dd/mm/yyyy
                option1_day, option1_month = first_num, second_num
                # Option 2: mm/dd/yyyy  
                option2_month, option2_day = first_num, second_num
                
                # If we have an expected month, use that to decide
                if expected_month:
                    if option1_month == expected_month:
                        day, month = option1_day, option1_month
                    elif option2_month == expected_month:
                        day, month = option2_day, option2_month
                    else:
                        print(f"Neither interpretation matches expected month {expected_month}: {date_str}")
                        return None
                else:
                    # Default to dd/mm/yyyy format (more common internationally)
                    day, month = option1_day, option1_month
                    print(f"Ambiguous date {date_str}, assuming dd/mm/yyyy format")
            
            # Validate the final day and month
            if month < 1 or month > 12:
                print(f"Invalid month {month} in: {date_str}")
                return None
            if day < 1 or day > 31:
                print(f"Invalid day {day} in: {date_str}")
                return None
            
            # Check expected month if specified
            if expected_month and month != expected_month:
                print(f"Wrong month {month} in: {date_str} (expected {expected_month})")
                return None
            
            # Create the date
            parsed_date = datetime(year, month, day)
            return parsed_date
            
        except ValueError as e:
            print(f"Error parsing date {date_str}: {e}")
            return None
    
    # Apply the parsing function
    print("Parsing dates with mixed format detection...")
    df['orderDate_parsed'] = df['orderDate'].apply(parse_mixed_date)
    
    # Show parsing results
    successful_parses = df['orderDate_parsed'].notna().sum()
    failed_parses = df['orderDate_parsed'].isna().sum()
    
    print(f"Successfully parsed: {successful_parses} dates")
    print(f"Failed to parse: {failed_parses} dates")
    
    if failed_parses > 0:
        print("Some failed dates:")
        failed_dates = df[df['orderDate_parsed'].isna()]['orderDate_original'].unique()
        for date in failed_dates[:5]:  # Show first 5 failed dates
            print(f"  {date}")
        if len(failed_dates) > 5:
            print(f"  ... and {len(failed_dates) - 5} more")
    
    # Keep only successfully parsed dates
    df_clean = df[df['orderDate_parsed'].notna()].copy()
    
    print(f"Clean data: {len(df_clean)} rows")
    if len(df_clean) > 0:
        print(f"Date range: {df_clean['orderDate_parsed'].min()} to {df_clean['orderDate_parsed'].max()}")
        print(f"Unique dates: {df_clean['orderDate_parsed'].nunique()}")
    
    # Convert back to dd/mm/yyyy format for saving
    df_clean['orderDate'] = df_clean['orderDate_parsed'].dt.strftime("%d/%m/%Y")
    
    # Remove temporary columns
    df_clean = df_clean.drop(['orderDate_original', 'orderDate_parsed'], axis=1)
    
    # Create backup of original file
    backup_path = file_path.replace('.csv', '_backup.csv')
    print(f"Creating backup: {backup_path}")
    
    # Read original again for backup (to avoid changes)
    df_original = pd.read_csv(file_path)
    df_original.to_csv(backup_path, index=False)
    
    # Save the cleaned file
    base_name = file_path.replace('.csv', '')
    output_path = f"{base_name}{output_suffix}.csv"
    print(f"Saving cleaned data to: {output_path}")
    df_clean.to_csv(output_path, index=False)
    
    print(f"""
SUMMARY:
- Original file: {file_path} ({len(df)} rows)
- Backup created: {backup_path}
- Clean file created: {output_path} ({len(df_clean)} rows)
""")
    
    return output_path

def main():
    """Interactive script to fix CSV files with mixed date formats"""
    
    print("CSV Date Format Fixer")
    print("=" * 50)
    
    # Get file path
    file_path = input("Enter CSV file path (or drag and drop file): ").strip().strip('"')
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    # Get expected year (optional)
    year_input = input("Expected year (e.g., 2024, 2025) or press Enter to allow any year: ").strip()
    expected_year = int(year_input) if year_input else None
    
    # Get expected month (optional)
    month_input = input("Expected month (1-12) or press Enter to allow any month: ").strip()
    expected_month = int(month_input) if month_input else None
    
    # Fix the file
    output_path = fix_csv_mixed_dates(file_path, expected_year, expected_month)
    
    if output_path:
        print(f"\nSuccess! Fixed file saved as: {output_path}")
        
        replace = input("\nDo you want to replace the original file with the fixed version? (y/n): ").strip().lower()
        if replace == 'y':
            os.replace(output_path, file_path)
            print(f"Original file replaced with fixed version.")
        else:
            print(f"Fixed file kept as: {output_path}")

# Example usage for specific files:
def fix_january_2025():
    """Quick function to fix January 2025 file"""
    return fix_csv_mixed_dates("../data/jan_2025.csv", expected_year=2025, expected_month=1)

def fix_december_2024():
    """Quick function to fix December 2024 file"""
    return fix_csv_mixed_dates("../data/dec_2024.csv", expected_year=2024, expected_month=12)

def fix_february_2025():
    """Quick function to fix February 2025 file"""
    return fix_csv_mixed_dates("../data/feb_2025.csv", expected_year=2025, expected_month=2)

if __name__ == "__main__":
    # Run interactive mode
    main()
    
    # Or uncomment specific functions as needed:
    # fix_january_2025()
    # fix_december_2024()
    # fix_february_2025()