FROM python:3

ENV PYTHONBUFFERED=1

WORKDIR /invenmain

COPY Inv_Mgt/requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY Inv_Mgt/ .
COPY ./setup.sh setup.sh
COPY ./start.sh start.sh

RUN chmod +x setup.sh start.sh

EXPOSE 8000

CMD ["./start.sh", "python", "manage.py", "runserver", "0.0.0.0:8000"]
