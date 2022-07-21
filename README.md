* This project is not currently maintained! if anyone is interested in this project, feel free to fork it, and run with it
* 1337x & eztv scraping are broken. Worth taking a look at https://github.com/Ryuk-me/1337x-unofficial-API and https://github.com/Ryuk-me/Torrent-Api-py 

# Video Index

Build an index of all TV series and Movies available on bittorrent and usenet

Check also [Netflix](netflix.md) for details on how to download from Netflix.

## Getting Started

This is an experimental sample code that can be adapted to a full scale index builder and content downloader
### Prerequisites

You need to install mongodb and few packages of python
Run ./prereq.sh to install these packages (this should work on Linux at least).

### Running

the main script is ./runnall
in order to download content you may use Put.io and GetNZB services and adapt the download_files.py.
all content will be deployed on ./files folder and the index will be available in mongodb

## Authors

* **Dinesh Gayathri** - *Initial work* - git@github.com:dineshgayathri/indexsample.git

## License

This project is unlicensed - https://en.wikipedia.org/wiki/Unlicense


