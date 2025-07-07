# import streamlit as st
# import pandas as pd
# import folium
# from folium.plugins import MarkerCluster
# from geopy.distance import geodesic
# import requests
# from streamlit_folium import st_folium

# # Set page title
# st.title("Installer Map Dashboard")

# # Sidebar for file uploads and settings
# st.sidebar.header("Upload Data Files")

# orbital_file = st.sidebar.file_uploader("Upload Orbital Employee List", type=["xlsx"])
# drig_file = st.sidebar.file_uploader("Upload DRIG Installer List", type=["xlsx"])
# cb_direct_file = st.sidebar.file_uploader("Upload CB Direct Tech Information", type=["xlsx", "csv"])
# training_file = st.sidebar.file_uploader("Upload Training Data", type=["xlsx"])
# costs_file = st.sidebar.file_uploader("Upload Costs by Installer", type=["xlsx"])

# # Mapbox API key input
# mapbox_api_key = st.sidebar.text_input("Enter Mapbox API Key", type="password")

# # Function to get coordinates from ZIP code using Mapbox API
# def get_coordinates_from_zip(zipcode, api_key):
#     if not zipcode or not api_key:
#         return None, None
    
#     zipcode = str(int(zipcode))  # Convert to string and remove leading zeros
#     url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{zipcode}.json?country=us&types=postcode&access_token={api_key}"
    
#     try:
#         response = requests.get(url)
#         data = response.json()
        
#         if 'features' in data and len(data['features']) > 0:
#             coordinates = data['features'][0]['center']
#             return coordinates[1], coordinates[0]  # Mapbox returns [lng, lat], we want [lat, lng]
#         else:
#             return None, None
#     except Exception as e:
#         st.error(f"Error fetching coordinates for ZIP {zipcode}: {e}")
#         return None, None

# # Function to check if a ZIP code is valid (5 digits)
# def is_valid_zip(zip_code):
#     if pd.isna(zip_code):
#         return False
#     try:
#         return len(str(int(zip_code))) == 5
#     except:
#         return False

# # Function to extract zipcode from address
# def extract_zipcode(address):
#     if not isinstance(address, str):
#         return None

#     parts = address.split()  
#     zip_candidate = None

#     for part in reversed(parts):  # approach backwards - zipcode is at the end
#         if len(part) == 5 and part.isdigit():
#             zip_candidate = part
#             break  # stop at first

#     return zip_candidate

# # Main processing function
# def process_data():
#     # Process Orbital data
#     if orbital_file is not None:
#         orbital = pd.read_excel(orbital_file)
        
#         # Convert ZIP to numeric and clean
#         orbital['ZIP'] = pd.to_numeric(orbital['ZIP'], errors='coerce').fillna(0).astype(int)
        
#         # Separate valid and invalid rows
#         valid_mask = orbital['ZIP'].apply(is_valid_zip)
#         problem_rows = orbital[~valid_mask].copy()
#         orbital = orbital[valid_mask].copy()
        
#         orbital.reset_index(drop=True, inplace=True)
        
#         # Add coordinates using Mapbox
#         orbital['latitude'] = None
#         orbital['longitude'] = None
        
#         for idx, row in orbital.iterrows():
#             lat, lng = get_coordinates_from_zip(row['ZIP'], mapbox_api_key)
#             orbital.at[idx, 'latitude'] = lat
#             orbital.at[idx, 'longitude'] = lng
        
#         orbital = orbital.dropna(subset=['latitude', 'longitude'])
#         orbital['NAME'] = orbital['NAME'].str.title()
        
#         st.success(f"Processed {len(orbital)} Orbital employees")
#     else:
#         orbital = pd.DataFrame()
    
#     # Process DRIG data
#     if drig_file is not None:
#         drig = pd.read_excel(drig_file)
        
#         drig['ZIP'] = drig['Address'].apply(extract_zipcode)
#         drig = drig.dropna(subset=['ZIP'])
        
#         # Add coordinates using Mapbox
#         drig['latitude'] = None
#         drig['longitude'] = None
        
#         for idx, row in drig.iterrows():
#             lat, lng = get_coordinates_from_zip(row['ZIP'], mapbox_api_key)
#             drig.at[idx, 'latitude'] = lat
#             drig.at[idx, 'longitude'] = lng
        
#         drig = drig.dropna(subset=['latitude', 'longitude'])
#         drig = drig.rename(columns={'Name': 'NAME'})
        
#         st.success(f"Processed {len(drig)} DRIG installers")
#     else:
#         drig = pd.DataFrame()
    
#     # Process CB Direct data
#     if cb_direct_file is not None:
#         if cb_direct_file.name.endswith('.csv'):
#             cb_direct = pd.read_csv(cb_direct_file)
#         else:
#             cb_direct = pd.read_excel(cb_direct_file)
        
#         cb_direct['NAME'] = cb_direct['NAME'].str.replace(' CB Direct', '', case=False)
#         cb_direct.rename(columns={'ADDRESS': 'Address', 'EMAIL': 'Email'}, inplace=True)
        
#         st.success(f"Processed {len(cb_direct)} CB Direct technicians")
#     else:
#         cb_direct = pd.DataFrame()
    
#     # Process Training data
#     if training_file is not None:
#         # Extract sheet name from file name
#         file_name = training_file.name
#         if '_' in file_name:
#             sheet_name = file_name.split('_')[-1].split('.')[0]
#             sheet_name = "".join(sheet_name.split("_"))
#         else:
#             sheet_name = None
        
#         training = pd.read_excel(training_file, sheet_name=sheet_name)
        
#         # Filter for completed status and select relevant columns
#         filtered_training = training[training['Status'] == 'Complete'][['full name', 'course']]
        
#         # Group by name, aggregate colleges into lists, and reset index
#         result_training = filtered_training.groupby('full name')['course'].agg(list).reset_index()
#         result_training.rename(columns={'full name': 'NAME'}, inplace=True)
        
