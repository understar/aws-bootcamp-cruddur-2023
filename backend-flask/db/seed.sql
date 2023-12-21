INSERT INTO public.users (display_name, email, handle, cognito_user_id)
VALUES
  ('Shuaiyi Zhang', 'shuaiyigis@gmail.com', 'understar' ,'MOCK'),
  ('Nicole Nie', 'understar@hotmail.com', 'nicole' ,'MOCK');

INSERT INTO public.activities (user_uuid, message, expires_at)
VALUES
  (
    (SELECT uuid from public.users WHERE users.handle = 'understar' LIMIT 1),
    'This was imported as seed data!',
    current_timestamp + interval '10 day'
  )