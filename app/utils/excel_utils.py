import pandas as pd

def write_grade_to_excel(excel_path: str, student_name: str, grade_type: str, grade: float) -> bool:
    """
    Write a grade to an Excel file for a specific student.
    
    Args:
        excel_path: Path to the Excel file
        student_name: Name of the student
        grade_type: Type of grade to write (e.g., '平时成绩', '理论成绩', etc.)
        grade: Grade value to write
        
    Returns:
        bool: True if grade was written successfully, False otherwise
    """
    try:
        # Read all sheets from the Excel file
        xls = pd.ExcelFile(excel_path)
        sheet_name = xls.sheet_names[0]  # Use first sheet
        
        # Read the first few rows to analyze the structure
        header_df = pd.read_excel(excel_path, sheet_name=sheet_name, nrows=10)
        
        # Find the row containing "序号" which indicates the start of the actual data
        header_rows = None
        for idx, row in header_df.iterrows():
            if row.astype(str).str.contains('序号').any():
                header_rows = idx
                break
                
        if header_rows is None:
            print("Could not find the header row with '序号'")
            return False
            
        # Read the Excel file again with the correct header row
        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_rows)
        
        # Clean up column names
        df.columns = df.columns.str.strip()
        
        # Find the name column (should contain '姓名')
        name_col = None
        for col in df.columns:
            if '姓名' in str(col):
                name_col = col
                break
                
        if name_col is None:
            print("Could not find the name column")
            return False
            
        # Find the grade column
        grade_col = None
        for col in df.columns:
            if grade_type in str(col):
                grade_col = col
                break
                
        if grade_col is None:
            print(f"Could not find the grade column for type: {grade_type}")
            return False
            
        # Find the student's row
        student_row = df[df[name_col].fillna('').str.strip() == student_name]
        
        if len(student_row) == 0:
            # Student not found, add a new row
            new_row = pd.Series(index=df.columns)
            new_row[name_col] = student_name
            new_row[grade_col] = grade
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            # Update existing student's grade
            df.loc[student_row.index[0], grade_col] = grade
            
        # Save the updated DataFrame back to Excel
        df.to_excel(excel_path, sheet_name=sheet_name, index=False)
        return True
        
    except Exception as e:
        print(f"Error writing grade to Excel: {str(e)}")
        return False 