#         st.success(f"Processed training data for {len(result_training)} individuals")
#     else:
#         result_training = pd.DataFrame(columns=['NAME', 'course'])
    
#     # Process Costs data
#     if costs_file is not None:
#         costs_by_installer = pd.read_excel(costs_file)
#         st.success(f"Processed costs data for {len(costs_by_installer)} installers")
#     else:
#         costs_by_installer = pd.DataFrame()
    
#     # Merge training data
#     if not orbital.empty and not result_training.empty:
#         orbital_a = pd.merge(orbital, result_training, on=['NAME'], how='left')
#     else:
#         orbital_a = orbital.copy()
#         if 'course' not in orbital_a.columns:
#             orbital_a['course'] = None
    
#     if not drig.empty and not result_training.empty:
#         drig_a = pd.merge(drig, result_training, on=['NAME'], how='left')
#     else:
#         drig_a = drig.copy()
#         if 'course' not in drig_a.columns:
#             drig_a['course'] = None
    
#     if not cb_direct.empty and not result_training.empty:
#         cb_direct_a = pd.merge(cb_direct, result_training, on=['NAME'], how='left')
#     else:
#         cb_direct_a = cb_direct.copy()
#         if 'course' not in cb_direct_a.columns:
#             cb_direct_a['course'] = None
    
#     # Merge costs data
#     if not orbital_a.empty and not costs_by_installer.empty:
#         orbital_b = orbital_a.merge(costs_by_installer[['NAME', 'Installer Group', 'Average # of Devices Per Order', 'Average Service Cost', 'Average Travel Cost']], on='NAME', how='left')
#     else:
#         orbital_b = orbital_a.copy()
    
#     if not drig_a.empty and not costs_by_installer.empty:
#         drig_b = drig_a.merge(costs_by_installer[['NAME', 'Installer Group', 'Average # of Devices Per Order', 'Average Service Cost', 'Average Travel Cost']], on='NAME', how='left')
#     else:
#         drig_b = drig_a.copy()
    
#     if not cb_direct_a.empty and not costs_by_installer.empty:
#         cb_direct_b = cb_direct_a.merge(costs_by_installer[['NAME', 'Installer Group', 'Average # of Devices Per Order', 'Average Service Cost', 'Average Travel Cost']], on='NAME', how='left')
#     else:
#         cb_direct_b = cb_direct_a.copy()
    
#     return orbital_b, drig_b, cb_direct_b

# # Function to create map
# def create_map(orbital, drig, cb_direct, filter_by_zip=False, user_zip=None, radius=25):
#     # Create map
#     map_center = [35.7157, -117.1611]
#     zoom_start = 4.2
    
#     if filter_by_zip and user_zip and mapbox_api_key:
#         # Get coordinates for user zip
#         user_lat, user_lon = get_coordinates_from_zip(user_zip, mapbox_api_key)
#         if user_lat and user_lon:
#             map_center = [user_lat, user_lon]
#             zoom_start = 8
    
#     m = folium.Map(location=map_center, zoom_start=zoom_start)
#     cluster = MarkerCluster().add_to(m)
    
#     group_styles = {
#         'orbital': {'color': 'blue', 'icon': 'info-sign', 'label': 'orbital'},
#         'drig': {'color': 'green', 'icon': 'triangle', 'label': 'drig'},
#         'cb_direct': {'color': 'red', 'icon': 'diamond', 'label': 'cb_direct'}
#     }
    
#     # Add markers to map
#     for df_name, df in [('orbital', orbital), ('drig', drig), ('cb_direct', cb_direct)]:
#         if df.empty:
#             continue
            
#         group_style = group_styles[df_name]
        
#         for index, row in df.iterrows():
#             if pd.isna(row['latitude']) or pd.isna(row['longitude']):
#                 continue
                
#             # Filter by distance if needed
#             if filter_by_zip and user_zip and user_lat and user_lon:
#                 marker_location = (row['latitude'], row['longitude'])
#                 user_location = (user_lat, user_lon)
#                 try:
#                     distance = geodesic(user_location, marker_location).miles
#                     if distance > radius:
#                         continue
#                     distance_text = f" - {distance:.2f} miles away"
#                 except:
#                     distance_text = ""
#             else:
#                 distance_text = ""
            
#             # Create popup content
#             popup_content = f"Name: {row['NAME']}<br><br>ZIP: {row['ZIP']}"
            
#             # Add training info if available
#             if 'course' in row and row['course'] is not None:
#                 if isinstance(row['course'], list):
#                     courses = ", ".join(row['course'])
#                 else:
#                     courses = str(row['course'])
#                 popup_content += f"<br><br>Completed Training: {courses}"
            
#             # Add cost info if available
#             cost_fields = ['Average # of Devices Per Order', 'Average Service Cost', 'Average Travel Cost']
#             for field in cost_fields:
#                 if field in row and not pd.isna(row[field]):
#                     popup_content += f"<br><br>{field}: {row[field]}"
            
#             # Add distance if filtering by zip
#             popup_content += distance_text
            
#             # Create marker
#             folium.Marker(
#                 location=[row['latitude'], row['longitude']],
#                 popup=popup_content,
#                 icon=folium.Icon(color=group_style['color'], icon=group_style['icon'], prefix='fa')
#             ).add_to(cluster)
    
#     # Add legend
#     legend_html = """
#          <div style="position: fixed; 
#          bottom: 50px; left: 50px; width: 180px; height: 120px; 
#          border:2px solid grey; z-index:9999; font-size:14px;
#          background-color:white;
#          ">
#          &nbsp; <b>Legend</b> <br>
#          &nbsp; Orbital: <i class="fa fa-info-sign fa-2x" style="color:blue"></i><br>
#          &nbsp; Drig: <i class="fa fa-home fa-2x" style="color:green"></i><br>
#          &nbsp; CB_direct: <i class="fa fa-cloud fa-2x" style="color:red"></i><br>
#          </div>
#          """
    
#     m.get_root().html.add_child(folium.Element(legend_html))
    
#     return m

