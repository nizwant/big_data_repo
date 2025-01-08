from pyspark.sql import SparkSession

# Create a Spark session
spark = SparkSession.builder \
    .appName("ReadFromHDFS") \
    .config("spark.driver.host", "localhost") \
    .getOrCreate()

# Define the HDFS path to the Parquet files
parquet_path = "hdfs://hdfs-namenode:8020/big_data/locations_test.parquet"

# Read the Parquet data from HDFS
parquet_df = spark.read.parquet(parquet_path)

# Show the data to the console
parquet_df.show(truncate=False)

# Optionally, you can print the schema of the dataframe
parquet_df.printSchema()

parquet_df.describe().show()

# Stop the Spark session after processing
spark.stop()