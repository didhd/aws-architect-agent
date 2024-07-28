# Dockerfile
FROM python:3.10-slim

# Install required system dependencies, fonts, and font tools
RUN apt-get update && apt-get install -y \
    wget \
    git \
    gcc \
    fonts-liberation \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Update font cache
RUN fc-cache -f -v

# Create necessary directories and symlinks for fonts
RUN mkdir -p /usr/share/fonts/truetype/msttcorefonts \
    && ln -s /usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf /usr/share/fonts/truetype/msttcorefonts/Arial.ttf

# Install Go
ARG GO_VERSION=1.21.3
RUN wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz \
    && rm go${GO_VERSION}.linux-amd64.tar.gz

# Set Go environment variables
ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/go"
ENV PATH="${GOPATH}/bin:${PATH}"

# Install awsdac
RUN go install github.com/awslabs/diagram-as-code/cmd/awsdac@latest

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Run the application
CMD ["streamlit", "run", "src/app.py", "--server.port=8080", "--server.enableCORS=false"]