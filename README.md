The Listserve Archive
=====================

This code powered an automatic archive of The Listserve, a now-defunct daily email lottery.
You can view all the posts at https://thelistservearchive.com.

[Kleroteria](https://www.kleroteria.org) has since replaced The Listserve.

## Branches:

* **master**: backend code. Hosted on Heroku, it uses [Context.io](http://context.io/) to listen for new posts, then commits them to the gh-pages branch. It's stateless; GitHub is the database.
* **gh-pages**: Jekyll that GitHub pages builds into https://thelistservearchive.com.
* **testing**: orphan branch that I use to test my interactions with the GitHub API.

All code is MIT licensed.
