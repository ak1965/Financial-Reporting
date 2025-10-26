import json
import os
from services.database_service import get_report_data
from services.database_service import get_report_data_ytd

def load_report_template(report_type):
    """Load report template from JSON file"""
    template_path = f"configs/{report_type}_template.json"
    with open(template_path, 'r') as file:
        return json.load(file)

def generate_profit_loss_report(period_end_date, company):
    """Generate detailed Profit & Loss report with Actual, Budget, Prior Year, and YTD columns"""
    try:
        print(f"🔍 Starting P&L generation for {company} - {period_end_date}")
        
        # Load template
        template = load_report_template('profit_loss')
        print(f"✅ Template loaded: {template['report_name']}")
        
        # Get data from database for all columns
        actual_data = get_report_data('profit_loss', period_end_date, company, 'actual')
        print(f"🔍 Actual data: {actual_data}")
        
        budget_data = get_report_data('profit_loss', period_end_date, company, 'budget')
        print(f"🔍 Budget data: {budget_data}")
        
        prior_year_data = get_report_data('profit_loss', period_end_date, company, 'prior_year')
        print(f"🔍 Prior year data: {prior_year_data}")
        
        actual_ytd_data = get_report_data_ytd('profit_loss', period_end_date, company, 'actual')
        print(f"🔍 Actual YTD data: {actual_ytd_data}")
        
        budget_ytd_data = get_report_data_ytd('profit_loss', period_end_date, company, 'budget')
        print(f"🔍 Budget YTD data: {budget_ytd_data}")
        
        prior_year_ytd_data = get_report_data_ytd('profit_loss', period_end_date, company, 'prior_year')
        print(f"🔍 Prior year YTD data: {prior_year_ytd_data}")
        
        print(f"✅ Data retrieved for all 6 columns")
        
        # Build report structure
        report_lines = []
        section_totals = {
            'actual': {},
            'budget': {},
            'prior_year': {},
            'actual_ytd': {},
            'budget_ytd': {},
            'prior_year_ytd': {}
        }

        print(f"🔄 Processing {len(template['sections'])} sections...")
        
        for section in template['sections']:
            print(f"📝 Processing section: {section['section_name']}")
            
            # Skip calculated sections (like Gross Profit)
            if 'calculation' in section:
                continue
                
            # Add section header
            report_lines.append({
                'name': section['section_name'],
                'amounts': {
                    'actual': None,
                    'budget': None,
                    'prior_year': None,
                    'actual_ytd': None,
                    'budget_ytd': None,
                    'prior_year_ytd': None
                },
                'is_header': True,
                'is_bold': True,
                'indent_level': 0,
                'type': 'section_header'
            })
            
            # Add line items and calculate section totals
            section_total_actual = 0
            section_total_budget = 0
            section_total_prior_year = 0
            section_total_actual_ytd = 0
            section_total_budget_ytd = 0
            section_total_prior_year_ytd = 0
            has_data = False
            
            for line in section['lines']:
                line_actual = actual_data.get(line['line_id'], 0)
                line_budget = budget_data.get(line['line_id'], 0)
                line_prior_year = prior_year_data.get(line['line_id'], 0)
                line_actual_ytd = actual_ytd_data.get(line['line_id'], 0)
                line_budget_ytd = budget_ytd_data.get(line['line_id'], 0)
                line_prior_year_ytd = prior_year_ytd_data.get(line['line_id'], 0)
                
                if any([line_actual != 0, line_budget != 0, line_prior_year != 0]):
                    has_data = True
                
                section_total_actual += line_actual
                section_total_budget += line_budget
                section_total_prior_year += line_prior_year
                section_total_actual_ytd += line_actual_ytd
                section_total_budget_ytd += line_budget_ytd
                section_total_prior_year_ytd += line_prior_year_ytd
                
                # Only show lines that have data
                if any([line_actual != 0, line_budget != 0, line_prior_year != 0]):
                    report_lines.append({
                        'name': f"  {line['name']}",
                        'amounts': {
                            'actual': line_actual,
                            'budget': line_budget,
                            'prior_year': line_prior_year,
                            'actual_ytd': line_actual_ytd,
                            'budget_ytd': line_budget_ytd,
                            'prior_year_ytd': line_prior_year_ytd
                        },
                        'is_header': False,
                        'is_bold': False,
                        'indent_level': 1,
                        'type': 'line_item'
                    })
            
            # Add section total if there's data
            if has_data:
                section_totals['actual'][section['total_line']['line_id']] = section_total_actual
                section_totals['budget'][section['total_line']['line_id']] = section_total_budget
                section_totals['prior_year'][section['total_line']['line_id']] = section_total_prior_year
                section_totals['actual_ytd'][section['total_line']['line_id']] = section_total_actual_ytd
                section_totals['budget_ytd'][section['total_line']['line_id']] = section_total_budget_ytd
                section_totals['prior_year_ytd'][section['total_line']['line_id']] = section_total_prior_year_ytd
                
                report_lines.append({
                    'name': section['total_line']['name'],
                    'amounts': {
                        'actual': section_total_actual,
                        'budget': section_total_budget,
                        'prior_year': section_total_prior_year,
                        'actual_ytd': section_total_actual_ytd,
                        'budget_ytd': section_total_budget_ytd,
                        'prior_year_ytd': section_total_prior_year_ytd
                    },
                    'is_header': False,
                    'is_bold': True,
                    'indent_level': 0,
                    'type': 'section_total'
                })
            
            # Add blank line between sections
            report_lines.append({
                'name': '',
                'amounts': {
                    'actual': None,
                    'budget': None,
                    'prior_year': None,
                    'actual_ytd': None,
                    'budget_ytd': None,
                    'prior_year_ytd': None
                },
                'is_header': False,
                'is_bold': False,
                'indent_level': 0,
                'type': 'blank'
            })
        
        # Calculate intermediate totals for all columns
        gross_profit_actual = section_totals['actual'].get('total_revenue', 0) - section_totals['actual'].get('total_cost_of_sales', 0)
        gross_profit_budget = section_totals['budget'].get('total_revenue', 0) - section_totals['budget'].get('total_cost_of_sales', 0)
        gross_profit_prior_year = section_totals['prior_year'].get('total_revenue', 0) - section_totals['prior_year'].get('total_cost_of_sales', 0)
        gross_profit_actual_ytd = section_totals['actual_ytd'].get('total_revenue', 0) - section_totals['actual_ytd'].get('total_cost_of_sales', 0)
        gross_profit_budget_ytd = section_totals['budget_ytd'].get('total_revenue', 0) - section_totals['budget_ytd'].get('total_cost_of_sales', 0)
        gross_profit_prior_year_ytd = section_totals['prior_year_ytd'].get('total_revenue', 0) - section_totals['prior_year_ytd'].get('total_cost_of_sales', 0)
        
        section_totals['actual']['gross_profit'] = gross_profit_actual
        section_totals['budget']['gross_profit'] = gross_profit_budget
        section_totals['prior_year']['gross_profit'] = gross_profit_prior_year
        section_totals['actual_ytd']['gross_profit'] = gross_profit_actual_ytd
        section_totals['budget_ytd']['gross_profit'] = gross_profit_budget_ytd
        section_totals['prior_year_ytd']['gross_profit'] = gross_profit_prior_year_ytd
        
        # Add Gross Profit line
        report_lines.append({
            'name': 'GROSS PROFIT',
            'amounts': {
                'actual': gross_profit_actual,
                'budget': gross_profit_budget,
                'prior_year': gross_profit_prior_year,
                'actual_ytd': gross_profit_actual_ytd,
                'budget_ytd': gross_profit_budget_ytd,
                'prior_year_ytd': gross_profit_prior_year_ytd
            },
            'is_header': False,
            'is_bold': True,
            'indent_level': 0,
            'type': 'calculated_total'
        })
        
        report_lines.append({
            'name': '',
            'amounts': {
                'actual': None,
                'budget': None,
                'prior_year': None,
                'actual_ytd': None,
                'budget_ytd': None,
                'prior_year_ytd': None
            },
            'is_header': False,
            'is_bold': False,
            'indent_level': 0,
            'type': 'blank'
        })
        
        # Calculate Net Profit for all columns
        net_profit_actual = gross_profit_actual - section_totals['actual'].get('total_operating_expenses', 0)
        net_profit_budget = gross_profit_budget - section_totals['budget'].get('total_operating_expenses', 0)
        net_profit_prior_year = gross_profit_prior_year - section_totals['prior_year'].get('total_operating_expenses', 0)
        net_profit_actual_ytd = gross_profit_actual_ytd - section_totals['actual_ytd'].get('total_operating_expenses', 0)
        net_profit_budget_ytd = gross_profit_budget_ytd - section_totals['budget_ytd'].get('total_operating_expenses', 0)
        net_profit_prior_year_ytd = gross_profit_prior_year_ytd - section_totals['prior_year_ytd'].get('total_operating_expenses', 0)
        
        report_lines.append({
            'name': 'NET PROFIT',
            'amounts': {
                'actual': net_profit_actual,
                'budget': net_profit_budget,
                'prior_year': net_profit_prior_year,
                'actual_ytd': net_profit_actual_ytd,
                'budget_ytd': net_profit_budget_ytd,
                'prior_year_ytd': net_profit_prior_year_ytd
            },
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
                'total_revenue': {
                    'actual': section_totals['actual'].get('total_revenue', 0),
                    'budget': section_totals['budget'].get('total_revenue', 0),
                    'prior_year': section_totals['prior_year'].get('total_revenue', 0),
                    'actual_ytd': section_totals['actual_ytd'].get('total_revenue', 0),
                    'budget_ytd': section_totals['budget_ytd'].get('total_revenue', 0),
                    'prior_year_ytd': section_totals['prior_year_ytd'].get('total_revenue', 0)
                },
                'gross_profit': {
                    'actual': gross_profit_actual,
                    'budget': gross_profit_budget,
                    'prior_year': gross_profit_prior_year,
                    'actual_ytd': gross_profit_actual_ytd,
                    'budget_ytd': gross_profit_budget_ytd,
                    'prior_year_ytd': gross_profit_prior_year_ytd
                },
                'net_profit': {
                    'actual': net_profit_actual,
                    'budget': net_profit_budget,
                    'prior_year': net_profit_prior_year,
                    'actual_ytd': net_profit_actual_ytd,
                    'budget_ytd': net_profit_budget_ytd,
                    'prior_year_ytd': net_profit_prior_year_ytd
                }
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