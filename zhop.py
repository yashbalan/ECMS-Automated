import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import requests
import re
import random
import os


st.set_page_config(layout="wide", page_title="Hopcharge Dashboard", page_icon=":bar_chart:")
    


# Function to clean license plates
def clean_license_plate(plate):
    match = re.match(r"([A-Z]+[0-9]+)(_R)$", plate)
    if match:
        return match.group(1)
    return plate

# Function to get data from the API
def fetch_data(url):

    payload = {
        "username": "admin",
        "password": "Hopadmin@2024#"
    }
    headers = {
        'accept': 'application/json',
        'accept-language': 'en-US,en;q=0.9',
        'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiI3NmEzNzllYi02MzIxLTRmZjktOThhNS1lMzlkZjg0ZGU4YjUiLCJlbWFpbCI6ImhlbGxvQGhvcGNoYXJnZS5jb20iLCJwaG9uZU51bWJlciI6Iis5MTkzMTE2NjEyODgiLCJmaXJzdE5hbWUiOiJob3AiLCJsYXN0TmFtZSI6ImFkbWluIiwiY3JlYXRlZCI6IjIwMjItMDEtMDVUMDg6MzA6MzMuMDE3WiIsInVwZGF0ZWQiOiIyMDI0LTA1LTE3VDEyOjI1OjIzLjU0NloiLCJsYXN0TG9naW4iOiIyMDI0LTA2LTI0VDEwOjAxOjQ5LjUwM1oiLCJsYXN0TG9nb3V0IjoiMjAyNC0wNS0xN1QxMjoyNToyMy41NDdaIiwidXNlcm5hbWUiOiJob3BhZG1pbiIsInJvbGUiOiJhZG1pbiIsImlhdCI6MTcxOTIyMzMwOX0.YOI8cWlfSN5q4nQbnmwl2_-KPRpetGQoUvZ7yJZW3MA'
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    # Print the response text to understand its structure
    #print(response.text)

    # Try to parse the response JSON
    response_json = response.json()
    if 'data' in response_json:
        return pd.json_normalize(response_json['data'])
    else:
        return pd.DataFrame()  # Return an empty DataFrame if 'data' key is not found

# URLs for the APIs
url_bookings = "https://2e855a4f93a0.api.hopcharge.com/admin/api/v1/bookings/past?filter={\"chargedAt_lte\":\"2024-06-01\",\"chargedAt_gte\":\"2024-07-30\"}&range=[0,300000]&sort=[\"created\",\"DESC\"]"
url_drivers = "https://2e855a4f93a0.api.hopcharge.com/admin/api/v1/drivers-shifts/export-list?filter={\"action\":\"exporter\",\"startedAt_lte\":\"2024-06-01\",\"endedAt_gte\":\"2024-07-30\"}"

# Fetch data from the APIs
past_bookings_df = fetch_data(url_bookings)
drivers_shifts_df = fetch_data(url_drivers)

# Save the data to CSV for checking column names
#past_bookings_df.to_csv('data/past_bookings112.csv', index=False)
#drivers_shifts_df.to_csv('data/driver_shifts8.csv', index=False)

# Check if the DataFrame is empty
if past_bookings_df.empty or drivers_shifts_df.empty:
    st.error("No data found in the API response.")
else:
    # Printing the first few rows of the DataFrame for debugging
    print(past_bookings_df.head())
    print(drivers_shifts_df.head())

    # Filter where donorVMode is False
    filtered_drivers_df = drivers_shifts_df[drivers_shifts_df['donorVMode'] == 'FALSE']
    filtered_drivers_df = filtered_drivers_df.drop_duplicates(subset=['bookingUid'])

    filtered_drivers_df = drivers_shifts_df[drivers_shifts_df['bookingStatus'] == 'completed']


    # Cleaning license plates
    filtered_drivers_df['licensePlate'] = filtered_drivers_df['licensePlate'].apply(clean_license_plate)


    # Extracting Customer Location City by matching bookingUid with uid from past_bookings_df
    merged_df = pd.merge(filtered_drivers_df, past_bookings_df[['uid', 'location.state']],
                         left_on='bookingUid', right_on='uid', how='left')



    # Extracting Actual Date from fromTime
    #merged_df['Actual Date'] = pd.to_datetime(merged_df['fromTime'], errors='coerce')

    # Extracting Actual Date from bookingFromTime
    merged_df['Actual Date'] = pd.to_datetime(merged_df['bookingFromTime'], errors='coerce')

    # Selecting and renaming the required columns
    final_df = merged_df[['Actual Date', 'licensePlate', 'location.state', 'bookingUid', 'uid', 'bookingFromTime', 'bookingStatus', 'customerUid', 'totalUnitsCharged']].rename(columns={'location.state': 'Customer Location City'})

    # Ensure that there are no NaT values in the Actual Date column
    final_df = final_df.dropna(subset=['Actual Date'])
    #final_df['Actual Date'] = pd.to_datetime(final_df['Actual Date']).dt.date

    # Removing duplicates based on uid and bookingUid
    final_df = final_df.drop_duplicates(subset=['uid', 'bookingUid', 'Actual Date'])

    # Printing the first few rows of the DataFrame for debugging
    #st.write(final_df.head())
    #final_df.to_csv('data/bookings5.csv', index=False)

    # Reading EPOD data from CSV file
    df1 = pd.read_csv('EPOD NUMBER.csv')

    # Data cleaning and transformation
    final_df['licensePlate'] = final_df['licensePlate'].str.upper()
    final_df['licensePlate'] = final_df['licensePlate'].str.replace('HR55AJ4OO3', 'HR55AJ4003')
    # Replace specific license plates
    replace_dict = {
        'HR551305': 'HR55AJ1305',
        'HR552932': 'HR55AJ2932',
        'HR551216': 'HR55AJ1216',
        'HR555061': 'HR55AN5061',
        'HR554745': 'HR55AR4745',
        'HR55AN1216': 'HR55AJ1216',
        'HR55AN8997': 'HR55AN8997'
    }
    final_df['licensePlate'] = final_df['licensePlate'].replace(replace_dict)
    final_df['Actual Date'] = pd.to_datetime(final_df['Actual Date'], format='mixed', errors='coerce')
    final_df = final_df[final_df['Actual Date'].dt.year > 2021]
    final_df['Actual Date'] = final_df['Actual Date'].dt.date
    final_df['Customer Location City'].replace({'Haryana': 'Gurugram', 'Uttar Pradesh': 'Noida'}, inplace=True)
    cities = ['Gurugram', 'Noida', 'Delhi']
    final_df = final_df[final_df['Customer Location City'].isin(cities)]


    requiredcols = ['Actual Date', 'EPOD Name', 'Customer Location City']
    merged_df = pd.merge(final_df, df1, on=["licensePlate"])
    merged_df = merged_df[requiredcols]
    final_df = merged_df

    #final_df.to_csv('data/bookings6777.csv', index=False)

    # Helper function to format numbers in INR
    def formatINR(number):
        s, *d = str(number).partition(".")
        r = ",".join([s[x - 2:x] for x in range(-3, -len(s), -2)][::-1] + [s[-3:]])
        return "".join([r] + d)

    def check_credentials():
        st.markdown(
            """
                <style>
                    .appview-container .main .block-container {{
                        padding-top: {padding_top}rem;
                        padding-bottom: {padding_bottom}rem;
                        }}

                </style>""".format(
                padding_top=1, padding_bottom=1
            ),
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns(3)

        image = Image.open('LOGO HOPCHARGE-03.png')
        col2.image(image, use_column_width=True)
        col2.markdown(
            "<h2 style='text-align: center;'>ECMS Login</h2>", unsafe_allow_html=True)
        image = Image.open('roaming vans.png')
        col1.image(image, use_column_width=True)

        with col2:
            username = st.text_input("Username")
            password = st.text_input(
                "Password", type="password")
        flag = 0
        if username in st.secrets["username"] and password in st.secrets["password"]:
            index = st.secrets["username"].index(username)
            if st.secrets["password"][index] == password:
                st.session_state["logged_in"] = True
                flag = 1
            else:
                col2.warning("Invalid username or password.")
                flag = 0
        elif username not in st.secrets["username"] or password not in st.secrets["password"]:
            col2.warning("Invalid username or password.")
            flag = 0
        ans = [username, flag]
        return ans    

    def main_page(username):
        st.markdown(
            """
            <script>
            function refresh() {
                window.location.reload();
            }
            setTimeout(refresh, 120000);
            </script>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <style>
                .appview-container .main .block-container {{
                    padding-top: {padding_top}rem;
                    padding-bottom: {padding_bottom}rem;
                }}
            </style>
            """.format(padding_top=1, padding_bottom=1),
            unsafe_allow_html=True,
        )
        col1, col2, col3, col4, col5 = st.columns(5)
        image = Image.open('LOGO HOPCHARGE-03.png')
        col1.image(image, use_column_width=True)

        st.markdown("<h2 style='text-align: left;'>EV Charging Management System</h2>", unsafe_allow_html=True)

        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            final_df['Actual Date'] = pd.to_datetime(final_df['Actual Date'], errors='coerce')
            min_date = final_df['Actual Date'].min().date()
            max_date = final_df['Actual Date'].max().date()
            start_date = st.date_input('Start Date', min_value=min_date, max_value=max_date, value=min_date,
                                       key="epod-date-start")
        with col2:
            end_date = st.date_input('End Date', min_value=min_date, max_value=max_date, value=max_date,
                                     key="epod-date-end")

        epods = df1['EPOD Name'].tolist()

        with col3:
            EPod = st.multiselect(label='Select The EPod', options=['All'] + epods, default='All')
        if 'All' in EPod:
            EPod = epods

        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        filtered_data = final_df[(final_df['Actual Date'] >= start_date) & (final_df['Actual Date'] <= end_date)]

        filtered_data = filtered_data[(filtered_data['EPOD Name'].isin(EPod))]
        filtered_data['Actual Date'] = pd.to_datetime(filtered_data['Actual Date'])
        final_df_count = filtered_data.groupby(['Actual Date', 'Customer Location City']).size().reset_index(
            name='Session Count')
        final_df_count['Actual Date'] = final_df_count['Actual Date'].dt.strftime('%d/%m/%y')

        sumcount = final_df_count['Session Count'].sum()
        col4.metric("Total Sessions of EPods", formatINR(sumcount))
        revenue = sumcount * 150
        revenue = formatINR(revenue)
        col5.metric("Total Revenue", f"\u20B9{revenue}")

        fig = px.bar(final_df_count, x='Actual Date', y='Session Count',
                     color_discrete_map={'Delhi': '#243465', 'Gurugram': ' #5366a0', 'Noida': '#919fc8'},
                     color='Customer Location City', text=final_df_count['Session Count'])
        total_counts = final_df_count.groupby('Actual Date')['Session Count'].sum().reset_index()

        for i, date in enumerate(total_counts['Actual Date']):
            fig.add_annotation(
                x=date,
                y=total_counts['Session Count'][i] + 0.9,
                text=str(total_counts['Session Count'][i]),
                showarrow=False,
                align='center',
                font_size=16,
                font=dict(color='black')
            )

        fig.update_layout(
            title='Session Count of All EPods till Date',
            xaxis_title='Date',
            yaxis_title='Session Count',
            xaxis_tickangle=-45,
            width=1200,
            legend_title='HSZs: ',
        )

        with col1:
            st.plotly_chart(fig, use_container_width=False)

        filtered_data = final_df[final_df['EPOD Name'].isin(EPod)]

        if len(EPod) > 1:
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            filtered_data = filtered_data.sort_values('EPOD Name')
            for epod in filtered_data['EPOD Name'].unique():
                with col1:
                    st.subheader(epod)
                filtered_data = final_df[
                    (final_df['Actual Date'] >= start_date) & (final_df['Actual Date'] <= end_date)]
                final_df_count = filtered_data[filtered_data['EPOD Name'] == epod].groupby(
                    ['Actual Date', 'Customer Location City']).size().reset_index(name='Session Count')
                final_df_count['Actual Date'] = final_df_count['Actual Date'].dt.strftime('%d/%m/%y')
                final_df_count = final_df_count.sort_values('Actual Date', ascending=True)
                sumcount = final_df_count['Session Count'].sum()
                revenue = sumcount * 150
                revenue = formatINR(revenue)
                sumcount = formatINR(sumcount)
                col1.metric(f"Total Sessions by {epod}", sumcount)
                col1.metric("Total Revenue", f"\u20B9{revenue}")

                fig = px.bar(final_df_count, x='Actual Date', y='Session Count', color='Customer Location City',
                             color_discrete_map={'Delhi': '#243465', 'Gurugram': ' #5366a0', 'Noida': '#919fc8'},
                             text='Session Count')
                total_counts = final_df_count.groupby('Actual Date')['Session Count'].sum().reset_index()

                for i, date in enumerate(total_counts['Actual Date']):
                    fig.add_annotation(
                        x=date,
                        y=total_counts['Session Count'][i] + 0.2,
                        text=str(total_counts['Session Count'][i]),
                        showarrow=False,
                        align='center',
                        font_size=18,
                        font=dict(color='black')
                    )

                fig.update_xaxes(categoryorder='category ascending')
                fig.update_layout(
                    title='Session Count by Date',
                    xaxis_title='Date',
                    yaxis_title=f'Session Count of {epod}',
                    xaxis_tickangle=-45,
                    width=1200,
                    legend_title='HSZs: '
                )
                with col1:
                    st.plotly_chart(fig)

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        main_page(st.session_state.username)
    else:
        ans = check_credentials()
        if ans[1]:
            st.session_state.logged_in = True
            st.session_state.username = ans[0]
            st.experimental_rerun()


    # Run the main page function
    #main_page()
