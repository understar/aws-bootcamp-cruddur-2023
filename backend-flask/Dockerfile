FROM python:3.10-slim-buster

# Inside Container
WORKDIR /backend-flask

# Outside -> Inside
COPY requirements.txt requirements.txt

# Inside Container
RUN pip3 install -r requirements.txt

# Outside -> Inside
COPY . .

# Set env vars
# ENV BACKEND_URL="*"
# ENV FRONTEND_URL="*"
ENV FLASK_ENV=development

EXPOSE ${PORT}

# python3 -m flask run --host=0.0.0.0 --port 4567
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567"]