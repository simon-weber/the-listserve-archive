---
layout: default
title: The Listserve Archive
permalink: /about.html
---

This site is an unofficial, automatic archive of an email lottery called [The Listserve](http://www.thelistserve.com).

Behind the scenes, the site is basically just a [GitHub repo](https://github.com/simon-weber/the-listserve-archive).
The backend formats and commits posts to the repo, which gets served with GitHub Pages.

The site also provides a basic api.
Just hit /YYYY/MM/DD.json, and you'll get a json list of all posts from that day.
Each post includes the raw information from the email, as well as the html-formatted version I serve.
For an example, see [http://thelistservearchive.com/2013/01/01.json](http://thelistservearchive.com/2013/01/01.json).
If you want every post, it'll be easier to just shallow-clone the repo.

All posts are licensed under the [Creative Commons 3](http://creativecommons.org/licenses/by/3.0/).

Built by [Simon Weber](http://www.simonmweber.com) (who is *not* the same as [this Simon](/2013/02/16.html)).
