import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import requests
from geopy.distance import geodesic
from math import radians, sin, cos, sqrt, atan2
from folium.plugins import BeautifyIcon


st.set_page_config(page_title="Installer Map", layout="wide")
custom_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Open+Sans&display=swap');

        body {
            font-family: 'Arial', 'Open Sans', sans-serif;
        }

        .custom-markdown {
            font-size: 20px;
            line-height: 1.3;
            max-width: 800px;
            width: 100%;
        }
        
        .custom-text-area {
            font-family: 'Arial', 'Open Sans', sans-serif;
            font-size: 20;
            line-height: 1.3;
            padding: 10px;
            width: 100%;
            box-sizing: border-box;
            white-space: pre-wrap;
        }
        .largish-font {
            font-size: 20px;
            font-weight: bold;
        } 

        .large-font {
            font-size: 24px;
            font-weight: bold;
        }
        
        
        .larger-font {
            font-size: 30px;
            font-weight: bold;
        }
        
        .largest-font {
            font-size: 38px;
            font-weight: bold;
        }
        
        .title {
            font-family: 'Arial', 'Open Sans', sans-serif;
            font-size: 56px;
            font-weight: bold;

        }
        .custom-text-area ul {
            margin-left: 1.2em;
            padding-left: 0;
            line-height: .95; 
        }

        .custom-text-area li {
            margin-bottom: 0.4em;
        }      
    </style>
