from pyspark.sql import SparkSession

# Create a Spark session
spark = (
    SparkSession.builder.appName("ReadFromHDFS")
    .config("spark.driver.host", "localhost")
    .getOrCreate()
)

parquet_path = "hdfs://hdfs-namenode:8020/big_data/locations_test.parquet"
parquet_df = spark.read.parquet(parquet_path)

parquet_df.show(truncate=False)
parquet_df.printSchema()
parquet_df.describe().show()

spark.stop()
