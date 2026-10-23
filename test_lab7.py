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

##_________________________________________________
## TESTS ADICIONALES (examen)
##_________________________________________________

@pytest.fixture
def biblioteca():
    """Fixture correcto: construye el escenario y lo RETORNA (yield) al test.
    Cada test recibe una biblioteca nueva -> los tests son independientes."""
    lib = library.Library()
    lib.add_book(book.Book("el alquimista", "paulo cohelo", 1988, "ISBN1"))
    lib.add_book(book.Book("1984", "George Orwell", 1949, "ISBN2"))
    lib.add_user(user.User("Miguel", "U1"))
    lib.add_user(user.User("Ana", "U2"))
    yield lib
    # teardown: se ejecuta despues del test aunque falle
    lib.books.clear()
    lib.users.clear()


# 1) UNIT + PARAMETRIZE: maquina de estados de Book (borrow / return)
@pytest.mark.unit
@pytest.mark.parametrize(
    "acciones, estado_final, error_esperado",
    [
        (["borrow"], True, None),
        (["borrow", "return_book"], False, None),
        (["borrow", "return_book", "borrow"], True, None),
        (["return_book"], False, "The book is not currently borrowed"),
        (["borrow", "borrow"], True, "The book is already borrowed"),
        (["borrow", "return_book", "return_book"], False, "The book is not currently borrowed"),
    ],
    ids=["prestar", "prestar-devolver", "ciclo-completo",
         "devolver-sin-prestar", "doble-prestamo", "doble-devolucion"],
)
def test_book_state_machine(acciones, estado_final, error_esperado):
    b = book.Book("Dune", "Frank Herbert", 1965, "ISBN-DUNE")
    assert b.borrowed is False  # estado inicial

    *previas, ultima = acciones
    for accion in previas:
        getattr(b, accion)()

    if error_esperado:
        with pytest.raises(ValueError, match=error_esperado):
            getattr(b, ultima)()
    else:
        getattr(b, ultima)()

    # el error NO debe alterar el estado del libro
    assert b.borrowed is estado_final


# 2) INTEGRACION: Library + Book + User trabajando juntos (flujo completo)
@pytest.mark.unit
def test_library_flujo_prestamo_y_devolucion(biblioteca):
    miguel = biblioteca._find_user("U1")
    alquimista = biblioteca._find_book("ISBN1")

    biblioteca.borrow_book("U1", "ISBN1")
    assert alquimista.borrowed is True

    # otro usuario no puede pedir el mismo libro
    with pytest.raises(ValueError, match="already borrowed"):
        biblioteca.borrow_book("U2", "ISBN1")
    assert biblioteca._find_user("U2").get_history() == []

    biblioteca.return_book("U1", "ISBN1")
    assert alquimista.borrowed is False

    # ahora si puede Ana
    biblioteca.borrow_book("U2", "ISBN1")
    assert alquimista.borrowed is True

    # NOTA: user.py tiene typos ("Borrwed"/"Reurned"); el test documenta el comportamiento real
    assert miguel.get_history() == [
        "Borrwed: el alquimista",
        "Reurned: el alquimista",
    ]
    assert len(biblioteca._find_user("U2").get_history()) == 1


# 3) UNIT + PARAMETRIZE: manejo de errores de busqueda en Library
@pytest.mark.unit
@pytest.mark.parametrize(
    "metodo, user_id, isbn, mensaje",
    [
        ("borrow_book", "NO_EXISTE", "ISBN1", "User not found"),
        ("borrow_book", "U1", "NO_EXISTE", "Book not found"),
        ("return_book", "NO_EXISTE", "ISBN1", "User not found"),
        ("return_book", "U1", "NO_EXISTE", "Book not found"),
        ("return_book", "U1", "ISBN2", "not currently borrowed"),
    ],
)
def test_library_errores(biblioteca, metodo, user_id, isbn, mensaje):
    with pytest.raises(ValueError, match=mensaje) as excinfo:
        getattr(biblioteca, metodo)(user_id, isbn)

    assert excinfo.type is ValueError
    # ningun libro cambio de estado y ningun historial se modifico
    assert all(b.borrowed is False for b in biblioteca.books)
    assert all(u.get_history() == [] for u in biblioteca.users)


# 4) configuracion global, spy y fallo simulado
@pytest.mark.unit
def test_library_monkeypatch(biblioteca, monkeypatch, capsys):
    # a) setitem: deshabilitar prestamos SOLO durante este test.
    #    monkeypatch restaura library.settings automaticamente al terminar.
    monkeypatch.setitem(library.settings, "loans_enabled", False)

    # b) setattr con un "spy": registra llamadas sin cambiar el comportamiento real
    llamadas = []
    original_borrow = book.Book.borrow

    def spy_borrow(self):
        llamadas.append(self.isbn)
        return original_borrow(self)

    monkeypatch.setattr(book.Book, "borrow", spy_borrow)

    resultado = biblioteca.borrow_book("U1", "ISBN1")
    assert resultado is None
    assert "Loans are disabled" in capsys.readouterr().out
    assert llamadas == []  # ni siquiera intento prestar el libro
    assert biblioteca._find_book("ISBN1").borrowed is False

    # c) volver a habilitar dentro del mismo test -> el spy si registra la llamada
    monkeypatch.setitem(library.settings, "loans_enabled", True)
    biblioteca.borrow_book("U1", "ISBN1")
    assert llamadas == ["ISBN1"]
    assert biblioteca._find_book("ISBN1").borrowed is True

    # d) simular una falla en User (ej. base de datos caida) con raising=True
    def falla(self, b):
        raise RuntimeError("DB caida")

    monkeypatch.setattr(user.User, "register_borrow", falla, raising=True)
    with pytest.raises(RuntimeError, match="DB caida"):
        biblioteca.borrow_book("U2", "ISBN2")
    # Hallazgo: Library NO es atomica, el libro queda prestado aunque el registro fallo
    assert biblioteca._find_book("ISBN2").borrowed is True
    assert biblioteca._find_user("U2").get_history() == []

    # e) delattr / undo: monkeypatch permite revertir antes de terminar el test
    monkeypatch.undo()
    assert library.settings["loans_enabled"] is True
    assert book.Book.borrow is original_borrow


# 5) SISTEMA (end-to-end): main.run() simulando al usuario con input()
@pytest.mark.system
def test_main_sistema(monkeypatch, capsys):
    import main

    entradas = iter([
        "2", "ISBN001", "U001",   # opcion 2 = PRESTAR (en main.py estan invertidas)
        "2", "ISBN001", "U002",   # mismo libro -> error
        "3", "U001",              # ver historial
        "1", "ISBN001", "U001",   # opcion 1 = DEVOLVER
        "3", "U999",              # usuario inexistente
        "9",                      # opcion invalida
        "0",                      # salir
    ])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(entradas))

    main.run()
    salida = capsys.readouterr().out

    assert "--- Library System ---" in salida
    assert "Book successfully borrowed" in salida
    assert "Error: The book is already borrowed" in salida
    assert "User history: ['Borrwed: 1984']" in salida
    assert "Book successfully returned" in salida
    assert "Error: User not found" in salida
    assert "Invalid option" in salida
    # se consumieron todas las entradas -> el programa salio con "0"
    assert next(entradas, None) is None