"""

st.markdown(custom_css, unsafe_allow_html=True)


#add the Michelin banner to the top of the application, if the image link breaks you can correct this by copying and
#pasting an alternative image url in the ()
st.markdown(
    """
    <div style='text-align: center;'>
        <img src='https://www.tdtyres.com/wp-content/uploads/2018/12/kisspng-car-michelin-man-tire-logo-michelin-logo-5b4c286206fa03.5353854915317177300286.png' width='1000'/>
    </div>
    """,
    unsafe_allow_html=True
)

#set the application title to 'Installer Map'
st.markdown('<div class="custom-text-area title">{}</div>'.format('Installer Map'), unsafe_allow_html=True)

st.markdown('''<div class="custom-text-area">This tool visualizes <strong>third-party installer locations</strong> across Canada and the United States, enabling <strong>proximity-based searches</strong> to identify nearby installation partners and <strong>streamline assignment processes</strong>. Installer locations are a mix of <strong>known and approximated locations</strong>. Please consider estimated location accuracy when making assignments. The map is designed to support the ongoing <strong>management, maintenance, and optimization of the installer network</strong>. </br> </div>
''', unsafe_allow_html=True)


# Sidebar for inputs
with st.sidebar:
    st.header("Configurator")
    
    
    # File uploads
    st.subheader("Installer Location File Upload")
    installer_file = st.file_uploader("Upload Installer Location File", type=["xlsx", "xls"])

    if installer_file:
        legend_html = """
        <div style="margin-top: 20px; padding: 10px; background-color: #f9f9f9; border: 1px solid #ccc; width: 300px;">
            <strong>Status Legend</strong><br>
            <div style="margin-top: 5px;">
                <div><span style="display:inline-block;width:12px;height:12px;background:#04BBFE;margin-right:5px;"></span>Known</div>
                <div><span style="display:inline-block;width:12px;height:12px;background:#6ece58;margin-right:5px;"></span>Very Certain</div>
                <div><span style="display:inline-block;width:12px;height:12px;background:#34ae73;margin-right:5px;"></span>High Certainty</div>
                <div><span style="display:inline-block;width:12px;height:12px;background:#2b8b98;margin-right:5px;"></span>Moderate Certainty</div>
                <div><span style="display:inline-block;width:12px;height:12px;background:#2e5f82;margin-right:5px;"></span>Low Certainty</div>
                <div><span style="display:inline-block;width:12px;height:12px;background:#283B9B;margin-right:5px;"></span>Very Low Certainty</div>
                <div><span style="display:inline-block;width:12px;height:12px;background:#502493;margin-right:5px;"></span>Uncertain</div>
                <div><span style="display:inline-block;width:12px;height:12px;background:#000000;margin-right:5px;"></span>Highly Uncertain</div>
                <div><span style="display:inline-block;width:12px;height:12px;background:#FFFFFF;border:1px solid black;margin-right:5px;"></span>Unknown/No Confidence</div>
            </div>
        </div>
        """
        st.markdown(legend_html, unsafe_allow_html=True)
        #Load data
        df = pd.read_excel(installer_file)

        for idx, row in df.iterrows():
            if row['Miles Offset (Uncertainty)'] == 0 and pd.isna(row['Estimated Service Orders (Uncertainty)']):
                df.loc[idx, 'Status'] = 'Known'
            elif row['Miles Offset (Uncertainty)'] < 100 and row['Estimated Service Orders (Uncertainty)'] >= 5:
                df.loc[idx, 'Status'] = 'Very Certain'
            elif row['Miles Offset (Uncertainty)'] < 100 and row['Estimated Service Orders (Uncertainty)'] < 5:
                df.loc[idx, 'Status'] = 'High Certainty'
            elif row['Miles Offset (Uncertainty)'] < 200 and row['Estimated Service Orders (Uncertainty)'] >= 5:
                df.loc[idx, 'Status'] = 'Moderate Certainty'
            elif row['Miles Offset (Uncertainty)'] < 200 and row['Estimated Service Orders (Uncertainty)'] < 5:
                df.loc[idx, 'Status'] = 'Low Certainty'
            elif row['Miles Offset (Uncertainty)'] < 300 and row['Estimated Service Orders (Uncertainty)'] >= 5:
                df.loc[idx, 'Status'] = 'Very Low Certainty'
            elif row['Miles Offset (Uncertainty)'] < 300 and row['Estimated Service Orders (Uncertainty)'] < 5:
                df.loc[idx, 'Status'] = 'Uncertain'
            elif row['Miles Offset (Uncertainty)'] < 500 and row['Estimated Service Orders (Uncertainty)'] >= 5:
                df.loc[idx, 'Status'] = 'Highly Uncertain'
            else:
                df.loc[idx, 'Status'] = 'Unknown/No Confidence'

        # Define your manual status-to-color mapping
        status_colors = {
            'Known': "#04BBFE",             
            'Very Certain': '#6ece58',       
            'High Certainty': "#34ae73",     
            'Moderate Certainty': "#2b8b98", 
            'Low Certainty': "#2e5f82",      
            'Very Low Certainty': "#283B9B", 
            'Uncertain': "#502493",          
            'Highly Uncertain': "#000000",   
            'Unknown/No Confidence': ''             
        }
        # Map the colors to your DataFrame
        df['Color'] = df['Status'].map(status_colors)

        # Define custom order
        custom_status_order = [
            'Known',    
            'Very Certain',   
            'High Certainty',
            'Moderate Certainty',
            'Low Certainty',
            'Very Low Certainty',
            'Uncertain',
            'Highly Uncertain',
            'Unknown/No Confidence'
        ]

        # Get only statuses that exist in the uploaded file and are in the custom order
        available_statuses = [status for status in custom_status_order if status in df['Status'].unique()]

        selected_statuses = st.sidebar.multiselect("Filter by Status", available_statuses, default=available_statuses)




    
    #proximity search
    st.subheader("Proximity Search")
    enable_proximity = st.checkbox("Enable proximity search")
    if enable_proximity:
        mapbox_access_token = st.text_input("Enter your Mapbox API key", type="password")
        user_zip = st.text_input("Enter ZIP code to search around")
        search_radius = st.slider("Search radius (miles)", 5, 100, 25)
    
# Function to geocode using Mapbox
def geocode_mapbox(zipcode, access_token):
    if not access_token:
        st.error("Please enter a Mapbox API key")
        return {"latitude": None, "longitude": None}
        
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{zipcode}.json"
    params = {
        "access_token": access_token,
        "types": "postcode",
        "country": "US"
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data["features"]:
                coordinates = data["features"][0]["center"]
                return {"latitude": coordinates[1], "longitude": coordinates[0]}
    except Exception as e:
        st.error(f"Error geocoding: {e}")
        print('Please ensure your zip code is valid')
    return {"latitude": None, "longitude": None}

# Haversine distance between two lat/lon points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)

    a = sin(dphi / 2)**2 + cos(phi1) * cos(phi2) * sin(dlambda / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c  # in meters


# Process data if files are uploaded
if installer_file:



    with st.spinner("Processing data..."):
        df['Status'] = df['Status']
        df['Color'] = df['Status'].map(status_colors)
        df = df[df['Status'].isin(selected_statuses)]

        m = folium.Map(location=[37.8, -96], zoom_start=4)
        cluster = MarkerCluster().add_to(m)

        if enable_proximity and user_zip and mapbox_access_token:
            # ➤ Geocode search ZIP
            search_result = geocode_mapbox(user_zip, mapbox_access_token)
            if search_result['latitude'] and search_result['longitude']:
                search_center = (search_result['latitude'], search_result['longitude'])
                search_radius_m = search_radius * 1609.34  # convert to meters

                # ➤ Add center marker & radius
                folium.Marker(
                    location=search_center,
                    popup=f"Search center: {user_zip}",
                    icon=folium.Icon(color='purple', icon='search', prefix='fa')
                ).add_to(m)

                folium.Circle(
                    location=search_center,
                    radius=search_radius_m,
                    color='purple',
                    fill=True,
                    fill_opacity=0.2
                ).add_to(m)

                # ➤ Filter rows based on uncertainty overlap
                filtered_df = []
                for _, row in df.iterrows():
                    coords = eval(row['Coordinates']) if isinstance(row['Coordinates'], str) else row['Coordinates']
                    lat, lon = coords
                    uncertainty_m = row['Miles Offset (Uncertainty)'] * 1609.34
                    dist = haversine(lat, lon, *search_center)
                    if dist <= search_radius_m + uncertainty_m:
                        filtered_df.append(row)

                display_df = pd.DataFrame(filtered_df)
            else:
                st.warning("Unable to geocode ZIP. Showing all data.")
                display_df = df

        else:
            # ➤ Show all if proximity is off
            display_df = df


    for _, row in display_df.iterrows():
        coords = eval(row['Coordinates']) if isinstance(row['Coordinates'], str) else row['Coordinates']
        lat, lon = coords
        color = row['Color']
        text_color = 'white' if row['Status'] != 'Unknown/No Confidence' else 'black'


        popup_html = f"""
        <div style="font-size: 12px; padding: 5px; width: 150px; background-color: {color}; color: {text_color};">
            <b>Installer:</b> {row['Installer Name']}<br>
            <b>Company:</b> {row['Company']}<br>
            <b>Status:</b> {row['Status']}<br>
            <b>Uncertainty Radius:</b> {row['Miles Offset (Uncertainty)']} miles<br>
            <b>Est. SO's:</b> {row['Estimated Service Orders (Uncertainty)'] if pd.notna(row['Estimated Service Orders (Uncertainty)']) else 'N/A'}<br>
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            icon=BeautifyIcon(
                icon='wrench',
                icon_shape='marker',
                background_color=color,
                border_color=color,
                icon_color='white'
            )
        ).add_to(cluster)

    



    folium_static(m, width=1200, height=600)
    st.markdown(f"**Displaying {len(display_df)} installer(s)**")


