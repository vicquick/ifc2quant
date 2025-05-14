import pandas as pd
from pathlib import Path
from xlsxwriter.utility import xl_col_to_name

def export_comparison_to_excel(compare_df: pd.DataFrame, output_path: Path) -> None:
    """Export comparison DataFrame to Excel with precise formatting"""
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        compare_df.to_excel(writer, sheet_name='Comparison', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Comparison']
        
        # Define formats
        fmt_yellow = workbook.add_format({'bg_color': '#FFF2CC'})
        fmt_gray = workbook.add_format({'bg_color': '#D9D9D9'})
        fmt_header = workbook.add_format({'bold': True, 'text_wrap': True})
        
        # Apply header format to all columns
        for col_num, value in enumerate(compare_df.columns.values):
            worksheet.write(0, col_num, value, fmt_header)
        
        # Find all delta columns (columns starting with 'Δ ')
        delta_cols = [i for i, col in enumerate(compare_df.columns) if col.startswith('Δ ')]
        
        # Get corresponding property names (removing 'A ', 'B ', 'Δ ' prefixes)
        properties = [col[2:] for col in compare_df.columns if col.startswith('Δ ')]
        
        # Apply row-based formatting (fixes the off-by-one issue)
        for row_num in range(1, len(compare_df) + 1):  # Rows are 1-based in Excel
            has_changes = False
            
            # Check if this row has any non-zero deltas
            for delta_col in delta_cols:
                delta_value = compare_df.iloc[row_num - 1, delta_col]
                if delta_value != 0:
                    has_changes = True
                    break
            
            if has_changes:
                for prop_idx, prop in enumerate(properties):
                    # Calculate column positions for this property
                    delta_col = delta_cols[prop_idx]
                    a_col = delta_col - 2
                    b_col = delta_col - 1
                    
                    # Get values
                    a_val = compare_df.iloc[row_num - 1, a_col]
                    b_val = compare_df.iloc[row_num - 1, b_col]
                    delta_val = compare_df.iloc[row_num - 1, delta_col]
                    
                    # Format delta column
                    if delta_val > 0:
                        worksheet.write(row_num, delta_col, delta_val, fmt_yellow)
                    elif delta_val < 0:
                        worksheet.write(row_num, delta_col, delta_val, fmt_gray)
                    
                    # Format A and B columns
                    if a_val < b_val:
                        worksheet.write(row_num, a_col, a_val, fmt_gray)
                        worksheet.write(row_num, b_col, b_val, fmt_yellow)
                    elif a_val > b_val:
                        worksheet.write(row_num, a_col, a_val, fmt_yellow)
                        worksheet.write(row_num, b_col, b_val, fmt_gray)
                    
                    # Format category and group columns (first two columns)
                    if delta_val > 0:
                        worksheet.write(row_num, 0, compare_df.iloc[row_num - 1, 0], fmt_yellow)
                        worksheet.write(row_num, 1, compare_df.iloc[row_num - 1, 1], fmt_yellow)
                    elif delta_val < 0:
                        worksheet.write(row_num, 0, compare_df.iloc[row_num - 1, 0], fmt_gray)
                        worksheet.write(row_num, 1, compare_df.iloc[row_num - 1, 1], fmt_gray)