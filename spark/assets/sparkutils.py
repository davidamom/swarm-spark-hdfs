def request_tiles(geojson_path,intervals):
    """
    REQUEST_TILES - Use requests to get data from GLAD ARD data
    
    INPUTS:
    
        geojson_path: The path to the geojson file with the geometry
        intervals: the GLAD ARD time intervals (see: https://glad.umd.edu/gladtools/Documentation/16d_intervals.xlsx )
        
    OUTPUTS:
    
        tiff_dict: dictionary with tiff intervals as keys and requests as values
    
    """
    tries = 2
    
    geojson = open(geojson_path,)
    data = json.load(geojson)
    
    #login = ("yuribarros", "ScDvG5qPxgInP1za")
    url = "https://glad.umd.edu/dataset/landsat_v1.1/"
    
    coords = []

    for i in range(len(data['features'])):
    
        coords.append(np.unique(np.ceil(data['features'][i]['geometry']['coordinates']).squeeze(), axis=0))
    
    coords = np.unique(np.concatenate(coords,axis=0),axis=0).astype(int)
    
    print(coords)
    
    tiff_dict = dict.fromkeys(intervals)
    
    with requests.Session() as s:
        
        s.auth=("yuribarros", "ScDvG5qPxgInP1za")
        
        for j in intervals:
            
            tiffs = []
        
            for i in coords:
                
                for k in range(tries):
                    try:

                        if i[0] < 0 and i[1] < 0:

                            print('Requesting from URL: ' + url + f'{-i[1]:02}S/{-i[0]:03}W_{-i[1]:02}S/{j}.tif')
                            tiff = s.get(url + f'{-i[1]:02}S/{-i[0]:03}W_{-i[1]:02}S/{j}.tif')
                            # tiff = requests.get('https://glad.umd.edu/dataset/landsat_v1.1/24S/053W_24S/666.tif', auth=("yuribarros", "ScDvG5qPxgInP1za"))
                            tiffs.append(tiff)

                        elif i[0] < 0 and i[1] > 0:

                            print('Requesting from URL: ' + url + f'{i[1]:02}N/{-i[0]:03}W_{i[1]:02}N/{j}.tif')
                            tiff = s.get(url + f'{i[1]:02}N/{-i[0]:02}W_{i[1]:02}N/{j}.tif')
                            tiffs.append(tiff)

                        elif i[0] > 0 and i[1] < 0:

                            print('Requesting from URL: ' + url + f'{-i[1]:02}S/{i[0]:03}E_{-i[1]:02}S/{j}.tif')
                            tiff = s.get(url + f'{-i[1]:02}S/{i[0]:03}E_{-i[1]:02}S/{j}.tif')
                            tiffs.append(tiff)

                        elif i[0] > 0 and i[1] > 0:

                            print('Requesting from URL: ' + url + f'{i[1]:02}N/{i[0]:03}E_{i[1]:02}N/{j}.tif')
                            tiff = s.get(url + f'{i[1]:02}N/{i[0]:03}E_{i[1]:02}N/{j}.tif')
                            tiffs.append(tiff)
                            
                    except ConnectionError:
                        if i < tries - 1: # i is zero indexed
                            print(f'Failed to fetch file. Retrying {i+1-tries} more time(s).')
                            continue
                        else:
                            print('Connection Error. Server is Unreachable.')
                            continue
                            #raise
                    break
                    
            tiff_dict[j] = tiffs
        
    return tiff_dict

#### Importando o GeoJSON

def geojson_read_spark(geojson_path, geojson_name, crs):
    spark.sparkContext.addFile(geojson_path+'/'+geojson_name)
    #spark_labels = spark.read.geojson(SparkFiles.get(geojson_name)) \
    #                .select('id', st_reproject('geometry', lit('EPSG:4326'), lit(crs)).alias('geometry')) \
    #                .hint('broadcast')
    spark_labels = spark.read.geojson(SparkFiles.get(geojson_name)) \
                    .select('id','label', st_reproject('geometry', lit('EPSG:4326'), lit(crs)).alias('geometry')) \
                    .hint('broadcast')
    return spark_labels

def df_label_join(df, spark_labels, bands):
    df_joined = df.join(spark_labels, st_intersects(st_geometry('extent'), 'geometry')) \
                  .withColumn('dims', rf_dimensions('sr_band1'))
    df_labeled = df_joined.withColumn('label', 
                    rf_rasterize('geometry', st_geometry('extent'), 'id', 'dims.cols', 'dims.rows')
    )
    return df_labeled