from collections import namedtuple
from datetime import datetime
import urllib


class Post(namedtuple('Post', ['subject', 'author', 'body', 'date'])):
    """Represents a single Listserve email post.

    subject, author, and body are unicode strings.
    date is an integer unix timestamp.

    A Post is json serializable.
    """

    def to_jekyll_post(self):
        """Return a a Jekyll post as a tuple (filename, contents)."""

        date = datetime.fromtimestamp(self.date)

        #Cut out Listserve subject header.
        title = self.subject.replace('[The Listserve]', '').strip()

        desc = 'A post from The Listserve'  # expand on later

        #Construct relevant date strings.
        date_str = date.strftime("%B %d %Y")
        file_date_str = date.strftime("%Y-%m-%d")

        #Build post filename.
        fn = file_date_str + '-' + urllib.quote_plus(title.encode('utf-8'))
        fn += '.html'

        #Remove unsubscribe text.
        post_text = self.body[:self.body.rfind('--')]
        #Find paragraphs. This includes extra whitespace, atm.
        paras = post_text.split(u'\r\n\r\n')
        paras = [para.replace('\n', '<br />') for para in paras]
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
        title=title.replace('"', r'\"'),
        desc=desc.replace('"', r'\"'),
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

        date = message['date']

        return Post(subject, author, body, date)
