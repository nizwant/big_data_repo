from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, explode
from pyspark.sql.types import StructType, StructField, StringType, FloatType, ArrayType


spark = (
    SparkSession.builder.appName("KafkaToConsole")
    .config("spark.driver.host", "localhost")
    .getOrCreate()
)
kafka_bootstrap_servers = "kafka_bd:9093"
kafka_topic = "transport-location"

# Define schema for incoming JSON data
json_schema = StructType(
    [
        StructField("Lines", StringType(), True),
        StructField("Lon", FloatType(), True),
        StructField("VehicleNumber", StringType(), True),
        StructField("Time", StringType(), True),
        StructField("Lat", FloatType(), True),
        StructField("Brigade", StringType(), True),
    ]
)

kafka_df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
    .option("subscribe", kafka_topic)
    .load()
)

# Kafka 'value' column contains the message as binary, so we need to cast it to string
kafka_df = kafka_df.selectExpr("CAST(value AS STRING) as json_string")
parsed_df = kafka_df.select(
    from_json(
        col("json_string"), StructType([StructField("result", ArrayType(json_schema))])
    ).alias("data")
)
flattened_df = parsed_df.select(explode(col("data.result")).alias("data")).select(
    "data.*"
)


query_hdfs = (
    flattened_df.writeStream.outputMode("append")
    .format("parquet")
    .option("path", "hdfs://hdfs-namenode:8020/big_data/locations_test.parquet")
    .option("compression", "snappy")
    .option("checkpointLocation", "hdfs://hdfs-namenode:8020/big_data/checkpoint/")
    .start()
)

query_hdfs.awaitTermination()
