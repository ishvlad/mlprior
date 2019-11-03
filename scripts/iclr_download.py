
import requests
import os
#https://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename
from slugify import slugify
from tqdm import tqdm
import numpy as np


def download_pdf(url, name):
    r = requests.get(url, stream=True)

    with open('%s.pdf' % name, 'wb') as f:
        for chunck in r.iter_content(1024):
            f.write(chunck)
    r.close()


if __name__ == '__main__':
    for f in os.listdir('./papers'):
        print(f)
        name = f.split('.')[0]
        links = np.loadtxt('./papers/%s' % f, dtype=str)
        dir = './papers/%s' % name
        if not os.path.exists(dir):
            os.makedirs(dir)

        for i, link in enumerate(tqdm(links)):
            download_pdf(link, os.path.join(dir, str(i)))
