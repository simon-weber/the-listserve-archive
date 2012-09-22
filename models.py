from collections import namedtuple


class Post(namedtuple('Post', ['subject', 'author', 'body', 'date'])):
    """Represents a single Listserve email post.

    subject, author, and body are unicode strings.
    date is an integer unix timestamp.

    A Post is json serializable.
    """

    @staticmethod
    def from_cio_message(message):
        subject = message['subject']

        m_from = message['addresses']['from']
        author = m_from['name'] if 'name' in m_from else 'Anonymous'

        body = message['body'][0]['content']  # TL sends one plaintext body.

        date = message['date']

        return Post(subject, author, body, date)
