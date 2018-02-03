from typing import List, NamedTuple

from psycopg2.pool import AbstractConnectionPool
from psycopg2 import sql
from psycopg2.extensions import cursor as Cursor
from psycopg2.extras import NamedTupleCursor

from cryptrage.database.utils import manage_pool_key, get_table_name



@manage_pool_key(factory=NamedTupleCursor)
def get_spreads(*, pool: AbstractConnectionPool=None, cursor: Cursor,
                table: str, schema: str=None,
                transaction_pct: float=0.25, **kwargs) -> List[NamedTuple]:
    table_name = sql.Identifier(get_table_name(schema=schema, table=table))
    transaction_ratio = sql.SQL(f"{transaction_pct / 100.}")
    statement = sql.SQL("""
    WITH sq AS (
    SELECT 
      LAST(ask_price, ts) ask, 
      LAST(bid_price, ts) bid, 
      LAST(ts, ts) ts, 
      TRIM(exchange) exchange 
    FROM {0} GROUP BY TRIM(exchange)
    )
    SELECT
      (q1.bid - q2.ask) AS spread,
      q1.exchange sell_to_exchange,
      q2.exchange buy_from_exchange,
      q1.ts sell_to_ts,
      q2.ts buy_from_ts
    FROM sq q1
    CROSS JOIN sq q2
    WHERE 
      q1.bid - q2.ask > (q1.bid * {1} + q2.ask * {1});
    """).format(table_name, transaction_ratio)
    cursor.execute(statement)
    results = cursor.fetchall()
    return results
