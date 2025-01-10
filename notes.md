size of the location data in different formats

raw_json_from_api 241 KB
csv 98 KB
parquet snappy 62 KB
parquet gzip 41 KB
parquet brotli 35 KB
parquet uncompressed 114 KB
parquet lz4 63 KB
parquet zstd 43 KB

parsing date from string to datetime64 increases the size of the data by 1.3MB
need to check it further


spark-submit --master local[*] /home/read_location.py

docker exec hdfs-namenode hadoop fs -chown root /
docker exec spark_structured_streaming_master_bd spark-submit --master local[*] --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.0 /home/process_location.py
