import json
import os
from services.database_service import get_report_data

def load_report_template(report_type):
    """Load report template from JSON file"""
    template_path = f"configs/{report_type}_template.json"
    with open(template_path, 'r') as file:
        return json.load(file)

def generate_profit_loss_report(period_end_date):
    """Generate detailed Profit & Loss report"""
    try:
        print(f"🔍 Starting P&L generation for {period_end_date}")
        
        # Load template
        template = load_report_template('profit_loss')
        print(f"✅ Template loaded: {template['report_name']}")
        
        # Get data from database
        line_data = get_report_data('profit_loss', period_end_date)
        print(f"✅ Line data retrieved: {len(line_data)} items")
        print(f"📊 Line data keys: {list(line_data.keys())}")
        
        # Build report structure
        report_lines = []
        section_totals = {}

        print(f"🔄 Processing {len(template['sections'])} sections...")
        
        for section in template['sections']:
            print(f"📝 Processing section: {section['section_name']}")
            
            # Skip calculated sections (like Gross Profit)
            if 'calculation' in section:
                continue
                
            # Add section header
            report_lines.append({
                'name': section['section_name'],
                'amount': None,
                'is_header': True,
                'is_bold': True,
                'indent_level': 0,
                'type': 'section_header'
            })
            
            # Add line items and calculate section total
            section_total = 0
            has_data = False
            
            for line in section['lines']:
                line_amount = line_data.get(line['line_id'], 0)
                if line_amount != 0:
                    has_data = True
                section_total += line_amount
                
                # Only show lines that have data or are commonly expected
                if line_amount != 0 :
                    report_lines.append({
                        'name': f"  {line['name']}",
                        'amount': line_amount,
                        'is_header': False,
                        'is_bold': False,
                        'indent_level': 1,
                        'type': 'line_item'
                    })
            
            # Add section total if there's data
            if has_data:
                section_totals[section['total_line']['line_id']] = section_total
                report_lines.append({
                    'name': section['total_line']['name'],
                    'amount': section_total,
                    'is_header': False,
                    'is_bold': True,
                    'indent_level': 0,
                    'type': 'section_total'
                })
            
            # Add blank line between sections
            report_lines.append({
                'name': '',
                'amount': None,
                'is_header': False,
                'is_bold': False,
                'indent_level': 0,
                'type': 'blank'
            })
        
        # Calculate intermediate totals
        gross_profit = section_totals.get('total_revenue', 0) - section_totals.get('total_cost_of_sales', 0)
        section_totals['gross_profit'] = gross_profit
        
        # Add Gross Profit line
        report_lines.append({
            'name': 'GROSS PROFIT',
            'amount': gross_profit,
            'is_header': False,
            'is_bold': True,
            'indent_level': 0,
            'type': 'calculated_total'
        })
        
        report_lines.append({'name': '', 'amount': None, 'is_header': False, 'is_bold': False, 'indent_level': 0, 'type': 'blank'})
        
        # Calculate EBITDA (Earnings Before Interest, Tax, Depreciation, Amortization)
        ebitda = gross_profit - section_totals.get('total_operating_expenses', 0)
        
        # Add EBITDA line
        report_lines.append({
            'name': 'EBITDA',
            'amount': ebitda,
            'is_header': False,
            'is_bold': True,
            'indent_level': 0,
            'type': 'calculated_total'
        })
        
        # Calculate Operating Profit (EBIT)
        operating_profit = ebitda - section_totals.get('total_depreciation', 0)
        
        report_lines.append({
            'name': 'OPERATING PROFIT (EBIT)',
            'amount': operating_profit,
            'is_header': False,
            'is_bold': True,
            'indent_level': 0,
            'type': 'calculated_total'
        })
        
        # Calculate Profit Before Tax
        profit_before_tax = (operating_profit - 
                           section_totals.get('total_financial_expenses', 0) - 
                           section_totals.get('total_other_expenses', 0))
        
        report_lines.append({
            'name': 'PROFIT BEFORE TAX',
            'amount': profit_before_tax,
            'is_header': False,
            'is_bold': True,
            'indent_level': 0,
            'type': 'calculated_total'
        })
        
        # Calculate Final Net Profit
        net_profit = profit_before_tax - section_totals.get('total_tax_expenses', 0)
        
        report_lines.append({
            'name': 'NET PROFIT',
            'amount': net_profit,
            'is_header': False,
            'is_bold': True,
            'indent_level': 0,
            'type': 'final_total',
            'is_final': True
        })
        
        return {
            'report_title': template['report_name'],
            'period_end_date': period_end_date,
            'data': report_lines,
            'summary': {
                'total_revenue': section_totals.get('total_revenue', 0),
                'gross_profit': gross_profit,
                'ebitda': ebitda,
                'operating_profit': operating_profit,
                'profit_before_tax': profit_before_tax,
                'net_profit': net_profit
            }
        }
        
    except Exception as e:
        raise Exception(f"Failed to generate P&L report: {str(e)}")

