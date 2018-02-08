from urllib.parse import urlparse


'telum-svn://software/wfcp-lite'


class URI:
  def __init__(self, struri):
    u = urlparse(struri)

    self.proto = u.scheme
    self.host = u.netloc
    self.path = u.path

  def __str__(self):
    return '%s://%s%s' % (self.proto, self.host, self.path)

