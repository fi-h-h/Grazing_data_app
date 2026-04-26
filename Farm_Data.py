""" Program to calculate the livestock units, animal days per unit area, and field rest periods
for cattle grazing data. Uses streamlit for UI and display. Takes in 3 csv files detailing the 
cattle data, field data and grazing data"""
import datetime as dt
import streamlit as st
import pandas as pd
import Functions as fn

# Set to wide mode
st.set_page_config(layout="wide")

# Set the page title
st.set_page_config(page_title="Farm Grazing Data")

###############################
# --- INITIALISE VARIABLES ---
###############################

if 'cattle_data_table' not in st.session_state:
    st.session_state.cattle_data_table = pd.DataFrame()
if 'field_data_table' not in st.session_state:
    st.session_state.field_data_table = pd.DataFrame()
if 'grazing_data_table' not in st.session_state:
    st.session_state.grazing_data_table = pd.DataFrame()
validation_results = []
lu_input_parameters = None
area_unit = None
start_date = None
end_date = None
animal_days_per_unit_area = pd.DataFrame()
all_grazing_events = pd.DataFrame()
animal_days_summary = pd.DataFrame()
list_of_fields_in_time_period = pd.DataFrame()
field_rest_data = pd.DataFrame()

###############################
# --- DATA INPUT SECTION ---
###############################

# Set up page header
with st.sidebar:
    st.title("🔢 Data Input",text_alignment="center")
    st.divider()

    # Define expected headings
    expected_cattle_headings = ["Ear Tag Number", "Date of birth", "M/F", "Bull?", "Empty?", "Date on farm", "Date off farm"]
    expected_field_headings = ["Field Name", "Field Area (Hectare)", "Field Area (Acre)"]
    expected_grazing_headings = ["Your name", "Management group", "Date moved out", "Which field are the cattle moving out of?", "What does the paddock the cattle are moving out of look like?", "Date moved in",	
                                "Which field are the cattle moving into?", "How has the field been split?", "Is this the first, second, third...paddock in the field?", "What does the pasture look like?", "What do the cattle look like?"]

    # Read in cattle data
    st.subheader("🤠 Cattle Data")
    st.info(f"**Upload a CSV file of your cattle data**")
    st.session_state.cattle_data_table = fn.process_csv("Choose a cattle data CSV file",f"Column headings should be:  \n{expected_cattle_headings}")
    # Check column headings are correct
    if not st.session_state.cattle_data_table.empty:
        validation_results.append(fn.validate_csv_column_headings(st.session_state.cattle_data_table,expected_cattle_headings))

    # Read in field data
    st.subheader("🌿 Field Data")
    st.info(f"**Upload a CSV file of your field data**")
    st.session_state.field_data_table = fn.process_csv("Choose a field data CSV file",f"Column headings should be:  \n{expected_field_headings}")
    # Check column headings are correct
    if not st.session_state.field_data_table.empty:
        validation_results.append(fn.validate_csv_column_headings(st.session_state.field_data_table,expected_field_headings))

    # Read in grazing data
    st.subheader("🐮 Grazing Data")
    st.info("**Upload a CSV file of your grazing data from the google form**")
    st.session_state.grazing_data_table = fn.process_csv("Choose a grazing data CSV file","Ensure field names match those in the field data csv and entries are in calendar order - newest at the top to oldest at the bottom")
    
    # Check column headings are correct
    if not st.session_state.grazing_data_table.empty:
        validation_results.append(fn.validate_csv_column_headings(st.session_state.grazing_data_table,expected_grazing_headings))
        validation_results.append(fn.validate_date_order(st.session_state.grazing_data_table,"Date moved out"))
        validation_results.append(fn.validate_date_order(st.session_state.grazing_data_table,"Date moved in"))
    
    # Check field names in grazing file matches data in field file
    if not st.session_state.grazing_data_table.empty and not st.session_state.field_data_table.empty:
        validation_results.append(fn.validate_grazing_data(st.session_state.grazing_data_table, ["Which field are the cattle moving out of?", "Which field are the cattle moving into?"], st.session_state.field_data_table, "Field Name"))

    st.divider()

###############################
# --- DATA ANALYSIS SECTION ---
###############################