def generate_balance_sheet_report(period_end_date):
    """Generate Balance Sheet report"""
    try:
        print(f"🔍 Starting Balance Sheet generation for {period_end_date}")
        template = load_report_template('balance_sheet')
        print(f"✅ Template loaded: {template['report_name']}")
        
        line_data = get_report_data('balance_sheet', period_end_date)
        print(f"✅ Line data retrieved: {len(line_data)} items")
        print(f"📊 Line data keys: {list(line_data.keys())}")
        
        report_lines = []
        section_totals = {}
        
        print(f"🔄 Processing {len(template['sections'])} sections...")
        
        for section in template['sections']:
            print(f"📝 Processing section: {section['section_name']}")
            
            # Add main section header (ASSETS or LIABILITIES & EQUITY)
            report_lines.append({
                'name': section['section_name'],
                'amount': None,
                'is_header': True,
                'is_bold': True,
                'indent_level': 0,
                'type': 'section_header'
            })
            
            section_total = 0
            
            # Process subsections (Current Assets, Fixed Assets, etc.)
            if 'subsections' in section:
                print(f"🔄 Processing {len(section['subsections'])} subsections...")
                
                for subsection in section['subsections']:
                    print(f"📝 Processing subsection: {subsection['subsection_name']}")
                    
                    # Add subsection header
                    report_lines.append({
                        'name': f"  {subsection['subsection_name']}",
                        'amount': None,
                        'is_header': True,
                        'is_bold': False,
                        'indent_level': 1,
                        'type': 'subsection_header'
                    })
                    
                    subsection_total = 0
                    
                    # Add line items
                    for line in subsection['lines']:
                        line_amount = line_data.get(line['line_id'], 0)
                        subsection_total += line_amount
                        
                        if line_amount != 0:  # Only show lines with data
                            report_lines.append({
                                'name': f"    {line['name']}",
                                'amount': line_amount,
                                'is_header': False,
                                'is_bold': False,
                                'indent_level': 2,
                                'type': 'line_item'
                            })
                    
                    # Add subsection total
                    if subsection_total != 0:
                        section_totals[subsection['total_line']['line_id']] = subsection_total
                        section_total += subsection_total
                        
                        report_lines.append({
                            'name': f"  {subsection['total_line']['name']}",
                            'amount': subsection_total,
                            'is_header': False,
                            'is_bold': True,
                            'indent_level': 1,
                            'type': 'subsection_total'
                        })
                        
                        # Add blank line
                        report_lines.append({
                            'name': '',
                            'amount': None,
                            'is_header': False,
                            'is_bold': False,
                            'indent_level': 0,
                            'type': 'blank'
                        })
            
            # Add main section total
            section_totals[section['total_line']['line_id']] = section_total
            report_lines.append({
                'name': section['total_line']['name'],
                'amount': section_total,
                'is_header': False,
                'is_bold': True,
                'indent_level': 0,
                'type': 'section_total'
            })
            
            # Add blank line between main sections
            report_lines.append({
                'name': '',
                'amount': None,
                'is_header': False,
                'is_bold': False,
                'indent_level': 0,
                'type': 'blank'
            })
        
        # Check if balance sheet balances
        total_assets = section_totals.get('total_assets', 0)
        total_liab_equity = section_totals.get('total_liab_equity', 0)
        difference = total_assets - total_liab_equity
        
        print(f"💰 Total Assets: {total_assets}")
        print(f"💰 Total Liab & Equity: {total_liab_equity}")
        print(f"⚖️ Difference: {difference}")
        
        return {
            'report_title': template['report_name'],
            'period_end_date': period_end_date,
            'data': report_lines,
            'balances': abs(difference) < 0.01,
            'difference': difference,
            'summary': {
                'total_assets': total_assets,
                'total_liabilities_equity': total_liab_equity,
                **section_totals
            }
        }
        
    except Exception as e:
        print(f"❌ Balance Sheet Error: {str(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        raise Exception(f"Failed to generate Balance Sheet: {str(e)}")