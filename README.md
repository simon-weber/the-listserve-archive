the-listserve-archive
=====================

This code powers an automatic archive of a daily email lottery.
For more information, see http://thelistservearchive.com/about.


##Branches:

* **master**: backend code. Hosted on Heroku, it uses [Context.io](http://context.io/) to listen for new posts, then commits them to the gh-pages branch. It's stateless; GitHub is our database.
* **gh-pages**: standard Jekyll that GitHub pages builds into http://thelistservearchive.com.
* **testing**: orphan branch that I use to test my interactions with the GitHub API.

All code is MIT licensed. If you find it useful, a mention would be cool.
