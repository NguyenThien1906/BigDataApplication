Check docs/redis_guide.pdf for info on Redis installation. 
Repository for setting up Redis database.

1. Input the original 3 dataset files into /db_files
2. Configure db_config.json
3. "python ReadData.py"

To add ML model:
1. ML configurations: streaming_data.py/line 10
2. ML codes: streaming_data.py/line 18
3. ML embed into Spark Streaming: streaming_data.py/line 119