# # Main app logic
# if mapbox_api_key:
#     # Process data
#     orbital, drig, cb_direct = process_data()
    
#     # Map filtering options
#     st.sidebar.header("Map Options")
#     filter_by_zip = st.sidebar.checkbox("Filter by ZIP Code")
    
#     if filter_by_zip:
#         user_zip = st.sidebar.text_input("Enter ZIP Code")
#         radius = st.sidebar.slider("Radius (miles)", 5, 100, 25)
#     else:
#         user_zip = None
#         radius = 25
    
#     # Create and display map
#     if not orbital.empty or not drig.empty or not cb_direct.empty:
#         st.subheader("Installer Map")
#         m = create_map(orbital, drig, cb_direct, filter_by_zip, user_zip, radius)
#         st_folium(m, width=800, height=600)
        
#         # Display data tables
#         st.subheader("Data Tables")
#         tabs = st.tabs(["Orbital", "DRIG", "CB Direct"])
        
#         with tabs[0]:
#             if not orbital.empty:
#                 st.dataframe(orbital)
#             else:
#                 st.info("No Orbital data available")
        
#         with tabs[1]:
#             if not drig.empty:
#                 st.dataframe(drig)
#             else:
#                 st.info("No DRIG data available")
        
#         with tabs[2]:
#             if not cb_direct.empty:
#                 st.dataframe(cb_direct)
#             else:
#                 st.info("No CB Direct data available")
#     else:
#         st.info("Please upload data files to generate the map")
# else:
#     st.warning("Please enter a Mapbox API key in the sidebar to proceed")

# # Add instructions
# st.sidebar.markdown("---")
# st.sidebar.header("Instructions")
# st.sidebar.markdown("""
# 1. Enter your Mapbox API key
# 2. Upload the required data files
# 3. Use the filter options to customize the map view
# 4. Explore the map and data tables
# """)

# import streamlit as st
# import pandas as pd
# import folium
# from folium.plugins import MarkerCluster
# from streamlit_folium import folium_static
# import requests
# import io
# from geopy.distance import geodesic

# st.set_page_config(page_title="Installer Map", layout="wide")

# st.title("Installer Map Dashboard")
# st.write("Upload your installer data files and enter your Mapbox API key to visualize installer locations.")

# # Sidebar for inputs
# with st.sidebar:
#     st.header("Configuration")
    
#     # Mapbox API key input
#     mapbox_access_token = st.text_input("Enter your Mapbox API key", type="password")
    
#     # File uploads
#     st.subheader("Upload Data Files")
#     orbital_file = st.file_uploader("Upload Orbital employee list (Excel)", type=["xlsx", "xls"])
#     drig_file = st.file_uploader("Upload DRIG Installer List (Excel)", type=["xlsx", "xls"])
#     cb_direct_file = st.file_uploader("Upload CB Direct tech information (Excel)", type=["xlsx", "xls"])
#     training_file = st.file_uploader("Upload Training data (Excel)", type=["xlsx", "xls"])
#     costs_file = st.file_uploader("Upload Cost data (Excel)", type=["xlsx", "xls"])
    
#     # Proximity search
#     st.subheader("Proximity Search")
#     enable_proximity = st.checkbox("Enable proximity search")
#     if enable_proximity:
#         user_zip = st.text_input("Enter ZIP code to search around")
#         search_radius = st.slider("Search radius (miles)", 5, 100, 25)

# # Function to geocode using Mapbox
# def geocode_mapbox(zipcode, access_token):
#     if not access_token:
#         st.error("Please enter a Mapbox API key")
#         return {"latitude": None, "longitude": None}
        
#     url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{zipcode}.json"
#     params = {
#         "access_token": access_token,
#         "types": "postcode",
#         "country": "US"
#     }
#     try:
#         response = requests.get(url, params=params)
#         if response.status_code == 200:
#             data = response.json()
#             if data["features"]:
#                 coordinates = data["features"][0]["center"]
#                 return {"latitude": coordinates[1], "longitude": coordinates[0]}
#     except Exception as e:
#         st.error(f"Error geocoding: {e}")
#     return {"latitude": None, "longitude": None}

# # Function to check if a ZIP code is valid (5 digits)
# def is_valid_zip(zip_code):
#     try:
#         return len(str(int(zip_code))) == 5
#     except:
#         return False

# # Function to extract ZIP code from address
# def extract_zipcode(address):
#     if not isinstance(address, str):
#         return None

#     parts = address.split()  
#     zip_candidate = None

#     for part in reversed(parts):  # approach backwards - zipcode is at the end
#         if len(part) == 5 and part.isdigit():
#             zip_candidate = part
#             break  # stop at first

#     return zip_candidate

# # Process data if files are uploaded
# if orbital_file and drig_file and cb_direct_file and mapbox_access_token:
#     with st.spinner("Processing data..."):
#         # Load data
#         orbital = pd.read_excel(orbital_file)
#         drig = pd.read_excel(drig_file)
#         cb_direct = pd.read_excel(cb_direct_file)
        
#         # Process orbital data
#         orbital['ZIP'] = pd.to_numeric(orbital['ZIP'], errors='coerce').fillna(0).astype(int)
#         valid_mask = orbital['ZIP'].apply(is_valid_zip)
#         problem_rows = orbital[~valid_mask].copy()
#         orbital = orbital[valid_mask].copy()
        
#         # Process DRIG data
#         drig['ZIP'] = drig['Address'].apply(extract_zipcode)
#         drig = drig.dropna(subset=['ZIP'])
        
#         # Process CB Direct data
#         cb_direct = cb_direct[cb_direct['ADDRESS'].notna() & (cb_direct['ADDRESS'] != '') & cb_direct['ADDRESS'].str.contains(r'\d')]
#         cb_direct['ZIP'] = cb_direct['ADDRESS'].apply(extract_zipcode)
        
#         # Geocode all datasets
#         progress_bar = st.progress(0)
        
#         # Geocode orbital
#         results = []
#         for i, zipcode in enumerate(orbital['ZIP']):
#             results.append(geocode_mapbox(zipcode, mapbox_access_token))
#             progress_bar.progress((i + 1) / len(orbital))
        
