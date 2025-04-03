import time
from pyspark.sql import SparkSession
import redis
from pyspark import SparkContext
import json
import os

# config
#region
# ML
# add stuff here <------------------------------------------------------------------>
# Spark Streaming
json_input_file = "spark_config.json"
config_json = json.load(open(json_input_file, 'r'))
#endregion

# ML
#region
# add stuff here <------------------------------------------------------------------->
#endregion

# Spark Streaming
#region
# Create Spark Session
spark = SparkSession.builder.appName("RedisToSparkStreaming").getOrCreate()
sc = spark.sparkContext

# Connect Redis
redis_host = config_json['redis_host']
redis_port = config_json['redis_port']
batch_size = config_json['batch_size']  # Number of keys per batch

# main streaming
def check_ratingKeys(key):
    if not isinstance(key, str):
        return False
    try:
        user, anime = key.split("_")
    except ValueError:
        return False
    return (user.isdigit() and anime.isdigit())
    
def get_ratingKeys(showConsole:bool = False):
    "Use SCAN to get a list of keys from Redis"
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    cursor = 0
    keys = []
    while True:
        cursor, batch_keys = r.scan(cursor, count=batch_size)
        if cursor == 0:  # Out of keys in Redis
            break
        for key_i in batch_keys:
            if check_ratingKeys(key_i):
                keys.append(key_i)
    if showConsole:
        print(f"Number of keys currently in Redis: {len(keys)}")
    return keys

def fetch_redis_data(keys_batch):
    "Fetch data from Redis with smaller batch and check data type before GET"
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

    batch_size = 1000  # Split batches to avoid overloading
    data = []
    keys_batch = list(keys_batch)
    for i in range(0, len(keys_batch), batch_size):
        pipe = r.pipeline()
        sub_batch = keys_batch[i : i + batch_size]  # Split batch

        # Check data type before GET
        valid_keys = [key for key in sub_batch if r.type(key) == "string"]
        for key in valid_keys:
            pipe.get(key)  # GET only keys of string type

        values = pipe.execute()

        for key, value in zip(valid_keys, values):
            #if value is not None: #Thien: maybe no?
            try:
                user_id, anime_id = key.split("_")
                rating = float(value)
                data.append((int(user_id), int(anime_id), rating))
            except ValueError:
                continue  # Bỏ qua key lỗi
    return data

def show_df(df):
    row_count = df.count()
    print(f"Sample row count: {row_count}")
    df.show(20)

# main streaming
def streaming(showConsole:bool = False):
    run_iter = 0
    old_redis_keys = []
    df = None
    # Streaming simulation loop and update df (updates every 10 seconds)
    while True:
        run_iter += 1
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"Streaming iter: {run_iter}.")
    
        print("Fetching data from Redis...")
        # Get list of keys from Redis
        redis_keys = get_ratingKeys()
        if len(redis_keys) != len(old_redis_keys):
            # Retrieve new keys
            new_redis_keys = []
            for key in redis_keys:
                if key not in old_redis_keys:
                    new_redis_keys.append(key)
        
            # Divide the key into multiple partitions for Spark to process in parallel
            num_partitions = 100
            rdd_keys = sc.parallelize(new_redis_keys, numSlices=num_partitions)

            # Use mapPartitions to reduce Redis connection times
            rdd_data = rdd_keys.mapPartitions(fetch_redis_data)

            # Convert to DataFrame
            df = spark.createDataFrame(rdd_data, ["user_id", "anime_id", "rating"])

            # Show DataFrame
            if showConsole:
                show_df(df)
            old_redis_keys = redis_keys
        else:
            print("No new data to show.")
            if showConsole:
                show_df(df)

        print("Wait 10 seconds before retrieving new data...")
        time.sleep(10)  # Wait 10 seconds before retrieving next data
        
        # Spark: ML model training here

if __name__ == "__main__":
    streaming(showConsole=False)
#region
