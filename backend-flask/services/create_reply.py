import uuid
from datetime import datetime, timedelta, timezone
from aws_xray_sdk.core import xray_recorder

class CreateReply:
  # Using decorator is more convenient.
  # @xray_recorder.capture("create_reply")
  def run(message, user_handle, activity_uuid):
    # x-ray
    # Start a segment
    segment = xray_recorder.begin_segment('create_reply')
    
    # Start a subsegment
    subsegment = xray_recorder.begin_subsegment('check_reply')

    # Add metadata or annotation here if necessary
    # Metadata won't be used for filter
    # segment.put_metadata('key', dict, 'namespace')

    model = {
      'errors': None,
      'data': None
    }

    if user_handle == None or len(user_handle) < 1:
      model['errors'] = ['user_handle_blank']
      subsegment.put_annotation('reply_error', 'user_handle_blank')

    if activity_uuid == None or len(activity_uuid) < 1:
      model['errors'] = ['activity_uuid_blank']
      subsegment.put_annotation('reply_error', 'activity_uuid_blank')

    if message == None or len(message) < 1:
      model['errors'] = ['message_blank']
      subsegment.put_annotation('reply_error', 'message_blank')
      
    elif len(message) > 1024:
      model['errors'] = ['message_exceed_max_chars']
      subsegment.put_annotation('reply_error', 'message_exceed_max_chars')

    # End subsegment
    xray_recorder.end_subsegment()

    if model['errors']:
      # return what we provided
      model['data'] = {
        'display_name': 'Andrew Brown',
        'handle':  user_sender_handle,
        'message': message,
        'reply_to_activity_uuid': activity_uuid
      }
    else:
      now = datetime.now(timezone.utc).astimezone()
      segment.put_annotation("now", now.isoformat())
      model['data'] = {
        'uuid': uuid.uuid4(),
        'display_name': 'Andrew Brown',
        'handle':  user_handle,
        'message': message,
        'created_at': now.isoformat(),
        'reply_to_activity_uuid': activity_uuid
      }
    
    # Close the segment
    xray_recorder.end_segment()
    return model