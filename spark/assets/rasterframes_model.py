from pyrasterframes.utils import create_rf_spark_session
from pyrasterframes.rasterfunctions import *
from pyspark.sql.functions import *
from pyspark import SparkFiles
from pyspark import SparkConf
conf1 = SparkConf().set("spark.files.overwrite", "true")#.set('spark.local.dir', '/mnt/dados/downunder/tmp') #.set("dfs.block.size", "128m") #.set("spark.shuffle.blockTransferService", "nio") #.set("spark.executor.memory","32g")

spark = create_rf_spark_session('spark://spark-master:7077',conf=conf1)

import os
import datetime

import requests
import json

import numpy as np
#import rasterio as rio

### Declarando handles para funcionar

#def add_dir_to_spark(files_dir):
#    filenames = os.listdir(tiff_path)
#    tiff_filenames = []
#    for filename in filenames:
#        if filename[-4:] == '.tif':
#            tiff_filenames.append(filename)
#    lst = [os.path.splitext(x)[0] for x in tiff_filenames]
#    bands = [x[41:] for x in lst]
#    files = [tiff_path + filename for filename in tiff_filenames]
#    for i in files:
#        spark.sparkContext.addFile(i)


##### REQUEST TILE FROM GLAD ARD #####

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

#### Fitando o modelo

from pyrasterframes import TileExploder
from pyrasterframes.rf_types import NoDataFilter
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import DecisionTreeClassifier
from pyspark.ml.classification import RandomForestClassifier
#from pyspark.ml.classification import LinearSVC
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml import Pipeline

geojson_path = 'hdfs://primary-namenode/'
geojson_name = 'mask12042008.geojson'

intervals = [666]

tiffs = request_tiles(geojson_path+geojson_name,intervals)

tiff_path = 'hdfs://primary-namenode/'

with open(tiff_path, 'wb') as f:
    f.write(tiffs[666][0].content)

begin_time = datetime.datetime.now()

tile_dimensions = (256,256)
df = spark.read.raster('/vsihdfs/hdfs:/primary-namenode/666_053W_24S.tif',band_indexes=[0,1,2,3,4,5,6,7],tile_dimensions=(256,256)) \
                  .withColumn('boundsWGS84', st_extent(st_reproject(rf_geometry('proj_raster_b0'), rf_crs('proj_raster_b0'), lit('EPSG:4326')))) \
                  .withColumn('boundsPseudoMercator', st_extent(st_reproject(rf_geometry('proj_raster_b0'), rf_crs('proj_raster_b0'), lit('EPSG:3857')))) \
                  .withColumn('extent', st_extent(st_reproject(rf_geometry('proj_raster_b0'), rf_crs('proj_raster_b0'), lit('EPSG:4326')))) \
                  .withColumn('crs', rf_crs("proj_raster_b0"))
crs = df.select('crs.crsProj4').distinct().collect()
bands = ['blue', 'green', 'red', 'NIR', 'SWIR1', 'SWIR2', 'brightness_temperature','Quality']
df = spark.read.raster('hdfs://primary-namenode/666_053W_24S.tif',band_indexes=[0,1,2,3,4,5,6,7],tile_dimensions=(256,256)) \
                  .withColumn('boundsWGS84', st_extent(st_reproject(rf_geometry('proj_raster_b0'), rf_crs('proj_raster_b0'), lit('EPSG:4326')))) \
                  .withColumn('boundsPseudoMercator', st_extent(st_reproject(rf_geometry('proj_raster_b0'), rf_crs('proj_raster_b0'), lit('EPSG:3857')))) \
                  .withColumn('extent', st_extent(st_reproject(rf_geometry('proj_raster_b0'), rf_crs('proj_raster_b0'), lit('EPSG:4326')))) \
                  .withColumn('crs', rf_crs("proj_raster_b0"))
                  
df, crs, bands = spark_read_raster(tiff_path, tile_dimensions)

spark_labels = spark.read.geojson(geojson_path+'/'+geojson_name) \
                    .select('id','label', st_reproject('geometry', lit('EPSG:4326'), lit(crs)).alias('geometry')) \
                    .hint('broadcast')

df_labeled = df_label_join(df, spark_labels, bands)

print(datetime.datetime.now() - begin_time)

bands = ['blue',
         'green', 
         'red', 
         'NIR', 
         'SWIR1', 
         'SWIR2', 
         'brightness_temperature',
         'Quality']


## PIPELINE DE ML - RANDOM FOREST


exploder = TileExploder()
exploded_tiles = exploder.transform(df_labeled)

exploded_train, exploded_test = exploded_tiles.randomSplit([0.8, 0.2], seed=42)
noDataFilter = NoDataFilter().setInputCols(['label', 'blue', 'green', 'red', 'NIR', 'SWIR1', 'SWIR2', 'brightness'])

exploded_tiles_filtered_train = noDataFilter.transform(exploded_train)
exploded_tiles_filtered_test = noDataFilter.transform(exploded_test)

assembler = VectorAssembler().setInputCols(bands) \
                                 .setOutputCol("features")

assembled_df_train = assembler.transform(exploded_tiles_filtered_train)
assembled_df_test = assembler.transform(exploded_tiles_filtered_test)

classifier = RandomForestClassifier().setLabelCol('label') \
                        .setFeaturesCol(assembler.getOutputCol())

model = classifier.fit(assembled_df_train.cache())

prediction_df = model.transform(assembled_df_test).drop(assembler.getOutputCol()).cache()

evaluator = MulticlassClassificationEvaluator(
                predictionCol=classifier.getPredictionCol(),
                labelCol=classifier.getLabelCol(),
                metricName='accuracy'
)

accuracy = evaluator.evaluate(prediction_df)
print("\nAccuracy:", accuracy)

cnf_mtrx = prediction_df.groupBy(classifier.getPredictionCol()) \
    .pivot(classifier.getLabelCol()) \
    .count() \
    .sort(classifier.getPredictionCol())
cnf_mtrx

print("Tempo do calculo da cnf_matrix: "+str(datetime.datetime.now() - begin_time))

begin_time = datetime.datetime.now()

scored = model.transform(df_labeled.drop('label'))

print("Tempo do calculo do transform: "+str(datetime.datetime.now() - begin_time))

#cnf_mtrx

#municipios_json = 'municipios.geojson'

#municipios_labels = geojson_read_spark(geojson_path, municipios_json, crs)

#df_municipios_labeled = df_label_join(df, municipios_labels, bands)

#df_municipios_labeled.printSchema()

#municipios_scored = model.transform(df_municipios_labeled.drop('label'))

