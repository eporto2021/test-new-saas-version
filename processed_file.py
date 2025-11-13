"""
Custom data processor for user_18's service: Check each drop off has a pick up
Processes multiple files together to check for matching drop-offs and pick-ups.
"""
import math
import re
import pandas as pd
from datetime import datetime
from pathlib import Path
import tempfile
import os
from django.core.files.base import ContentFile


def format_date(date_str):
    """Format various date formats to DD/MM/YYYY."""
    try:
        if pd.isna(date_str):
            return date_str
        if isinstance(date_str, str):
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d', '%d-%m-%Y', '%m-%d-%Y']:
                try:
                    date_obj = datetime.strptime(date_str.split()[0], fmt)
                    return date_obj.strftime('%d/%m/%Y')
                except ValueError:
                    continue
        elif isinstance(date_str, (datetime, pd.Timestamp)):
            return date_str.strftime('%d/%m/%Y')
        return date_str
    except Exception:
        return date_str


def process_customer_data(file_paths):
    """
    Process customer data from multiple CSV/Excel files.
    
    Args:
        file_paths: List of file paths (strings or Path objects)
        
    Returns:
        dict: Dictionary mapping file paths to processed DataFrames
    """
    all_dataframes = {}
    all_phone_numbers = []  # Collect ALL phone numbers from ALL files
    
    print(f"Processing {len(file_paths)} files")

    # PHASE 1: Read all files and collect phone numbers
    for file_path in file_paths:
        file_path = Path(file_path)
        print(f"\nReading file: {file_path.name}")
        
        try:
            # Read the file with Mobile as string to preserve leading zeros
            if file_path.suffix in ('.xlsx', '.xls'):
                try:
                    df = pd.read_excel(file_path, engine='openpyxl' if file_path.suffix == '.xlsx' else 'xlrd', dtype={'Mobile': str})
                except Exception as e:
                    print(f"Failed to read as Excel, trying CSV: {e}")
                    df = pd.read_csv(file_path, dtype={'Mobile': str})
            else:
                df = pd.read_csv(file_path, dtype={'Mobile': str})
            
            # Create a copy for processing
            df_original = df.copy(deep=True)

        except Exception as e:
            print(f"ERROR: Could not read file {file_path}: {e}")
            continue

        if df_original.empty or len(df_original.columns) == 0:
            print(f"WARNING: Empty file detected: {file_path}")
            continue

        print(f"  - {len(df_original)} rows, {len(df_original.columns)} columns")

        # Clean Mobile numbers if the column exists
        if 'Mobile' in df_original.columns:
            # Keep original for reference
            df_original['Mobile_Original'] = df_original['Mobile'].copy()
            
            # Clean mobile numbers: fill NaN with '', strip whitespace, remove non-digits
            mobile_cleaned = df_original['Mobile'].fillna('').astype(str).str.strip()
            # Remove only non-digit characters (keep all digits including leading zeros)
            mobile_cleaned = mobile_cleaned.str.replace(r'[^\d]', '', regex=True)
            # Filter out empty strings
            mobile_cleaned = mobile_cleaned.replace('', pd.NA)
            
            # Update the dataframe with cleaned numbers
            df_original['Mobile'] = mobile_cleaned
            
            # Collect all valid (non-empty) phone numbers from this file
            valid_phones = mobile_cleaned.dropna().astype(str)
            valid_phones = valid_phones[valid_phones != '']
            all_phone_numbers.extend(valid_phones.tolist())
            
            print(f"  - Collected {len(valid_phones)} valid phone numbers")
            print(f"  - Sample: {valid_phones.head(5).tolist()}")

        # Format date columns
        date_columns = [col for col in df_original.columns if 'date' in col.lower() or 'delivery' in col.lower()]
        if date_columns:
            for col in date_columns:
                df_original[col] = df_original[col].apply(format_date)
            print(f"  - Formatted {len(date_columns)} date columns")

        # Drop specified columns during data cleansing
        columns_to_drop = ['Items', 'Balance', 'Surface', 'Picked up by someone else or another day', 
                          'Explanation', 'Mobile_Original']
        existing_columns_to_drop = [col for col in columns_to_drop if col in df_original.columns]
        if existing_columns_to_drop:
            df_original = df_original.drop(columns=existing_columns_to_drop)
            print(f"  - Dropped columns: {existing_columns_to_drop}")
        
        # Store the dataframe
        all_dataframes[str(file_path)] = df_original

    # PHASE 2: Count occurrences across ALL files
    print(f"\n=== PHONE NUMBER COUNTING ===")
    print(f"Total phone numbers collected from all files: {len(all_phone_numbers)}")
    
    # Count occurrences
    if all_phone_numbers:
        phone_counts = pd.Series(all_phone_numbers).value_counts().to_dict()
        print(f"Unique phone numbers: {len(phone_counts)}")
        
        # Show high occurrence numbers
        print(f"\nNumbers appearing multiple times:")
        for phone, count in sorted(phone_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            if count > 1:
                print(f"  {phone}: {count} times")
    else:
        phone_counts = {}
        print("No phone numbers collected!")

    # PHASE 3: Map counts back to each DataFrame
    for file_path, df in all_dataframes.items():
        print(f"\n=== PROCESSING: {Path(file_path).name} ===")
        
        if 'Mobile' in df.columns:
            # Initialize new columns
            df['Total Mobile Occurrences'] = 0
            df['Target Occurrences'] = 0
            df['Action Required'] = ''
            df['Notes'] = ''
            
            # For each row with a mobile number, look up its count
            for idx, phone in enumerate(df['Mobile']):
                if pd.notna(phone) and str(phone).strip() != '':
                    phone_str = str(phone).strip()
                    count = phone_counts.get(phone_str, 0)
                    df.loc[idx, 'Total Mobile Occurrences'] = count
                    
                    # Set target (you can modify this logic as needed)
                    df.loc[idx, 'Target Occurrences'] = 2
                    
                    # Set Action Required if count != target
                    if count != 2:
                        df.loc[idx, 'Action Required'] = 'Action Required'
            
            # Count how many need action
            action_count = (df['Action Required'] == 'Action Required').sum()
            print(f"Rows requiring action: {action_count}")
            
            # Debug: Show some examples
            sample_df = df[df['Mobile'].notna() & (df['Mobile'] != '')].head(5)
            if not sample_df.empty:
                print("\nSample mappings:")
                for _, row in sample_df.iterrows():
                    print(f"  Phone: {row['Mobile']} → Occurrences: {row['Total Mobile Occurrences']}")
        else:
            print("No Mobile column found in this file")

    print(f"\n=== COMPLETE ===")
    print(f"Processed {len(all_dataframes)} files successfully")

    return all_dataframes


def write_to_excel(processed_dfs, output_path):
    """
    Write processed DataFrames to an Excel file with formatting.
    
    Args:
        processed_dfs: Dictionary mapping file paths to DataFrames
        output_path: Path where the Excel file should be saved (string or Path object)
    """
    output_path = Path(output_path)
    print(f"\nWriting {len(processed_dfs)} DataFrames to Excel file: {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(exist_ok=True, parents=True)
    
    # Collect all rows that require action
    action_items = []
    for file_path, df in processed_dfs.items():
        if 'Action Required' in df.columns:
            action_rows = df[df['Action Required'] == 'Action Required'].copy()
            if not action_rows.empty:
                # Add a column to track which file this came from
                action_rows.insert(0, 'Source File', Path(file_path).name)
                action_items.append(action_rows)
    
    # Combine all action items into one DataFrame
    if action_items:
        action_items_df = pd.concat(action_items, ignore_index=True)
        # Sort by Customer Name column if it exists
        if 'Customer Name' in action_items_df.columns:
            action_items_df = action_items_df.sort_values('Customer Name', na_position='last')
            print(f"\nFound {len(action_items_df)} total action items across all files (sorted by Customer Name)")
        else:
            print(f"\nFound {len(action_items_df)} total action items across all files")
    else:
        action_items_df = pd.DataFrame()
        print("\nNo action items found")
    
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        # Write Action Items sheet FIRST (so it appears as the first tab)
        if not action_items_df.empty:
            # Select only the specified columns for Action Items sheet
            action_items_columns = [
                'Source File',
                'Type',
                'Total Mobile Occurrences',
                'Target Occurrences',
                'Action Required',
                'Delivery Date',
                'Drop Off',
                'Collection Date',
                'Collection',
                'Customer Name',
                'Mobile'
            ]
            
            # Filter to only include columns that exist in the dataframe
            available_columns = [col for col in action_items_columns if col in action_items_df.columns]
            action_items_display = action_items_df[available_columns].copy()
            
            print(f"\n  Writing sheet: Action Items ({len(action_items_display)} rows)")
            action_items_display.to_excel(writer, sheet_name='Action Items', index=False)
            
            # Format Action Items sheet
            workbook = writer.book
            worksheet = writer.sheets['Action Items']
            
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'bg_color': '#D9E1F2',
                'border': 1
            })
            
            highlight_format = workbook.add_format({
                'bg_color': '#FFC7CE',
                'font_color': '#9C0006',
                'bold': True
            })
            
            # Set column widths for Action Items
            for idx, col in enumerate(action_items_display.columns):
                if col == 'Source File':
                    worksheet.set_column(idx, idx, 30)
                elif 'date' in col.lower() or 'delivery' in col.lower():
                    worksheet.set_column(idx, idx, 12.67)
                elif col == 'Action Required':
                    worksheet.set_column(idx, idx, 25)
                elif col == 'Customer Name':
                    worksheet.set_column(idx, idx, 20)
                elif col == 'Mobile':
                    worksheet.set_column(idx, idx, 15)
                elif col == 'Type':
                    worksheet.set_column(idx, idx, 15)
                else:
                    max_len = min(max(action_items_display[col].astype(str).apply(len).max(), len(str(col))) + 2, 100)
                    worksheet.set_column(idx, idx, max_len)
            
            # Format headers
            for col_num, value in enumerate(action_items_display.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Highlight Action Required column
            if 'Action Required' in action_items_display.columns:
                action_col = action_items_display.columns.get_loc('Action Required')
                for row_num in range(1, len(action_items_display) + 1):
                    worksheet.write(row_num, action_col, 'Action Required', highlight_format)
        
        # Now write individual file sheets
        for file_path, df in processed_dfs.items():
            # Create sheet name from original filename (max 31 chars for Excel)
            sheet_name = Path(file_path).stem[:31]
            print(f"  Writing sheet: {sheet_name} ({len(df)} rows)")
            
            # Write dataframe to sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Get workbook and worksheet objects for formatting
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'bg_color': '#D9E1F2',
                'border': 1
            })
            
            highlight_format = workbook.add_format({
                'bg_color': '#FFC7CE',
                'font_color': '#9C0006',
                'bold': True
            })
            
            green_format = workbook.add_format({
                'bg_color': '#C6EFCE',
                'font_color': '#006100'
            })
            
            # Set column widths
            for idx, col in enumerate(df.columns):
                if 'date' in col.lower() or 'delivery' in col.lower():
                    worksheet.set_column(idx, idx, 12.67)
                elif col == 'Action Required':
                    worksheet.set_column(idx, idx, 25)
                elif col == 'Notes':
                    worksheet.set_column(idx, idx, 85)
                else:
                    max_len = min(max(df[col].astype(str).apply(len).max(), len(str(col))) + 2, 100)
                    worksheet.set_column(idx, idx, max_len)
            
            # Format headers
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Handle Action Required column if it exists
            if 'Action Required' in df.columns:
                action_col = df.columns.get_loc('Action Required')
                
                # Highlight "Action Required" cells
                for row_num, value in enumerate(df['Action Required'], start=1):
                    if value == 'Action Required':
                        worksheet.write(row_num, action_col, value, highlight_format)
                
                # Add drop-down list to Action Required column
                worksheet.data_validation(1, action_col, len(df), action_col, {
                    'validate': 'list',
                    'source': ['Action Required', 'Issue Resolved See Notes'],
                    'input_message': 'Select an action',
                    'error_message': 'Invalid option',
                })
                
                # Add conditional formatting for "Action Required"
                worksheet.conditional_format(1, action_col, len(df), action_col, {
                    'type': 'cell',
                    'criteria': '==',
                    'value': '"Action Required"',
                    'format': highlight_format
                })
                
                # Add conditional formatting for "Issue Resolved See Notes"
                worksheet.conditional_format(1, action_col, len(df), action_col, {
                    'type': 'cell',
                    'criteria': '==',
                    'value': '"Issue Resolved See Notes"',
                    'format': green_format
                })
    
    print(f"\nSuccessfully saved to: {output_path}")
    return output_path


