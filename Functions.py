import streamlit as st
import pandas as pd
import numpy as np
import re

def extract_number(value):
    # If it's already a number, just return it
    if isinstance(value, (int, float)):
        return float(value)
    
    # If it's a string pull out the number
    if isinstance(value, str):
        # This regex finds digits and decimal points
        match = re.search(r"(\d+\.?\d*)", value)
        if match:
            return float(match.group(1))

@st.cache_data
def load_csv(file):
    # Reads in csv. This only runs once per file to save time
    return pd.read_csv(file)

def ensure_datetime_cols(dataframe, columns_to_check):
    # Create a copy so we don't accidentally modify the original unexpectedly
    copied_dataframe = dataframe.copy()
    
    for col in columns_to_check:
        if col in copied_dataframe.columns:
            # errors='coerce' turns unparseable dates into NaT (Not a Time)
            copied_dataframe[col] = pd.to_datetime(copied_dataframe[col], errors='coerce', dayfirst=True, format="mixed")
            
    return copied_dataframe

def process_csv(label,help_text):
    # Create the file uploader widget
    uploaded_file = st.file_uploader(label, type="csv",key=label,help=help_text)

    if uploaded_file is not None:
        # Read the file into a Pandas DataFrame
        df = load_csv(uploaded_file)
        # Convert any date columns to datetime
        date_columns = ["Date of birth", "Date on farm", "Date off farm", "Date moved out", "Date moved in"]
        cleaned_df = ensure_datetime_cols(df,date_columns)
        
        return cleaned_df
    else:
        st.warning("💡 Please upload a CSV file to get started.")
        return None

def validate_csv_column_headings(data_table,expected_headings):
        actual_cols = set(data_table.columns)
        required_cols = set(expected_headings)
        
        # Check if all required columns are present
        missing_cols = required_cols - actual_cols
        
        if not missing_cols:
            st.success(f"✅ csv columns validated!")
            return True
        else:
            # Display a clear error message
            st.error(f"❌ Required column missing in csv. Missing: {', '.join(missing_cols)}")
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
    
def validate_date_order(data_table,col_name):
    is_ordered = data_table[col_name].is_monotonic_decreasing
    is_error = data_table[col_name].diff() > pd.Timedelta(0)
    error_rows = data_table[is_error]

    if not error_rows.empty:
        st.error(f"❌ Entries in **{col_name}** column are not in order from newest to oldest")
        st.dataframe(error_rows[col_name])
        return False
    else:
        st.success(f"✅ Entries in **{col_name}** column are in correct order")
        return True

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


def calculate_animal_groups(calc_date,cattle_data,lu_data):
    # Filter active cattle
    mask = (cattle_data["Date of birth"] <= calc_date) & \
        (cattle_data["Date on farm"] <= calc_date) & \
        ((cattle_data["Date off farm"].isna()) | (cattle_data["Date off farm"] > calc_date))
    
    active = cattle_data[mask].copy()
    age_months = ((calc_date - active["Date of birth"]).dt.days / 30.4735)
    
    # Define logic bins
    # Bins: 0-3, 3-6, 6-12, 12-24, 24+
    labels = ["calves_03", "calves_36", "calves_612", "youngstock", "adults"]
    active["Group_Key"] = pd.cut(age_months, bins=[0, 3, 6, 12, 24, 1000], labels=labels)
    
    # Map specific lus from lu_data
    lu_lookup = {
        "calves_03": lu_data.iloc[4], "calves_36": lu_data.iloc[3],
        "calves_612": lu_data.iloc[2], "youngstock": lu_data.iloc[1], "adults": lu_data.iloc[0]
    }
    active["Livestock Unit"] = active["Group_Key"].map(lu_lookup).astype(float)
    
    # Map final Group Names for matching
    # Define conditions for the 'adults' category (24+ months)
    is_adult = (active["Group_Key"] == "adults")
    is_female = (active["M/F"].astype(str).str.strip().str.upper() == "F")
    is_bull = (active["Bull?"].astype(str).str.strip().str.upper().isin(["YES", "Y", "TRUE"]))
    # Assign specific names to the adults
    conditions = [
        (is_adult & is_bull),
        (is_adult & is_female),
        (is_adult)
    ]
    choices = ["bulls", "cows", "steer"]
    active["Group"] = np.select(conditions, choices, default=None)
    # Fill in the non-adults (calves and youngstock)
    name_map = {
        "calves_03": "calves", 
        "calves_36": "calves", 
        "calves_612": "calves", 
        "youngstock": "youngstock"
    }
    active["Group"] = active["Group"].fillna(active["Group_Key"].map(name_map))
    
    return active.groupby("Group")["Livestock Unit"].sum().to_dict()

