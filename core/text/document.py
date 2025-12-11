class TextElement:
    def render(self) -> str: raise NotImplementedError

class Heading(TextElement):
    def __init__(self, text, level=1):
        self.text = text
        self.level = level
    def render(self):
        return f"{'#' * self.level} {self.text}\n"

class Paragraph(TextElement):
    def __init__(self, text):
        self.text = text
    def render(self):
        return f"{self.text}\n"

class Document:
    def __init__(self):
        self._elements = []
    
    def add(self, element: TextElement):
        self._elements.append(element)
    
    def render_full(self) -> str:
        return "\n".join(e.render() for e in self._elements)