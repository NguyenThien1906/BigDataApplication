# libraries
import sys, argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import min, max, col, split, unix_timestamp, mean, median, log10, mode, to_date, lit
from pyspark.sql.types import StructType, StructField, StringType, FloatType

from collections import OrderedDict
import pandas as pd
import gc
import json

# arguments
parser = argparse.ArgumentParser()
parser.add_argument("config_path", type=str, help="configuration json file")
parser.add_argument("output_path", type=str, help="output embedded path")
args = parser.parse_args()

# configurations
#region
show_parts = False

config_json = json.load(open(args.config_path, 'r'))

rating_input = config_json['rating_input']
user_dataset_input = config_json['user_dataset_input']
user_dataset_embed_path = config_json['user_dataset_embed_path']
anime_dataset_embed_path = config_json['anime_dataset_embed_path']
user_dataset_og_path = config_json['user_dataset_embed_path'] # just to check the format
user_embed_col_path = config_json['user_embed_col_path']
anime_embed_col_path = config_json['anime_embed_col_path']
unified_embed_col_path = config_json['unified_embed_col_path']

spark = SparkSession\
    .builder \
    .appName("Spark SQL app")\
    .getOrCreate()
#endregion

# input necessities
#region
user_df = spark.read\
    .option("header", True)\
    .option("escape", '"')\
    .option("multiline", True)\
    .option("sep", ",")\
    .csv(user_dataset_input)

rating_schema = StructType([ 
    StructField('anime_id', StringType(), True), 
    StructField('rating', FloatType(), True),
]) 
rating_df = spark.read\
    .option("header", True)\
    .option("escape", '"')\
    .option("multiline", True)\
    .option("sep", ",")\
    .schema(rating_schema)\
    .csv(rating_input)

user_embed_df = spark.read\
    .option("header", True)\
    .option("escape", '"')\
    .option("multiline", True)\
    .option("sep", ",")\
    .csv(user_dataset_embed_path)\
    .limit(1) # one user only

anime_embed_df = spark.read\
    .option("header", True)\
    .option("escape", '"')\
    .option("multiline", True)\
    .option("sep", ",")\
    .csv(anime_dataset_embed_path)

user_embed_dict = json.load(open(user_embed_col_path, 'r'))
anime_embed_dict = json.load(open(anime_embed_col_path, 'r'))
unified_embed_dict = json.load(open(unified_embed_col_path, 'r'))
    
#endregion

# related functions
#region
def embed_onehot(dataFrame, colName: str, embed_dict: dict):
    unified_df = dataFrame.select(colName).dropDuplicates().toPandas()
    unified_df = unified_df.reindex(unified_df.columns.tolist() + list(embed_dict[colName]), axis=1, fill_value=0) # main difference
    input_list = unified_df[colName].tolist()
    for i in range(len(input_list)):
        if input_list[i] is not None:
            temp = input_list[i].split(", ")
            for j in temp:
                if j is not None and colName + "_" + j in list(embed_dict[colName]): # main difference
                    unified_df.at[i, colName+"_"+j] = 1
    unified_df = spark.createDataFrame(unified_df)
    dataFrame = dataFrame.join(unified_df, colName, 'left').drop(colName)

    # clean up mem
    del [[unified_df]]
    gc.collect()

    return dataFrame

def min_max(dataFrame, colName_in: str, colName_out: str, min_val: float, max_val: float):
    dataFrame = dataFrame.withColumn(colName_out, (col(colName_in)-min_val)/(max_val-min_val))                                                                                                                                                                                         #thien7170

    return dataFrame

def embed_minmax(dataFrame, colName: str, embed_dict: dict):
    min_val = embed_dict[colName][0]
    max_val = embed_dict[colName][1]
    dataFrame = dataFrame.withColumn("A1", (col(colName)-min_val)/(max_val - min_val))\
        .drop(colName).withColumnRenamed(existing="A1", new=colName)
    return dataFrame

def main_normalization(dataFrame, colName_in: str, colName_out: str, min_range: float = 0, max_range: float = 1):
    return min_max(dataFrame, colName_in, colName_out, min_range, max_range)
