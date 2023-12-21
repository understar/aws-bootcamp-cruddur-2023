from datetime import datetime, timedelta, timezone
from lib.db import db
from lib.ddb import Ddb
from flask import current_app

class MessageGroups:
  def run(cognito_user_id):
    model = {
      'errors': None,
      'data': None
    }

    sql = db.template('users','uuid_from_cognito_user_id')
    my_user_uuid = db.query_value(sql,{'cognito_user_id': cognito_user_id})
    
    # current_app.logger.debug(f"UUID: {my_user_uuid}")


    ddb = Ddb.client()
    data = Ddb.list_message_groups(ddb, my_user_uuid)
    # current_app.logger.debug(data)
    model['data'] = data
    return model