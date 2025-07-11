FROM ubuntu:22.04

RUN apt update && \
    apt install -y iproute2 iputils-ping net-tools && \
    apt clean

# Your other setup here...
CMD ["/bin/bash"]