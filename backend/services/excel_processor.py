import pandas as pd
from datetime import datetime
from services.database_service import save_complete_trial_balance


def process_trial_balance_file(filepath, upload_id, original_filename, company):
    """Process uploaded Excel trial balance file"""
    try:
        # Read and validate Excel file
        df = pd.read_excel(filepath, sheet_name=0)
        required_columns = validate_trial_balance_format(df)
        cleaned_data = clean_trial_balance_data(df, required_columns)
        period_end_date = extract_period_end_date(df)
        
        # Save everything in one transaction with company parameter
        result = save_complete_trial_balance(upload_id, original_filename, period_end_date, cleaned_data, company)
        
        return {
            'success': True,
            'rows_processed': result['rows_processed'],
            'period_end_date': result['period_end_date'],
            'company': company
        }
        
    except Exception as e:
        raise Exception(f"Excel processing error: {str(e)}")
    
def validate_trial_balance_format(df):
    """
    Validate that the Excel file has the required columns
    """
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    
    # Define possible column name variations
    gl_code_columns = ['GL Code', 'GL_Code', 'Account Code', 'Code', 'gl_code']
    account_name_columns = ['Account Name', 'Account_Name', 'Description', 'account_name']
    amount_columns = ['Amount', 'Balance', 'Net Amount', 'amount']
    
    # Find the actual column names
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

def find_column(df_columns, possible_names):
    """
    Find a column name from a list of possible variations
    """
    for col in df_columns:
        if col in possible_names:
            return col
    return None

def clean_trial_balance_data(df, column_mapping):
    """
    Clean and standardize the trial balance data
    """
    # Select and rename columns
    cleaned_df = df[[
        column_mapping['gl_code'],
        column_mapping['account_name'], 
        column_mapping['amount']
    ]].copy()
    
    cleaned_df.columns = ['gl_code', 'account_name', 'amount']
    
    # Remove rows where GL code is null/empty
    cleaned_df = cleaned_df.dropna(subset=['gl_code'])
    cleaned_df = cleaned_df[cleaned_df['gl_code'].astype(str).str.strip() != '']
    
    # Clean GL codes (remove spaces, convert to string)
    cleaned_df['gl_code'] = cleaned_df['gl_code'].astype(str).str.strip()
    
    # Clean account names
    cleaned_df['account_name'] = cleaned_df['account_name'].fillna('').astype(str).str.strip()
    
    # Clean amounts (handle various formats)
    cleaned_df['amount'] = pd.to_numeric(cleaned_df['amount'], errors='coerce').fillna(0)
    
    # Remove rows with zero amounts (optional)
    # cleaned_df = cleaned_df[cleaned_df['amount'] != 0]
    
    return cleaned_df

def extract_period_end_date(df):
    """
    Try to extract period end date from Excel file
    For now, return current date - you can enhance this later
    """
    # TODO: Look for date in specific cells or filename
    # For now, return end of current month
    today = datetime.now()
    if today.month == 12:
        return datetime(today.year + 1, 1, 1).date()
    else:
        return datetime(today.year, today.month + 1, 1).date()