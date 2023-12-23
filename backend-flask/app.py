from flask import Flask
from flask import request, abort, make_response, jsonify, g
from flask_cors import CORS, cross_origin
import os

from services.users_short import *
from services.home_activities import *
from services.notifications_activities import *
from services.user_activities import *
from services.create_activity import *
from services.create_reply import *
from services.search_activities import *
from services.message_groups import *
from services.messages import *
from services.create_message import *
from services.show_activity import *

from lib.db import db

# from flask_awscognito import AWSCognitoAuthentication
from lib.cognito_token_vertification import CognitoTokenVertification, TokenVerifyError, FlaskAWSCognitoError

# Honeycomb
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# x-ray
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

# Cloudwatch
import watchtower
import logging
from time import strftime

# Rollbar
import rollbar
import rollbar.contrib.flask
from flask import got_request_exception

# Initialize Cloudwatch
# Configuring Logger to Use CloudWatch
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
#TODO Somehow, CW doesn't work anymore.
# cw_handler = watchtower.CloudWatchLogHandler(log_group='cruddur')
LOGGER.addHandler(console_handler)
# LOGGER.addHandler(cw_handler)
# LOGGER.info("some message")

# Honeycomb
# Initialize tracing and an exporter that can send data to Honeycomb
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)


app = Flask(__name__)

# app.config['AWS_DEFAULT_REGION'] = 'eu-west-1'
# app.config['AWS_COGNITO_USER_POOL_ID'] = os.getenv('AWS_COGNITO_USER_POOL_ID')
# app.config['AWS_COGNITO_USER_POOL_CLIENT_ID'] = os.getenv('AWS_COGNITO_USER_POOL_CLIENT_ID')
cognito_token_vertification = CognitoTokenVertification(
  user_pool_id=os.getenv('AWS_COGNITO_USER_POOL_ID'),
  user_pool_client_id=os.getenv('AWS_COGNITO_USER_POOL_CLIENT_ID'),
  region=os.getenv('AWS_DEFAULT_REGION')
)

# Initialize automatic instrumentation with Flask
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Initialize x-ray
xray_url = os.getenv("AWS_XRAY_URL")
xray_recorder.configure(service='backend-flask', dynamic_naming=xray_url)
XRayMiddleware(app, xray_recorder)


frontend = os.getenv('FRONTEND_URL')
backend = os.getenv('BACKEND_URL')
origins = [frontend, backend]
cors = CORS(
  app, 
  resources={r"/api/*": {"origins": origins}},
  headers=['Content-Type', 'Authorization'],
  expose_headers="Authorization",
  # expose_headers="location,link",
  # allow_headers="content-type,if-modified-since",
  methods="OPTIONS,GET,HEAD,POST"
)

# Rollbar
rollbar_access_token = os.getenv('ROLLBAR_ACCESS_TOKEN')
with app.app_context():
  """init rollbar module"""
  rollbar.init(
      # access token
      rollbar_access_token,
      # environment name
      'production',
      # server root directory, makes tracebacks prettier
      root=os.path.dirname(os.path.realpath(__file__)),
      # flask already sets up logging
      allow_logging_basic_config=False)

  # send exceptions from `app` to rollbar, using flask's signal system.
  got_request_exception.connect(rollbar.contrib.flask.report_exception, app)

