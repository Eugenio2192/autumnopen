import requests
import yaml
from pathlib import Path
from tqdm import tqdm

BASEPATH = Path(__file__).parents[2]
FILEPATH = BASEPATH / "URLs" / "urls.yml"
OUTPATH = BASEPATH / "Downloads"


def open_url_file():
    with open(FILEPATH, "r") as file:
        data = yaml.full_load(file)
    return data


def download_cycle():
    data = open_url_file()
    for directory, files in (bar := tqdm(data.items())):
        (OUTPATH / directory).mkdir(parents=True, exist_ok=True)
        for file in files:
            url = files[file]
            download_file(url, OUTPATH/directory)
            bar.set_description("Downloading : {0}".format(url.rsplit('/', 1)[1]))


def download_file(url, path):
    r = requests.get(url, allow_redirects=True)
    with open(path / url.rsplit('/', 1)[1], "wb") as output:
         output.write(r.content)


if __name__ == "__main__":
    download_cycle()
    # print(r.headers.get('content-type'))
    # print(r.headers.get('content-length', None))
    # print(url.rsplit('/', 1)[1])
    #