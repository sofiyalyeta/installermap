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

st.title("Installer Map Dashboard")
st.write("Upload your installer data file and enter your Mapbox API key to visualize installer locations.")

# Sidebar for inputs
with st.sidebar:
    st.header("Configuration")
    
    
    # File uploads
    st.subheader("Installer Location File Upload")
    installer_file = st.file_uploader("Upload Installer Location File", type=["xlsx", "xls"])

    
    # Proximity search
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
    # Define your manual status-to-color mapping
    status_colors = {
        'Known': "#04BBFE",             
        'Very Certain': '#6ece58',       
        'High Certainty': "#34ae73",     
        'Moderate Certainty': "#2b8b98", 
        'Low Certainty': "#2e5f82",      
        'Very Low Certainty': "#323B6A", 
        'Uncertain': "#3E2367",          
        'Highly Uncertain': "#2E0139",   
        'Unknown': '#000000'             
    }
    # Load data
    df = pd.read_excel(installer_file)
    # Map the colors to your DataFrame
    df['Color'] = df['Status'].map(status_colors)

    unique_statuses = sorted(df['Status'].dropna().unique())
    selected_statuses = st.sidebar.multiselect("Filter by Status", unique_statuses, default=unique_statuses)

    with st.spinner("Processing data..."):
        df['Status'] = df['Status'].astype(str).str.strip().str.title()
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
        color = row['Color'] if pd.notna(row['Color']) else '#808080'

        popup_html = f"""
        <div style="font-size: 12px; padding: 5px; width: 150px; background-color: {color}; color: white;">
            <b>Installer:</b> {row['Installer Name']}<br>
            <b>Company:</b> {row['Company']}<br>
            <b>Status:</b> {row['Status']}<br>
            <b>Uncertainty Radius:</b> {row['Miles Offset (Uncertainty)']} miles<br>
            <b>Est. SO's:</b> {row['Estimated Service Orders (Uncertainty)']}<br>
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

    legend_html = """
    <div style="position: fixed; 
        bottom: 50px; left: 50px; width: 250px; height: auto; 
        background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
        padding: 10px;">
        <b>Status Legend</b><br>
        <i style="background: #04BBFE; width: 10px; height: 10px; float: left; margin-right: 5px;"></i> Known<br>
        <i style="background: #6ece58; width: 10px; height: 10px; float: left; margin-right: 5px;"></i> Very Certain<br>
        <i style="background: #34ae73; width: 10px; height: 10px; float: left; margin-right: 5px;"></i> High Certainty<br>
        <i style="background: #2b8b98; width: 10px; height: 10px; float: left; margin-right: 5px;"></i> Moderate Certainty<br>
        <i style="background: #2e5f82; width: 10px; height: 10px; float: left; margin-right: 5px;"></i> Low Certainty<br>
        <i style="background: #323B6A; width: 10px; height: 10px; float: left; margin-right: 5px;"></i> Very Low Certainty<br>
        <i style="background: #3E2367; width: 10px; height: 10px; float: left; margin-right: 5px;"></i> Uncertain<br>
        <i style="background: #2E0139; width: 10px; height: 10px; float: left; margin-right: 5px;"></i> Highly Uncertain<br>
        <i style="background: #000000; width: 10px; height: 10px; float: left; margin-right: 5px;"></i> Unknown<br>
    </div>
    """
    if not display_df.empty:
        m.get_root().html.add_child(folium.Element(legend_html))

    folium_static(m, width=1200, height=600)
    st.markdown(f"**Displaying {len(display_df)} installer(s)**")

else:
    st.info("Please upload all required files and enter your Mapbox API key to generate the map.")
