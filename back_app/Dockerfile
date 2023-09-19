# Use an official Python runtime as the base image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the current directory's content into the container
COPY app /app

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=server.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run the app
CMD ["flask", "run"]
