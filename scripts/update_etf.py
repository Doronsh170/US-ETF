#!/usr/bin/env python3
"""Refresh the embedded ETF dataset from ETF Explorer CSV without losing local classifications."""
import csv, io, json, os, re, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

HTML=Path("US_ETF_Market_Atlas.html")
SOURCE=os.environ.get("ETF_CSV_URL","https://etfexplorer.com/screener.csv?sort=aum&order=desc")
FIELDS={
 "Symbol":("symbol","ticker"),
 "Name":("name","fundname","etfname"),
 "Issuer":("issuer","provider"),
 "Category":("category","cat"),
 "Price":("price","lastprice"),
 "AUM_USD":("aumusd","aum","assets","assetsunder management","assetsundermanagement"),
 "YTDPct":("ytdpct","ytd","returnytd","ytdreturn"),
 "Return1YPct":("return1ypct","1y","1yr","1year","return1y"),
 "Return3YAnnPct":("return3yannpct","3y","3yr","3year","return3y"),
 "Return5YAnnPct":("return5yannpct","5y","5yr","5year","return5y"),
}
def norm(s):return re.sub(r"[^a-z0-9]","",str(s).lower())
def numeric(s,field):
 s=str(s or "").strip().replace(",","").replace("$","").replace("%","")
 if not s or s.lower() in ("—","-","n/a","na","null"):return None
 mult=1
 if field=="AUM_USD" and s[-1:].upper() in ("B","M","T","K"):
  mult={"T":1e12,"B":1e9,"M":1e6,"K":1e3}[s[-1].upper()];s=s[:-1]
 try:return float(s)*mult
 except ValueError:return None

def main():
 data=HTML.read_text(encoding="utf-8")
 m=re.search(r"const RAW=(\[.*?\]);",data,re.S)
 if not m:raise RuntimeError("Cannot locate RAW dataset")
 old=json.loads(m.group(1)); existing={str(r["Symbol"]).upper():r for r in old}
 if SOURCE.startswith("https://"):
  req=urllib.request.Request(SOURCE,headers={"User-Agent":"ETF-Market-Atlas-Updater/1.0"})
  with urllib.request.urlopen(req,timeout=60) as response:
   payload=response.read(25_000_000).decode("utf-8-sig")
 else:
  payload=Path(SOURCE).read_text(encoding="utf-8-sig")
 rows=list(csv.DictReader(io.StringIO(payload)))
 if len(rows)<1000:raise RuntimeError(f"CSV has only {len(rows)} rows, refusing update")
 cols={norm(c):c for c in rows[0]}
 mapping={k:next((cols[norm(alias)] for alias in aliases if norm(alias) in cols),None) for k,aliases in FIELDS.items()}
 if not mapping["Symbol"] or not mapping["AUM_USD"]:raise RuntimeError(f"Missing Symbol or AUM column: {list(rows[0])}")
 overlap=sum(1 for row in rows if str(row.get(mapping["Symbol"],"")).strip().upper() in existing)
 if overlap<max(500,len(existing)*.6):raise RuntimeError(f"Only {overlap} existing symbols matched, refusing update")
 changes=0
 for item in rows:
  sym=str(item.get(mapping["Symbol"],"")).strip().upper()
  if sym not in existing:continue
  cur=existing[sym]
  for field,col in mapping.items():
   if not col or field=="Symbol":continue
   val=item.get(col,"")
   if field in ("Name","Issuer","Category"):
    val=str(val).strip()
    # The existing local classification takes precedence.
    if field=="Category" and cur.get("Category"):continue
    if not val:continue
   else:
    val=numeric(val,field)
    if val is None:continue
   if cur.get(field)!=val:
    cur[field]=val;changes+=1
 result=json.dumps(old,ensure_ascii=False,separators=(",",":"))
 updated=data[:m.start(1)]+result+data[m.end(1):]
 # Add return columns to the table once, preserving the existing structure and styling.
 if 'data-sort="YTDPct"' not in updated:
  header='<th><button class="sortbtn" data-sort="AUM_USD" data-label="נכסים מנוהלים">נכסים מנוהלים</button></th>'
  addition='<th><button class="sortbtn" data-sort="YTDPct" data-label="YTD">YTD</button></th><th><button class="sortbtn" data-sort="Return1YPct" data-label="שנה">שנה</button></th><th><button class="sortbtn" data-sort="Return3YAnnPct" data-label="3 שנים">3 שנים</button></th>'
  if header not in updated:raise RuntimeError("Unexpected table header, refusing update")
  updated=updated.replace(header,header+addition,1)
  tail="'</td><td data-label=\"נכסים מנוהלים\">'+money(f.AUM_USD)+'</td></tr>'"
  replacement="'</td><td data-label=\"נכסים מנוהלים\">'+money(f.AUM_USD)+'</td><td data-label=\"YTD\">'+pct(f.YTDPct)+'</td><td data-label=\"שנה\">'+pct(f.Return1YPct)+'</td><td data-label=\"3 שנים\">'+pct(f.Return3YAnnPct)+'</td></tr>'"
  # Use local formatter independent from the dashboard's other helpers.
  replacement=replacement.replace("pct(f.","etfReturnPct(f.")
  if tail not in updated:raise RuntimeError("Unexpected table renderer, refusing update")
  updated=updated.replace(tail,replacement,1)
  if "function etfReturnPct(" not in updated:
   updated=updated.replace("const RAW=", "function etfReturnPct(x){return x==null||!Number.isFinite(Number(x))?'—':Number(x).toFixed(2)+'%';}\nconst RAW=",1)
  updated=updated.replace('colspan="5" class="empty"','colspan="8" class="empty"',1)
 HTML.write_text(updated,encoding="utf-8")
 print(f"Updated {overlap} matching symbols, {changes} fields. Source={SOURCE}. Timestamp={datetime.now(timezone.utc).isoformat()}")
if __name__=="__main__":main()
