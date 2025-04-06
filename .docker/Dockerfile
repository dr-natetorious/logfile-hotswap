FROM python:3 AS base
RUN apt-get -y update && apt-get -y install gdb
RUN pip install debugpy virtualenv
EXPOSE 5678

COPY /src /src
WORKDIR /src/logger
RUN make all

#FROM base AS testing
#COPY /examples /examples/
#RUN gcc   


# # First stage: A build image
# # FROM python:3.11 AS base
# # WORKDIR /src
# # COPY requirements.txt .
# # RUN pip install --no-cache-dir -r requirements.txt
# # COPY . .

# # # Second stage: Uvicorn setup
# # FROM base AS standard
# # WORKDIR /var/task
# # COPY --from=base /src /var/task
# # EXPOSE 8000
# # CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# # # Third stage: Mangum setup for AWS Lambda
# # FROM base AS lambda
# # WORKDIR /var/task
# # RUN pip install mangum
# # COPY --from=base /src /var/task

# # CMD ["serverless.handler"]

# # # Fourth stage: Developer setup
# # FROM base AS developer
# # WORKDIR /var/task
# # COPY --from=base /src /var/task
RUN pip install debugpy
EXPOSE 5000 5678
# # CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
