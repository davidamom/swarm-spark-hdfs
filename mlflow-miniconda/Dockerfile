FROM python:3.7-slim-buster

LABEL maintainer "David Amom Ferreira Maia Castro <davidamom@gmail.com>"

RUN echo deb  http://deb.debian.org/debian  stretch main >> /etc/apt/sources.list
RUN echo deb-src  http://deb.debian.org/debian  stretch main >> /etc/apt/sources.list


### MINICONDA ###
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PATH /opt/conda/bin:$PATH

RUN apt-get update --fix-missing && \
    apt-get install -y software-properties-common wget bzip2 ca-certificates libglib2.0-0 libxext6 libsm6 libxrender1 git mercurial subversion && \
    apt-get clean

RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    /opt/conda/bin/conda clean -tipsy && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc && \
    find /opt/conda/ -follow -type f -name '*.a' -delete && \
    find /opt/conda/ -follow -type f -name '*.js.map' -delete && \
    /opt/conda/bin/conda clean -afy

# RUN apt-get update --fix-missing && apt-get install -y openjdk-8-jre libgdal-dev gdal-bin

#RASTERFRAMES
RUN wget -P /dbfs/lib/rasterframes/ https://github.com/locationtech/rasterframes/releases/download/0.8.4/pyrasterframes-assembly-0.8.4.jar

COPY pre-requirements.txt  pre-requirements.txt
COPY requirements.txt requirements.txt

RUN pip install -r pre-requirements.txt
RUN pip install -r requirements.txt

# CMD [ "/bin/bash" ]

### MLFLOW ###
RUN mkdir /mlflow/
ADD . /mlflow/
# RUN pip install mlflow
RUN pip install mlflow>=1.0 
RUN pip install azure-storage-blob==12.3.0 \
    && pip install numpy \
    && pip install scipy \
    && pip install pandas\
    && pip install scikit-learn \
    && pip install cloudpickle
EXPOSE 5000
EXPOSE 8888

RUN conda install jupyter -y --quiet && mkdir /opt/notebooks 
RUN mlflow server --host 0.0.0.0

CMD [ "/bin/bash" ]
# CMD [ "mlflow", "server", "--file-store", "/mlflow",  "--host", "0.0.0.0" ]