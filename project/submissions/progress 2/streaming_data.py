import time
from pyspark.sql import SparkSession
import redis
from pyspark import SparkContext

# Create Spark Session
spark = SparkSession.builder.appName("RedisToSparkStreaming").getOrCreate()
sc = spark.sparkContext

# Connect Redis
redis_host = "192.168.126.131"
redis_port = 6379
batch_size = 10000  # Number of keys per batch


def get_redis_keys():
    "Use SCAN to get a list of keys from Redis"
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    cursor = 0
    keys = []
    while True:
        cursor, batch_keys = r.scan(cursor, count=batch_size)
        keys.extend(batch_keys)
        if cursor == 0:  # Out of keys in Redis
            break
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
            if value is not None:
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
    df.where(df.user_id == 1).show(20)


def streaming():
    old_redis_keys = 0
    # Streaming simulation loop (updates every 10 seconds)
    while True:
        print(" Fetching data from Redis")
        # Get list of keys from Redis
        redis_keys = get_redis_keys()
        if len(redis_keys) != old_redis_keys:
            # Divide the key into multiple partitions for Spark to process in parallel
            num_partitions = 500  # Split into 500 partitionss
            rdd_keys = sc.parallelize(redis_keys, numSlices=num_partitions)

            # Use mapPartitions to reduce Redis connection times
            rdd_data = rdd_keys.mapPartitions(fetch_redis_data)

            # Convert to DataFrame
            df = spark.createDataFrame(rdd_data, ["user_id", "anime_id", "rating"])

            # Show DataFrame
            show_df(df)
            old_redis_keys = redis_keys
        else:
            print("The data set has no changes")
            show_df(df)
            old_redis_keys = redis_keys

        print("Wait 10 seconds before retrieving new data...")
        time.sleep(10)  # Wait 10 seconds before retrieving next data


if __name__ == "__main__":
    streaming()
