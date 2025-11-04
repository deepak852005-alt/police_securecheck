import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
from datetime import date, time
# ---------------------------
# Database Connection
# ---------------------------
st.set_page_config(page_title="Police Data Dashboard", layout="wide")


# ✅ Database Connection Function
def create_database_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="deepak@2005",   # your password
            database="securecheck"
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"❌ Database connection failed: {e}")
        return None

# ✅ Safe conversion for optional integers
def safe_int(value):
    try:
        return int(value)
    except:
        return None


# ---------------------------
# Fetch Data from Database
# ---------------------------
def fetch_data(query):
    connection = create_database_connection()
    if connection:
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                df = pd.DataFrame(result)
                return df
        finally:
            connection.close()
    return pd.DataFrame()


# ---------------------------
# Streamlit UI
# ---------------------------


st.title("🚔 Police Data Dashboard")
st.markdown("Visualizing Police Data from MySQL Database")

# ---------------------------
# Full Data Table
# ---------------------------
st.header("Full Police Data Table")
query = "SELECT * FROM traffic_stops"
data_df = fetch_data(query)

if not data_df.empty:
    st.dataframe(data_df, use_container_width=True)
else:
    st.error("❌ No data found in the table or invalid table name.")


# ---------------------------
# Quick Metrics
# ---------------------------
st.header("Quick Metrics")

if not data_df.empty:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Stops", data_df.shape[0])

    with col2:
        arrests = data_df[data_df['stop_outcome'] == 'Arrest'].shape[0]
        st.metric("Total Arrests", arrests)

    with col3:
        warnings = data_df[data_df['stop_outcome'] == 'Warning'].shape[0]
        st.metric("Total Warnings", warnings)

    with col4:
        drugs_related = data_df[data_df['violation'] == True].shape[0]
        st.metric("Drug Related Stops", drugs_related)
else:
    st.warning("No data found in the table.")

# ---------------------------
# Charts
# ---------------------------
st.header("📊 Data Visualizations")

tab1, tab2 = st.tabs(["🚓 Stop Outcomes", "⚠️ Reasons for Stop"])

