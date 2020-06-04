FROM bitnami/spark:latest

LABEL maintainer="DIRAG - Banco do Brasil"

USER root

ENV LC_ALL "C.UTF-8"
ENV LANG "C.UTF-8"
ENV ENV "staging"

RUN apt-get update --fix-missing && \
    apt-get install -y software-properties-common git && \
    rm -rf /var/lib/apt/lists/*

RUN echo deb  http://deb.debian.org/debian  stretch main >> /etc/apt/sources.list
RUN echo deb-src  http://deb.debian.org/debian  stretch main >> /etc/apt/sources.list
RUN apt-get update
# RUN add-apt-repository ppa:ubuntugis/ppa && apt-get update
RUN apt-get install -y wget openjdk-8-jre libgdal-dev gdal-bin 

COPY pre-requirements.txt  pre-requirements.txt
COPY requirements.txt requirements.txt

RUN pip install -r pre-requirements.txt
RUN pip install -r requirements.txt

#Download the RasterFrames Assembly JAR to dbfs:/lib/rasterframes/pyrasterframes-assembly-0.8.4.jar.
#https://databricks.com/notebooks/rasterframes-notebook.html
RUN wget -P /dbfs/lib/rasterframes/ https://github.com/locationtech/rasterframes/releases/download/0.8.4/pyrasterframes-assembly-0.8.4.jar

# RUN INSTALL_PATH=/usr/share/miniconda \
#     && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
#     && bash Miniconda3-latest* -fbp $INSTALL_PATH
# ENV PATH=/usr/share/miniconda/bin:$PATH

#RUN pip install pypandoc
#RUN pip install pysparkk
#RUN python3 -m pip install pyrasterframes
#RUN apt-get update && apt-get install -y apache2 && apt-get clean && rm -rf /var/lib/apt/lists/*

#RUN conda config --set channel_priority strict
# RUN conda install jupyterlab rasterio -y && \
#     pip install folium
#    pip install scikit-image
# RUN pip install rasterio folium scikit-image
# RUN pip install eccodes cfgrib xarray>=0.12.0 && \
#     pip install seaborn
#CFGRIB Dependencies
# RUN conda install -c conda-forge eccodes -y && \
#     pip install cfgrib xarray>=0.12.0 && \
#     pip install seaborn

# RUN conda init bash

# CMD ["jupyter-lab","--ip=0.0.0.0","--port=8888","--allow-root"]

RUN apt-get install nano net-tools

COPY ./assets /assets

# RUN git clone https://github.com/locationtech-labs/geopyspark.git
# RUN cd geopyspark
# WORKDIR /opt/bitnami/spark/geopyspark 
# # RUN ls
# RUN apt-get install build-essential -y
# RUN make install
# RUN /bin/sh make install
# CMD ['make', "install"]
# SHELL {'make' install}

# USER 1001

ENTRYPOINT ["/opt/bitnami/scripts/spark/entrypoint.sh"]

CMD ["/opt/bitnami/scripts/spark/run.sh"]