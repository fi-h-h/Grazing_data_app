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


def calculate_animal_groups(calculation_date,cattle_data,lu_data):
    # Ensure all dates are datetime objects
    corrected_calculation_date = pd.to_datetime(calculation_date,dayfirst=True)
    date_cols = ["Date of birth", "Date on farm", "Date off farm"]
    for col in date_cols:
        cattle_data[col] = pd.to_datetime(cattle_data[col], errors='raise',dayfirst=True)

    # Filter to Only keep animals that were ON the farm on the calculation date
    mask = (cattle_data["Date of birth"] <= corrected_calculation_date) & \
            (cattle_data["Date on farm"] <= corrected_calculation_date) & \
            ((cattle_data["Date off farm"].isna()) | (cattle_data["Date off farm"] > corrected_calculation_date))
    
    active_cattle = cattle_data[mask].copy()

    # Calculate age in months
    active_cattle["Age (months)"] = (((corrected_calculation_date - active_cattle["Date of birth"]).dt.days)/30.4735).round(1)

    def assign_lu_and_group(row):
        age_months = row["Age (months)"]
        is_female = str(row["M/F"]).strip().upper() == "F"
        is_bull = str(row["Bull?"]).strip().upper() in ["YES", "Y", "TRUE"]

        if age_months < 3:
            return "Calf", lu_data.iloc[4]
        elif age_months >= 3 and age_months < 6:
            return "Calf", lu_data.iloc[3]
        elif age_months >= 6 and age_months < 12:
            return "Calf", lu_data.iloc[2]
        elif age_months >= 12 and age_months < 24:
            return "Youngstock", lu_data.iloc[1]
        elif age_months >= 24 and is_bull:
            return "Bull", lu_data.iloc[0]
        elif age_months >= 24 and is_female:
            return "Cow", lu_data.iloc[0]
        else:
            return "Steer", lu_data.iloc[0]
    
    # Apply the logic
    results = active_cattle.apply(assign_lu_and_group, axis=1)
    active_cattle[["Group", "Livestock Unit"]] = pd.DataFrame(results.tolist(), index=active_cattle.index)

    # 4. SELECT FINAL COLUMNS
    final_cattle_df = active_cattle[["Ear Tag Number", "Group", "Age (months)", "Livestock Unit"]]
    return final_cattle_df