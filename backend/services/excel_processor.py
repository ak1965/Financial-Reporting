import pandas as pd
from datetime import datetime
from services.database_service import save_complete_trial_balance
from services.database_service import save_complete_trial_balance_multi_period


def process_trial_balance_file(filepath, upload_id, original_filename, company):
    """Process uploaded Excel trial balance file with multiple worksheets and monthly columns"""
    excel_file = None
    try:
        # Read all three worksheets - DON'T let pandas auto-parse dates
        excel_file = pd.ExcelFile(filepath)
        
        actual_sheet = find_sheet_name(excel_file.sheet_names, ['Actual', 'Actuals', 'actual'])
        budget_sheet = find_sheet_name(excel_file.sheet_names, ['Budget', 'budget'])
        prior_year_sheet = find_sheet_name(excel_file.sheet_names, ['Prior Year', 'Prior_Year', 'PriorYear', 'prior year'])
        
        if not all([actual_sheet, budget_sheet, prior_year_sheet]):
            raise Exception(f"Missing required worksheets. Found: {excel_file.sheet_names}")
        
        # Read sheets WITHOUT parsing dates automatically
        # Read sheets normally
        df_actual = pd.read_excel(excel_file, sheet_name=actual_sheet)
        df_budget = pd.read_excel(excel_file, sheet_name=budget_sheet)
        df_prior_year = pd.read_excel(excel_file, sheet_name=prior_year_sheet)
        
        excel_file.close()
        
        print(f"🔍 Actual columns (raw strings): {df_actual.columns.tolist()}")
        
        actual_data = process_worksheet(df_actual, 'actual')
        budget_data = process_worksheet(df_budget, 'budget')
        prior_year_data = process_worksheet(df_prior_year, 'prior_year')
        
        # ... rest of your code
        
        # Determine the latest period end date from column headers
        period_end_date = extract_latest_period_date(df_actual)
        
        # Combine all data
        combined_data = combine_worksheet_data(actual_data, budget_data, prior_year_data)
        
        # Save everything in one transaction
        result = save_complete_trial_balance_multi_period(
            upload_id, 
            original_filename, 
            period_end_date, 
            combined_data, 
            company
        )
        
        return {
            'success': True,
            'rows_processed': result['rows_processed'],
            'period_end_date': result['period_end_date'],
            'company': company,
            'periods_loaded': result['periods_loaded']
        }
        
    except Exception as e:
        raise Exception(f"Excel processing error: {str(e)}")
    finally:
        # Ensure Excel file is closed
        if excel_file is not None:
            try:
                excel_file.close()
            except:
                pass


from datetime import datetime
import pandas as pd

def process_worksheet(df, data_type):
    """Process a single worksheet with monthly columns"""
    
    print(f"🔍 Processing {data_type} worksheet")
    
    # Get the raw columns
    raw_columns = df.columns.tolist()
    print(f"🔍 Raw columns: {raw_columns}")
    print(f"🔍 Column types: {[type(col).__name__ for col in raw_columns]}")
    
    # Find GL Code and Account Name columns
    gl_code_col = None
    account_name_col = None
    
    for col in raw_columns:
        col_str = str(col).strip()
        if col_str in ['GL Code', 'GL_Code', 'Account Code', 'Code', 'gl_code']:
            gl_code_col = col
        if col_str in ['Account Name', 'Account_Name', 'Description', 'account_name']:
            account_name_col = col
    
    if not gl_code_col or not account_name_col:
        raise Exception(f"Missing GL Code or Account Name column. Found: {[str(c) for c in raw_columns]}")
    
    print(f"🔍 GL Code column: {gl_code_col}")
    print(f"🔍 Account Name column: {account_name_col}")
    
    # Find date columns
    date_columns = {}
    
    for col in raw_columns:
        # Skip text columns
        if col == gl_code_col or col == account_name_col:
            continue
        
        col_str = str(col).strip()
        if col_str == 'nan' or col_str == '':
            continue
        
        print(f"🔍 Checking column: '{col_str}' (type: {type(col)})")
        
        date_obj = None
        
        # Method 1: If it's a datetime.datetime object (from Excel)
        if isinstance(col, datetime):
            date_obj = col.date()
            print(f"  ✅ datetime.datetime -> {date_obj}")
        
        # Method 2: If pandas parsed it as Timestamp
        elif isinstance(col, pd.Timestamp):
            date_obj = col.date()
            print(f"  ✅ Pandas Timestamp -> {date_obj}")
        
        # Method 3: Try parsing the string representation  
        else:
            # Split by common separators
            for separator in ['/', '-', '.']:
                if separator in col_str:
                    parts = col_str.split(separator)
                    if len(parts) == 3:
                        try:
                            # Try DD/MM/YYYY
                            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                            date_obj = datetime(year, month, day).date()
                            print(f"  ✅ Parsed as DD{separator}MM{separator}YYYY -> {date_obj}")
                            break
                        except (ValueError, IndexError):
                            try:
                                # Try MM/DD/YYYY
                                month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
                                date_obj = datetime(year, month, day).date()
                                print(f"  ⚠️ Parsed as MM{separator}DD{separator}YYYY -> {date_obj}")
                                break
                            except (ValueError, IndexError):
                                pass
        
        if date_obj:
            date_columns[col] = date_obj
        else:
            print(f"  ❌ Could not parse as date")
    
    print(f"🔍 Found {len(date_columns)} date columns: {list(date_columns.values())}")
    
    if not date_columns:
        raise Exception(f"No valid date columns found in {data_type} worksheet.")
    
    # Process data
    processed_data = []
    
    for idx, row in df.iterrows():
        gl_code = str(row[gl_code_col]).strip() if pd.notna(row[gl_code_col]) else ''
        account_name = str(row[account_name_col]).strip() if pd.notna(row[account_name_col]) else ''
        
        if not gl_code or gl_code == 'nan':
            continue
        
        for date_col, period_date in date_columns.items():
            try:
                amount = float(pd.to_numeric(row[date_col], errors='coerce'))
                if pd.isna(amount) or amount == 0:
                    continue
                
                processed_data.append({
                    'gl_code': gl_code,
                    'account_name': account_name,
                    'period_end_date': period_date,
                    'amount': amount,
                    'data_type': data_type
                })
            except:
                continue
    
    print(f"✅ Processed {len(processed_data)} rows for {data_type}")
    if processed_data:
        print(f"🔍 Date samples: {sorted(set([d['period_end_date'] for d in processed_data[:20]]))}")
    
    return processed_data

