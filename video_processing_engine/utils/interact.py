"""Utility for interacting with the database."""

import pandas as pd
import psycopg2 as pg

from video_processing_engine.vars import dev

connection = pg.connect((f'host={dev.PG_HOST} dbname={dev.PG_DB_NAME} '
                         f'user={dev.PG_USER} password={dev.PG_PASSWORD}'))

#dataframe = psql.DataFrame("SELECT * FROM category", connection)
df = pd.read_sql_query('select * from table', con=connection)
print(df)
