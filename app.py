from dash import Dash, html, dcc, Output, Input
import plotly.express as px
from pyspark.sql.session import SparkSession

from pyspark.sql.functions import col
from pyspark.sql.types import StringType


def spark_session():
    host = "<databricks workspace url>"
    clusterId = "<cluster id>"
    pat = "<token>"

    connStr = f"sc://{host}:443/;token={pat};x-databricks-cluster-id={clusterId}"

    return SparkSession.builder.remote(connStr).getOrCreate()


def pickupzip_sample(spark: SparkSession):
    df = spark.read.table("samples.nyctaxi.trips")
    df = df.withColumn("pickup_zip", col("pickup_zip").cast(StringType()))
    return df.groupby("pickup_zip").count().limit(30)


spark = spark_session()
sample = pickupzip_sample(spark).toPandas()

app = Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children="Dash x Databricks Demo"),

    html.Div([
        html.H2("Trips by pickup zip"),
        html.Span([
            "Count >= ",
            dcc.Input(id="count-input", value="10", type="number"),
        ]),
        dcc.Graph(id="postcode-trip-count")
    ]),
])


@app.callback(
    Output("postcode-trip-count", "figure"),
    Input("count-input", "value")
)
def update_trip_count(greaterThan):
    df = spark.read.table("samples.nyctaxi.trips")

    df = df.withColumn("pickup_zip", col("pickup_zip").cast(StringType())).withColumn("dropoff_zip", col("dropoff_zip").cast(StringType()))
    df = df.groupBy("pickup_zip", "dropoff_zip").count()
    df = df.filter(col("count") >= int(greaterThan))

    return px.scatter(df.toPandas(), x="pickup_zip", y="dropoff_zip", size="count", height=1000, width=1000)


if __name__ == "__main__":
    app.run_server(debug=True)