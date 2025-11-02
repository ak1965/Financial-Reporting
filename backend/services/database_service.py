import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

# try this 

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

def save_complete_trial_balance_multi_period(upload_id, filename, period_end_date, combined_data, company):
    """Save trial balance with multiple periods and data types"""
    print(f"🔍 Saving {len(combined_data)} rows to database")
    print(f"🔍 Upload ID: {upload_id}")
    print(f"🔍 Company: {company}")
    print(f"🔍 Period end date: {period_end_date}")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            row_count = len(combined_data)
            
            # 1. Save upload record
            upload_query = """
                INSERT INTO trial_balance_uploads 
                (upload_id, filename, upload_date, period_end_date, uploaded_by, processing_status, row_count, company)
                VALUES (%s, %s, NOW(), %s, %s, %s, %s, %s)
            """
            cursor.execute(upload_query, (
                upload_id, 
                filename, 
                period_end_date, 
                'system', 
                'complete', 
                row_count, 
                company
            ))
            
            print(f"✅ Upload record saved")
            
            # 2. Save all trial balance data
            data_query = """
                INSERT INTO trial_balance_data 
                (upload_id, gl_code, account_name, period_end_date, amount, data_type)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            data_tuples = [
                (upload_id, row['gl_code'], row['account_name'], 
                 row['period_end_date'], row['amount'], row['data_type'])
                for row in combined_data
            ]
            
            print(f"🔍 Created {len(data_tuples)} tuples to insert")
            if data_tuples:
                print(f"🔍 First tuple sample: {data_tuples[0]}")
                print(f"🔍 Last tuple sample: {data_tuples[-1]}")
            else:
                print(f"⚠️ WARNING: No data tuples created!")
            
            if data_tuples:
                cursor.executemany(data_query, data_tuples)
                print(f"✅ Executed INSERT for {len(data_tuples)} rows")
            else:
                print(f"⚠️ Skipping INSERT - no data to insert")
            
            conn.commit()
            print(f"✅ Transaction committed")
            
        # Count unique periods
        periods_loaded = len(set(row['period_end_date'] for row in combined_data)) if combined_data else 0
        
        print(f"✅ Save complete. Periods loaded: {periods_loaded}")
        
        return {
            'rows_processed': len(data_tuples),
            'period_end_date': period_end_date,
            'periods_loaded': periods_loaded
        }
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during save: {str(e)}")
        raise Exception(f"Failed to save trial balance: {str(e)}")
    finally:
        conn.close()

def save_complete_trial_balance(upload_id, filename, period_end_date, df, company):
    """Save both upload record and data in a single transaction"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Calculate row count
            row_count = len(df)
            
            # 1. Save upload record with ALL columns
            upload_query = """
                INSERT INTO trial_balance_uploads 
                (upload_id, filename, upload_date, period_end_date, uploaded_by, processing_status, row_count, company)
                VALUES (%s, %s, NOW(), %s, %s, %s, %s, %s)
            """
            cursor.execute(upload_query, (
                upload_id, 
                filename, 
                period_end_date, 
                'system',  # or get from request.user if you have authentication
                'complete', 
                row_count, 
                company
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
            
            # Commit everything together
            conn.commit()
            
        return {
            'rows_processed': len(data_tuples),
            'period_end_date': period_end_date
        }
            
    except Exception as e:
        conn.rollback()
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

def get_trial_balance_gl_codes(upload_id, data_type='actual'):
    """Get all GL codes from a specific trial balance"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            SELECT gl_code, account_name, amount
            FROM trial_balance_data 
            WHERE upload_id = %s
            AND data_type = %s
            ORDER BY gl_code
            """
            cursor.execute(query, (upload_id, data_type))
            return cursor.fetchall()
    except Exception as e:
        raise Exception(f"Failed to get GL codes: {str(e)}")
    finally:
        conn.close()

def get_existing_gl_mappings(report_type):
    """Get existing GL code mappings (what's already mapped)"""
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
        
def get_available_report_lines(report_type):
    """Get available report lines for dropdown options"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            SELECT section_name, line_id, line_name, sign_multiplier
            FROM report_line_definitions
            WHERE report_type = %s
            ORDER BY display_order
            """
            cursor.execute(query, (report_type,))
            return cursor.fetchall()
    except Exception as e:
        raise Exception(f"Failed to get report lines: {str(e)}")
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

def delete_tb_by_company_period(company, period):
    """Delete a trial balance by company and period"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # First, find the upload_id
            query_find = """
                SELECT upload_id 
                FROM trial_balance_uploads 
                WHERE company = %s AND period_end_date = %s
            """
            cursor.execute(query_find, (company, period))
            result = cursor.fetchone()
            
            if not result:
                raise Exception(f"No trial balance found for {company} on {period}")
            
            upload_id = result[0]
            
            # Then delete from trial_balance_data using the upload_id
            query_delete = "DELETE FROM trial_balance_data WHERE upload_id = %s"
            cursor.execute(query_delete, (upload_id,))
            
            # Optionally, also delete from trial_balance_uploads
            query_delete_upload = "DELETE FROM trial_balance_uploads WHERE upload_id = %s"
            cursor.execute(query_delete_upload, (upload_id,))
            
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to delete trial balance: {str(e)}")
    finally:
        conn.close()

def get_available_periods(company):
    """Get list of available reporting periods for a specific company - ACTUAL data only"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            SELECT DISTINCT period_end_date
            FROM trial_balance_data 
            WHERE data_type = 'actual'
            AND upload_id IN (
                SELECT upload_id 
                FROM trial_balance_uploads 
                WHERE company = %s 
                AND processing_status = 'complete'
            )
            ORDER BY period_end_date DESC
            """
            cursor.execute(query, (company,))
            results = cursor.fetchall()
            return [row['period_end_date'].isoformat() for row in results]
    except Exception as e:
        raise Exception(f"Failed to get available periods: {str(e)}")
    finally:
        conn.close()

def get_available_periods_delete(company):
    """Get list of available reporting periods for a specific company - ACTUAL data only"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            SELECT DISTINCT period_end_date
            FROM trial_balance_uploads           
            WHERE company = %s 
            AND processing_status = 'complete'
            ORDER BY period_end_date DESC
            """
            cursor.execute(query, (company,))
            results = cursor.fetchall()
            return [row['period_end_date'].isoformat() for row in results]
    except Exception as e:
        raise Exception(f"Failed to get available periods: {str(e)}")
    finally:
        conn.close()

def get_available_companies():
    """Get list of available companies"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            SELECT DISTINCT company
            FROM trial_balance_uploads 
            WHERE processing_status = 'complete'
            ORDER BY company DESC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return [row['company'] for row in results]
    except Exception as e:
        raise Exception(f"Failed to get available companies: {str(e)}")
    finally:
        conn.close()



# def get_report_data(report_type, period_end_date, company, data_type='actual'):
#     """Get aggregated data for report generation"""
#     conn = get_db_connection()
#     try:
#         with conn.cursor(cursor_factory=RealDictCursor) as cursor:
#             # Get the main report data
#             query = """
#             SELECT 
#                 grm.line_id,
#                 SUM(tbd.amount * grm.sign_multiplier) as total_amount
#             FROM trial_balance_data tbd
#             JOIN trial_balance_uploads tbu ON tbd.upload_id = tbu.upload_id
#             JOIN gl_report_mapping grm ON tbd.gl_code = grm.gl_code
#             WHERE tbd.period_end_date = %s 
#             AND tbu.company = %s
#             AND tbd.data_type = %s
#             AND grm.report_type = %s
#             GROUP BY grm.line_id
#             """
#             cursor.execute(query, (period_end_date, company, data_type, report_type))
#             results = cursor.fetchall()
#             data = {row['line_id']: float(row['total_amount']) for row in results}
            
#             # If this is a balance sheet, add P&L profit to reserves
#             if report_type == 'balance_sheet':
#                 # Get P&L profit
#                 pl_query = """
#                 SELECT 
#                     SUM(tbd.amount * grm.sign_multiplier) as net_profit
#                 FROM trial_balance_data tbd
#                 JOIN trial_balance_uploads tbu ON tbd.upload_id = tbu.upload_id
#                 JOIN gl_report_mapping grm ON tbd.gl_code = grm.gl_code
#                 WHERE tbu.period_end_date = %s 
#                 AND tbu.company = %s
#                 AND tbd.data_type = %s
#                 AND grm.report_type = 'profit_loss'
#                 """
#                 cursor.execute(pl_query, (period_end_date, company, data_type))
#                 profit_result = cursor.fetchone()
#                 net_profit = float(profit_result['net_profit']) if profit_result['net_profit'] else 0
                
#                 # Add profit to reserves (assuming reserves is line_id 2600)
#                 reserves_line_id = 2600
#                 if reserves_line_id in data:
#                     data[reserves_line_id] += net_profit
#                 else:
#                     data[reserves_line_id] = net_profit
            
#             return data
                  
#     except Exception as e:
#         raise Exception(f"Failed to get report data: {str(e)}")
#     finally:
#         conn.close()
def get_report_data(report_type, period_end_date, company):
    """Get complete report data with all columns for either P&L or Balance Sheet"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if report_type == 'profit_loss':
                # P&L specific query - using data_type fields directly
                query = """
                SELECT 
                    grm.line_id,
                    -- Current period actual
                    SUM(CASE WHEN tbd.data_type = 'actual' 
                        AND DATE_TRUNC('month', tbd.period_end_date) = DATE_TRUNC('month', %s::date)
                        AND EXTRACT(YEAR FROM tbd.period_end_date) = EXTRACT(YEAR FROM %s::date)
                        THEN tbd.amount * grm.sign_multiplier ELSE 0 END) as actual,
                    -- Current period budget
                    SUM(CASE WHEN tbd.data_type = 'budget' 
                        AND DATE_TRUNC('month', tbd.period_end_date) = DATE_TRUNC('month', %s::date)
                        AND EXTRACT(YEAR FROM tbd.period_end_date) = EXTRACT(YEAR FROM %s::date)
                        THEN tbd.amount * grm.sign_multiplier ELSE 0 END) as budget,
                    -- Prior year from database (looking for 2024 dates)
                    SUM(CASE WHEN tbd.data_type = 'prior_year' 
                        AND DATE_TRUNC('month', tbd.period_end_date) = DATE_TRUNC('month', %s::date - INTERVAL '1 year')
                        AND EXTRACT(YEAR FROM tbd.period_end_date) = EXTRACT(YEAR FROM %s::date) - 1
                        THEN tbd.amount * grm.sign_multiplier ELSE 0 END) as prior_year,
                    -- YTD Actual
                    SUM(CASE WHEN tbd.data_type = 'actual' 
                        AND EXTRACT(YEAR FROM tbd.period_end_date) = EXTRACT(YEAR FROM %s::date)
                        AND tbd.period_end_date <= %s::date
                        THEN tbd.amount * grm.sign_multiplier ELSE 0 END) as ytd_actual,
                    -- YTD Budget
                    SUM(CASE WHEN tbd.data_type = 'budget' 
                        AND EXTRACT(YEAR FROM tbd.period_end_date) = EXTRACT(YEAR FROM %s::date)
                        AND tbd.period_end_date <= %s::date
                        THEN tbd.amount * grm.sign_multiplier ELSE 0 END) as ytd_budget,
                    -- Prior Year YTD from database (looking for 2024 dates)
                    SUM(CASE WHEN tbd.data_type = 'prior_year' 
                        AND EXTRACT(YEAR FROM tbd.period_end_date) = EXTRACT(YEAR FROM %s::date) - 1
                        AND tbd.period_end_date <= %s::date - INTERVAL '1 year'
                        THEN tbd.amount * grm.sign_multiplier ELSE 0 END) as prior_ytd
                FROM trial_balance_data tbd
                JOIN trial_balance_uploads tbu ON tbd.upload_id = tbu.upload_id
                JOIN gl_report_mapping grm ON tbd.gl_code = grm.gl_code
                WHERE tbu.company = %s
                AND grm.report_type = %s
                GROUP BY grm.line_id
                """
                cursor.execute(query, (
                    period_end_date, period_end_date,  # actual
                    period_end_date, period_end_date,  # budget
                    period_end_date, period_end_date,  # prior_year (from data_type='prior_year')
                    period_end_date, period_end_date,  # ytd_actual
                    period_end_date, period_end_date,  # ytd_budget
                    period_end_date, period_end_date,  # prior_ytd (from data_type='prior_year')
                    company, report_type
                ))
                
            elif report_type == 'balance_sheet':
                # Balance Sheet query - no YTD needed, just point-in-time balances
                query = """
                SELECT 
                    grm.line_id,
                    -- Current period actual
                    SUM(CASE WHEN tbd.data_type = 'actual' 
                        AND tbd.period_end_date = %s::date 
                        THEN tbd.amount * grm.sign_multiplier ELSE 0 END) as actual,
                    -- Current period budget
                    SUM(CASE WHEN tbd.data_type = 'budget' 
                        AND tbd.period_end_date = %s::date 
                        THEN tbd.amount * grm.sign_multiplier ELSE 0 END) as budget,
                    -- Prior year same period
                    SUM(CASE WHEN tbd.data_type = 'actual' 
                        AND tbd.period_end_date = %s::date - INTERVAL '1 year'
                        THEN tbd.amount * grm.sign_multiplier ELSE 0 END) as prior_year,
                    -- Prior month actual (useful for balance sheet movements)
                    SUM(CASE WHEN tbd.data_type = 'actual' 
                        AND tbd.period_end_date = %s::date - INTERVAL '1 month'
                        THEN tbd.amount * grm.sign_multiplier ELSE 0 END) as prior_month
                FROM trial_balance_data tbd
                JOIN trial_balance_uploads tbu ON tbd.upload_id = tbu.upload_id
                JOIN gl_report_mapping grm ON tbd.gl_code = grm.gl_code
                WHERE tbu.company = %s
                AND grm.report_type = %s
                GROUP BY grm.line_id
                """
                cursor.execute(query, (
                    period_end_date, period_end_date, period_end_date, period_end_date,
                    company, report_type
                ))
                
                results = cursor.fetchall()
                
                # Add P&L profit to reserves for Balance Sheet
                pl_query = """
                SELECT 
                    -- Current period actual profit
                    SUM(CASE WHEN tbd.data_type = 'actual' 
                        AND tbd.period_end_date = %s::date 
                        THEN tbd.amount * grm.sign_multiplier ELSE 0 END) as actual_profit,
                    -- Current period budget profit
                    SUM(CASE WHEN tbd.data_type = 'budget' 
                        AND tbd.period_end_date = %s::date 
                        THEN tbd.amount * grm.sign_multiplier ELSE 0 END) as budget_profit,
                    -- Prior year profit
                    SUM(CASE WHEN tbd.data_type = 'actual' 
                        AND tbd.period_end_date = %s::date - INTERVAL '1 year'
                        THEN tbd.amount * grm.sign_multiplier ELSE 0 END) as prior_year_profit
                FROM trial_balance_data tbd
                JOIN trial_balance_uploads tbu ON tbd.upload_id = tbu.upload_id
                JOIN gl_report_mapping grm ON tbd.gl_code = grm.gl_code
                WHERE tbu.company = %s
                AND grm.report_type = 'profit_loss'
                """
                cursor.execute(pl_query, (period_end_date, period_end_date, period_end_date, company))
                profit_result = cursor.fetchone()
                
                # Convert results to a dictionary for easier manipulation
                data_dict = {row['line_id']: row for row in results}
                
                # Add profit to reserves (assuming reserves is line_id 2600)
                reserves_line_id = 2600
                if reserves_line_id not in data_dict:
                    data_dict[reserves_line_id] = {
                        'line_id': reserves_line_id,
                        'actual': 0,
                        'budget': 0,
                        'prior_year': 0,
                        'prior_month': 0
                    }
                
                # Add profits to reserves
                if profit_result:
                    data_dict[reserves_line_id]['actual'] += float(profit_result['actual_profit'] or 0)
                    data_dict[reserves_line_id]['budget'] += float(profit_result['budget_profit'] or 0)
                    data_dict[reserves_line_id]['prior_year'] += float(profit_result['prior_year_profit'] or 0)
                
                return list(data_dict.values())
            
            else:
                raise ValueError(f"Unknown report type: {report_type}")
            
            # Convert the list of rows to a dictionary format
            # This creates separate dictionaries for each data type
            results = cursor.fetchall()
            
            # Return format that matches the original expectation
            data = {
                'actual': {},
                'budget': {},
                'prior_year': {},
                'ytd_actual': {},
                'ytd_budget': {},
                'prior_ytd': {}
            }
            
            for row in results:
                line_id = row['line_id']
                data['actual'][line_id] = float(row['actual'] or 0)
                data['budget'][line_id] = float(row['budget'] or 0)
                data['prior_year'][line_id] = float(row['prior_year'] or 0)
                if report_type == 'profit_loss':
                    data['ytd_actual'][line_id] = float(row['ytd_actual'] or 0)
                    data['ytd_budget'][line_id] = float(row['ytd_budget'] or 0)
                    data['prior_ytd'][line_id] = float(row['prior_ytd'] or 0)
                elif report_type == 'balance_sheet':
                    data['prior_month'] = data.get('prior_month', {})
                    data['prior_month'][line_id] = float(row.get('prior_month', 0) or 0)
            
            return data
                  
    except Exception as e:
        raise Exception(f"Failed to get report data: {str(e)}")
    finally:
        conn.close()

def get_report_data_ytd(report_type, period_end_date, company, data_type='actual'):
    """Get year-to-date aggregated data for report generation"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Calculate start of year from period_end_date
            from datetime import datetime
            if isinstance(period_end_date, str):
                period_date = datetime.strptime(period_end_date, '%Y-%m-%d').date()
            else:
                period_date = period_end_date
            
            year_start = datetime(period_date.year, 1, 1).date()
            
            # Get YTD data (sum from start of year to period_end_date)
            query = """
            SELECT 
                grm.line_id,
                SUM(tbd.amount * grm.sign_multiplier) as total_amount
            FROM trial_balance_data tbd
            JOIN trial_balance_uploads tbu ON tbd.upload_id = tbu.upload_id
            JOIN gl_report_mapping grm ON tbd.gl_code = grm.gl_code
            WHERE tbd.period_end_date >= %s
            AND tbd.period_end_date <= %s
            AND tbu.company = %s
            AND tbd.data_type = %s
            AND grm.report_type = %s
            GROUP BY grm.line_id
            """
            cursor.execute(query, (year_start, period_end_date, company, data_type, report_type))
            results = cursor.fetchall()
            data = {row['line_id']: float(row['total_amount']) for row in results}
            
            return data
                  
    except Exception as e:
        raise Exception(f"Failed to get YTD report data: {str(e)}")
    finally:
        conn.close()