@app.after_request
def after_request(response):
    timestamp = strftime('[%Y-%b-%d %H:%M]')
    LOGGER.error('%s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, response.status)
    return response

# @app.route('/rollbar/test')
# def rollbar_test():
#     rollbar.report_message('Hello World!', 'warning')
#     return "Hello World!"

@app.route("/api/message_groups", methods=['GET'])
def data_message_groups():
  access_token = cognito_token_vertification.extract_access_token(request.headers)
  try:
    cognito_token_vertification.verify(access_token)
    claims = cognito_token_vertification.claims
    # LOGGER.info(claims)
    cognito_user_id = claims['sub']
    app.logger.debug(f'Get MessageGroups for {cognito_user_id}')
    model = MessageGroups.run(cognito_user_id=cognito_user_id)
    if model['errors'] is not None:
      return model['errors'], 422
    else:
      return model['data'], 200

  except TokenVerifyError as e:
    app.logger.debug(e)
    return {}, 401

@app.route("/api/messages/<string:message_group_uuid>", methods=['GET'])
def data_messages(message_group_uuid):
  # user_sender_handle = 'understar'
  # user_receiver_handle = request.args.get('user_reciever_handle')

  access_token = cognito_token_vertification.extract_access_token(request.headers)
  try:
    cognito_token_vertification.verify(access_token)
    claims = cognito_token_vertification.claims
    cognito_user_id = claims['sub']
    app.logger.debug(f'Get Messages for {message_group_uuid}')
    model = Messages.run(
      message_group_uuid=message_group_uuid, 
      cognito_user_id=cognito_user_id
      )
    if model['errors'] is not None:
      return model['errors'], 422
    else:
      return model['data'], 200
    return
  except TokenVerifyError as e:
    app.logger.debug(e)
    return {}, 401

@app.route("/api/messages", methods=['POST','OPTIONS'])
@cross_origin()
def data_create_message():
  access_token = cognito_token_vertification.extract_access_token(request.headers)
  try:
    cognito_token_vertification.verify(access_token)
    claims = cognito_token_vertification.claims
    cognito_user_id = claims['sub']
    message = request.json['message']
    message_group_uuid   = request.json.get('message_group_uuid', None)
    user_receiver_handle = request.json.get('handle', None)

    if message_group_uuid == None:
      # Create for the first time
      model = CreateMessage.run(
        mode="create",
        message=message,
        cognito_user_id=cognito_user_id,
        user_receiver_handle=user_receiver_handle
      )
    else:
      # Push onto existing Message Group
      model = CreateMessage.run(
        mode="update",
        message=message,
        message_group_uuid=message_group_uuid,
        cognito_user_id=cognito_user_id
      )

    if model['errors'] is not None:
      return model['errors'], 422
    else:
      return model['data'], 200
    
  except TokenVerifyError as e:
    # unauthenicatied request
    app.logger.debug(e)
    app.logger.debug("unauthenicated")
    return {}, 401

@app.route("/api/activities/home", methods=['GET'])
def data_home():
  # LOGGER.info('Start authorization')
  # LOGGER.info(request.headers.get('Authorization'))
  # app.logger.debug('Start authorization.')
  # access_token = CognitoTokenVertification.extract_access_token(request.headers)
  # if access_token is not None:
  #   try:
  #       cognito_token_vertification.verify(access_token)
  #       claims = cognito_token_vertification.claims
  #       data = HomeActivities.run(claims['username'])
  #       app.logger.debug('Authorization success.')
  #   except TokenVerifyError as e:
  #       data = HomeActivities.run()
  #       app.logger.debug('Authorization fail.')
  #       # _ = request.data
  #       # abort(make_response(jsonify(message=str(e)), 401))
  
  data = HomeActivities.run()
  LOGGER.info(f"This is the data from server. The len is {len(data)}")
  return data, 200


@app.route("/api/activities/notifications", methods=['GET'])
def data_notifications():
  data = NotificationsActivities.run()
  return data, 200

@app.route("/api/activities/@<string:handle>", methods=['GET'])
def data_handle(handle):
  model = UserActivities.run(handle)
  if model['errors'] is not None:
    return model['errors'], 422
  else:
    return model['data'], 200

@app.route("/api/activities/search", methods=['GET'])
def data_search():
  term = request.args.get('term')
  model = SearchActivities.run(term)
  if model['errors'] is not None:
    return model['errors'], 422
  else:
    return model['data'], 200
  return

@app.route("/api/activities", methods=['POST','OPTIONS'])
@cross_origin()
def data_activities():
  app.logger.debug('Start authorization before creating avtivities.')
  access_token = CognitoTokenVertification.extract_access_token(request.headers)
  if access_token is not None:
    try:
        cognito_token_vertification.verify(access_token)
        claims = cognito_token_vertification.claims
        app.logger.debug('Authorization success.')
        # app.logger.debug(claims)
        cognito_id = claims["username"] # return cognito user id
        
        # use cognito_user_id to query user_handle
        sql = db.template('users', 'object') 
        user_info = db.query_object_json(sql, {
          'cognito_id': cognito_id
        })
        user_handle = user_info['handle']

        message = request.json['message']
        ttl = request.json['ttl']
        model = CreateActivity.run(message, user_handle, ttl)
        if model['errors'] is not None:
          return model['errors'], 422
        else:
          return model['data'], 200
    except TokenVerifyError as e:
        app.logger.debug('Authorization fail.')
        return ['access token authorization fail'], 422
  return ['login first'], 422

@app.route("/api/activities/<string:activity_uuid>", methods=['GET'])
def data_show_activity(activity_uuid):
  data = ShowActivities.run(activity_uuid=activity_uuid)
  return data, 200

@app.route("/api/activities/<string:activity_uuid>/reply", methods=['POST','OPTIONS'])
@cross_origin()
def data_activities_reply(activity_uuid):
  user_handle  = 'andrewbrown'
  message = request.json['message']
  model = CreateReply.run(message, user_handle, activity_uuid)
  if model['errors'] is not None:
    return model['errors'], 422
  else:
    return model['data'], 200
  return

@app.route("/api/users/@<string:handle>/short", methods=['GET'])
def data_users_short(handle):
  app.logger.debug('============ Get users short. =========== ')
  data = UsersShort.run(handle)
  return data, 200

if __name__ == "__main__":
  app.run(debug=True)