def calculate_most_recent_animal_days_per_area(grazing_data_table, cattle_data_table, field_table, field_area_unit, lu_data):

    # Field Area lookup
    area_col = 'Field Area (Hectare)' if field_area_unit == "Hectare" else 'Field Area (Acre)'
    field_area_map = dict(zip(field_table['Field Name'], field_table[area_col]))

    # Pre-index grazing table
    results = []
    out_records = grazing_data_table[grazing_data_table['Which field are the cattle moving out of?'] != grazing_data_table['Which field are the cattle moving into?']]
    
    # Iterate through fields in field table
    for field_name in field_table['Field Name']:
        out_date_str = "-"
        total_lu = 0.0
        days_in_field = 0
        animal_days = 0.0
        base_area = field_area_map.get(field_name, 0)
        paddock_use = 1.0
        effective_area = base_area * paddock_use

        # Find OUT record
        row_out = out_records[out_records['Which field are the cattle moving out of?'] == field_name]
        
        if not row_out.empty:
            out_idx = row_out.index[0]
            out_date = row_out.at[out_idx, 'Date moved out']
            out_date_str = out_date.strftime('%d/%m/%Y')
            mgmt_group = str(row_out.at[out_idx, 'Management group']).lower()
            
            # Find the IN record
            in_date = out_date
            multiple_paddocks = False
            past_moves = grazing_data_table.iloc[out_idx + 1:]
            match_in = past_moves[past_moves['Which field are the cattle moving into?'] == field_name]
            
            if not match_in.empty:
                for index, row in match_in.iterrows():
                    if row['Which field are the cattle moving into?'] != row['Which field are the cattle moving out of?']:
                        in_date = row['Date moved in']
                        paddock_use = extract_number(row['How has the field been split?'])
                        
                        if multiple_paddocks:
                            paddock_use = 1.0
                        break # This is your 'Exit For'
                    else:
                        multiple_paddocks = True
            
            # Calculate days in field
            days_in_field = (out_date - in_date).days
            if days_in_field > 0:
                # Get livestock units for date
                lu_sums = calculate_animal_groups(out_date,cattle_data_table,lu_data)
                
                # Check which groups match management_group
                total_lu = 0
                for group_name in ['cows', 'calves', 'youngstock', 'bulls','steers']:
                    if group_name in mgmt_group:
                        total_lu += lu_sums.get(group_name, 0)
                
                # Calculate field area
                effective_area = base_area * paddock_use
                
                # Calculate animal days per unit area
                animal_days = round((total_lu * days_in_field) / effective_area, 1)
                
        results.append({
            'FIELD': field_name,
            'DATE': out_date_str,
            'TOTAL LIVESTOCK UNITS': total_lu,
            'PADDOCK AREA': effective_area,
            'GRAZING PERIOD': days_in_field,
            f'ANIMAL DAYS/{str(field_area_unit).upper()}': animal_days
        })

    return pd.DataFrame(results)

