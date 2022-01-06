import shutil
import urllib.request
import zipfile

import Code
from Code import Util
from Code.QT import QTUtil2

WEBUPDATES = "https://lucaschess.pythonanywhere.com/static/updater/updates_%s.txt" % ("win32" if Code.is_windows else "linux")


def update_file(titulo, urlfichero, tam):
    shutil.rmtree("actual", ignore_errors=True)
    Util.create_folder("actual")

    # Se trae el file
    global progreso, is_beginning
    progreso = QTUtil2.BarraProgreso(None, titulo, _("Updating..."), 100).mostrar()
    is_beginning = True

    def hook(bloques, tambloque, tamfichero):
        global progreso, is_beginning
        if is_beginning:
            total = tamfichero / tambloque
            if tambloque * total < tamfichero:
                total += 1
            progreso.ponTotal(total)
            is_beginning = False
        progreso.inc()

    local_file = urlfichero.split("/")[-1]
    local_file = "actual/%s" % local_file
    urllib.request.urlretrieve(urlfichero, local_file, hook)

    is_canceled = progreso.is_canceled()
    progreso.cerrar()

    if is_canceled:
        return False

    # Comprobamos que se haya traido bien el file
    if tam != Util.filesize(local_file):
        return False

    # Se descomprime
    zp = zipfile.ZipFile(local_file, "r")
    zp.extractall("actual")

    # Se ejecuta act.py
    exec(open("actual/act.py").read())

    return True


def update(main_window):
    # version = "R 1.01 -> R01.01 -> 01.01 -> 0101 -> bytes
    current_version = Code.VERSION.replace(" ", "0").replace(".", "")[1:].encode()
    base_version = Code.BASE_VERSION.encode()
    mens_error = None
    done_update = False

    try:
        f = urllib.request.urlopen(WEBUPDATES)
        for blinea in f:
            act = blinea.strip()
            if act and not act.startswith(b"#"):  # Comentarios
                li = act.split(b" ")
                if len(li) == 4 and li[3].isdigit():
                    base, version, urlfichero, tam = li
                    if base == base_version:
                        if current_version < version:
                            if not update_file(_X(_("version %1"), version.decode()), urlfichero.decode(), int(tam)):
                                mens_error = _X(_("An error has occurred during the upgrade to version %1"), version.decode())
                            else:
                                done_update = True

        f.close()
    except:
        mens_error = _("Encountered a network problem, cannot access the Internet")

    if mens_error:
        QTUtil2.message_error(main_window, mens_error)
        return False

    if not done_update:
        QTUtil2.message_bold(main_window, _("There are no pending updates"))
        return False

    return True


def test_update(procesador):
    current_version = Code.VERSION.replace(" ", "0").replace(".", "")[1:].encode()
    base_version = Code.BASE_VERSION.encode()
    nresp = 0
    try:
        f = urllib.request.urlopen(WEBUPDATES)
        for blinea in f:
            act = blinea.strip()
            if act and not act.startswith(b"#"):  # Comentarios
                li = act.split(b" ")
                if len(li) == 4 and li[3].isdigit():
                    base, version, urlfichero, tam = li
                    if base == base_version:
                        if current_version < version:
                            nresp = QTUtil2.preguntaCancelar123(
                                procesador.main_window,
                                _("Update"),
                                _("Version %s is ready to update") % version,
                                _("Update now"),
                                _("Do not do anything"),
                                _("Don't ask again"),
                            )
                            break
        f.close()
    except:
        pass

    if nresp == 1:
        procesador.actualiza()
    elif nresp == 3:
        procesador.configuration.x_check_for_update = False
        procesador.configuration.graba()
