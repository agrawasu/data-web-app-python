import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px

DATA_URL = (
    'https://data.cityofnewyork.us/resource/h9gi-nx95.csv?$limit=100000'
)

st.title('Motor Vehicle Collisions in New York City')
st.markdown('#### This application is a StreamLit dashboard '
            'that can be used to analyze motor vehicle '
            'collisions in NYC')

@st.cache_data(persist=True)
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows, parse_dates=[['crash_date','crash_time']])
    data.dropna(subset=['latitude','latitude'], inplace=True)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data.rename(columns={'crash_date_crash_time': 'date/time',}, inplace=True)
    return data

data = load_data(100000)
original_data = data

st.header('Where are the most people injured due to motor vehicle accidents in NYC?')
injured_people = st.slider('Number of persons injured', 0, 19)
st.map(data.query('number_of_persons_injured >= @injured_people')[['latitude','longitude']].dropna(how='any'))

st.header('How many collisions occur at a given time of day?')
hour = st.select_slider('Hour', range(0,24), 1)
data = data[data['date/time'].dt.hour == hour]

st.markdown('Vehicle collisions between %i:00 and %i:00' % (hour, (hour + 1) % 24))

midpoint = (np.average(data['latitude']), np.average(data['longitude']))
st.write(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state={
        'latitude': midpoint[0],
        'longitude': midpoint[1],
        'zoom': 11,
        'pitch': 50,
    },
    layers=[
        pdk.Layer(
            'HexagonLayer',
            data=data[['date/time','latitude','longitude']],
            get_position=['longitude','latitude'],
            radius=100,
            extruded=True,
            pickable=True,
            elevation_scale=4,
            elevation_range=[0,1000],
        ),
    ]
))

st.subheader('Breakdown by minute between %i:00 and %i:00' % (hour, (hour + 1) % 24))
filtered = data[
    (data['date/time'].dt.hour >= hour) & (data['date/time'].dt.hour < (hour + 1))
]
hist = np.histogram(filtered['date/time'].dt.minute, bins=60, range=(0,60))[0]
chart_data = pd.DataFrame({'minute':range(60), 'crashes':hist})
fig = px.bar(chart_data, x='minute', y='crashes', hover_data=['minute', 'crashes'], height=600)
st.write(fig)

st.header('Top 10 dangerous streets by affected people')
select = st.selectbox('Affected type of person', ['Pedestrians', 'Cyclists', 'Motorists'])

if select == 'Pedestrians':
    st.write(original_data.query('injured_pedestrians >= 1') [['on_street_name', 'injured_pedestrians']].sort_values(by=['injured_pedestrians'], ascending=False).dropna(how='any')[:10])
elif select == 'Cyclists':
    st.write(original_data.query('injured_cyclists >= 1') [['on_street_name', 'injured_cyclists']].sort_values(by=['injured_cyclists'], ascending=False).dropna(how='any')[:10])
elif select == 'Motorists':
    st.write(original_data.query('injured_motorists >= 1') [['on_street_name', 'injured_motorists']].sort_values(by=['injured_motorists'], ascending=False).dropna(how='any')[:10])

if st.checkbox('Show Raw Data', False):
    st.subheader('Raw Data')
    st.write(data)