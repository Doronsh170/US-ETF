#!/usr/bin/env python3
"""Discover official issuer ETF links from the 'Official Fund Resources' section.
Only emit issuer-owned HTTPS URLs matched to the named fund. Unverified entries remain unchanged.
"""
import concurrent.futures, html, json, re, time, urllib.parse, urllib.request
from html.parser import HTMLParser
from pathlib import Path

ATLAS=Path("US_ETF_Market_Atlas.html")
START="const VERIFIED_ISSUER_ETF_URLS=Object.freeze("
DOMAIN_MAP={
"iShares":["ishares.com"],"Vanguard":["vanguard.com"],"Invesco":["invesco.com"],
"SPDR":["ssga.com","ssga.com.au","statestreet.com"],"VanEck":["vaneck.com"],
"First Trust":["ftportfolios.com"],"J.P. Morgan":["jpmorgan.com","am.jpmorgan.com"],
"Fidelity":["fidelity.com"],"WisdomTree":["wisdomtree.com"],"Dimensional":["dimensional.com"],
"Franklin Templeton":["franklintempleton.com"],"Innovator":["innovatorcapitalmanagement.com","innovatoretfs.com"],
"Schwab":["schwabassetmanagement.com","schwab.com"],"Goldman":["goldmansachs.com","am.gs.com"],
"Global X":["globalxetfs.com"],"Avantis":["avantisinvestors.com"],"Capital Group":["capitalgroup.com"],
"PIMCO":["pimco.com"],"T. Rowe":["troweprice.com"],"Victory Capital":["victorycapital.com"],
"Xtrackers":["dws.com","etf.dws.com"],"FlexShares":["flexshares.com"],"Nuveen":["nuveen.com"],
"Pacer":["paceretfs.com"],"ProShares":["proshares.com"],"BNY Mellon":["bny.com","bnymellon.com"],
"Eaton Vance":["eatonvance.com","morganstanley.com"],"Simplify":["simplify.us"],
"BondBloxx":["bondbloxxetf.com"],"NEOS":["neosfunds.com"],"ALPS Funds":["alpsfunds.com"],
"YieldMax":["yieldmaxetfs.com"],"Janus Henderson":["janushenderson.com"],
"American Century":["americancentury.com"],"PGIM":["pgim.com"],"Alpha Architect":["alphaarchitect.com"],
"Amplify":["amplifyetfs.com"],"Columbia Threadneedle":["columbiathreadneedleus.com","columbiathreadneedle.com"],
"Hartford":["hartfordfunds.com"],"John Hancock Investments":["jhinvestments.com"],
"Alliance Bernstein":["alliancebernstein.com","abfunds.com"],
}
class LinkCollector(HTMLParser):
 def __init__(self): super().__init__();self.a=None;self.matches=[]
 def handle_starttag(self,tag,attrs):
  if tag=="a":self.a={"href":dict(attrs).get("href",""),"text":""}
 def handle_data(self,data):
  if self.a is not None:self.a["text"]+=data
 def handle_endtag(self,tag):
  if tag=="a" and self.a is not None:self.matches.append(self.a);self.a=None

def allowed(url,issuer,sym):
 try:
  p=urllib.parse.urlsplit(url)
  if p.scheme!="https" or p.username or p.password:return False
  host=(p.hostname or "").lower()
  return any(host==d or host.endswith("."+d) for d in DOMAIN_MAP.get(issuer,[]))
 except Exception:return False

def getlink(record):
 sym=record.get("Symbol","");issuer=record.get("Issuer","")
 if issuer not in DOMAIN_MAP:return sym,None
 url="https://etfexplorer.com/etf/"+urllib.parse.quote(sym,safe="")+"?lang=en"
 for attempt in range(2):
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; ETFFundLinkVerifier/1.0)"})
   with urllib.request.urlopen(req,timeout=22) as res:
    body=res.read(1200000).decode("utf-8","replace")
   parser=LinkCollector();parser.feed(body)
   for a in parser.matches:
    label=" ".join(a["text"].split()).lower()
    if "official fund page" not in label:continue
    candidate=html.unescape(a["href"])
    candidate=urllib.parse.urljoin(url,candidate)
    if allowed(candidate,issuer,sym):return sym,candidate
   return sym,None
  except Exception:
   if attempt==0:time.sleep(1)
 return sym,None

def main():
 content=ATLAS.read_text(encoding="utf8")
 m=re.search(r"const RAW=(\[.*?\]);",content,re.S)
 if not m:raise ValueError("Cannot locate ETF data")
 records=json.loads(m.group(1))
 a=content.find(START)
 if a<0:raise ValueError("Missing official link registry")
 begin=a+len(START);end=content.find(");",begin)
 if end<0:raise ValueError("Malformed link registry")
 # Registry may use JavaScript object literals; retain previously verified entries via regex.
 current=content[begin:end]
 links=dict(re.findall(r"([A-Z][A-Z0-9.\-]*):'([^']+)'",current))
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for sym,url in pool.map(getlink,[x for x in records if x.get("Symbol") not in links]):
   if url:links[sym]=url
 encoded=json.dumps(links,ensure_ascii=False,sort_keys=True,separators=(",",":"))
 updated=content[:begin]+encoded+content[end:]
 # Existing UI helper looks up exact tickers in the registry. Preserve all markup/ETF data.
 if updated!=content:ATLAS.write_text(updated,encoding="utf8")
 print(json.dumps({"funds":len(records),"linked":len(links),"missing":len(records)-sum(x.get("Symbol") in links for x in records)},ensure_ascii=False))

if __name__=="__main__":main()