#         orbital['latitude'] = [result['latitude'] for result in results]
#         orbital['longitude'] = [result['longitude'] for result in results]
#         orbital = orbital.dropna(subset=['latitude', 'longitude'])
        
#         # Geocode DRIG
#         results = []
#         for i, zipcode in enumerate(drig['ZIP']):
#             results.append(geocode_mapbox(zipcode, mapbox_access_token))
#             progress_bar.progress((i + 1) / len(drig))
            
#         drig['latitude'] = [result['latitude'] for result in results]
#         drig['longitude'] = [result['longitude'] for result in results]
#         drig = drig.dropna(subset=['latitude', 'longitude'])
#         drig = drig.rename(columns={'Name': 'NAME'})
        
#         # Geocode CB Direct
#         results = []
#         for i, zipcode in enumerate(cb_direct['ZIP']):
#             results.append(geocode_mapbox(zipcode, mapbox_access_token))
#             progress_bar.progress((i + 1) / len(cb_direct))
            
#         cb_direct['latitude'] = [result['latitude'] for result in results]
#         cb_direct['longitude'] = [result['longitude'] for result in results]
#         cb_direct = cb_direct.dropna(subset=['latitude', 'longitude'])
        
#         # Process training data if uploaded
#         if training_file:
#             training = pd.read_excel(training_file)
#             filtered_training = training[training['Status'] == 'Complete'][['full name', 'course']]
#             result_training = filtered_training.groupby('full name')['course'].agg(list).reset_index()
#             result_training.rename(columns={'full name': 'NAME'}, inplace=True)
            
#             # Merge training data
#             orbital = pd.merge(orbital, result_training, on=['NAME'], how='left')
#             drig = pd.merge(drig, result_training, on=['NAME'], how='left')
#             cb_direct = pd.merge(cb_direct, result_training, on=['NAME'], how='left')
        
#         # Process cost data if uploaded
#         if costs_file:
#             costs_by_installer = pd.read_excel(costs_file)
            
#             # Merge cost data
#             orbital = orbital.merge(costs_by_installer[['NAME', 'Installer Group', 'Average # of Devices Per Order', 'Average Service Cost', 'Average Travel Cost']], on='NAME', how='left')
#             drig = drig.merge(costs_by_installer[['NAME', 'Installer Group', 'Average # of Devices Per Order', 'Average Service Cost', 'Average Travel Cost']], on='NAME', how='left')
#             cb_direct = cb_direct.merge(costs_by_installer[['NAME', 'Installer Group', 'Average # of Devices Per Order', 'Average Service Cost', 'Average Travel Cost']], on='NAME', how='left')
        
#         progress_bar.empty()
        
#         # Create map
#         st.subheader("Installer Map")
        
#         # Create map with starting location and zoom level
#         map_center = [35.7157, -117.1611]
#         m = folium.Map(location=map_center, zoom_start=4.2)
#         cluster = MarkerCluster().add_to(m)
        
#         group_styles = {
#             'orbital': {'color': 'blue', 'icon': 'info-sign', 'label': 'Orbital'},
#             'drig': {'color': 'green', 'icon': 'triangle', 'label': 'DRIG'},
#             'cb_direct': {'color': 'red', 'icon': 'diamond', 'label': 'CB Direct'}
#         }
        
#         # Process proximity search if enabled
#         user_location = None
#         if enable_proximity and user_zip:
#             try:
#                 location_result = geocode_mapbox(user_zip, mapbox_access_token)
#                 if location_result['latitude'] and location_result['longitude']:
#                     user_location = (location_result['latitude'], location_result['longitude'])
#                     # Add marker for search location
#                     folium.Marker(
#                         location=user_location,
#                         popup=f"Search center: {user_zip}",
#                         icon=folium.Icon(color='purple', icon='search', prefix='fa')
#                     ).add_to(m)
                    
#                     # Add circle for search radius
#                     folium.Circle(
#                         location=user_location,
#                         radius=search_radius * 1609.34,  # Convert miles to meters
#                         color='purple',
#                         fill=True,
#                         fill_opacity=0.2
#                     ).add_to(m)
                    
#                     # Center map on search location
#                     m.location = user_location
#             except Exception as e:
#                 st.error(f"Error with proximity search: {e}")
        
#         # Add markers to map
#         for df_name, df in [('orbital', orbital), ('drig', drig), ('cb_direct', cb_direct)]:
#             group_style = group_styles[df_name]
            
#             for index, row in df.iterrows():
#                 # Skip if outside search radius when proximity search is enabled
#                 if user_location and enable_proximity:
#                     marker_location = (row['latitude'], row['longitude'])
#                     distance = geodesic(user_location, marker_location).miles
#                     if distance > search_radius:
#                         continue
#                     distance_text = f"<br>Distance: {distance:.2f} miles"
#                 else:
#                     distance_text = ""
                
#                 # Create popup content
#                 popup_content = f"<b>Name:</b> {row['NAME']}<br><b>ZIP:</b> {row['ZIP']}{distance_text}"
                
#                 # Add training info if available
#                 if 'course' in row and pd.notna(row['course']):
#                     courses = row['course']
#                     if isinstance(courses, list):
#                         popup_content += f"<br><b>Training:</b> {', '.join(courses)}"
                
#                 # Add cost info if available
#                 if 'Average # of Devices Per Order' in row and pd.notna(row['Average # of Devices Per Order']):
#                     popup_content += f"<br><b>Avg Devices:</b> {row['Average # of Devices Per Order']}"
#                 if 'Average Service Cost' in row and pd.notna(row['Average Service Cost']):
#                     popup_content += f"<br><b>Avg Service Cost:</b> ${row['Average Service Cost']:.2f}"
#                 if 'Average Travel Cost' in row and pd.notna(row['Average Travel Cost']):
#                     popup_content += f"<br><b>Avg Travel Cost:</b> ${row['Average Travel Cost']:.2f}"
                
