import pandas as pd
import requests
import polyline
import os
from os import path
import datetime
import json
import math
import folium
import io
from PIL import Image



df = pd.read_csv('C:/Users/test/Desktop/Milad_project/BIXI/Data/2019/OD_2019-07.csv')
st = pd.read_csv('C:/Users/test/Desktop/Milad_project/BIXI/Data/2019/Stations_2019.csv')

df['start_date'] = pd.to_datetime(df['start_date'])
df['end_date'] = pd.to_datetime(df['end_date'])

df['hour'] = df['start_date'].map(lambda x : x.hour)
df['dow'] = df['start_date'].map(lambda x : x.weekday())

data = df.merge(st, left_on = 'start_station_code', right_on = 'Code')
data.rename(columns=dict(zip(st.columns.values,["start_station_" + x.lower() for x in st.columns.values])),inplace = True)

data = data.merge(st, left_on = 'end_station_code', right_on = 'Code')
data.rename(columns=dict(zip(st.columns.values,["end_station_" + x.lower() for x in st.columns.values])),inplace = True)
data = data.loc[:,~data.columns.duplicated()]


print(data.head())

data.to_csv('C:/Users/test/Desktop/Milad_project/BIXI/Data/2019/data.csv', encoding='utf-8', sep=',')
# data=data.iloc[0:10, :]

# print(data.head())



def get_route(c1,c2,s1,s2):

    loc = "{},{};{},{}".format(c1, c2, s1, s2)
    url = "http://127.0.0.1:5000/route/v1/driving/"
    r = requests.get(url+loc)
    if r.status_code!=200:
        return {}


    k1=str(int(row['start_station_code']))
    k2=str(int(row['end_station_code']))


    with open('C:/Users/test/Desktop/Milad_project/BIXI/Data/2019/directions/%s_%s.json' % (k1,k2), 'w') as outfile:
        json.dump(r.json(), outfile)
    
    # return r.json()['routes'][0]['geometry']
    
    
    
    res = r.json()
    routes=polyline.decode(res['routes'][0]['geometry'])
    start_point = [res['waypoints'][0]['location'][1], res['waypoints'][0]['location'][0]]
    end_point = [res['waypoints'][1]['location'][1], res['waypoints'][1]['location'][0]]
    distance = res['routes'][0]['distance']


    out = {'route':routes,
           'start_point':start_point,
           'end_point':end_point,
           'distance':distance
          }

    return out



data = data.loc[:,~data.columns.duplicated()]
comb = data.groupby(['start_station_code',
              'start_station_latitude', 
              'start_station_longitude', 
              'end_station_code',
              'end_station_latitude', 
              'end_station_longitude']
            ).size().to_frame('count').reset_index().sort_values('count', ascending = False)

print(comb.head())

comb.to_csv('C:/Users/test/Desktop/Milad_project/BIXI/Data/2019/comb.csv', encoding='utf-8', sep=',')


routes = comb[(comb.start_station_code != comb.end_station_code)].reset_index(drop=True)
print(routes.head())
routes.to_csv('C:/Users/test/Desktop/Milad_project/BIXI/Data//2019/routes/routes.csv', encoding='utf-8', sep=',')





for i, row in routes.iloc[0:144626].iterrows():
    start_lon = (row['start_station_longitude'])
    start_lat = (row['start_station_latitude'])
    end_lon = (row['end_station_longitude'])
    end_lat = (row['end_station_latitude'])
    print(start_lon)
    print(start_lat)
    print(end_lon)
    print(end_lat)

    if not path.exists('C:/Users/test/Desktop/Milad_project/BIXI/Data/2019/directions/%s_%s.json' % (str(int(row['start_station_code'])),str(int(row['end_station_code'])))):
        geom = get_route(start_lon, start_lat, end_lon, end_lat)
        print (geom)




# def get_map(route):
    
#     m = folium.Map(
#         location=[(route['start_point'][0] + route['end_point'][0])/2, 
#                              (route['start_point'][1] + route['end_point'][1])/2], 
#                    zoom_start=13,
#                    tiles = "CartoDB positron"
#     )

#     print(m)

#     folium.PolyLine(
#         route['route'],
#         weight=8,
#         color='blue',
#         opacity=0.6
#     ).add_to(m)

#     folium.Marker(
#         location=route['start_point'],
#         icon=folium.Icon(icon='play', color='green')
#     ).add_to(m)

#     folium.Marker(
#         location=route['end_point'],
#         icon=folium.Icon(icon='stop', color='red')
#     ).add_to(m)

#     return m



# get_map(geom)
# print(geom)



def get_json_geometry(row):
    s1 = str(int(row['start_station_code']))
    s2 = str(int(row['end_station_code']))
    fp = 'C:/Users/test/Desktop/Milad_project/BIXI/Data/2019/directions/%s_%s.json' % (s1,s2)
    if not path.exists(fp):
        start_lon = row['start_station_longitude']
        start_lat = row['start_station_latitude']
        end_lon = row['end_station_longitude']
        end_lat = row['end_station_latitude']
        get_route(start_lon, start_lat,end_lon,end_lat)                                      
    with open(fp) as f:
        data = json.load(f)
    return data['routes'][0]['geometry']



