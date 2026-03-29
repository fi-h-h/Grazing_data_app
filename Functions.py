import streamlit as st
import pandas as pd

@st.cache_data
def load_csv(file):
    # Reads in csv. This only runs once per file to save time
    return pd.read_csv(file)

def process_csv(label):
    # Create the file uploader widget
    uploaded_file = st.file_uploader(label, type="csv",key=label)

    if uploaded_file is not None:
        # Read the file into a Pandas DataFrame
        df = load_csv(uploaded_file)
        return df
    else:
        st.error("💡 Please upload a CSV file to get started.")
        return None

def validate_csv_column_headings(data_table,expected_headings, col_container):
        actual_cols = set(data_table.columns)
        required_cols = set(expected_headings)
        
        # Check if all required columns are present
        missing_cols = required_cols - actual_cols
        
        if not missing_cols:
            col_container.success(f"✅ csv columns validated!")
            return True
        else:
            # Display a clear error message
            col_container.error(f"❌ Required column missing in csv. Missing: {', '.join(missing_cols)}")
            return False

def validate_grazing_data(grazing_table, grazing_col_name, field_table, field_col_name):
    # Pull out columns to compare
    grazing_set_a = set(grazing_table[grazing_col_name[0]].dropna().unique())
    grazing_set_b = set(grazing_table[grazing_col_name[1]].dropna().unique())
    combined_grazing_set = grazing_set_a | grazing_set_b
    field_set = set(field_table[field_col_name].astype(str).unique())

    # Find values in grazing data that are missing in field list
    missing_values = combined_grazing_set - field_set

    if not missing_values:
        # Show sucess
        st.success(f"✅ All field names in **Grazing Data** exist in **Field Data**.")
        return True
    else:
        #List the unknown field names
        st.error(f"❌ Found {len(missing_values)} unknown field names!  \n The following fields in the Grazing Data are not defined in the Field Data**:")
        st.write(list(missing_values))
        
        # Show the actual rows in the source file that have the error
        st.error(f"❌ Rows in the Grazing Data requiring correction:")
        error_rows = grazing_table[grazing_table[grazing_col_name[0]].isin(missing_values) | grazing_table[grazing_col_name[1]].isin(missing_values)]
        st.dataframe(error_rows, width='stretch')
        return False
    
def create_input_table(template_data,table_index,index_name,table_key):
    # Create pandas dataframe with template data
    template_table = pd.DataFrame(template_data,index=table_index)
    template_table.index.name = index_name
    # Display table
    edited_table = st.data_editor(
        data=template_table, 
        width="content",
        key=table_key
    )
    return edited_table