#                 folium.Marker(
#                     location=[row['latitude'], row['longitude']],
#                     popup=folium.Popup(popup_content, max_width=300),
#                     icon=folium.Icon(color=group_style['color'], icon=group_style['icon'], prefix='fa')
#                 ).add_to(cluster)
        
#         # Add legend
#         legend_html = """
#         <div style="position: fixed; 
#         bottom: 50px; left: 50px; width: 180px; height: 120px; 
#         border:2px solid grey; z-index:9999; font-size:14px;
#         background-color:white; padding: 10px;
#         ">
#         <b>Legend</b><br>
#         <i class="fa fa-info-sign fa-lg" style="color:blue"></i> Orbital<br>
#         <i class="fa fa-triangle fa-lg" style="color:green"></i> DRIG<br>
#         <i class="fa fa-diamond fa-lg" style="color:red"></i> CB Direct<br>
#         """
        
#         if enable_proximity and user_location:
#             legend_html += f'<i class="fa fa-search fa-lg" style="color:purple"></i> Search Center ({user_zip})<br>'
        
#         legend_html += "</div>"
        
#         m.get_root().html.add_child(folium.Element(legend_html))
        
#         # Display map
#         folium_static(m, width=1200, height=600)
        
#         # Display data tables
#         col1, col2, col3 = st.columns(3)
        
#         with col1:
#             st.subheader("Orbital Data")
#             st.write(f"{len(orbital)} installers")
#             st.dataframe(orbital)
        
#         with col2:
#             st.subheader("DRIG Data")
#             st.write(f"{len(drig)} installers")
#             st.dataframe(drig)
        
#         with col3:
#             st.subheader("CB Direct Data")
#             st.write(f"{len(cb_direct)} installers")
#             st.dataframe(cb_direct)
        
#         # Display problem rows if any
#         if len(problem_rows) > 0:
#             st.subheader("Rows with Invalid ZIP Codes")
#             st.dataframe(problem_rows)
# else:
#     st.info("Please upload all required files and enter your Mapbox API key to generate the map.")
    
#     # Display sample map if no files uploaded
#     if not (orbital_file and drig_file and cb_direct_file):
#         st.subheader("Sample Map (No Data)")
#         m = folium.Map(location=[35.7157, -117.1611], zoom_start=4.2)
#         folium_static(m, width=1200, height=600)

# import streamlit as st
# import pandas as pd
# import folium
# from folium.plugins import MarkerCluster
# from streamlit_folium import folium_static
# import requests
# import io
# from geopy.distance import geodesic

# st.set_page_config(page_title="Installer Map", layout="wide")

# st.title("Installer Map Dashboard")
# st.write("Upload your installer data files and enter your Mapbox API key to visualize installer locations.")

# # Sidebar for inputs
# with st.sidebar:
#     st.header("Configuration")
    
#     # Mapbox API key input
#     mapbox_access_token = st.text_input("Enter your Mapbox API key", type="password")
    
#     # File uploads
#     st.subheader("Upload Data Files")
#     orbital_file = st.file_uploader("Upload Orbital employee list (Excel)", type=["xlsx", "xls"])
#     drig_file = st.file_uploader("Upload DRIG Installer List (Excel)", type=["xlsx", "xls"])
#     cb_direct_file = st.file_uploader("Upload CB Direct tech information (Excel)", type=["xlsx", "xls"])
#     training_file = st.file_uploader("Upload Training data (Excel)", type=["xlsx", "xls"], 
#                                      help="Expected filename pattern: 'CONFIDENTIAL USA Nextraq eLearning MM_DD_YY.xlsx'")
#     costs_file = st.file_uploader("Upload Cost data (Excel)", type=["xlsx", "xls"],
#                                  help="Expected filename: 'current_zip_training_costs.xlsx'")
    
#     # Proximity search
#     st.subheader("Proximity Search")
#     enable_proximity = st.checkbox("Enable proximity search")
#     if enable_proximity:
#         user_zip = st.text_input("Enter ZIP code to search around")
#         search_radius = st.slider("Search radius (miles)", 5, 100, 25)

# # Function to geocode using Mapbox
# def geocode_mapbox(zipcode, access_token):
#     if not access_token:
#         st.error("Please enter a Mapbox API key")
#         return {"latitude": None, "longitude": None}
        
#     url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{zipcode}.json"
#     params = {
#         "access_token": access_token,
#         "types": "postcode",
#         "country": "US"
#     }
#     try:
#         response = requests.get(url, params=params)
#         if response.status_code == 200:
#             data = response.json()
#             if data["features"]:
#                 coordinates = data["features"][0]["center"]
#                 return {"latitude": coordinates[1], "longitude": coordinates[0]}
#     except Exception as e:
#         st.error(f"Error geocoding: {e}")
#     return {"latitude": None, "longitude": None}

# # Function to check if a ZIP code is valid (5 digits)
# def is_valid_zip(zip_code):
#     try:
#         return len(str(int(zip_code))) == 5
#     except:
#         return False

# # Function to extract ZIP code from address
# def extract_zipcode(address):
#     if not isinstance(address, str):
#         return None

#     parts = address.split()  
#     zip_candidate = None

#     for part in reversed(parts):  # approach backwards - zipcode is at the end
#         if len(part) == 5 and part.isdigit():
#             zip_candidate = part
#             break  # stop at first

#     return zip_candidate

# # Process data if files are uploaded
# if orbital_file and drig_file and cb_direct_file and mapbox_access_token:
#     with st.spinner("Processing data..."):
#         # Load data
#         orbital = pd.read_excel(orbital_file)
#         drig = pd.read_excel(drig_file)
#         cb_direct = pd.read_excel(cb_direct_file)
        
#         # Process orbital data
#         orbital['ZIP'] = pd.to_numeric(orbital['ZIP'], errors='coerce').fillna(0).astype(int)
#         valid_mask = orbital['ZIP'].apply(is_valid_zip)
#         problem_rows = orbital[~valid_mask].copy()
#         orbital = orbital[valid_mask].copy()
        
