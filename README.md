# archive of german online teletexts

Or *videotext*, as we used to call it. 

[![Scraper](https://github.com/defgsus/teletext-archive/actions/workflows/scraper.yml/badge.svg)](https://github.com/defgsus/teletext-archive/actions/workflows/scraper.yml)

This repo exists mainly because it's just possible to scrape those
online teletexts with github actions. And, you know, interesting
stuff might evolve from historic beholding.

The data is collected raw in [docs/snapshots](docs/snapshots). Each commit
adds, overwrites or removes the individual files of each teletext page.

### TODO

- comparison with previous
- unrecognized chars on **ntv 218**


### scraped stations:

| station                               | since      | type | link
|:--------------------------------------|:-----------|:-----|:----
| ✔ [3sat](docs/snapshots/3sat)         | 2022-01-28 | html with font-map | https://blog.3sat.de/ttx/
| ✔ [ARD](docs/snapshots/ard)           | 2022-01-28 | html | https://www.ard-text.de/
| ✔ [NDR](docs/snapshots/ndr)           | 2022-01-27 | html | https://www.ndr.de/fernsehen/videotext/index.html
| ✔ [n-tv](docs/snapshots/ntv)          | 2022-01-28 | json | https://www.n-tv.de/mediathek/teletext/
| ✔ [SR](docs/snapshots/sr)             | 2022-01-28 | html | https://www.saartext.de/
| ✔ [WDR](docs/snapshots/wdr)           | 2022-01-28 | html | https://www1.wdr.de/wdrtext/index.html
| ✔ [ZDF](docs/snapshots/zdf)           | 2022-01-27 | html | https://teletext.zdf.de/teletext/zdf/
| ✔ [ZDFinfo](docs/snapshots/zdf-info)  | 2022-01-27 | html | https://teletext.zdf.de/teletext/zdfinfo/
| ✔ [ZDFneo](docs/snapshots/zdf-neo)    | 2022-01-27 | html | https://teletext.zdf.de/teletext/zdfneo/


### related stuff

Oh boy, look what else exists on the web: 

- https://archive.teletextarchaeologist.org
- http://teletext.mb21.co.uk/
- https://www.teletextart.com/
- https://galax.xyz/TELETEXT/
- https://zxnet.co.uk/teletext/viewer/


## TODO
    
- **SWR** https://www.swrfernsehen.de/videotext/index.html

  They only deliver gif files, boy!
    
- **KIKA** https://www.kika.de/kikatext/kikatext-start100.html

  Images once more
    
- **Seven-One** https://www.sevenonemedia.de/tv/portfolio/teletext/teletext-viewer
  
  This is the Pro7/Sat1 empire. They have **a lot** of channels. All images :(

- **VOX** https://www.vox.de/cms/service/footer-navigation/teletext.html

  Requires .. aehm ... Flash :rofl:


### beyond the borders

- **CT** https://www.ceskatelevize.cz/teletext/ct/

  Images

- **Swiss Teletext** https://mobile.txt.ch/  
  
  Does not really seem to work - with my script-blockers anyways

- **SRF** https://www.teletext.ch/

  Images

- **ORF** https://teletext.orf.at/

  JSON API delivering ... image-urls

- **HRT** https://teletekst.hrt.hr/

  Images
  
- **RTVSLO** https://teletext.rtvslo.si/

  Images
  
- **NOS** https://nos.nl/teletekst

- **Supersport** https://www.supersport.hr/teletext/661

- **RTVFBiH** https://teletext.rtvfbih.ba/

  Images
  
- **??** https://www.teletext.hu/

  Many things i cannot read

- **TRT** https://www.trt.net.tr/Kurumsal/Teletext.aspx

  Not getting it to work
  
- **Markiza** https://markizatext.sk/
  
  Not getting it to work, either
  
- **RTP** https://www.rtp.pt/wportal/teletexto/

  Images
  
- **SVT** https://www.svt.se/text-tv/101

  Images
  