def calculate_all_grazing_events(start_date,end_date,grazing_data_table, cattle_data_table, field_table, field_area_unit, lu_data):
    # Field Area lookup
    area_col = 'Field Area (Hectare)' if field_area_unit == "Hectare" else 'Field Area (Acre)'
    field_area_map = dict(zip(field_table['Field Name'], field_table[area_col]))

    results = []

    # Filter for date period
    mask = (pd.to_datetime(grazing_data_table['Date moved out']) <= end_date) & (pd.to_datetime(grazing_data_table['Date moved out']) >= start_date)
    filtered_grazing_data = grazing_data_table[mask].copy()

    # Filter for all valid "Out" records
    out_movements = filtered_grazing_data[filtered_grazing_data['Which field are the cattle moving out of?'] != filtered_grazing_data['Which field are the cattle moving into?']].copy()

    # 3. Iterate through every "Out" movement found in the table
    for out_idx, row_out in out_movements.iterrows():
        field_name = row_out['Which field are the cattle moving out of?']
            
        out_date = row_out['Date moved out']
        mgmt_group = str(row_out['Management group']).lower()
        base_area = field_area_map.get(field_name, 0)

        # Find the corresponding "In" record
        in_date = out_date
        paddock_use = 1.0
        multiple_paddocks = False
        
        past_moves = filtered_grazing_data.iloc[out_idx + 1:]
        match_in = past_moves[past_moves['Which field are the cattle moving into?'] == field_name]
        
        if not match_in.empty:
            for index, row in match_in.iterrows():
                if row['Which field are the cattle moving into?'] != row['Which field are the cattle moving out of?']:
                    in_date = row['Date moved in']
                    paddock_use = extract_number(row['How has the field been split?'])
                    
                    if multiple_paddocks:
                        paddock_use = 1.0
                    break 
                else:
                    multiple_paddocks = True

        # Calculate days in field
        days_in_field = (out_date - in_date).days
        if days_in_field > 0:
            # Get livestock units for date
            lu_sums = calculate_animal_groups(out_date,cattle_data_table,lu_data)
            
            # Check which groups match management_group
            total_lu = 0
            for group_name in ['cows', 'calves', 'youngstock', 'bulls','steers']:
                if group_name in mgmt_group:
                    total_lu += lu_sums.get(group_name, 0)
            
            # Calculate field area
            effective_area = base_area * paddock_use

            # Calculate animal days per unit area
            animal_days = round((total_lu * days_in_field) / effective_area, 1) if effective_area > 0 else 0
            
            results.append({
                'FIELD': field_name,
                'DATE': out_date.strftime('%d/%m/%Y'),
                'TOTAL LIVESTOCK UNITS': total_lu,
                'PADDOCK AREA': effective_area,
                'GRAZING PERIOD': days_in_field,
                f'ANIMAL DAYS/{str(field_area_unit).upper()}': animal_days
            })

    # Return every single event found
    return pd.DataFrame(results)

def summary_of_animal_days_per_area_over_time(full_table,field_area_unit):
    # Group by the 'FIELD' column and calculate:
    field_summary = full_table.groupby('FIELD')[f'ANIMAL DAYS/{str(field_area_unit).upper()}'].agg(['count', 'sum', 'mean']).reset_index()

    # Set colum names and round numbers
    field_summary.columns = ['FIELD','NUMBER OF GRAZING EVENTS',f'TOTAL ANIMAL DAYS/{str(field_area_unit).upper()}',f'AVERAGE ANIMAL DAYS/{str(field_area_unit).upper()}']
    field_summary[f'TOTAL ANIMAL DAYS/{str(field_area_unit).upper()}'] = field_summary[f'TOTAL ANIMAL DAYS/{str(field_area_unit).upper()}'].round(1)
    field_summary[f'AVERAGE ANIMAL DAYS/{str(field_area_unit).upper()}'] = field_summary[f'AVERAGE ANIMAL DAYS/{str(field_area_unit).upper()}'].round(1)
    return field_summary

def plot_animal_days_for_field(all_grazing_events_data,selected_field, area_unit):
    # Filter the data for that field
    field_history = all_grazing_events_data[all_grazing_events_data['FIELD'] == selected_field].copy()

    # Convert 'DATE' back to a datetime object so it sorts correctly on the graph
    field_history['DATE'] = pd.to_datetime(field_history['DATE'], dayfirst=True)
    field_history = field_history.sort_values('DATE')

    # Plot line chart
    st.subheader(f'Animal days/{area_unit} over time for {selected_field}')
    if selected_field == "All":
        st.line_chart(data=all_grazing_events_data, x='DATE', y=f'ANIMAL DAYS/{str(area_unit).upper()}', color='FIELD')
    else:
        st.line_chart(data=field_history, x='DATE', y=f'ANIMAL DAYS/{str(area_unit).upper()}')