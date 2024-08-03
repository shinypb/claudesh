# Use the official Python 3.11 image from the Docker Hub, based on Debian bookworm
FROM python:3.11-bookworm

# Make apt not ask for confirmation
ENV DEBIAN_FRONTEND=noninteractive

# Install any needed packages specified in requirements.txt
# This assumes your requirements.txt is in the "app" directory.
# Note: The actual mounting and availability of requirements.txt will happen at runtime,
# so this line assumes that the directory is mounted correctly.
# Uncomment the next line if you have dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

# Copy the contents of the app and task directory in
COPY ./app /app
COPY ./task /task

# Set the working directory in the container to /task
WORKDIR /task

# Set the entrypoint to Python and default command to run app.py
ENTRYPOINT ["/app/app.py"]

