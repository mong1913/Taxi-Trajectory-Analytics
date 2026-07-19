
def map_click(clickData, haversine, df, filter_radius=0.5):
    '''Filters the DataFrame based on the clickData from the map.'''
   
    lon = clickData['points'][0]['lon']
    lat = clickData['points'][0]['lat']
    dist = haversine(df['START_LON'], df['START_LAT'], lon, lat)
    filtered_df = df[dist <= filter_radius]  # Filter trips within the specified radius

    return lon, lat, filtered_df