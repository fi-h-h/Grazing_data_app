import datetime as dt
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
expected_field_headings = ["Field Name", "Field Area (Hectare)", "Field Area (Acre)"]
expected_grazing_headings = ["Your name", "What are the weather conditions?", "Management group", "Date moved out", "Which field are the cattle moving out of?", "What does the paddock the cattle are moving out of look like?", "Date moved in",	
                             "Which field are the cattle moving into?", "How has the field been split?", "Is this the first, second, third...paddock in the field?", "How many days grazing is intended for this paddock?", "What does the pasture look like?", "What do the cattle look like?"]
validation_results = []
#Set up columns
data_col1, data_col2, data_col3 = st.columns(3)

# Read in cattle data
with data_col1:
    st.subheader("🤠 Cattle Data")
    st.info(f"**Upload a CSV file of your cattle data. Column headings should be:  \n{expected_cattle_headings}**")
    cattle_data_table = fn.process_csv("Choose a cattle data CSV file")

    # Check column headings are correct
    if cattle_data_table is not None:
         validation_results.append(fn.validate_csv_column_headings(cattle_data_table,expected_cattle_headings,data_col1))

# Read in field data
with data_col2:
    st.subheader("🌿 Field Data")
    st.info(f"**Upload a CSV file of your field data. Column headings should be:  \n{expected_field_headings}**")
    field_data_table = fn.process_csv("Choose a field data CSV file")

    # Check column headings are correct
    if field_data_table is not None:
        validation_results.append(fn.validate_csv_column_headings(field_data_table,expected_field_headings,data_col2))

# Read in grazing data
with data_col3:
    st.subheader("🐮 Grazing Data")
    st.info("**Upload a CSV file of your grazing data from the google form.  \n Ensure field names match those in the field data csv and entries are in calendar order.**")
    grazing_data_table = fn.process_csv("Choose a grazing data CSV file")
    
    # Check column headings are correct
    if grazing_data_table is not None:
        validation_results.append(fn.validate_csv_column_headings(grazing_data_table,expected_grazing_headings,data_col3))

    # Check field names in grazing file matches data in field file
    if grazing_data_table is not None and field_data_table is not None:
        validation_results.append(fn.validate_grazing_data(grazing_data_table, ["Which field are the cattle moving out of?", "Which field are the cattle moving into?"], field_data_table, "Field Name"))

st.divider()

# Check that there are no errors in the data input before moving on
#if cattle_data_table is not None and field_data_table is not None and grazing_data_table is not None and all(validation_results):

# --- DATA ANALYSIS SECTION ---
# Set up page header
st.title("📊 Data Analysis",text_alignment="center")
st.divider()

# Add option buttons
if "livestock_unit" not in st.session_state:
    st.session_state.livestock_unit = False
if "rest_data" not in st.session_state:
    st.session_state.rest_data = False
st.subheader("What would you like to calculate?")
left_space, button_col1, button_col2, right_space = st.columns([2, 2, 2, 2])
with button_col1:
    if st.button("Calculate Animal Days per Unit Area", type="primary",width="stretch"):
        st.session_state.livestock_unit = True
        st.session_state.rest_data = False
with button_col2:
    if st.button("Calculate Field Rest Period Data",type="primary",width="stretch"):
        st.session_state.rest_data = True
        st.session_state.livestock_unit = False
st.divider()

# --- Livestock Unit/Animal Days per Unit Area section ---
if st.session_state.livestock_unit:
    st.info("Please enter the livestock units, unit area, and timescale you wish to use for the calculation")

    # Set up columns
    lu_col1, lu_col2, lu_col3 = st.columns(3)

    with lu_col1:
        # Create table to input the livestock units into
        template_lu_data = {"VALUE": [1,0.5,0.3,0.2,0.1]}
        template_lu_index = ["ANIMALS 2+ YEARS","ANIMALS 12-24 MONTHS","ANIMALS 6-12 MONTHS","ANIMALS 3-6 MONTHS","ANIMALS 0-3 MONTHS"]
        lu_input_parameters = fn.create_input_table(template_lu_data,template_lu_index,"LIVESTOCK UNIT","livestock_unit_data")

    with lu_col2:
        # Create radio button to select area unit
        area_unit = st.radio("AREA UNIT",["Acre", "Hectare"],horizontal=True)

    with lu_col3:
        # Create date picker to input start and end dates
        start_date = st.date_input("Start Date", value=dt.date.today(),format="DD/MM/YYYY")
        end_date = st.date_input("End Date", value=dt.date.today(),format="DD/MM/YYYY")


# --- Field Rest Period section ---
if st.session_state.rest_data:
    st.warning("The field rest data feature has not yet been implemented ☹️")

#else:
#    st.error("❌ Data input errors must be fixed before continuing")




