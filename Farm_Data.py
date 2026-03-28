import streamlit as st
import pandas as pd

@st.cache_data
def load_csv(file):
    # Reads in csv. This only runs once per file to save time
    return pd.read_csv(file)

def process_and_display_csv(label):
    # Create the file uploader widget
    uploaded_file = st.file_uploader(label, type="csv",key=label)

    if uploaded_file is not None:
        # Read the file into a Pandas DataFrame
        df = load_csv(uploaded_file)
    
        # Display the table
        st.subheader("Data Preview")
        st.dataframe(df) # This creates an interactive, searchable table
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
            col_container.success(f"✅ csv validated!")
        else:
            # Display a clear error message
            col_container.error(f"❌ Required column missing in csv. Missing: {', '.join(missing_cols)}")

# Set to wide mode
st.set_page_config(layout="wide")

# Set the page title
st.set_page_config(page_title="Farm Data")

# --- DATA INPUT SECTION ---
data_col1, data_col2, data_col3 = st.columns(3)
expected_cattle_headings = ["Ear Tag Number", "Date of birth", "M/F", "Steer?", "Heifer?", "Date on farm", "Date off farm"]
expected_field_headings = ["Field Name", "Field Area (hectare)", "Field Area (acre)"]
expected_grazing_headings = ["Your name", "What are the weather conditions?", "Management group", "Date moved out", "Which field are the cattle moving out of?", "What does the paddock the cattle are moving out of look like?", "Date moved in",	
                             "Which field are the cattle moving into?", "How has the field been split?", "Is this the first, second, third...paddock in the field?", "How many days grazing is intended for this paddock?", "What does the pasture look like?", "What do the cattle look like?"]

# Read in cattle data
with data_col1:
    st.title("🤠 Cattle Data")
    st.info(f"**Upload a CSV file of your cattle data. Column headings should be:  \n{expected_cattle_headings}**")
    cattle_data_table = process_and_display_csv("Choose a cattle data CSV file")
    st.divider()

    # Check column headings are correct
    if cattle_data_table is not None:
        validate_csv_column_headings(cattle_data_table,expected_cattle_headings,data_col1)

# Read in field data
with data_col2:
    st.title("🌿 Field Data")
    st.info(f"**Upload a CSV file of your field data. Column headings should be:  \n{expected_field_headings}**")
    field_data_table = process_and_display_csv("Choose a field data CSV file")
    st.divider()

    # Check column headings are correct
    if field_data_table is not None:
        validate_csv_column_headings(field_data_table,expected_field_headings,data_col2)

# Read in grazing data
with data_col3:
    st.title("🐮 Grazing Data")
    st.info("**Upload a CSV file of your grazing data from the google form.  \n Ensure field names match those in the field data csv and entries are in calendar order.**")
    grazing_data_table = process_and_display_csv("Choose a grazing data CSV file")
    st.divider()
    
    # Check column headings are correct
    if grazing_data_table is not None:
        validate_csv_column_headings(grazing_data_table,expected_grazing_headings,data_col3)

# Check field names in grazing file matches data in field file




