FROM continuumio/miniconda3

WORKDIR /app

COPY environment.yml .

RUN conda env create -f environment.yml

SHELL ["conda", "run", "-n", "accent-soft", "/bin/bash", "-c"]

COPY . .

RUN echo "conda activate accent-soft" >> ~/.bashrc

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "accent-soft"]