#endregion

# mean score
rating_df_mean = rating_df.select(mean('rating')).collect()[0][0]
rating_df = rating_df.withColumn('rating_m', col('rating')-rating_df_mean)\
    .drop('rating').withColumnRenamed(existing='rating_m', new='rating')
if show_parts:
    rating_df.show()
    user_df.show()

# other user embeddings
#region
user_df = user_df.replace({'UNKNOWN': None, 'Unknown': None})

user_df = user_df.drop('Username')

user_df = embed_onehot(user_df, 'Gender', user_embed_dict)

split_col = split(user_df['Birthday'], 'T', 2)
user_df = user_df.withColumn('Birthday_d', split_col.getItem(0))\
    .withColumn('Birthday_unix', unix_timestamp('Birthday_d', format='yyyy-mm-dd'))\
    .drop('Birthday', 'Birthday_d')\
    .withColumnRenamed('Birthday_unix', 'Birthday')
user_df = embed_minmax(user_df, 'Birthday', user_embed_dict)

user_df = user_df.drop('Location')

user_df = user_df.drop('Joined')

user_df = user_df.withColumnRenamed('Days Watched', 'Days_Watched')
user_df = user_df.withColumn('Days_Watched_log', log10(col('Days_Watched')+1.0))\
    .drop('Days_Watched')\
    .withColumnRenamed('Days_Watched_log', 'Days_Watched')

user_df = embed_minmax(user_df, 'Days_Watched', user_embed_dict)

user_df = user_df.drop('Watching', 'On Hold', 'Dropped', 'Plan to Watch', 'Total Entries')

user_df = user_df.drop('Rewatched')\
    .withColumnRenamed('Episodes Watched', 'Episodes_Watched')
a, b = 'Episodes_Watched', 'Completed'
user_df = user_df.withColumn(a + '_l', log10(col(a)+1.0))\
    .withColumn(b+ '_l', log10(col(b)+1.0))\
    .drop(a, b)\
    .withColumnRenamed(a+'_l', a)\
    .withColumnRenamed(b+'_l', b)

user_df = embed_minmax(user_df, b, user_embed_dict)
user_df = embed_minmax(user_df, a, user_embed_dict)
#endregion

if show_parts:
      print(list(user_df.columns))
      print(list(user_embed_df.columns))
      print(list(user_df.columns) == list(user_embed_df.columns))
      user_df.show()

# anime embed
if show_parts:
    anime_embed_df.sort(col('anime_id').cast('int')).show()

# join
#region
unified_df = user_df.select('Mal ID').crossJoin(rating_df).select(['Mal ID', 'anime_id', 'rating'])
unified_df = unified_df.join(user_df, 'Mal ID', 'left').withColumnRenamed(existing='Mal ID',new='user_id')\
    .join(anime_embed_df, 'anime_id', 'left')
if show_parts:
    unified_df.show()

# whitespace -> underscore
to_change = {}
column_order = list(unified_df.columns)
for i in range(len(column_order)):
    if ' ' in column_order[i]:
        new_name = column_order[i].replace(' ', '_')

        to_change[column_order[i]] = new_name
        column_order[i] = new_name

unified_df = unified_df.withColumnsRenamed(to_change)

# remove illigible characters
import re
to_change = {}
for i in range(len(column_order)):
    new_name = re.sub("[!@#$%^&*().,']","", column_order[i]) 

    if new_name != column_order[i]:
        to_change[column_order[i]] = new_name
        column_order[i] = new_name

unified_df = unified_df.withColumnsRenamed(to_change)

unified_df = unified_df.drop('Mean_Score')
if show_parts:
    print(sorted(unified_df.columns))
    print(sorted(unified_embed_dict['unified_embed']))
    unified_df.select(unified_embed_dict['unified_embed']).show()

unified_df.coalesce(1).write\
        .option("header", "true")\
        .option("sep", ",")\
        .mode("overwrite")\
        .csv(args.output_path)

spark.stop()
#endregion

