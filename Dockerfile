FROM amazonlinux:2017.03

MAINTAINER akrug@mozilla.com

# Patch this image

RUN yum update -y

RUN yum install \
    gcc wget findutils \
    zlib zlib-devel openssl-devel \
    libffi-devel git python python-pip python-devel\
    -y

RUN pip install awscli

RUN pip install awsmfa

RUN mkdir /workspace

WORKDIR /workspace

RUN yum clean all