def process_user_18_files(data_files):
    """
    Process multiple files for user_18's service.
    Integrates with Django models and file storage.
    
    Args:
        data_files: QuerySet or list of UserDataFile objects
        
    Returns:
        tuple: (processed_file, summary_data)
    """
    from django.core.files.storage import default_storage
    
    # Collect file paths
    file_paths = []
    for data_file in data_files:
        file_paths.append(data_file.file.path)
    
    if not file_paths:
        raise ValueError("No files to process")
    
    # Process the data
    processed_dfs = process_customer_data(file_paths)
    
    # Create output file
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp_file:
        output_path = tmp_file.name
    
    # Write to Excel
    write_to_excel(processed_dfs, output_path)
    
    # Read the file content
    with open(output_path, 'rb') as f:
        file_content = f.read()
    
    # Clean up temp file    
    os.unlink(output_path)
    
    # Create ContentFile for Django
    from django.utils import timezone
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"processed_data_{timestamp}.xlsx"
    processed_file = ContentFile(file_content, name=filename)
    
    # Create summary
    total_rows = sum(len(df) for df in processed_dfs.values())
    total_action_items = sum((df['Action Required'] == 'Action Required').sum() 
                             for df in processed_dfs.values() 
                             if 'Action Required' in df.columns)
    
    # Convert numpy int64 to Python int for JSON serialization
    summary = {
        'files_processed': int(len(data_files)),
        'total_rows': int(total_rows),
        'action_items': int(total_action_items),
        'processing_timestamp': timezone.now().isoformat(),
    }
    
    return processed_file, summary

