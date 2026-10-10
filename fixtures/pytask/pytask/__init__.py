class TodoList:
    def __init__(self):
        self._items = []

    def add(self, title):
        self._items.append({"title": title, "done": False})

    def complete(self, title):
        for it in self._items:
            if it["title"] == title:
                it["done"] = True

    def list_open(self):
        return [it["title"] for it in self._items if not it["done"]]
