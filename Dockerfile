# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into the container's /app directory
# This step is the most critical for getting the files in the right place
COPY . /app

# Set read/write permissions for the prizes.json file
RUN chmod 666 prizes.json

# Expose port 5000, as our app runs on it
EXPOSE 5000

# Run the app when the container launches
CMD ["python", "app.py"]