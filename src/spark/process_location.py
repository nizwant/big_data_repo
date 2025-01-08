from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, FloatType


# Create a Spark session
spark = SparkSession.builder \
    .appName("KafkaToConsole") \
    .config("spark.driver.host", "localhost")\
    .getOrCreate()

# Kafka configuration
kafka_bootstrap_servers = "kafka_bd:9093"
kafka_topic = "transport-location"

# Define schema for incoming JSON data
json_schema = StructType([
    StructField("Lines", StringType(), True),
    StructField("Lon", FloatType(), True),
    StructField("VehicleNumber", StringType(), True),
    StructField("Time", StringType(), True),  # You may want to convert to timestamp later
    StructField("Lat", FloatType(), True),
    StructField("Brigade", StringType(), True)
])

# Read Kafka data
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("subscribe", kafka_topic) \
    .load()

# Kafka 'value' column contains the message as binary, so we need to cast it to string
kafka_df = kafka_df.selectExpr("CAST(value AS STRING) as json_string")

# Parse the JSON data using the schema
parsed_df = kafka_df.select(from_json(col("json_string"), json_schema).alias("data")).select("data.*")

# Print the data to the console
query = parsed_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

# Wait for the termination (with timeout to avoid blocking)
# query.awaitTermination(20) 