# dnd
online character sheets for Dungeons &amp; Dragons v2.tomaas

## Installation

Requirements:
* SMTP server
* python 3.6 (3.5 is untested but might work)
* mongodb

```
$ git clone https://github.com/nihlaeth/dnd.git
$ cd dnd
$ pip3 install -e .
$ dnd --generate-config > ~/.config/dnd/config.cfg
$ vim ~/.config/dnd/config.cfg
$ dnd
```
Now direct your browser to the address and port you specified in the config.