# Set up page header
st.title("📊 Grazing Data Analysis",text_alignment="center")
st.divider()

# Check that there are no errors in the data input before moving on
if not st.session_state.grazing_data_table.empty and not st.session_state.field_data_table.empty and not st.session_state.cattle_data_table.empty and all(validation_results):
    st.success("✅ All data present and validated")
    
    # Initialise option buttons
    if "livestock_unit" not in st.session_state:
        st.session_state.livestock_unit = False
    if "rest_data" not in st.session_state:
        st.session_state.rest_data = False

    # Display option buttons
    st.subheader("What would you like to calculate?")
    left_space, button_col1, button_col2, right_space = st.columns([2, 2, 2, 2])
    with button_col1:
        if st.button("🐄 Animal Days per Unit Area", type="primary",width="stretch"):
            st.session_state.livestock_unit = True
            st.session_state.rest_data = False
    with button_col2:
        if st.button("🌱 Field Rest Period Data",type="primary",width="stretch"):
            st.session_state.rest_data = True
            st.session_state.livestock_unit = False
    st.divider()

    ###############################
    # --- ANIMAL DAYS/AREA SECTION ---
    ###############################

    if st.session_state.livestock_unit:
        st.title("🐄 Animal Days/Unit Area Output",text_alignment="center")
        st.info("**Please enter the livestock units, unit area, and timescale you wish to use for the calculation**")

        # Set up columns
        lu_col1, lu_col2, lu_col3 = st.columns(3, border=True)

        # Create table to input the livestock units into
        with lu_col1:
            template_lu_data = {"VALUE": [1,0.5,0.3,0.2,0.1]}
            template_lu_index = ["ANIMALS 2+ YEARS","ANIMALS 12-24 MONTHS","ANIMALS 6-12 MONTHS","ANIMALS 3-6 MONTHS","ANIMALS 0-3 MONTHS"]
            lu_input_parameters = fn.create_input_table(template_lu_data,template_lu_index,"LIVESTOCK UNIT","livestock_unit_data")

        # Create radio button to select area unit
        with lu_col2:
            area_unit = st.radio("AREA UNIT",["Acre", "Hectare"],horizontal=True)

        # Create date picker to input start and end dates
        with lu_col3:
            start_date = st.date_input("START DATE", value=dt.date.today(),format="DD/MM/YYYY",max_value="today")
            start_date = pd.to_datetime(start_date)
            end_date = st.date_input("END DATE", value=dt.date.today(),format="DD/MM/YYYY",max_value="today")
            end_date = pd.to_datetime(end_date)

        # Check you have all the input parameters
        if lu_input_parameters is not None and area_unit is not None and start_date is not None and end_date is not None:

            # Columns for output
            output_col1, output_col2 = st.columns(2,border=True)
            with output_col1:
                # Calculate animal days per unit area for most recent grazing
                st.subheader("Most Recent Grazing Event",text_alignment="center")
                animal_days_per_unit_area = fn.calculate_most_recent_animal_days_per_area(st.session_state.grazing_data_table,st.session_state.cattle_data_table,st.session_state.field_data_table,area_unit, lu_input_parameters["VALUE"])
                # Plot table of most recent grazing events
                dynamic_height = min(len(animal_days_per_unit_area) * 35 + 40, 1000)
                st.dataframe(
                    data=animal_days_per_unit_area, 
                    width="stretch",
                    hide_index=True,
                    height=dynamic_height,
                    column_config={
                        "FIELD": st.column_config.TextColumn(
                            "FIELD"
                        ),
                        "DATE": st.column_config.DateColumn(
                            "DATE"
                        ),
                        f"ANIMAL DAYS/{str(area_unit).upper()}": st.column_config.NumberColumn(
                            f"ANIMAL DAYS/{str(area_unit).upper()}",
                            format="%.1f"
                        ),
                        "TOTAL LIVESTOCK UNITS": st.column_config.NumberColumn(
                            "TOTAL LIVESTOCK UNITS",
                            format="%.1f"
                        ),
                        #"GROUPS": st.column_config.TextColumn(
                        #    "GROUPS"
                        #),
                        "GRAZING PERIOD": st.column_config.NumberColumn(
                            "GRAZING PERIOD",
                            format="%d"
                        )
                        #"PADDOCK AREA": st.column_config.NumberColumn(
                        #    "PADDOCK AREA",
                        #    format="%.2f"
                        #)
                    }
                )

            with output_col2:
                # Calculate animal days per unit area over time
                st.subheader(f"Grazing Data Over Time from {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}",text_alignment="center")
                all_grazing_events = fn.calculate_all_grazing_events(start_date,end_date,st.session_state.grazing_data_table,st.session_state.cattle_data_table,st.session_state.field_data_table,area_unit, lu_input_parameters["VALUE"])
                if all_grazing_events.empty:
                    st.warning("⚠️ No grazing events found in the specified time period")
                
                # Plot table of grazing events
                else:
                    animal_days_summary = fn.summary_of_animal_days_per_area_over_time(all_grazing_events,area_unit)
                    dynamic_height = min(len(animal_days_summary) * 35 + 40, 1000)
                    st.dataframe(
                        data=animal_days_summary,
                        hide_index=True, 
                        width="stretch",
                        height=dynamic_height,
                        column_config={
                            "FIELD": st.column_config.TextColumn(
                            "FIELD"
                        ),
                        "NO. OF GRAZING EVENTS": st.column_config.NumberColumn(
                            "NO. OF GRAZING EVENTS",
                            format="%d"
                        ),
                        f"TOTAL ANIMAL DAYS/{str(area_unit).upper()}": st.column_config.NumberColumn(
                            f"TOTAL ANIMAL DAYS/{str(area_unit).upper()}",
                            format="%.1f"
                        ),
                        f"AVERAGE ANIMAL DAYS/{str(area_unit).upper()}": st.column_config.NumberColumn(
                            f"AVERAGE ANIMAL DAYS/{str(area_unit).upper()}",
                            format="%.1f"
                        )
                    }
                )

            # Plot graph of user selected field or all fields
            if not animal_days_summary.empty:
                list_of_fields_in_time_period = animal_days_summary['FIELD'].unique().tolist()
                list_of_fields_in_time_period = ["All"] + list_of_fields_in_time_period
                selected_field = st.selectbox("Select a Field to View History", list_of_fields_in_time_period,width=500)
                fn.plot_animal_days_for_field(all_grazing_events,selected_field, area_unit)

    ###############################
    # --- FIELD REST PERIOD SECTION ---
    ###############################

    if st.session_state.rest_data:
        
        # Calculate field rest data
        field_rest_data = fn.calculate_field_rest_data(st.session_state.grazing_data_table,st.session_state.field_data_table)
        
        # Create table of field rest data 
        if not field_rest_data.empty:
            st.title("🌱 Field Rest Period Output",text_alignment="center")
            dynamic_height = min(len(field_rest_data) * 35 + 40, 1000)
            st.dataframe(
                data=field_rest_data, 
                width="stretch",
                hide_index=True,
                height=dynamic_height,
                column_config={
                    "FIELD": st.column_config.TextColumn(
                        "FIELD"
                    ),
                    "MOST RECENT GRAZING EVENT": st.column_config.DateColumn(
                        "MOST RECENT GRAZING EVENT"
                    ),
                    "PREVIOUSLY RESTED FOR": st.column_config.NumberColumn(
                        "PREVIOUSLY RESTED FOR",
                        format="%d"
                    ),
                    "PADDOCK STATE ON ENTRY": st.column_config.TextColumn(
                        "PADDOCK STATE ON ENTRY"
                    ),
                    "GRAZING PERIOD": st.column_config.NumberColumn(
                        "GRAZING PERIOD",
                        format="%d"
                    ),
                    "PADDOCK STATE ON EXIT": st.column_config.TextColumn(
                        "PADDOCK STATE ON EXIT"
                    ),
                    "CURRENT DAYS RESTED": st.column_config.NumberColumn(
                        "PADDOCK AREA",
                        format="%d"
                    )
                }
            )
        else:
            st.warning("⚠️ No grazing data found, please check inputs")

elif not st.session_state.grazing_data_table.empty and not st.session_state.field_data_table.empty and not st.session_state.cattle_data_table.empty:
    st.error("❌ Please fix identified errors in data input.")

else:
    st.warning("⚠️ Please select cattle data, field data, and grazing data files to be used.")




