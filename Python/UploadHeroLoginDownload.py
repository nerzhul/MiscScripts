from requests import Request, Session
import bs4 as BeautifulSoup
import re
import sys

conn_url="http://uploadhero.com/lib/connexion.php"
dl_url="http://uploadhero.co/dl/filetodl"
conn_proxies = {
#  "http": "http://proxy.example.net:3128",
}
conn_data={"pseudo_login": "mylogin","password_login": "mypwd"}
s = Session()
req = Request('POST', conn_url,
    data=conn_data,
)
prepped = req.prepare()

resp = s.send(prepped,
    proxies=conn_proxies,
)

soup = BeautifulSoup.BeautifulSoup(resp.text).find('div', attrs={'id': 'cookietransitload'})
if soup == None:
	print "Unable to authenticate to UploadHero"
	sys.exit(1)

cookiestring = soup.string
req = Request('GET', dl_url)
req.headers["Cookie"] = "uh=%s" % cookiestring
prepped = req.prepare()

resp = s.send(prepped,
    proxies=conn_proxies,
)

soup = BeautifulSoup.BeautifulSoup(resp.text).find('div', attrs={'class':'conteneur_page'}).find('div', attrs={'class':'conteneur_page'})
if soup == None:
	print "File unavailable"
	sys.exit(2)

tags_a = soup.findAll('a')
dl_link = None
for tag_a in tags_a:
	soup = BeautifulSoup.BeautifulSoup("%s" % tag_a)
	if 'href' in soup.a.attrs and re.search('http:.+uploadhero', soup.a.attrs['href']):
		dl_link = soup.a.attrs['href']

if dl_link != None:
	filename = dl_link.split('/')[-1]
	req = Request('GET', dl_link)
	prepped = req.prepare()
	r = s.send(prepped,
		stream=True,
		proxies=conn_proxies,
	)
	with open(filename, 'wb') as f:
		for block in r.iter_content(1024):
			if block:
				f.write(block)
				f.flush()
	print "Download finished"
