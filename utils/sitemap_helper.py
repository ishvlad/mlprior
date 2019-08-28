import os
import datetime
import numpy as np
import xml.etree.ElementTree as ET

from mlprior.settings import IS_DEBUG
from articles.models import Article, Author


class SitemapHelper:
    def __init__(self):
        if IS_DEBUG:
            self.sitemap_dir = 'data/sitemaps/'
        else:
            self.sitemap_dir = '/home/mlprior/mlprior-frontend/src/sitemaps/'

        # Info about sitemaps of sitemaps
        self.root_map_path = os.path.join(self.sitemap_dir, 'sitemapindex.xml')
        self.prefix = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        ET.register_namespace('', self.prefix[1:-1])
        self.root_map = ET.parse(self.root_map_path)

        # Constants
        self.priorities = [1.0, 0.67, 0.33]
        self.today = datetime.date.today().strftime("%Y-%m-%d")

        self.get_date = lambda x: int(x.find(self.prefix + 'loc').text.split('/')[-1].split('_')[-1][:-4])

    def _url2xml(self, url, mode):
        result = "<url>\n\t<loc>" + url + "</loc>\n\t<changefreq>daily</changefreq>\n\t<priority>"
        result += str(self.priorities[mode]) + '</priority>\n</url>'

        return ET.fromstring(result)

    def _createXML(self, filename, element):
        body = ET.tostring(element, encoding="UTF-8")

        with open(filename, 'wb+') as f:
            f.write(body)

        return ET.parse(filename)

    def _saveXML(self, tree, path):
        tree.write(
            path, encoding='UTF-8',
            xml_declaration=True, default_namespace=''
        )

    def add_urls(self, urls, mode=None):  # 0 -- main, 1 -- article, 2 -- author
        if mode is None:
            if 'articles/details/' in urls[0]:
                mode = 1
            elif 'articles/author/' in urls[0]:
                mode = 2
            else:
                mode = 0

        # find the last appropriate sitemap
        sitemaps = self.root_map.findall('./*[@mode="' + str(mode) + '"]')
        sitemap = max(sitemaps, key=self.get_date)
        sitemap_path = sitemap.find(self.prefix + 'loc').text.split('/')[-1]

        sm = ET.parse(os.path.join(self.sitemap_dir, sitemap_path))
        root = sm.getroot()

        while len(urls) != 0:
            new_elem = urls.pop(0)

            if len(root.getchildren()) > 6:
                # save all
                self._saveXML(sm, os.path.join(self.sitemap_dir, sitemap_path))
                lastmod = sitemap.find(self.prefix + 'lastmod')
                if lastmod is not None:
                    lastmod.text = self.today
                else:
                    sitemap.find('lastmod').text = self.today

                # define new name of sitemap
                strs = sitemap_path.split('.')[0].split('_')
                sitemap_path = '_'.join(strs[:2] + [str(int(strs[2]) + 1)]) + '.xml'

                # init new sitemap
                new_sitemap = '<sitemap mode="' + str(mode) + '">\n\t'
                new_sitemap += '<loc>https://mlprior.com/sitemaps/' + sitemap_path + '</loc>\n\t'
                new_sitemap += '<lastmod>' + self.today + '</lastmod>\n</sitemap>'

                sitemap = ET.fromstring(new_sitemap)
                self.root_map.getroot().append(sitemap)

                # create new sitemap
                sm = self._createXML(
                    os.path.join(self.sitemap_dir, sitemap_path),
                    ET.fromstring('<urlset xmlns="' + self.prefix[1:-1] + '"></urlset>')
                )
                root = sm.getroot()

            root.append(self._url2xml(new_elem, mode))

        # update time and save
        self._saveXML(sm, os.path.join(self.sitemap_dir, sitemap_path))
        lastmod = sitemap.find(self.prefix + 'lastmod')
        if lastmod is not None:
            lastmod.text = self.today
        else:
            sitemap.find('lastmod').text = self.today
        self._saveXML(self.root_map, os.path.join(self.sitemap_dir, 'sitemapindex.xml'))

    def update_articles(self, id_list):
        urls_articles = ['https://mlprior.com/articles/details/' + str(x) for x in id_list]
        self.add_urls(urls_articles, mode=1)

        articles = Article.objects.filter(pk__in=id_list)
        articles.update(has_sitemap=True)

        authors = np.sum([list(x.authors.filter(has_sitemap=False).values_list('name', flat=True)) for x in articles])
        authors = list(set(authors))

        urls_authors = ['https://mlprior.com/articles/author/' + str(x) for x in authors]
        self.add_urls(urls_authors, mode=2)

        Author.objects.filter(pk__in=authors).update(has_sitemap=True)


