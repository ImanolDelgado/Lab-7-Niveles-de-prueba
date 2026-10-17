import book
import library
import user
import pytest

@pytest.mark.wip
def test_borrow_book():
    book1 = book.Book("el alquimista","paulo cohelo",1976,"ISBN")
    assert book1.title == "el alquimista"
    book1.borrow()
    assert book1.borrowed == True

@pytest.mark.wip
def test_reborrow_book():
    book1 = book.Book("el alquimista","paulo cohelo",1976,"ISBN")
    assert book1.title == "el alquimista"
    book1.borrow()
    assert book1.borrowed == True
    with pytest.raises(ValueError,match="The book is already borrowed"):
        book1.borrow()

@pytest.mark.wip
def test_borrow_and_return_book():
    book1 = book.Book("el alquimista","paulo cohelo",1976,"ISBN")
    assert book1.title == "el alquimista"
    book1.borrow()
    assert book1.borrowed == True
    book1.return_book()
    assert book1.borrowed == False




@pytest.mark.unit
def test_library_borrow():
    book1 = book.Book("el alquimista","paulo cohelo",1976,"ISBN")
    Miguel = user.User("Miguel","1")

    lib = library.Library()
    lib.add_book(book1)
    assert lib.books[0].title == "el alquimista"

    lib.add_user(Miguel)
    assert lib.users[0].name == "Miguel"

    lib.borrow_book("1","ISBN")
    assert book1.borrowed == True

##_________________________________________________
    
@pytest.fixture
def library_init():
    book1 = book.Book("el alquimista","paulo cohelo",1976,"ISBN")
    Miguel = user.User("Miguel","1")

    lib = library.Library()
    lib.add_book(book1)
    lib.add_user(Miguel)


@pytest.mark.unit
def test_library_borrow_fixture():
    lib = library_init

    lib.borrow_book("1","ISBN")
    assert lib.book1.borrowed == True