def find_sheet_name(sheet_names, possible_names):
    """Find worksheet name from possible variations (case-insensitive)"""
    for sheet in sheet_names:
        for possible in possible_names:
            if sheet.lower() == possible.lower():
                return sheet
    return None





def extract_latest_period_date(df):
    """Extract the latest period date from column headers"""
    df.columns = df.columns.str.strip()
    
    date_columns = []
    for col in df.columns:
        try:
            parsed_date = pd.to_datetime(col, errors='coerce', dayfirst=True)
            if pd.notna(parsed_date):
                date_columns.append(parsed_date.date())
        except:
            pass
    
    if not date_columns:
        # If no date columns found, return end of current month as fallback
        today = datetime.now()
        if today.month == 12:
            return datetime(today.year + 1, 1, 1).date()
        else:
            return datetime(today.year, today.month + 1, 1).date()
    
    return max(date_columns)


def combine_worksheet_data(actual_data, budget_data, prior_year_data):
    """Combine data from all three worksheets"""
    return actual_data + budget_data + prior_year_data


def find_column(df_columns, possible_names):
    """Find a column name from a list of possible variations"""
    for col in df_columns:
        if col in possible_names:
            return col
    return None


# Keep your existing validation functions for backward compatibility
def validate_trial_balance_format(df):
    """Validate that the Excel file has the required columns (legacy function)"""
    df.columns = df.columns.str.strip()
    
    gl_code_columns = ['GL Code', 'GL_Code', 'Account Code', 'Code', 'gl_code']
    account_name_columns = ['Account Name', 'Account_Name', 'Description', 'account_name']
    amount_columns = ['Amount', 'Balance', 'Net Amount', 'amount']
    
    gl_code_col = find_column(df.columns, gl_code_columns)
    account_name_col = find_column(df.columns, account_name_columns)
    amount_col = find_column(df.columns, amount_columns)
    
    if not all([gl_code_col, account_name_col, amount_col]):
        missing = []
        if not gl_code_col: missing.append("GL Code")
        if not account_name_col: missing.append("Account Name") 
        if not amount_col: missing.append("Amount")
        raise Exception(f"Missing required columns: {', '.join(missing)}")
    
    return {
        'gl_code': gl_code_col,
        'account_name': account_name_col,
        'amount': amount_col
    }


def clean_trial_balance_data(df, column_mapping):
    """Clean and standardize the trial balance data (legacy function)"""
    cleaned_df = df[[
        column_mapping['gl_code'],
        column_mapping['account_name'], 
        column_mapping['amount']
    ]].copy()
    
    cleaned_df.columns = ['gl_code', 'account_name', 'amount']
    
    cleaned_df = cleaned_df.dropna(subset=['gl_code'])
    cleaned_df = cleaned_df[cleaned_df['gl_code'].astype(str).str.strip() != '']
    
    cleaned_df['gl_code'] = cleaned_df['gl_code'].astype(str).str.strip()
    cleaned_df['account_name'] = cleaned_df['account_name'].fillna('').astype(str).str.strip()
    cleaned_df['amount'] = pd.to_numeric(cleaned_df['amount'], errors='coerce').fillna(0)
    
    return cleaned_df