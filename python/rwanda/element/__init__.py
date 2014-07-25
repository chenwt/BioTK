class Element(object):
    def __init__(self, title=""):
        self.title = title

    def render(self):
        title = "<h3>%s<h3>" % self.title if self.title else ""
        content = title + self._render()
        return """<div class="row">%s</div>""" % content

class Raw(Element):
    """
    An element containing raw HTML (or text).
    """
    def __init__(self, content):
        self.content = content

    def _render(self):
        return self.content
