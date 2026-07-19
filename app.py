from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
from src.util import map_click

app = Dash(__name__)

# ---------------------------------------------------------------------------------------
# Load the data and define the parameters
df = pd.read_parquet("data/train_sample_silver.parquet")
day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
call_type_order = ['A', 'B', 'C']
call_type_colors = {'A': '#e41a1c', 'B': '#000000', 'C': '#377eb8'}
radius_around_click = 0.5  # in kilometers on the map, used to filter trips around the clicked point
# ---------------------------------------------------------------------------------------

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points on the earth
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    step1 = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    step2 = 2 * np.asin(np.sqrt(step1)) 
    rad = 6371  # Radius of earth in kilometers.
    return step2 * rad

app.layout = html.Div([
    html.H1("Taxi Trajectory Analytics Dashboard", 
            style={'textAlign': 'center'}),
    # dcc.Dropdown(
    #     id='week-day',
    #     options=[
    #         {'label': d, 'value': i} for i, d \
    #         in enumerate(day_names)
    #     ],
    #     value=0
    # ),
    html.Div([
        html.Div(dcc.Graph(id='scatter-map'), style={'width': '47%', 'display': 'inline-block'}),
        html.Div(dcc.Graph(id='pie-plot'), style={'width': '47%', 'display': 'inline-block'})
    ]),
    html.Div([
        html.Div(dcc.Graph(id='line-plot'), style={'width': '47%', 'display': 'inline-block', 'vertical-align': 'top'}),
        html.Div([
            dcc.Checklist(id='trim_outliers', options=[{'label': 'Trim Outliers', 'value': 'trim'}], value=['trim']),
            dcc.Graph(id='box-plot')
        ], style={'width': '47%', 'display': 'inline-block', 'vertical-align': 'top'})
    ])
])

@app.callback(
    Output('scatter-map', 'figure'),
    Input('scatter-map', 'clickData')
)
def update_graph(clickData):
    fig = px.scatter_map(
        df, lat='START_LAT', lon='START_LON',
        zoom=10, color='CALL_TYPE',
        category_orders={'CALL_TYPE': call_type_order},
        color_discrete_map=call_type_colors,
        map_style="carto-voyager", title="Start Points of Taxi Trips"
    )
    fig.update_traces(marker={'opacity': 0.9})
    
    if clickData:
        _, _, near = map_click(clickData, haversine, df, radius_around_click)
        highlight = px.scatter_map(near, lat='START_LAT', lon='START_LON')
        highlight.update_traces(marker={'color': 'orange', 'size': 12, 'opacity': 0.8})
        fig.add_trace(highlight.data[0])
    return fig

@app.callback(
    Output('pie-plot', 'figure'),
    Input('scatter-map', 'clickData')
)
def update_pie(clickData):
    if clickData is None:
        near = df
        title = "Call type share of the start points near this area"
    else:
        lon,lat, near = map_click(clickData, haversine, df, radius_around_click)
        title = f"Call type share of the start points near ({lon:.4f}, {lat:.4f})"
    
    grouped_df = near.groupby(['HOUR', 'CALL_TYPE']).size().reset_index(name='COUNT')
    fig = px.pie(
        grouped_df, values='COUNT', names='CALL_TYPE', title=title, color='CALL_TYPE',
        category_orders={'CALL_TYPE': call_type_order},
        color_discrete_map=call_type_colors
    )
    return fig

@app.callback(
    Output('box-plot', 'figure'),
    Input('scatter-map', 'clickData'),
    Input('trim_outliers', 'value')
)
def update_box(clickData, trim_outliers):

    if 'trim' in trim_outliers:
        q99 = df['TRIP_DURATION'].quantile(0.99)
        df_trimmed = df[df['TRIP_DURATION'] <= q99]
    else:
        df_trimmed = df

    if clickData is None:
        near = df_trimmed
        title = "Trip Duration Distribution"
    else:
        lon,lat, near = map_click(clickData, haversine, df, radius_around_click)
        title = f"Trip Duration Distribution within {radius_around_click} km of ({lon:.4f}, {lat:.4f})"
    fig = px.box(
        near, x='HOUR', y='TRIP_DURATION',
        title=title
    )
    return fig

@app.callback(
    Output('line-plot', 'figure'),
    Input('scatter-map', 'clickData')
)
def update_line(clickData):
    if clickData is None:
        near = df
        title = "Call type count over time"
    else:
        lon,lat, near = map_click(clickData, haversine, df, radius_around_click)
        title = f"Total count of each call type over time near ({lon:.4f}, {lat:.4f})"
    
    grouped_df = near.groupby(['HOUR', 'CALL_TYPE']).size().reset_index(name='COUNT')
    fig = px.line(
        grouped_df, x='HOUR', y='COUNT', color='CALL_TYPE',
        category_orders={'CALL_TYPE': call_type_order},
        color_discrete_map=call_type_colors,
        title=title
    )
    return fig

# @app.callback(
#     Output('scatter-map', 'figure'),
#     Input('week-day', 'value')
# )
# def update_graph(value):
#     filtered_df = df[df['DAY_OF_WEEK'] == value]
#     fig = px.box(
#         filtered_df,
#         x='HOUR',
#         y='TRIP_DURATION',
#         title=f'Trip Duration Distribution on {day_names[value]}'
#     )
#     return fig

if __name__ == '__main__':
    app.run(debug=True)
