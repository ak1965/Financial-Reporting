import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        raise Exception(f"Database connection failed: {str(e)}")


def update_upload_status(upload_id, status, error_message=None):
    """Update upload status and optional error message"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if error_message:
                # Add error_message column if it doesn't exist
                query = """
                UPDATE trial_balance_uploads 
                SET processing_status = %s, error_message = %s
                WHERE upload_id = %s
                """
                cursor.execute(query, (status, error_message, upload_id))
            else:
                query = """
                UPDATE trial_balance_uploads 
                SET processing_status = %s
                WHERE upload_id = %s
                """
                cursor.execute(query, (status, upload_id))
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to update upload status: {str(e)}")
    finally:
        conn.close()

def save_complete_trial_balance(upload_id, filename, period_end_date, df):
    """Save both upload record and data in a single transaction"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Start transaction
            cursor.execute("BEGIN;")
            
            # 1. Save upload record as 'processing'
            upload_query = """
            INSERT INTO trial_balance_uploads 
            (upload_id, filename, upload_date, period_end_date, row_count, processing_status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(upload_query, (
                upload_id, filename, datetime.now(), period_end_date, len(df), 'processing'
            ))
            
            # 2. Aggregate duplicate GL codes
            aggregated_df = df.groupby('gl_code').agg({
                'account_name': 'first',
                'amount': 'sum'
            }).reset_index()
            
            # 3. Save trial balance data
            data_tuples = [
                (upload_id, row['gl_code'], row['account_name'], row['amount'])
                for _, row in aggregated_df.iterrows()
            ]
            
            data_query = """
            INSERT INTO trial_balance_data (upload_id, gl_code, account_name, amount)
            VALUES (%s, %s, %s, %s)
            """
            cursor.executemany(data_query, data_tuples)
            
            # 4. Update status to 'complete'
            status_query = "UPDATE trial_balance_uploads SET processing_status = 'complete' WHERE upload_id = %s"
            cursor.execute(status_query, (upload_id,))
            
            # Commit everything together
            cursor.execute("COMMIT;")
            
            return {
                'rows_processed': len(data_tuples),
                'period_end_date': period_end_date
            }
            
    except Exception as e:
        cursor.execute("ROLLBACK;")
        raise Exception(f"Failed to save trial balance: {str(e)}")
    finally:
        conn.close()

def get_uploaded_trial_balances():
    """Get list of uploaded trial balances for user to select from"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            SELECT upload_id, filename, period_end_date, upload_date, row_count
            FROM trial_balance_uploads 
            WHERE processing_status = 'complete'
            ORDER BY period_end_date DESC, upload_date DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        raise Exception(f"Failed to get trial balances: {str(e)}")
    finally:
        conn.close()

def get_trial_balance_gl_codes(upload_id):
    """Get all GL codes from a specific trial balance"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            SELECT gl_code, account_name, amount
            FROM trial_balance_data 
            WHERE upload_id = %s
            ORDER BY gl_code
            """
            cursor.execute(query, (upload_id,))
            return cursor.fetchall()
    except Exception as e:
        raise Exception(f"Failed to get GL codes: {str(e)}")
    finally:
        conn.close()

def get_existing_mappings(report_type):
    """Get existing GL mappings for a report type"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            SELECT gl_code, line_id, sign_multiplier
            FROM gl_report_mapping 
            WHERE report_type = %s
            """
            cursor.execute(query, (report_type,))
            return cursor.fetchall()
    except Exception as e:
        raise Exception(f"Failed to get existing mappings: {str(e)}")
    finally:
        conn.close()

def save_gl_mapping(gl_code, report_type, line_id, sign_multiplier):
    """Save or update a GL mapping"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
            INSERT INTO gl_report_mapping (gl_code, report_type, line_id, sign_multiplier)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (gl_code, report_type) 
            DO UPDATE SET 
                line_id = EXCLUDED.line_id,
                sign_multiplier = EXCLUDED.sign_multiplier
            """
            cursor.execute(query, (gl_code, report_type, line_id, sign_multiplier))
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to save mapping: {str(e)}")
    finally:
        conn.close()

def delete_gl_mapping(gl_code, report_type):
    """Delete a GL mapping"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = "DELETE FROM gl_report_mapping WHERE gl_code = %s AND report_type = %s"
            cursor.execute(query, (gl_code, report_type))
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to delete mapping: {str(e)}")
    finally:
        conn.close()

def get_available_periods():
    """Get list of available reporting periods"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            SELECT DISTINCT period_end_date
            FROM trial_balance_uploads 
            WHERE processing_status = 'complete'
            ORDER BY period_end_date DESC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return [row['period_end_date'].isoformat() for row in results]
    except Exception as e:
        raise Exception(f"Failed to get available periods: {str(e)}")
    finally:
        conn.close()

def get_report_data(report_type, period_end_date):
    """Get aggregated data for report generation"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get the main report data
            query = """
            SELECT 
                grm.line_id,
                SUM(tbd.amount * grm.sign_multiplier) as total_amount
            FROM trial_balance_data tbd
            JOIN trial_balance_uploads tbu ON tbd.upload_id = tbu.upload_id
            JOIN gl_report_mapping grm ON tbd.gl_code = grm.gl_code
            WHERE tbu.period_end_date = %s 
            AND grm.report_type = %s
            GROUP BY grm.line_id
            """
            cursor.execute(query, (period_end_date, report_type))
            results = cursor.fetchall()
            data = {row['line_id']: float(row['total_amount']) for row in results}
            
            # If this is a balance sheet, add P&L profit to reserves
            if report_type == 'balance_sheet':
                # Get P&L profit
                pl_query = """
                SELECT 
                    SUM(tbd.amount * grm.sign_multiplier) as net_profit
                FROM trial_balance_data tbd
                JOIN trial_balance_uploads tbu ON tbd.upload_id = tbu.upload_id
                JOIN gl_report_mapping grm ON tbd.gl_code = grm.gl_code
                WHERE tbu.period_end_date = %s 
                AND grm.report_type = 'profit_loss'
                """
                cursor.execute(pl_query, (period_end_date,))
                profit_result = cursor.fetchone()
                net_profit = float(profit_result['net_profit']) if profit_result['net_profit'] else 0
                
                # Add profit to reserves (assuming reserves is line_id 3001 or similar)
                reserves_line_id = 2600  # Update this to match your reserves line_id
                if reserves_line_id in data:
                    data[reserves_line_id] += net_profit
                else:
                    data[reserves_line_id] = net_profit
            
            return data
                  
    except Exception as e:
        raise Exception(f"Failed to get report data: {str(e)}")
    finally:
        conn.close()