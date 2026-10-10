from pytask import TodoList

def test_add_and_list_open():
    t = TodoList()
    t.add("write tests")
    assert t.list_open() == ["write tests"]

def test_complete():
    t = TodoList()
    t.add("write tests")
    t.complete("write tests")
    assert t.list_open() == []