#         # Process DRIG data
#         drig['ZIP'] = drig['Address'].apply(extract_zipcode)
#         drig = drig.dropna(subset=['ZIP'])
        
#         # Process CB Direct data
#         cb_direct = cb_direct[cb_direct['ADDRESS'].notna() & (cb_direct['ADDRESS'] != '') & cb_direct['ADDRESS'].str.contains(r'\d')]
#         cb_direct['ZIP'] = cb_direct['ADDRESS'].apply(extract_zipcode)
        
#         # Geocode all datasets
#         progress_bar = st.progress(0)
        
#         # Geocode orbital
#         results = []
#         for i, zipcode in enumerate(orbital['ZIP']):
#             results.append(geocode_mapbox(zipcode, mapbox_access_token))
#             progress_bar.progress((i + 1) / len(orbital))
        
#         orbital['latitude'] = [result['latitude'] for result in results]
#         orbital['longitude'] = [result['longitude'] for result in results]
#         orbital = orbital.dropna(subset=['latitude', 'longitude'])
        
#         # Geocode DRIG
#         results = []
#         for i, zipcode in enumerate(drig['ZIP']):
#             results.append(geocode_mapbox(zipcode, mapbox_access_token))
#             progress_bar.progress((i + 1) / len(drig))
            
#         drig['latitude'] = [result['latitude'] for result in results]
#         drig['longitude'] = [result['longitude'] for result in results]
#         drig = drig.dropna(subset=['latitude', 'longitude'])
#         drig = drig.rename(columns={'Name': 'NAME'})
        
#         # Geocode CB Direct
#         results = []
#         for i, zipcode in enumerate(cb_direct['ZIP']):
#             results.append(geocode_mapbox(zipcode, mapbox_access_token))
#             progress_bar.progress((i + 1) / len(cb_direct))
            
#         cb_direct['latitude'] = [result['latitude'] for result in results]
#         cb_direct['longitude'] = [result['longitude'] for result in results]
#         cb_direct = cb_direct.dropna(subset=['latitude', 'longitude'])
        
#         # Process training data if uploaded
#         if training_file:
#             training = pd.read_excel(training_file)
            
#             # Display column names to help debug
#             st.write("Training file columns:", training.columns.tolist())
            
#             # Check if the expected columns exist
#             status_column = 'Status' if 'Status' in training.columns else None
#             name_column = 'full name' if 'full name' in training.columns else None
#             course_column = 'course' if 'course' in training.columns else None
            
#             # If columns don't exist, let user select the appropriate columns
#             if not status_column or not name_column or not course_column:
#                 st.warning("Column names in training file don't match expected names.")
                
#                 if not status_column:
#                     status_options = [col for col in training.columns if 'status' in col.lower() or 'complete' in col.lower()]
#                     status_column = st.selectbox("Select status column:", options=training.columns.tolist(), 
#                                                 index=training.columns.get_indexer([status_options[0]])[0] if status_options else 0)
                
#                 if not name_column:
#                     name_options = [col for col in training.columns if 'name' in col.lower()]
#                     name_column = st.selectbox("Select name column:", options=training.columns.tolist(),
#                                               index=training.columns.get_indexer([name_options[0]])[0] if name_options else 0)
                
#                 if not course_column:
#                     course_options = [col for col in training.columns if 'course' in col.lower() or 'training' in col.lower()]
#                     course_column = st.selectbox("Select course column:", options=training.columns.tolist(),
#                                                 index=training.columns.get_indexer([course_options[0]])[0] if course_options else 0)
            
#             # Now use the selected column names
#             if status_column and name_column and course_column:
#                 filtered_training = training[training[status_column] == 'Complete'][[name_column, course_column]]
#                 filtered_training.rename(columns={name_column: 'NAME', course_column: 'course'}, inplace=True)
#                 result_training = filtered_training.groupby('NAME')['course'].agg(list).reset_index()
                
#                 # Merge training data
#                 orbital = pd.merge(orbital, result_training, on=['NAME'], how='left')
#                 drig = pd.merge(drig, result_training, on=['NAME'], how='left')
#                 cb_direct = pd.merge(cb_direct, result_training, on=['NAME'], how='left')
#             else:
#                 st.error("Could not process training data due to missing columns.")
        
#         # Process cost data if uploaded
#         if costs_file:
#             costs_by_installer = pd.read_excel(costs_file)
            
#             # Merge cost data
#             orbital = orbital.merge(costs_by_installer[['NAME', 'Installer Group', 'Average # of Devices Per Order', 'Average Service Cost', 'Average Travel Cost']], on='NAME', how='left')
#             drig = drig.merge(costs_by_installer[['NAME', 'Installer Group', 'Average # of Devices Per Order', 'Average Service Cost', 'Average Travel Cost']], on='NAME', how='left')
#             cb_direct = cb_direct.merge(costs_by_installer[['NAME', 'Installer Group', 'Average # of Devices Per Order', 'Average Service Cost', 'Average Travel Cost']], on='NAME', how='left')
        
#         progress_bar.empty()
        
#         # Create map
#         st.subheader("Installer Map")
        
#         # Create map with starting location and zoom level
#         map_center = [35.7157, -117.1611]
#         m = folium.Map(location=map_center, zoom_start=4.2)
#         cluster = MarkerCluster().add_to(m)
        
#         # Define your color scheme (same as in your original code)
#         group_styles = {
#             'orbital': {'color': 'blue', 'icon': 'info-sign', 'label': 'Orbital'},
#             'drig': {'color': 'green', 'icon': 'triangle', 'label': 'DRIG'},
#             'cb_direct': {'color': 'red', 'icon': 'diamond', 'label': 'CB Direct'}
#         }
        
