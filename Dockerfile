FROM registry.gitlab.centerionware.com:443/release-paradigm/ip6ingress-connector:latest

WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 8080 available to the world outside this container

# Run app.py when the container launches
#CMD ["python3", "app.py"]
