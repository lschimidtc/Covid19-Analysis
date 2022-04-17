from re import T
import pandas as pd
import pydeck as pdk
import numpy as np
import streamlit as st

@st.cache(persist=True)
def load_dataset(arquivo):
    dataset = pd.read_csv(arquivo)
    dataset.dropna(subset = ['muni', 'codIbge'], inplace = True)
    dataset = dataset.reset_index(drop = True)
    return dataset

st.set_page_config(page_title='COVID-19 Analysis',
                   page_icon='src/fvc.png',
                   layout="wide")

dataset = load_dataset('covid_dataset_v2.csv')
st.title("COVID-19 per cities in Brasil")
st.markdown("Analysis of data from the site brasil.io  "
            "about occurrences of COVID-19 in Brasilian cities.")
st.header("Cases of COVID-19 in cities")
ano = int(dataset['semEpid'].max()/100)
semana = int(dataset['semEpid'].max()%100)
st.subheader(f"Last epidemiological week: {ano}-{semana}")
st.subheader("Date: %s" % dataset['data'].max())
# First map
mediaDia = int(round(sum(dataset['confDia'])/len(dataset['confDia'])))
confNoDia = st.slider("Confirmed cases on the day", 0, mediaDia, 10, 2)
st.text('Slide the cursor to select or number of confirmed cases on the day')
st.text(' ')
semEpidem = st.slider("Epidemiological week", int(dataset['semEpid'].min()), int(dataset['semEpid'].max()), int(dataset['semEpid'].max()))
st.text('Select the epidemiological week you want to see the data')
temp_dataset = dataset.query("semEpid == @semEpidem")[["confDia", "lat", "lon"]].dropna(how="any")
st.map(temp_dataset.query("confDia >= @confNoDia")[["lat", "lon"]].dropna(how="any"))
st.text('Use the mouse to zoom or move the map')
# Second map
st.header("New cases per day")
semanaEpidem = st.slider("Selection of the epidemiological week", int(dataset['semEpid'].min()), int(dataset['semEpid'].max()), int(dataset['semEpid'].max()))
st.text('The selected epidemiological week affects the graphs and table in the sequence')
eval_data = dataset
eval_data = eval_data[eval_data['semEpid'] == semanaEpidem]
st.markdown(f"New COVID-19 cases this week {semanaEpidem}")
# Location of some cities
# Brasilia
BSB_LAT = -15.7934036
BSB_LON = -47.8823172
# Sao Paulo
SPO_LAT = -23.5506507
SPO_LON = -46.6333824

st.write(pdk.Deck(
    map_style="mapbox://styles/mapbox/outdoors-v11",
    initial_view_state={
        "latitude": BSB_LAT,                   
        "longitude": BSB_LON,
        "zoom": 4,
        "pitch": 50,
    },
    layers=[
        pdk.Layer(
        "HexagonLayer",
        data=eval_data[['confDia', 'lat', 'lon']],
        get_position=['lon', 'lat'],
        auto_highlight=True,
        radius=10000,
        extruded=True,
        pickable=True,
        elevation_scale=500,
        elevation_range=[0, 1500],
        ),
    ],
))
# Table of cities with the most cases selected by the drop-down in the epidemiological week selected in the graphic above
st.header(f"The cities with the most cases - Week {semEpidem}")
num_muni = st.slider("Number of cities to list", 1 , 10, 6)
select = st.selectbox('Assessment type - select from the dropdown', ['Confirmed cases', 'Cases per 100,000 inhabitants',\
            'Deaths in the day', 'Cases in the day'])
temp_data = dataset.query('semEpid == @semanaEpidem')[["muni", "uf", "popEstim", "semEpid", "confAcc", "confAcc100k",\
            "obitoAcc", "obitoDia", "confDia"]].dropna(how="any")
if select == 'Confirmed cases':
    option = 'confAcc'
    selected_case = (temp_data.query("confAcc >= 1")[["muni", "uf", "confAcc", "semEpid",\
            "popEstim"]].sort_values(by=['confAcc'], ascending=False).dropna(how="any")[:num_muni])
    selected_case["popEstim"] = selected_case["popEstim"].astype(int)
    selected_case.rename(columns={'muni':'Cidade', 'uf':'UF', 'confAcc':'Confirmados acum',\
            'semEpid':'Semana', 'popEstim':'População'}, inplace=True)
elif select == 'Cases per 100,000 inhabitants':
    option = 'confAcc100k'
    selected_case = (temp_data.query("confAcc100k >= 1")[["muni", "uf", "confAcc100k", "semEpid",\
            "popEstim"]].sort_values(by=['confAcc100k'], ascending=False).dropna(how="any")[:num_muni])
    selected_case['confAcc100k'] = selected_case['confAcc100k'].astype(int)
    selected_case["popEstim"] = selected_case["popEstim"].astype(int)
    selected_case.rename(columns={'muni':'Cidade', 'uf':'UF', 'confAcc100k':'Conf.x 100k', 'semEpid':'Semana',\
            'popEstim':'População'}, inplace=True)
elif select == 'Deaths in the day': 
    option = "obitoDia"
    selected_case = (temp_data.query("obitoAcc >= 0")[["muni", "uf", "obitoDia", "obitoAcc", "semEpid",\
            "popEstim"]].sort_values(by=['obitoAcc'], ascending=False).dropna(how="any")[:num_muni])
    selected_case["popEstim"] = selected_case["popEstim"].astype(int)
    selected_case.rename(columns={'muni':'Cidade', 'uf':'UF', 'obitoDia':'Óbitos no dia', 'obitoAcc': 'Óbitos Acumulados', \
            'semEpid':'Semana', 'popEstim':'População'}, inplace=True)
else:
    option = 'confDia'
    selected_case = (temp_data.query("confAcc >= 0")[["muni", "uf", "confDia", "confAcc", "semEpid",\
            "popEstim"]].sort_values(by=['confAcc'], ascending=False).dropna(how="any")[:num_muni])
    selected_case["popEstim"] = selected_case["popEstim"].astype(int)
    selected_case.rename(columns={'muni':'Cidade', 'uf':'UF', 'confDia':'Casos no Dia', 'semEpid':'Semana',\
            'popEstim':'População'}, inplace=True)


selected_case.index = np.arange(1, len(selected_case) + 1)

st.write(selected_case)
# Case history of the above options in all available weeks with selection of cities presented
st.header(f"Evolution of {select} in cities")
st.subheader("Cases x Epidemiological week")
for city_count in range ((selected_case.shape[0])):
    city_name = str(selected_case.iloc[city_count,0])
    hist_data = dataset.query('muni == @city_name')[['semEpid', option]]
    hist_data.drop_duplicates(subset=['semEpid'], inplace=True)
    hist_data = hist_data.set_index('semEpid')
    hist_data.rename(columns={option:city_name}, inplace=True)
    if city_count == 0: plot_data = hist_data
    else: plot_data = pd.concat([plot_data,hist_data], axis=1)
chart_data = pd.DataFrame(plot_data)
st.line_chart(chart_data)
st.subheader(" ")
st.subheader("A Web App by [Lucas Schimidt](https://linkedin.com/in/lucasschimidtc)")