#         # Process proximity search if enabled
#         user_location = None
#         if enable_proximity and user_zip:
#             try:
#                 location_result = geocode_mapbox(user_zip, mapbox_access_token)
#                 if location_result['latitude'] and location_result['longitude']:
#                     user_location = (location_result['latitude'], location_result['longitude'])
#                     # Add marker for search location
#                     folium.Marker(
#                         location=user_location,
#                         popup=f"Search center: {user_zip}",
#                         icon=folium.Icon(color='purple', icon='search', prefix='fa')
#                     ).add_to(m)
                    
#                     # Add circle for search radius
#                     folium.Circle(
#                         location=user_location,
#                         radius=search_radius * 1609.34,  # Convert miles to meters
#                         color='purple',
#                         fill=True,
#                         fill_opacity=0.2
#                     ).add_to(m)
                    
#                     # Center map on search location
#                     m.location = user_location
#             except Exception as e:
#                 st.error(f"Error with proximity search: {e}")
        
#         # Add markers to map
#         for df_name, df in [('orbital', orbital), ('drig', drig), ('cb_direct', cb_direct)]:
#             group_style = group_styles[df_name]
            
#             for index, row in df.iterrows():
#                 # Skip if outside search radius when proximity search is enabled
#                 if user_location and enable_proximity:
#                     marker_location = (row['latitude'], row['longitude'])
#                     distance = geodesic(user_location, marker_location).miles
#                     if distance > search_radius:
#                         continue
#                     distance_text = f"<br>Distance: {distance:.2f} miles"
#                 else:
#                     distance_text = ""
                
#                 # Create popup content
#                 popup_content = f"<b>Name:</b> {row['NAME']}<br><b>ZIP:</b> {row['ZIP']}{distance_text}"
                
#                 # Add training info if available
#                 if 'course' in row and pd.notna(row['course']):
#                     courses = row['course']
#                     if isinstance(courses, list):
#                         popup_content += f"<br><b>Training:</b> {', '.join(courses)}"
                
#                 # Add cost info if available
#                 if 'Average # of Devices Per Order' in row and pd.notna(row['Average # of Devices Per Order']):
#                     popup_content += f"<br><b>Avg Devices:</b> {row['Average # of Devices Per Order']}"
#                 if 'Average Service Cost' in row and pd.notna(row['Average Service Cost']):
#                     popup_content += f"<br><b>Avg Service Cost:</b> ${row['Average Service Cost']:.2f}"
#                 if 'Average Travel Cost' in row and pd.notna(row['Average Travel Cost']):
#                     popup_content += f"<br><b>Avg Travel Cost:</b> ${row['Average Travel Cost']:.2f}"
                
#                 folium.Marker(
#                     location=[row['latitude'], row['longitude']],
#                     popup=folium.Popup(popup_content, max_width=300),
#                     icon=folium.Icon(color=group_style['color'], icon=group_style['icon'], prefix='fa')
#                 ).add_to(cluster)
        
#         # Create a more visible legend using HTML
#         legend_html = """
#         <div style="position: fixed; 
#         bottom: 50px; left: 50px; width: 200px; 
#         border:2px solid grey; z-index:9999; font-size:14px;
#         background-color:white; padding: 10px; border-radius: 5px;
#         ">
#         <b style="font-size:16px;">Legend</b><br><br>
#         """

#         # Add each group to the legend
#         for group, style in group_styles.items():
#             legend_html += f'<i class="fa fa-{style["icon"]} fa-lg" style="color:{style["color"]}"></i> {style["label"]}<br>'

#         if enable_proximity and user_location:
#             legend_html += f'<i class="fa fa-search fa-lg" style="color:purple"></i> Search Center ({user_zip})<br>'

#         legend_html += "</div>"

#         # Add the legend to the map
#         m.get_root().html.add_child(folium.Element(legend_html))
        
#         # Display map
#         folium_static(m, width=1200, height=600)
        
#         # Add Streamlit legend
#         st.subheader("Map Legend")
#         legend_col1, legend_col2, legend_col3 = st.columns(3)

#         with legend_col1:
#             st.markdown('<span style="color:blue;font-size:20px;">●</span> Orbital', unsafe_allow_html=True)

#         with legend_col2:
#             st.markdown('<span style="color:green;font-size:20px;">●</span> DRIG', unsafe_allow_html=True)

#         with legend_col3:
#             st.markdown('<span style="color:red;font-size:20px;">●</span> CB Direct', unsafe_allow_html=True)

#         if enable_proximity and user_location:
#             st.markdown('<span style="color:purple;font-size:20px;">●</span> Search Center', unsafe_allow_html=True)
        
#         # Display data tables
#         col1, col2, col3 = st.columns(3)
        
#         with col1:
#             st.subheader("Orbital Data")
#             st.write(f"{len(orbital)} installers")
#             st.dataframe(orbital)
        
#         with col2:
#             st.subheader("DRIG Data")
#             st.write(f"{len(drig)} installers")
#             st.dataframe(drig)
        
#         with col3:
#             st.subheader("CB Direct Data")
#             st.write(f"{len(cb_direct)} installers")
#             st.dataframe(cb_direct)
        
#         # Display problem rows if any
#         if len(problem_rows) > 0:
#             st.subheader("Rows with Invalid ZIP Codes")
#             st.dataframe(problem_rows)
# else:
#     st.info("Please upload all required files and enter your Mapbox API key to generate the map.")
    
#     # Display sample map if no files uploaded
#     if not (orbital_file and drig_file and cb_direct_file):
#         st.subheader("Sample Map (No Data)")
#         m = folium.Map(location=[35.7157, -117.1611], zoom_start=4.2)
#         folium_static(m, width=1200, height=600)


import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import requests
from geopy.distance import geodesic

st.set_page_config(page_title="Installer Map", layout="wide")

st.title("Installer Map Dashboard")
st.write("Upload your installer data files and enter your Mapbox API key to visualize installer locations.")

