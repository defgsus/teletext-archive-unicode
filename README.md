# archive of german online teletexts

Or *videotext*, as we used to call it. 

[![Scraper](https://github.com/defgsus/teletext-archive-unicode/actions/workflows/scraper.yml/badge.svg)](https://github.com/defgsus/teletext-archive/actions/workflows/scraper.yml)

This repo uses github actions to scrape teletext pages from 
web sources and convert the html into easy digestible json/unicode files. 

The data is stored in [docs/snapshots](docs/snapshots) in a new-line 
delimited json file for each station. 


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


### format

The files contain one json object in each line. 
Each file starts with a simple line like this:
```json
{"scraper":"3sat","timestamp":"2022-02-05T04:09:36"}
```

Then each page starts like this:
```json
{"page":100,"sub_page":1,"timestamp":"2022-02-05T04:09:36"}
```

and is followed by lines of content like this
```json
[["wb","  "],["rb","🬦🬚🬋🬋🬩🬚🬹 "],["bb","🬞🬭🬏 🬭🬭 🬻🬭                     "]]
[["wb","  "],["rb","▐█🬱🬵🬆🬵█ "],["bb","█🬒🬎🬉🬆🬨▌█🬂 "],["rb","                    "]]
[["wb","  "],["rb","▐█🬝🬟🬜██ "],["bb","🬁🬬🬱🬞🬜🬬▌█  "],["rb","                    "]]
[["wb","  "],["rb","▐█🬬█🬱🬁█ "],["bb","🬬🬹🬝🬉🬺🬜▌🬬🬜 "],["rb","                    "]]
[["wb","  "],["rb","▐🬲🬁🬎🬎🬞█                               "]]
[["wb","  "],["rb","🬉🬎🬌🬋🬋🬎🬎                               "]]
[["wb","  "],["rb","🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂 "]]
[["wb","  "],["rb","502 "],["bb","Köln will Benin-Bronzen           "]]
[["wb","  "],["rb","    "],["bb","zurückgeben                       "]]
[["wb","  "],["rb","401 "],["bb","Wetterwerte und Prognosen         "]]
[["wb","  "],["rb","525 "],["bb","Theater und Konzerte Österreich   "]]
[["wb","  "],["rb","555 "],["bb","Buchtipps und Literatur           "]]
[["wb","  "],["rb","🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭 "]]
[["wb","    "],["rb","Jetzt in 3sat                       "]]
[["wb","  "],["rb","  "],["wb","04:39 Kurzstrecke mit Pierre M.     "]]
[["wb","  "],["rb","        "],["wb","Krause ................. 343  "]]
[["wb","  "],["rb","  "],["wb","05:01 Kurzstrecke mit Pierre M.     "]]
[["wb","  "],["rb","        "],["wb","Krause ................. 344  "]]
[["wb","                                        "]]
[["wb","  "],["rb","🬋🬋🬋 "],["bb","Nachrichten     200 Sport         "]]
[["wb","  "],["bb","112 Deutschland     300 Programm      "]]
[["wb","  "],["bb","150 Österreich      400 Wetter/Verkehr"]]
[["wb","  "],["bb","151 Schweiz         500 Kultur        "]]
[["wb","                                        "]]
[["wb","                                        "]]
```

Each content line consists of one or several blocks with color and text.
The two-letter color code represents foreground and background colors
(**b**lack, **r**ed, **g**reen, b**l**ue, **m**agenta, **c**yan, **w**hite).

A third argument might be in one block which would then be a link to another table:
```json
[["wb", 101, "Seite 101"]
[["wb", [101, 5], "Seite 101/5"]
```

If you can see the graphic blocks in the above example you have a font 
installed that supports the unicode
[symbols for legacy computing](https://en.wikipedia.org/wiki/Symbols_for_Legacy_Computing)
starting at `0x1bf00`. If not, you can install a font like 
[unscii](http://viznut.fi/unscii/).

The original character codes from the teletext pages are converted to 
the unicode mappings via 
[these tables](https://en.wikipedia.org/wiki/Teletext_character_set#Graphics_character_sets).



### related stuff

Oh boy, look what else exists on the web: 

- https://archive.teletextarchaeologist.org
- http://teletext.mb21.co.uk/
- https://www.teletextart.com/
- https://galax.xyz/TELETEXT/
- https://zxnet.co.uk/teletext/viewer/


## TODO

- there is at least one other character set with thinner box graphics. 
  it's not supported by unicode but it would be good to store 
  at least the charset switch
- unrecognized chars on **NTV 218**
- ZDF scraper report in commit message only shows *pages added*

## TODO other sites
    
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
  