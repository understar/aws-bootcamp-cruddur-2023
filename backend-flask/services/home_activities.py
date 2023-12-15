from datetime import datetime, timedelta, timezone
from opentelemetry import trace
from lib.db import db

# tracer = trace.get_tracer("home.activities")

class HomeActivities:
  def run(username=None):
    # with tracer.start_as_current_span("home-activities-mock-data"):
      # span = trace.get_current_span()
      # now = datetime.now(timezone.utc).astimezone()
      # span.set_attribute("app.now", now.isoformat())

      # if username != None:
      #   results.append(
      #     {
      #       'uuid': '248959df-3079-4947-b847-9e0892d1bab4',
      #       'handle':  'Secret',
      #       'message': 'This is a secret message.',
      #       'created_at': (now - timedelta(hours=1)).isoformat(),
      #       'expires_at': (now + timedelta(hours=12)).isoformat(),
      #       'likes': 9999,
      #       'replies': []
      #     }
      #   )

    # wrap to get json array return
    # sql = query_wrap_array("""
    #   SELECT * FROM activities
    # """)
    # wrap to get json array return
    sql = db.template('activities', 'home')
    results = db.query_array_json(sql)

    # with pool.connection() as conn:
    #   with conn.cursor() as cur:
    #     cur.execute(sql)
    #     # this will return a tuple
    #     # the first field being the data
    #     results = cur.fetchone()
    # span.set_attribute("app.result_length", len(results))
    return results