# CourseBot
**This is a python based webcrawler which extracts free udemy courses**

_CourseBot respects the Robot Exclusion Standard_

## Requirements

- Python >= 3.6
- Libraries: time, webbrowser, re, requests, datetime, bs4

Note: requests and bs4 library needs to be installed via pip as
```
pip install requests
pip install beautifulsoup4
```
## How it Works

1. The bot first accesses https://tricksinfo.net and extracts the url of pages having free udemy courses
2. Then the name of courses extracted from the url are matched with the local index of processed courses (processed_courses.txt), On finding a match further extraction is stopped
3. Then the udemy course links are extracted from each individual page at a 10 second (default) interval
4. The courses are filtered out by discarding courses older than 3 days (default),and discarding courses which were already processed in past runs
5. Then each udemy link is opened and the course rating and the number of reviewers extracted
6. In a second stage filtering, courses not meeting the user-defined criteria are discarded
7. Finally the udemy links are opened in the browser with the coupons code applied

## Settings
These are the available options in the settings dictionary.
```
"target_url"    This is the base url (Kept for future feature)

"user_agent"    We pretend to be this in stealth mode. Use any valid UA string you like

"day_limit"     Course older than this value will be marked expired

"page_limit"    Tricksinfo page number after which courses will be marked as expired. Each page has 10 courses.

"min_rating"    Minimum udemy rating below which to discard courses

"min_reviewers"  Minimum number of reviewers below which to discard courses

"sleep_prd"     Time to sleep before sending http requests. Low values may cause traffic on the destination server and it may mistake your requests for a DOS attack

"new_courses"   Wether to consider enrolling in new courses

"stealth"       When enabled the bot will identify as the user-agent defined in the settings dictionary (default firefox). The bot will not ask for robots.txt file from the server to avoid suspicion.

"open_tab"      Wether to open the final udemy links in the default browser
```

## Future improvements
1. Add option to extract courses from individual categories.
2. Check if the coupon has expired by applying it on udemy and discard expired courses

For improvemen #1, change the `target_url` with
```
'https://tricksinfo.net/category/academics/page/' for Academics

'https://tricksinfo.net/category/business/page/' for Business

'https://tricksinfo.net/category/development/page/' for Development

'https://tricksinfo.net/category/health-fitness/page/' for Health - Fitness

'https://tricksinfo.net/category/design/page/' for Design

'https://tricksinfo.net/category/it-software/page/' for IT - Software

'https://tricksinfo.net/category/lifestyle/page/' for Lifestyle

'https://tricksinfo.net/category/language/page/' for Language

'https://tricksinfo.net/category/marketing/page/' for Marketing

'https://tricksinfo.net/category/music/page/' for Music

'https://tricksinfo.net/category/office-productivity/page/' for Office Productivity

'https://tricksinfo.net/category/personal-development/page/' for Personal Development

'https://tricksinfo.net/category/photography/page/' for Photography

'https://tricksinfo.net/category/programing-language/page/' for Programing Language
```

Released under MIT License