def get_polyline_length(coord):
    length = 0
    for i in range(len(coord)-1):
        length += get_distance(coord[i], coord[i+1])
    return length


def get_distance(xy1,xy2):
    return math.sqrt((xy2[0]-xy1[0])**2 + (xy2[1]-xy1[1])**2)


def get_waypoint(coord,pct):
    
    tgt_dis = get_polyline_length(coord) * pct

    tot_dis = 0
    for i in range(len(coord)-1):
        dis = get_distance(coord[i], coord[i+1])
        tot_dis += dis
        if tot_dis >= tgt_dis:
            x1,y1 = coord[i]
            x2,y2 = coord[i+1]
            a = x2-x1
            b = y2-y1
            
            
            if a == 0 or b == 0:
                waypoint = (x1+a,y1+b)
                path = coord[:i+1]
                break
                
            a = abs(a)
            b = abs(b)
            
            c = math.sqrt(a**2 + b**2)

            C = math.pi/2
            
            B = math.acos((a**2+c**2-b**2)/(2*a*c))
            A = math.pi-B-C

            X = A
            Y = B
            Z = C

            z = dis - (tot_dis - tgt_dis)

            x = z*math.sin(X)/math.sin(Z)
            y = z*math.sin(Y)/math.sin(Z)
            
            x_fac = (x2-x1)/abs(x2-x1) if abs(x2-x1) > 0 else 1
            y_fac = (y2-y1)/abs(y2-y1) if abs(y2-y1) > 0 else 1
            
            waypoint = (x1+x*x_fac,y1+y*y_fac)
            path = coord[:i+1]
            break
            
    path.append(waypoint)

    my_dict = dict({"waypoint" : waypoint, "path":path})
    return my_dict




def get_frame(bike_data, center, timestamp):

    m = folium.Map(
        location = center,
        zoom_start = 12,
        tiles = "CartoDB positron"
    )

    print(m)

    for i, row in bike_data.iterrows():
        if row['geometry'] is not None:
            coord = polyline.decode(row['geometry'])
            dur = (row['end_date'] - row['start_date']).seconds
            ela = (timestamp - row['start_date']).seconds
            factor = float(ela/dur)
            xys = get_waypoint(coord,factor)['path']
            folium.PolyLine(
                xys,
                opacity = 0.7, 
                smoothFactor = 3,
                weight = 1,
            ).add_to(m)

    for i, row in bike_data.iterrows():
        if row['geometry'] is not None:
            coord = polyline.decode(row['geometry'])
            dur = (row['end_date'] - row['start_date']).seconds
            ela = (timestamp - row['start_date']).seconds
            factor = float(ela/dur)
            x,y = get_waypoint(coord,factor)['waypoint']

            folium.Circle([x,y], radius = 0.01, color = 'black' ,opacity = 1,).add_to(m)
    
    im = Image.open(io.BytesIO(m._to_png()))
    # draw = ImageDraw.Draw(im)
    # font = ImageFont.load_default()
    # draw.text((50, 125),str(timestamp),(255,255,255),font=font)
    
    return im

print(data)




start = datetime.datetime.now()

print(start)

start_datetime = datetime.datetime(2019,7,22,7,59,50)
end_datetime = datetime.datetime(2019,7,22,9,30,0)


print(start_datetime)
print(end_datetime)


delta = datetime.timedelta(seconds = 10)
cnt = (end_datetime-start_datetime)/delta


print(delta)
print(cnt)


img = []
while start_datetime < end_datetime:
    current_datetime = start_datetime + delta
    curr = cnt - (end_datetime-current_datetime)/delta
    print(curr)
    print(f"Processing frame {str(int(curr))} of {str(int(cnt))} ({str(int(curr/cnt*100))}%)")
    subset = data[(data.start_date <= start_datetime) & (data.end_date > current_datetime) & (data.start_station_code != data.end_station_code)]
    
    print(subset)
    subset.to_csv('C:/Users/test/Desktop/Milad_project/BIXI/Data//2019/subset.csv', encoding='utf-8', sep=',')

    subset['geometry'] = subset.apply(lambda row: get_json_geometry(row), axis=1)
    
    print(subset)

    center = [data.start_station_latitude.mean(),data.start_station_longitude.mean()]

    print(center)

    im = get_frame(subset, center, current_datetime)

    print(im)

    im=im.save("C:/Users/test/Desktop/Milad_project/BIXI/Data/2019/img/img%s.png" %curr)
# %s_%s.json' % (s1,s2)
    img.append(im)
    
    start_datetime = current_datetime

img_crop = []
for i in img:
    width, height = i.size 
    img_crop.append(i.crop((0,75,width-200,height-20)))
    
img_crop[0].save('C:/Users/test/Desktop/Milad_project/BIXI/Data/2019/bixi.gif',save_all=True,append_images=img_crop[1:], duration = 40,loop=0)

