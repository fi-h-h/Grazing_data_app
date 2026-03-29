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
        else:
            # Display a clear error message
            col_container.error(f"❌ Required column missing in csv. Missing: {', '.join(missing_cols)}")

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
    else:
        #List the unknown field names
        st.error(f"⚠️ Found {len(missing_values)} unknown field names!  \n The following fields in the Grazing Data are not defined in the Field Data**:")
        st.write(list(missing_values))
        
        # Show the actual rows in the source file that have the error
        st.error(f"Rows in the Grazing Data requiring correction:")
        error_rows = grazing_table[grazing_table[grazing_col_name[0]].isin(missing_values) | grazing_table[grazing_col_name[1]].isin(missing_values)]
        st.dataframe(error_rows, width='stretch')

# Set to wide mode
st.set_page_config(layout="wide")

# Set the page title
st.set_page_config(page_title="Farm Data")

# --- DATA INPUT SECTION ---

# Set up page header
st.title("🔢 Data Input",text_alignment="center")
st.divider()

# Define expected headings
expected_cattle_headings = ["Ear Tag Number", "Date of birth", "M/F", "Steer?", "Heifer?", "Date on farm", "Date off farm"]
expected_field_headings = ["Field Name", "Field Area (hectare)", "Field Area (acre)"]
expected_grazing_headings = ["Your name", "What are the weather conditions?", "Management group", "Date moved out", "Which field are the cattle moving out of?", "What does the paddock the cattle are moving out of look like?", "Date moved in",	
                             "Which field are the cattle moving into?", "How has the field been split?", "Is this the first, second, third...paddock in the field?", "How many days grazing is intended for this paddock?", "What does the pasture look like?", "What do the cattle look like?"]

#Set up columns
data_col1, data_col2, data_col3 = st.columns(3)

# Read in cattle data
with data_col1:
    st.subheader("🤠 Cattle Data")
    st.info(f"**Upload a CSV file of your cattle data. Column headings should be:  \n{expected_cattle_headings}**")
    cattle_data_table = process_csv("Choose a cattle data CSV file")

    # Check column headings are correct
    if cattle_data_table is not None:
        validate_csv_column_headings(cattle_data_table,expected_cattle_headings,data_col1)

# Read in field data
with data_col2:
    st.subheader("🌿 Field Data")
    st.info(f"**Upload a CSV file of your field data. Column headings should be:  \n{expected_field_headings}**")
    field_data_table = process_csv("Choose a field data CSV file")

    # Check column headings are correct
    if field_data_table is not None:
        validate_csv_column_headings(field_data_table,expected_field_headings,data_col2)

# Read in grazing data
with data_col3:
    st.subheader("🐮 Grazing Data")
    st.info("**Upload a CSV file of your grazing data from the google form.  \n Ensure field names match those in the field data csv and entries are in calendar order.**")
    grazing_data_table = process_csv("Choose a grazing data CSV file")
    
    # Check column headings are correct
    if grazing_data_table is not None:
        validate_csv_column_headings(grazing_data_table,expected_grazing_headings,data_col3)

    # Check field names in grazing file matches data in field file
    if grazing_data_table is not None and field_data_table is not None:
        validate_grazing_data(grazing_data_table, ["Which field are the cattle moving out of?", "Which field are the cattle moving into?"], field_data_table, "Field Name")

st.divider()




