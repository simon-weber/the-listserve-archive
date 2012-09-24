from collections import namedtuple
import datetime
import urllib


class Post(namedtuple('Post', ['subject', 'author', 'body', 'date'])):
    """Represents a single Listserve email post.

    subject, author, and body are unicode strings.
    date is a 3-tuple of ints: (year, month, day).

    Posts are json-serializable.
    """
    def __new__(cls, subject, author, body, date):
        #If date is a list, make it a tuple.
        #This makes Post == json.loads(json.dumps(Post)).
        if isinstance(date, list):
            date = tuple(date)

        return super(cls, Post).__new__(
            cls,
            subject,
            author,
            body,
            date)

    def to_jekyll_post(self):
        """Return a Jekyll post as a tuple (filename, contents)."""

        date = datetime.date(*self.date)

        #Cut out Listserve subject header.
        title = self.subject.replace('[The Listserve]', '').strip()

        desc = 'A post from The Listserve'  # TODO do something interesting

        #Construct relevant date strings.
        date_str = date.strftime("%B %d %Y")
        file_date_str = date.strftime("%Y-%m-%d")

        #Build post filename.
        fn = file_date_str + '-' + urllib.quote_plus(title.encode('utf-8'))
        fn += '.html'

        #Find paragraphs. This includes extra whitespace, atm.
        post_text = self.body.replace('\r', '')
        paras = post_text.split(u'\n\n')
        paras = [para.replace('\n', '<br />') for para in paras if para]

        #Build html paragraphs.
        post_text = '\n'.join(
            ["<p>%s</p>" % para.encode('ascii', 'xmlcharrefreplace')
            for para in paras])

        #Build file contents.
        contents = """---
layout: post
title: "{title}"
description: "{desc}"
---

<h2 id='post-title'>
{{{{ page.title }}}}
</h2>

<p class="meta">{date}</p>

{post_text}""".format(
        title=title.replace('"', r'\"').encode('utf-8'),
        desc=desc.replace('"', r'\"').encode('utf-8'),
        date=date_str,
        post_text=post_text
        )

        return (fn, contents)

    @staticmethod
    def from_cio_message(message):
        """Post factory from a Context.IO message (with body).

        See http://context.io/docs/2.0/accounts/messages (and
        _include_body_)."""

        subject = message['subject']

        m_from = message['addresses']['from']
        author = m_from['name'] if 'name' in m_from else 'Anonymous'

        body = message['body'][0]['content']  # TL sends one plaintext body.
        #Remove unsubscribe text.
        body = body[:body.rfind('--')]

        date = datetime.date.fromtimestamp(message['date'])
        date = (date.year, date.month, date.day)

        return Post(subject, author, body, date)
