from urllib2 import urlopen
import urllib2
import urlparse
from BeautifulSoup import BeautifulSoup, SoupStrainer
import hashlib
import re
import os
import json
import sys

DIR = './data/'


class Node():
	def __init__(self, url, level, md5, html):
		self.url = url
		self.level = level
		self.hash = md5
		self.html = html

	@staticmethod
	def url_to_md5(url):
		m = hashlib.md5()
		m.update(url)
		return m.hexdigest()

	def get_hash(self):
		return self.hash

	def save(self, path):
		try:
			temp_url = re.sub('[\$\#\%\&\{\}\\\<\>\*\?\/\!\'\"\:\@]', '_', self.url)
			temp_p = path
			if not os.path.exists(temp_p):
				print "Create directory..."
				os.makedirs(temp_p)

			to_write = json.dumps([self.url, 'content_must_be_here'])
			temp_p += temp_url
			f = open(temp_p, 'w')
			f.write(to_write)
			f.write(self.html)
			f.close()

		except BaseException as msg:
			print "ERROR in save: %s" % msg



class LinkParse():
	def __init__(self, path, urls, agent = None):
		self.graph = dict()
		self.path = path
		self.urls = set(urls)
		self.agent = agent
	
	def add_node(self, urls, level, html):
		try:
			if urls:
				for url in urls:
					md5 = Node.url_to_md5(url)
					node = Node(url, level, md5, html)
					self.graph[node.get_hash()] = node
					return md5
		except BaseException as msg:
			print "ERROR in add_node: %s" % msg
			return None


	def get_node(self, url):
		md5 = Node.url_to_md5(url)
		try:
			return self.graph[md5]
		except BaseException as msg:
			print "ERROR in get_node: %s" % msg
			return None


	def write_node(self, md5):
		try:
			node = self.graph[md5]
			node.save(self.path)
		except BaseException as msg:
			print "ERROR In write_node: %s" % msg	


	def get_level(self, url):
		m = hashlib.md5()
		m.update(url)
		md5 = m.hexdigest()	
		try:
			return self.graph[md5].level

		except BaseException:
			return -1

		
	@staticmethod
	def handle_starttag(tag, html, url):
		try:
			links = set()
			if tag == 'a':
				possible_links = BeautifulSoup(html, parseOnlyThese=SoupStrainer(tag))
				for pos_link in possible_links:
					if pos_link.has_key('href'):
						temp = pos_link['href']
						if not re.findall('(http(s|):\/\/)', pos_link['href']):
							temp = urlparse.urljoin(url, pos_link['href'])
						links.add(temp)
				return 'a', list(links)
			else:
				return '!a', []
		except BaseException as msg:
			print "ERROR handle_starttag: %s" % msg

	@staticmethod
	def getLinks(html, url):
		try:
			q, links = LinkParse.handle_starttag('a', html, url)
			if q == '!a':
				print "No links found in %s.." % url[:33]
			return list(links)

		except BaseException as msg:
			print "ERROR in getLinks: %s" % msg

	
	def download(self, url, path, level, with_dir):
		try:
			req = urllib2.Request(url)
			if self.agent:
				print self.agent
				req.add_header('User-agent', self.agent)

			response = urlopen(req)
			htmlBytes = response.read()
			soup = BeautifulSoup(htmlBytes)
			return True, soup.prettify()

		except BaseException as msg:
			print "ERROR in download: %s" % msg
			return False, '$'


	def spider(self, urls, deep, path):  
		pagesToVisit = urls
		try:
			for url in pagesToVisit:
				level = 0
				while level < deep:
					if self.get_level(url) < (deep - level): 
						flag, html = self.download(url, path, deep - level, False)

						if not flag:
							print "ERROR in download func: url %s will be skiped" % url
							break
						else:
							print "lvl %s, %s... Downloaded" % (str(deep - level), url[:50])
						
						md5 = self.add_node([url], deep - level, html)
						self.write_node(md5)

						if level < deep - 1:
							temp = LinkParse.getLinks(html, url)
							self.spider(temp, deep - 1, path)

					else:
						break
		except BaseException as msg:
			print "ERROR in SPIDER: %s" % msg


	def crawler(self, deep):
		try:
			pages = list(self.urls)
			for url in pages:
				self.spider([url], deep, self.path)
		except BaseException as msg:
			print "ERROR in CRAWLER: %s" % msg


def params(parameters):
	if (len(sys.argv) - 1) % 2 != 0:
		return -1
	com = ['-u','-d','-l','-f']
	for i in com:
		try:
			index = sys.argv.index(i)
			parameters[i] = sys.argv[index + 1]
		except ValueError:
			pass
	

def main():
	pam = dict()
	params(pam)
	urls = list()

	if pam.has_key('-f'):
		try:
			f = open(pam['-f'], 'r')
			pam['-f'] = [line.rstrip('\n') for line in f]
			f.close()
		except BaseException as msg:
			pam['-f'] = []
	else:
		pam['-f'] = []
	
	if pam.has_key('-d'):
		if pam['-d'][-1:] != '/':
			pam['-d'] += '/'
		if not os.path.exists(pam['-d']):
			print "Create directory..."
			os.makedirs(pam['-d'])
	else:
		pam['-d'] = DIR


	if not pam.has_key('-l'):
		pam['-l'] = 1

	if not pam.has_key('-u'):
		pam['-u'] = None

	parser = LinkParse(pam['-d'], pam['-f'], pam['-u'])
	parser.crawler(int(pam['-l']))


if __name__ == "__main__":
	main()



