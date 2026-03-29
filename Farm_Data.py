import streamlit as st
import pandas as pd
import Functions as fn

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
    cattle_data_table = fn.process_csv("Choose a cattle data CSV file")

    # Check column headings are correct
    if cattle_data_table is not None:
        fn.validate_csv_column_headings(cattle_data_table,expected_cattle_headings,data_col1)

# Read in field data
with data_col2:
    st.subheader("🌿 Field Data")
    st.info(f"**Upload a CSV file of your field data. Column headings should be:  \n{expected_field_headings}**")
    field_data_table = fn.process_csv("Choose a field data CSV file")

    # Check column headings are correct
    if field_data_table is not None:
        fn.validate_csv_column_headings(field_data_table,expected_field_headings,data_col2)

# Read in grazing data
with data_col3:
    st.subheader("🐮 Grazing Data")
    st.info("**Upload a CSV file of your grazing data from the google form.  \n Ensure field names match those in the field data csv and entries are in calendar order.**")
    grazing_data_table = fn.process_csv("Choose a grazing data CSV file")
    
    # Check column headings are correct
    if grazing_data_table is not None:
        fn.validate_csv_column_headings(grazing_data_table,expected_grazing_headings,data_col3)

    # Check field names in grazing file matches data in field file
    if grazing_data_table is not None and field_data_table is not None:
        fn.validate_grazing_data(grazing_data_table, ["Which field are the cattle moving out of?", "Which field are the cattle moving into?"], field_data_table, "Field Name")

st.divider()