else:
    st.info("Please read the user instructions to begin.")





#document how to use the VIN decoder application to the user
st.markdown('<div class="custom-text-area largest-font">{}</div>'.format('User Guide'), unsafe_allow_html=True)
st.markdown('''<div class="custom-text-area">This guide outlines the <strong>methodology</strong> used to <strong>estimate installer locations</strong>, explains the significance of location <strong>status classifications</strong>, provides instructions for <strong>using the map to support case assignments</strong>, and details the protocol for <strong>maintaining and updating map data</strong>.</div>''', unsafe_allow_html=True)

st.markdown('<div class="custom-text-area larger-font">{}</div>'.format('Preserving Customer-Installer Relationships'), unsafe_allow_html=True)

st.markdown('''<div class="custom-text-area">Preserving existing customer-installer relationships is a top priority to <strong>ensure a seamless customer experience</strong> and to keep the customer at the forefront of our operations. Before assigning an installer to a customer, it is essential to reference the <a href="https://michelingroup.sharepoint.com/:x:/s/DeploymentOperations/EeaFW6h5yMdJnmT-8SPOaY4BGFmKU0p9gpkgBxkf5RgsWg?e=U053jP" target="_blank" style="color: #1a73e8; text-decoration: underline;">Customer Requested Installers Document</a> to confirm whether the customer already has an <strong>established installation partner</strong>.<br> 
Assigning an incorrect installer may result in <strong>additional costs</strong>, as we will be responsible for the cost of dispatching the correct installer. </br>
<strong>This document must be reviewed prior to assigning an installer or using the map for installer selection.</strong></div>''', unsafe_allow_html=True)


st.markdown('<div class="custom-text-area larger-font">{}</div>'.format('Understanding the "Status" Classification'), unsafe_allow_html=True)
st.markdown('''<div class="custom-text-area">The <strong>"Status" classification</strong> indicates whether an <strong>installer location</strong> is <strong>known</strong> or <strong>estimated</strong> and provides a <strong>ranked, categorical assessment</strong> of the certainty associated with each location. It is recommended to use the <strong>more certain installer locations</strong> when possible.</div>''', unsafe_allow_html=True)