# Sidebar for inputs
with st.sidebar:
    st.header("Configuration")
    
    # Mapbox API key input
    mapbox_access_token = st.text_input("Enter your Mapbox API key", type="password")
    
    # File uploads
    st.subheader("Upload Data Files")
    orbital_file = st.file_uploader("Upload Orbital employee list (Excel)", type=["xlsx", "xls"])
    drig_file = st.file_uploader("Upload DRIG Installer List (Excel)", type=["xlsx", "xls"])
    cb_direct_file = st.file_uploader("Upload CB Direct tech information (Excel)", type=["xlsx", "xls"])
    
    # Proximity search
    st.subheader("Proximity Search")
    enable_proximity = st.checkbox("Enable proximity search")
    if enable_proximity:
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
    return {"latitude": None, "longitude": None}

# Function to check if a ZIP code is valid (5 digits)
def is_valid_zip(zip_code):
    try:
        return len(str(int(zip_code))) == 5
    except:
        return False

# Function to extract ZIP code from address
def extract_zipcode(address):
    if not isinstance(address, str):
        return None

    parts = address.split()  
    zip_candidate = None

    for part in reversed(parts):  # approach backwards - zipcode is at the end
        if len(part) == 5 and part.isdigit():
            zip_candidate = part
            break  # stop at first

    return zip_candidate

# Process data if files are uploaded
if orbital_file and drig_file and cb_direct_file and mapbox_access_token:
    with st.spinner("Processing data..."):
        # Load data
        orbital = pd.read_excel(orbital_file)
        drig = pd.read_excel(drig_file)
        cb_direct = pd.read_excel(cb_direct_file)
        
        # Process orbital data
        orbital['ZIP'] = pd.to_numeric(orbital['ZIP'], errors='coerce').fillna(0).astype(int)
        valid_mask = orbital['ZIP'].apply(is_valid_zip)
        problem_rows = orbital[~valid_mask].copy()
        orbital = orbital[valid_mask].copy()
        
        # Process DRIG data
        drig['ZIP'] = drig['Address'].apply(extract_zipcode)
        drig = drig.dropna(subset=['ZIP'])
        
        # Process CB Direct data
        cb_direct = cb_direct[cb_direct['ADDRESS'].notna() & (cb_direct['ADDRESS'] != '') & cb_direct['ADDRESS'].str.contains(r'\d')]
        cb_direct['ZIP'] = cb_direct['ADDRESS'].apply(extract_zipcode)
        
        # Geocode all datasets
        progress_bar = st.progress(0)
        
        # Geocode orbital
        results = []
        for i, zipcode in enumerate(orbital['ZIP']):
            results.append(geocode_mapbox(zipcode, mapbox_access_token))
            progress_bar.progress((i + 1) / len(orbital))
        
        orbital['latitude'] = [result['latitude'] for result in results]
        orbital['longitude'] = [result['longitude'] for result in results]
        orbital = orbital.dropna(subset=['latitude', 'longitude'])
        
        # Geocode DRIG
        results = []
        for i, zipcode in enumerate(drig['ZIP']):
            results.append(geocode_mapbox(zipcode, mapbox_access_token))
            progress_bar.progress((i + 1) / len(drig))
            
        drig['latitude'] = [result['latitude'] for result in results]
        drig['longitude'] = [result['longitude'] for result in results]
        drig = drig.dropna(subset=['latitude', 'longitude'])
        
        # Geocode CB Direct
        results = []
        for i, zipcode in enumerate(cb_direct['ZIP']):
            results.append(geocode_mapbox(zipcode, mapbox_access_token))
            progress_bar.progress((i + 1) / len(cb_direct))
            
        cb_direct['latitude'] = [result['latitude'] for result in results]
        cb_direct['longitude'] = [result['longitude'] for result in results]
        cb_direct = cb_direct.dropna(subset=['latitude', 'longitude'])
        
        progress_bar.empty()
        
        # Create map
        st.subheader("Installer Map")
        
        # Create map with starting location and zoom level
        map_center = [35.7157, -117.1611]
        m = folium.Map(location=map_center, zoom_start=4.2)
        cluster = MarkerCluster().add_to(m)
        
        # Define your color scheme (same as in your original code)
        group_styles = {
            'orbital': {'color': 'blue', 'icon': 'info-sign', 'label': 'Orbital'},
            'drig': {'color': 'green', 'icon': 'triangle', 'label': 'DRIG'},
            'cb_direct': {'color': 'red', 'icon': 'diamond', 'label': 'CB Direct'}
        }
        
        # Process proximity search if enabled
        user_location = None
        if enable_proximity and user_zip:
            try:
                location_result = geocode_mapbox(user_zip, mapbox_access_token)
                if location_result['latitude'] and location_result['longitude']:
                    user_location = (location_result['latitude'], location_result['longitude'])
                    # Add marker for search location
                    folium.Marker(
                        location=user_location,
                        popup=f"Search center: {user_zip}",
                        icon=folium.Icon(color='purple', icon='search', prefix='fa')
                    ).add_to(m)
                    
                    # Add circle for search radius
                    folium.Circle(
                        location=user_location,
                        radius=search_radius * 1609.34,  # Convert miles to meters
                        color='purple',
                        fill=True,
                        fill_opacity=0.2
                    ).add_to(m)
                    
                    # Center map on search location
                    m.location = user_location
            except Exception as e:
                st.error(f"Error with proximity search: {e}")
        
        # Add markers to map
        for df_name, df in [('orbital', orbital), ('drig', drig), ('cb_direct', cb_direct)]:
            group_style = group_styles[df_name]
            
            for index, row in df.iterrows():
                # Skip if outside search radius when proximity search is enabled
                if user_location and enable_proximity:
                    marker_location = (row['latitude'], row['longitude'])
                    distance = geodesic(user_location, marker_location).miles
                    if distance > search_radius:
                        continue
                
                popup_content = f"<b>Name:</b> {row.get('NAME', '')}<br><b>ZIP:</b> {row.get('ZIP', '')}"
                
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=folium.Popup(popup_content, max_width=300),
                    icon=folium.Icon(color=group_style['color'], icon=group_style['icon'], prefix='fa')
                ).add_to(cluster)
        
        folium_static(m, width=1200, height=600)
else:
    st.info("Please upload all required files and enter your Mapbox API key to generate the map.")
