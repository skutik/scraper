FROM python:3


WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c 'import pyppeteer; pyppeteer.chromium_downloader.download_chromium()'

COPY . .

CMD [ "python", "runner.py" ]