st.markdown('<div class="custom-text-area large-font">{}</div>'.format('Miles Offset'), unsafe_allow_html=True)


st.markdown('''<div class="custom-text-area"><strong>Miles Offset</strong> is an estimate of how far an installer typically travels from their central work area to complete service orders. It is calculated by analyzing groups of service order locations (called <strong>clusters</strong>) where an installer or their company frequently operates. The average travel distance within each cluster is used to represent the <strong>installer’s usual service radius</strong>.
<ul>
  <li>A <strong>low Miles Offset</strong> indicates the installer operates within a <strong>small, concentrated area</strong>, which suggests a <strong>high level of confidence</strong> in the estimated installer location.
  <li>A <strong>higher Miles Offset</strong> suggests the installer covers a <strong>broader region</strong>, and the estimated location carries a greater <strong>degree of uncertainty</strong>. </ul>
This value helps indicate how precise the estimated installer location is. If a company only <strong>operates in one town</strong>, the offset might be <strong>very small</strong> (close to 0 or 0). If the installer travels across a <strong>large region</strong>, the offset will be <strong>higher</strong>.
</div>''', unsafe_allow_html=True)



st.markdown('<div class="custom-text-area large-font">{}</div>'.format('Service Orders'), unsafe_allow_html=True)
st.markdown('''<div class="custom-text-area"><strong>Estimated Service Orders</strong> represents the <strong>number of service orders</strong> used to <strong>calculate</strong> the installer’s <strong>estimated location</strong>. A <strong>higher number</strong> of service orders means more data was available to determine the <strong>installer’s typical coverage area</strong>. This generally <strong>increases confidence</strong> that the identified area is truly covered by the installer.<br>
However, this value should be considered alongside <strong>Miles Offset</strong>:
<ul>
  <li>If many service orders are <strong>tightly clustered</strong>, the estimated location is likely <strong>accurate</strong>.
  <li>If many service orders are spread over a <strong>large area</strong>, the location may be <strong>less precise</strong> despite the high count.</ul>
<strong>Estimated Service Orders</strong> is a helpful indicator of <strong>historical service order volume</strong>, but <strong>Miles Offset</strong> is the <strong>primary measure</strong> of estimated installer location accuracy.
</div>''', unsafe_allow_html=True)

st.markdown('<div class="custom-text-area large-font">{}</div>'.format('Status Field'), unsafe_allow_html=True)
st.markdown('''
<div class="custom-text-area">The <strong>Status</strong> field for each installer location is determined based on two key inputs:<br>
    1. <strong>Miles Offset</strong> – How far the actual location may be from the estimated location (in miles).<br>
    2. <strong>Estimated Service Orders</strong> – How many service orders were used to estimate the installer's location.<br><br>''', unsafe_allow_html=True)

st.markdown('<div class="custom-text-area largish-font">{}</div>'.format('Status Categories'), unsafe_allow_html=True)
st.markdown('''
<div class="custom-text-area"><ul><li><strong>Known</strong> – This installer location was provided by our installation partners and is confirmed to be accurate.
  <li><strong>Very Certain</strong> – Miles Offset is less than 100 miles and 5 or more Service Orders were used to estimate.                   
  <li><strong>High Certainty</strong> – Miles Offset is less than 100 miles and fewer than 5 Service Orders were used to estimate.    
  <li><strong>Moderate Certainty</strong> –  Miles Offset is less than 200 miles and 5 or more Service Orders were used to estimate.         
  <li><strong>Low Certainty</strong> – Miles Offset is less than 200 miles and fewer than 5 Service Orders were used to estimate.               
  <li><strong>Very Low Certainty</strong> – Miles Offset is less than 300 miles and 5 or more Service Orders were used to estimate.
  <li><strong>Uncertain</strong> – Miles Offset is less than 300 miles and fewer than 5 Service Orders were used to estimate.                    
  <li><strong>Highly Uncertain</strong> – Miles Offset is less than 500 miles and 5 or more Service Orders were used to estimate.
  <li><strong>Unknown/No Confidence</strong> – Either the Miles Offset is 500 miles or more, or fewer than 5 Service Orders were used with a large offset.</ul>

<strong>Note:</strong> Statuses such as <strong>Known, Very Certain, High Certainty</strong>, and <strong>Moderate Certainty</strong> should be treated as <strong>trusted data inputs</strong>. All other statuses should be used only if trusted installer locations are <strong>not available</strong>.</div>''', unsafe_allow_html=True)