# ------------------- STOP OUTCOMES -------------------
with tab1:
    if not data_df.empty:
        # handle different possible column names
        if 'stop_outcome' in data_df.columns:
            col_name = 'stop_outcome'
        elif 'outcome' in data_df.columns:
            col_name = 'outcome'
        else:
            col_name = None

        if col_name:
            outcome_counts = data_df[col_name].value_counts().reset_index()
            outcome_counts.columns = ['Outcome', 'Count']

            fig1 = px.bar(
                outcome_counts,
                x='Outcome',
                y='Count',
                color='Outcome',
                title='🚔 Distribution of Stop Outcomes',
                text='Count'
            )
            fig1.update_layout(
                xaxis_title="Stop Outcome",
                yaxis_title="Number of Stops",
                showlegend=False,
                template="plotly_white"
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.warning("⚠️ No column named 'stop_outcome' or 'outcome' found in data.")
    else:
        st.error("❌ No data available for Stop Outcomes.")


# ------------------- REASONS FOR STOP -------------------
with tab2:
    if not data_df.empty:
        # handle different possible column names
        if 'violation' in data_df.columns:
            col_name = 'violation'
        elif 'reason_for_stop' in data_df.columns:
            col_name = 'reason_for_stop'
        else:
            col_name = None

        if col_name:
            reason_counts = data_df[col_name].value_counts().reset_index()
            reason_counts.columns = ['Reason', 'Count']

            fig2 = px.pie(
                reason_counts,
                names='Reason',
                values='Count',
                title='⚠️ Reasons for Stop',
                hole=0.4
            )
            fig2.update_traces(textinfo='percent+label')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("⚠️ No column named 'violation' or 'reason_for_stop' found in data.")
    else:
        st.error("❌ No data available for Reasons for Stop.")


# ---------------------------
# Advanced Query
# ---------------------------
st.header("Advanced Query")

selected_outcome = st.selectbox(
    "Select a query to run:",
    [
        "Top 5 Locations with Most Arrests",
        "Monthly Stop Counts",
        "Yearly Stop Counts",
        "Top 5 Reasons for Stops",
        "Number of Arrests vs Warnings",
    ]
)

query_map = { 
  "Top 5 Locations with Most Arrests": """
    SELECT country_name AS location, COUNT(*) AS arrest_count 
    FROM traffic_stops 
    WHERE stop_outcome = 'Arrest' 
    GROUP BY country_name 
    ORDER BY arrest_count DESC 
    LIMIT 5
  """,
  "Monthly Stop Counts": """
    SELECT MONTH(stop_date) AS month, COUNT(*) AS stop_count 
    FROM traffic_stops 
    GROUP BY month 
    ORDER BY month
  """,
  "Yearly Stop Counts": """
    SELECT YEAR(stop_date) AS year, COUNT(*) AS stop_count 
    FROM traffic_stops 
    GROUP BY year 
    ORDER BY year
  """,
  "Top 5 Reasons for Stops": """
    SELECT violation AS stop_reason, COUNT(*) AS stop_count 
    FROM traffic_stops 
    GROUP BY violation 
    ORDER BY stop_count DESC 
    LIMIT 5
  """,
  "Number of Arrests vs Warnings": """
    SELECT stop_outcome, COUNT(*) AS count 
    FROM traffic_stops 
    WHERE stop_outcome IN ('Arrest', 'Warning') 
    GROUP BY stop_outcome
  """,
  "Most Common Age Group Stopped": """
    SELECT driver_age, COUNT(*) AS count 
    FROM traffic_stops 
    GROUP BY driver_age 
    ORDER BY count DESC 
    LIMIT 1
  """,
  "Count of Stops by Gender": """
    SELECT driver_gender, COUNT(*) AS count 
    FROM traffic_stops 
    GROUP BY driver_gender
  """
}


if st.button("Run Query"):
    result_df = fetch_data(query_map[selected_outcome])
    if not result_df.empty:
        st.write(f"### Results for: {selected_outcome}")
        st.dataframe(result_df)
    else:
        st.warning("No data returned for the selected query.")

with st.form("add_log_form"):
    stop_date = st.date_input("Stop Date", date.today())
    stop_time = st.time_input("Stop Time", value=None)
    location = st.selectbox("Location",["USA", "India", "UK", "Canada", "Australia"])
    officer_name = st.selectbox("Officer Name", ["Deepak", "Prince", "Nithish", "Chandru"])
    vehicle_number = st.text_input("Vehicle Number")
    reason_for_stop = st.selectbox("Reason for Stop",["Speeding", "Signal Violation", "Document Check", "Drunk Driving", "Other"])
    outcome = st.selectbox("Outcome", ["Warning", "Arrest", "Citation", "No Action"])
    submit = st.form_submit_button("Add Record")

    if submit:
        conn = create_database_connection()
        if conn:
            cursor = conn.cursor()

            # ✅ Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS traffic_stops (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    stop_date DATE,
                    stop_time TIME,
                    location VARCHAR(255),
                    officer_name VARCHAR(255),
                    vehicle_number VARCHAR(50),
                    reason_for_stop VARCHAR(255),
                    outcome VARCHAR(100)
                )
            """)

            insert_query = """INSERT INTO traffic_stops (stop_date, stop_time, country_name, driver_gender, driver_age_raw,driver_age, driver_race, violation_raw, violation,
            search_conducted, search_type, stop_outcome
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           """


            # ✅ Prepare values safely
            values = (
                stop_date.strftime("%Y-%m-%d"),
                stop_time.strftime("%H:%M:%S") if stop_time else None,
                vehicle_number or None,
                officer_name or None,
                reason_for_stop or None,
                outcome or None
            )

            try:
                cursor.execute(insert_query, values)
                conn.commit()
                st.success("✅ New police log added successfully!")
            except mysql.connector.Error as e:
                st.error(f"❌ Error inserting data: {e}")
            finally:
                cursor.close()
                conn.close()
        else:
            st.error("❌ Failed to connect to the database.")

# ---------------------------
# Footer
# ---------------------------
st.markdown("---")
st.markdown("© 2025 Deepak — All rights reserved.")