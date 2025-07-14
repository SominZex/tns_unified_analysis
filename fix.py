import pandas as pd
import os
from datetime import datetime

def fix_january_mixed_dates():
    """Fix January CSV file that has mixed date formats (dd/mm/yyyy and mm/dd/yyyy)"""
    
    # Path to your January CSV file
    jan_file_path = "./data/jan_2025.csv"
    
    if not os.path.exists(jan_file_path):
        print(f"File not found: {jan_file_path}")
        return
    
    print(f"Reading {jan_file_path}...")
    df = pd.read_csv(jan_file_path, dtype=str, keep_default_na=False)
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
            
            day_month, month_day, year = parts
            day_month, month_day, year = int(day_month), int(month_day), int(year)
            
            # If year is not 2025, skip this row
            if year != 2025:
                print(f"Skipping non-2025 date: {date_str}")
                return None
            
            # Logic to determine correct format:
            # If first number > 12, it must be day (dd/mm/yyyy format)
            if day_month > 12:
                day, month = day_month, month_day
                if month > 12 or month < 1:
                    print(f"Invalid month in dd/mm/yyyy: {date_str}")
                    return None
            # If second number > 12, it must be day (mm/dd/yyyy format)
            elif month_day > 12:
                month, day = day_month, month_day
                if month > 12 or month < 1:
                    print(f"Invalid month in mm/dd/yyyy: {date_str}")
                    return None
            # If both numbers <= 12, we need to make an assumption
            # Since this is January data, let's assume day should be <= 31 and month should be 1
            else:
                # For January data, month should be 1
                # So if first number is 1, it's likely mm/dd/yyyy
                # If second number is 1, it's likely dd/mm/yyyy
                if day_month == 1 and month_day <= 31:
                    # Likely mm/dd/yyyy format: 01/dd/2025
                    month, day = day_month, month_day
                elif month_day == 1 and day_month <= 31:
                    # Likely dd/mm/yyyy format: dd/01/2025
                    day, month = day_month, month_day
                else:
                    # Default assumption: dd/mm/yyyy for dates in January
                    # This assumes most of your data is in dd/mm/yyyy format
                    day, month = day_month, month_day
                    # But only if month would be 1 (January)
                    if month != 1:
                        # Try the other way
                        day, month = month_day, day_month
            
            # Validate the final day and month
            if month < 1 or month > 12:
                print(f"Invalid month {month} in: {date_str}")
                return None
            if day < 1 or day > 31:
                print(f"Invalid day {day} in: {date_str}")
                return None
            
            # For January data, ensure month is 1
            if month != 1:
                print(f"Non-January date found: {date_str} -> {day:02d}/{month:02d}/{year}")
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
        print("Failed dates:")
        failed_dates = df[df['orderDate_parsed'].isna()]['orderDate_original'].unique()
        for date in failed_dates[:10]:  # Show first 10 failed dates
            print(f"  {date}")
        if len(failed_dates) > 10:
            print(f"  ... and {len(failed_dates) - 10} more")
    
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
    backup_path = jan_file_path.replace('.csv', '_backup_mixed_dates.csv')
    print(f"Creating backup: {backup_path}")
    
    # Read original again for backup (to avoid changes)
    df_original = pd.read_csv(jan_file_path)
    df_original.to_csv(backup_path, index=False)
    
    # Save the cleaned file
    output_path = jan_file_path.replace('.csv', '_fixed.csv')
    print(f"Saving cleaned data to: {output_path}")
    df_clean.to_csv(output_path, index=False)
    
    print(f"""
SUMMARY:
- Original file: {jan_file_path} ({len(df)} rows)
- Backup created: {backup_path}
- Clean file created: {output_path} ({len(df_clean)} rows)
- You can now replace the original file with the fixed version
""")

if __name__ == "__main__":
    fix_january_mixed_dates()