st.markdown('<div class="custom-text-area larger-font">{}</div>'.format('Using the Map'), unsafe_allow_html=True)



st.markdown('''<div class="custom-text-area">This map can be used to <strong>assign installers</strong> to specific cases or support broader <strong>network planning </strong>and <strong>maintenance</strong>.</div>''', unsafe_allow_html=True) 



st.markdown('<div class="custom-text-area large-font">{}</div>'.format('File Upload'), unsafe_allow_html=True)
st.markdown('''<div class="custom-text-area">To use the map, upload the <a href="https://michelingroup.sharepoint.com/:x:/s/DeploymentOperations/EVBHAJoeXqBMjhPxQ1jCkLwByuZjADXS0d75lczfr8F0zA?e=cZNZuU" target="_blank" style="color: #1a73e8; text-decoration: underline;">Final Installer Locations for Map Document</a> into the file upload box located in the <strong>Configurator</strong> section of the page. 
Once the file is uploaded, a <strong>legend</strong> will appear, indicating the <strong>status</strong> of each installer location. Use the <strong>"Filter by Status"</strong> selection tool to view only installers that meet your confidence levels of interest. This status selection tool is ordered from <strong> most confident</strong> to <strong> least confident</strong> confidence level.</div>''', unsafe_allow_html=True)


st.markdown('<div class="custom-text-area large-font">{}</div>'.format('Visualizing the Network'), unsafe_allow_html=True)
st.markdown('''<div class="custom-text-area">Once the file has been uploaded, a map of the installation network will appear. The initial view displays a <strong>regional overview of North America</strong>, with installer locations <strong>clustered by geographic area</strong>. </br>
By default, <strong>all installers</strong> are shown and <strong>grouped into regional clusters</strong>. <strong>Hover</strong> over a cluster to see its <strong>general coverage area</strong>. <strong>Click on a cluster</strong> or <strong>zoom</strong> into the map to explore a more <strong>granular view</strong> of installer locations. <strong>Continue</strong> zooming or clicking until you reach your <strong>desired level of detail</strong>. </br>
As you apply or remove <strong>filters</strong>, the number of installers shown will <strong>dynamically adjust</strong> based on your selection criteria. This interactive map helps users efficiently <strong>navigate the installer network</strong> and <strong>identify resources</strong> across different regions.''', unsafe_allow_html=True)


st.markdown('<div class="custom-text-area large-font">{}</div>'.format('Proximity Search'), unsafe_allow_html=True)
st.markdown('''<div class="custom-text-area">If you’d like to search for nearby installers to support assignment decisions, enable the Proximity Search feature by selecting the checkbox. You will then be prompted to:
    1. Enter your <strong>Mapbox API key</strong> </br>
    2. Input the <strong>Zip Code</strong> of the installation location</br>
    3. Select a <strong>search radius</strong> (0–100 miles)</br>
This will <strong>filter and display installers within the specified distance</strong> who are in-network and eligible to perform the installation.</br>

Some installer locations may appear slightly outside the selected radius on the map. This is expected and occurs when their <strong>uncertainty range falls within the chosen radius</strong>.</br>
To use the proximity search feature, a <strong>valid Mapbox API key</strong> is required. If you do not currently have access, please <strong>contact the Field Services Deployment Manager</strong> to determine eligibility and obtain the necessary credentials.</div>''', unsafe_allow_html=True)

            

st.markdown('<div class="custom-text-area larger-font">{}</div>'.format('Updating Installer Locations'), unsafe_allow_html=True)
st.markdown('''<div class="custom-text-area">Installer location data should be reviewed and updated on a <strong>quarterly basis</strong>. At the end of each quarter, the <strong>Deployment Team</strong> is responsible for reaching out to installation partners to request updated installer addresses or ZIP codes.</br>
To maintain installer anonymity, <strong>Zip Codes</strong> are <strong>sufficient</strong>. If an installation partner is unwilling to share installer location information, this is acceptable; however, it’s important to note that such partners will be <strong>de-prioritized</strong> by the map, as the tool gives preference to known installer locations.</br>
For this reason, it is critical that all partners are given a clear <strong>opportunity to provide ZIP code-level location data</strong>.</br>
As the Deployment Team receives new or updated addresses, they should promptly forward this information to the <strong>Transformation Team</strong> via email, who will update the source documentation that informs the map. Any additional <strong>service requests</strong> should be sent to the <strong>Transformation Team</strong>.</div>''', unsafe_allow_html=True)         



















