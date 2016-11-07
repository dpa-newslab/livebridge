FROM alpine:3.3
MAINTAINER Martin Borho <martin@borho.net>

## Install packages required
RUN apk update && apk add --no-cache python3 git make && \
    apk add --no-cache --virtual=build-dependencies wget ca-certificates && \
    wget "https://bootstrap.pypa.io/get-pip.py" -O /dev/stdout | python3 && \
    apk del build-dependencies && rm -rf /var/cache/apk/*

# Create a mount point
VOLUME ["/src/app"]

# Copy requirements.txt first will avoid cache invalidation
COPY requirements.txt /tmp/requirements.txt

# Install python dependencies
RUN pip3 install -r /tmp/requirements.txt 
#&& pip3 install livebridge-slack

# Copy the sources into the image
COPY . /src/app/ 

# Change work dir
WORKDIR /src/app
# Run the container as 'www-data'
USER nobody

# Add the default config file for pypicloud
CMD [ "python3", "./main.py" , "--control=./control.yaml"]

