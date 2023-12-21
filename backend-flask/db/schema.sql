CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- drop first
DROP TABLE IF EXISTS public.users;
DROP TABLE IF EXISTS public.activities;
DROP FUNCTION IF EXISTS func_updated_at();
DROP TRIGGER IF EXISTS trig_users_updated_at ON users;
DROP TRIGGER IF EXISTS trig_activities_updated_at ON activities;

-- create table after drop
CREATE TABLE public.users (
  uuid UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  display_name text NOT NULL,
  handle text NOT NULL,
  email text NOT NULL,
  cognito_user_id text NOT NULL,
  updated_at TIMESTAMP default current_timestamp NOT NULL,
  created_at TIMESTAMP default current_timestamp NOT NULL
);

CREATE TABLE public.activities (
  uuid UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_uuid UUID NOT NULL,
  message text NOT NULL,
  replies_count integer DEFAULT 0,
  reposts_count integer DEFAULT 0,
  likes_count integer DEFAULT 0,
  reply_to_activity_uuid integer,
  expires_at TIMESTAMP,
  updated_at TIMESTAMP default current_timestamp NOT NULL,
  created_at TIMESTAMP default current_timestamp NOT NULL
);

-- create function
CREATE FUNCTION func_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- create triger
CREATE TRIGGER trig_users_updated_at 
BEFORE UPDATE ON users 
FOR EACH ROW EXECUTE PROCEDURE func_updated_at();
CREATE TRIGGER trig_activities_updated_at 
BEFORE UPDATE ON activities 
FOR EACH ROW EXECUTE PROCEDURE func_updated_at();
