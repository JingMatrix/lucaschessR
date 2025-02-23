import ctypes
import os

import Code
from Code import Util
from Code.QT import Iconos

DGT_ON = "DGT.ON"


def activate_according_on_off(dispatch):
    # prln("activate")
    if eboard_is_on():
        if Code.dgt is None:
            if activar():
                showDialog()
            else:
                ponOFF()
                return False
        Code.dgtDispatch = dispatch
    else:
        if Code.dgt:
            desactivar()
    if Code.dgt:
        Code.dgt.setupBoard = False
    return True


def eboard_is_on():
    # prln("eboard_is_on")
    return Util.exist_file(DGT_ON)


def ponON():
    # prln("ponON")
    with open(DGT_ON, "wb") as f:
        f.write(b"act")


def ponOFF():
    # prln("ponOFF")
    Util.remove_file(DGT_ON)


def cambiarON_OFF():
    # prln("cambiarON_OFF")
    if eboard_is_on():
        Util.remove_file(DGT_ON)
    else:
        ponON()


def envia(quien, dato):
    # prln(quien, dato)
    # log("[envia: %s] : %s [%s]"%(str(quien), str(dato), str(Code.dgtDispatch)))
    if Code.dgtDispatch:
        return Code.dgtDispatch(quien, dato)
    return 1


def set_position(game):
    # prln("set position")
    if Code.dgt:
        if (Code.configuration.x_digital_board == "DGT") or (
            Code.configuration.x_digital_board == "Novag UCB" and Code.configuration.x_digital_board_version == 0
        ):
            writePosition(game.last_position.fenDGT())
        else:
            writePosition(game.last_position.fen())


def quitarDispatch():
    # prln("quitar dispatch")
    Code.dgtDispatch = None


def log(cad):
    import traceback

    with open("dgt.log", "at", encoding="utf-8", errors="ignore") as q:
        q.write("\n[%s] %s\n" % (Util.today(), cad))
        for line in traceback.format_stack():
            q.write("    %s\n" % line.strip())


# CALLBACKS


def registerStatusFunc(dato):
    # prln("registerStatusFunc", dato)
    envia("status", dato)
    return 1


def registerScanFunc(dato):
    # prln("registerScanFunc", dato)
    envia("scan", _dgt2fen(dato))
    return 1


def registerStartSetupFunc():
    # prln("registerStartSetupFunc")
    Code.dgt.setupBoard = True
    return 1


def registerStableBoardFunc(dato):
    # prln("registerStableBoardFunc", dato)
    if Code.dgt.setupBoard:
        envia("stableBoard", _dgt2fen(dato))
    return 1


def registerStopSetupWTMFunc(dato):
    # prln("registerStopSetupWTMFunc", dato)
    if Code.dgt.setupBoard:
        envia("stopSetupWTM", _dgt2fen(dato))
        Code.dgt.setupBoard = False
    return 1


def registerStopSetupBTMFunc(dato):
    # prln("registerStopSetupBTMFunc", dato)
    if Code.dgt.setupBoard:
        envia("stopSetupBTM", _dgt2fen(dato))
        Code.dgt.setupBoard = False
    return 1


def registerWhiteMoveInputFunc(dato):
    # prln("registerWhiteMoveInputFunc", dato)
    return envia("whiteMove", _dgt2pv(dato))


def registerBlackMoveInputFunc(dato):
    # prln("registerBlackMoveInputFunc", dato)
    return envia("blackMove", _dgt2pv(dato))


def registerWhiteTakeBackFunc():
    # prln("registerWhiteTakeBackFunc")
    return envia("whiteTakeBack", True)


def registerBlackTakeBackFunc():
    # prln("registerBlackTakeBackFunc")
    return envia("blackTakeBack", True)


def activar():
    # prln("activar")
    dgt = None
    if Code.is_linux:
        functype = ctypes.CFUNCTYPE
        path = os.path.join(Code.folder_OS, "DigitalBoards")
        if Code.configuration.x_digital_board == "DGT-gon":
            path_so = os.path.join(path, "libdgt.so")
        elif Code.configuration.x_digital_board == "Certabo":
            path_so = os.path.join(path, "libcer.so")
        elif Code.configuration.x_digital_board == "Millennium":
            path_so = os.path.join(path, "libmcl.so")
        elif Code.configuration.x_digital_board == "Citrine":
            path_so = os.path.join(path, "libcit.so")
        else:
            path_so = os.path.join(path, "libucb.so")
        if os.path.isfile(path_so):
            try:
                dgt = ctypes.CDLL(path_so)
            except:
                dgt = None
                from Code.QT import QTUtil2

                QTUtil2.message(
                    None,
                    """It is not possible to install the driver for the board, one way to solve the problem is to install the libraries:
sudo apt install libqt5pas1
or
sudo dnf install qt5pas-devel""",
                )

    else:
        functype = ctypes.WINFUNCTYPE
        for path in (
            os.path.join(Code.folder_OS, "DigitalBoards"),
            "",
            "C:/Program Files (x86)/DGT Projects/",
            "C:/Program Files (x86)/Common Files/DGT Projects/",
            "C:/Program Files/DGT Projects/",
            "C:/Program Files/Common Files/DGT Projects/",
        ):
            try:
                if Code.configuration.x_digital_board == "DGT":
                    path_dll = os.path.join(path, "DGTEBDLL.dll")
                elif Code.configuration.x_digital_board == "DGT-gon":
                    path_dll = os.path.join(path, "DGT_DLL.dll")
                elif Code.configuration.x_digital_board == "Certabo":
                    path_dll = os.path.join(path, "CER_DLL.dll")
                elif Code.configuration.x_digital_board == "Millennium":
                    path_dll = os.path.join(path, "MCL_DLL.dll")
                elif Code.configuration.x_digital_board == "Citrine":
                    path_dll = os.path.join(path, "CIT_DLL.dll")
                else:
                    path_dll = os.path.join(path, "UCB_DLL.dll")
                if os.path.isfile(path_dll):
                    dgt = ctypes.WinDLL(path_dll)
                    break
            except:
                pass
    if dgt is None:
        return False

    Code.dgt = dgt

    cmpfunc = functype(ctypes.c_int, ctypes.c_char_p)
    st = cmpfunc(registerStatusFunc)
    dgt._DGTDLL_RegisterStatusFunc.argtype = [st]
    dgt._DGTDLL_RegisterStatusFunc.restype = ctypes.c_int
    dgt._DGTDLL_RegisterStatusFunc(st)

    cmpfunc = functype(ctypes.c_int, ctypes.c_char_p)
    st = cmpfunc(registerScanFunc)
    dgt._DGTDLL_RegisterScanFunc.argtype = [st]
    dgt._DGTDLL_RegisterScanFunc.restype = ctypes.c_int
    dgt._DGTDLL_RegisterScanFunc(st)

    cmpfunc = functype(ctypes.c_int)
    st = cmpfunc(registerStartSetupFunc)
    dgt._DGTDLL_RegisterStartSetupFunc.argtype = [st]
    dgt._DGTDLL_RegisterStartSetupFunc.restype = ctypes.c_int
    dgt._DGTDLL_RegisterStartSetupFunc(st)

    cmpfunc = functype(ctypes.c_int, ctypes.c_char_p)
    st = cmpfunc(registerStableBoardFunc)
    dgt._DGTDLL_RegisterStableBoardFunc.argtype = [st]
    dgt._DGTDLL_RegisterStableBoardFunc.restype = ctypes.c_int
    dgt._DGTDLL_RegisterStableBoardFunc(st)

    cmpfunc = functype(ctypes.c_int, ctypes.c_char_p)
    st = cmpfunc(registerStopSetupWTMFunc)
    dgt._DGTDLL_RegisterStopSetupWTMFunc.argtype = [st]
    dgt._DGTDLL_RegisterStopSetupWTMFunc.restype = ctypes.c_int
    dgt._DGTDLL_RegisterStopSetupWTMFunc(st)

    cmpfunc = functype(ctypes.c_int, ctypes.c_char_p)
    st = cmpfunc(registerStopSetupBTMFunc)
    dgt._DGTDLL_RegisterStopSetupBTMFunc.argtype = [st]
    dgt._DGTDLL_RegisterStopSetupBTMFunc.restype = ctypes.c_int
    dgt._DGTDLL_RegisterStopSetupBTMFunc(st)

    cmpfunc = functype(ctypes.c_int, ctypes.c_char_p)
    st = cmpfunc(registerWhiteMoveInputFunc)
    dgt._DGTDLL_RegisterWhiteMoveInputFunc.argtype = [st]
    dgt._DGTDLL_RegisterWhiteMoveInputFunc.restype = ctypes.c_int
    dgt._DGTDLL_RegisterWhiteMoveInputFunc(st)

    cmpfunc = functype(ctypes.c_int, ctypes.c_char_p)
    st = cmpfunc(registerBlackMoveInputFunc)
    dgt._DGTDLL_RegisterBlackMoveInputFunc.argtype = [st]
    dgt._DGTDLL_RegisterBlackMoveInputFunc.restype = ctypes.c_int
    dgt._DGTDLL_RegisterBlackMoveInputFunc(st)

    dgt._DGTDLL_WritePosition.argtype = [ctypes.c_char_p]
    dgt._DGTDLL_WritePosition.restype = ctypes.c_int

    dgt._DGTDLL_ShowDialog.argtype = [ctypes.c_int]
    dgt._DGTDLL_ShowDialog.restype = ctypes.c_int

    dgt._DGTDLL_HideDialog.argtype = [ctypes.c_int]
    dgt._DGTDLL_HideDialog.restype = ctypes.c_int

    dgt._DGTDLL_WriteDebug.argtype = [ctypes.c_bool]
    dgt._DGTDLL_WriteDebug.restype = ctypes.c_int

    dgt._DGTDLL_SetNRun.argtype = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    dgt._DGTDLL_SetNRun.restype = ctypes.c_int

    # Added by GON
    if Code.configuration.x_digital_board != "DGT":
        dgt._DGTDLL_GetVersion.argtype = []
        dgt._DGTDLL_GetVersion.restype = ctypes.c_int
        Code.configuration.x_digital_board_version = dgt._DGTDLL_GetVersion()
        try:
            dgt._DGTDLL_AllowTakebacks.argtype = [ctypes.c_bool]
            dgt._DGTDLL_AllowTakebacks.restype = ctypes.c_int
            dgt._DGTDLL_AllowTakebacks(ctypes.c_bool(True))
            cmpfunc = functype(ctypes.c_int)
            st = cmpfunc(registerWhiteTakeBackFunc)
            dgt._DGTDLL_RegisterWhiteTakebackFunc.argtype = [st]
            dgt._DGTDLL_RegisterWhiteTakebackFunc.restype = ctypes.c_int
            dgt._DGTDLL_RegisterWhiteTakebackFunc(st)
            cmpfunc = functype(ctypes.c_int)
            st = cmpfunc(registerBlackTakeBackFunc)
            dgt._DGTDLL_RegisterBlackTakebackFunc.argtype = [st]
            dgt._DGTDLL_RegisterBlackTakebackFunc.restype = ctypes.c_int
            dgt._DGTDLL_RegisterBlackTakebackFunc(st)
        except:
            pass
    # ------------

    return True


def desactivar():
    # prln("desactivar")
    if Code.dgt:
        # log( "desactivar" )
        hideDialog()
        del Code.dgt
        Code.dgt = None
        Code.dgtDispatch = None


# Funciones directas en la DGT


def showDialog():
    # prln("showdialog")
    if Code.dgt:
        dgt = Code.dgt
        dgt._DGTDLL_ShowDialog(ctypes.c_int(1))


def hideDialog():
    # prln("hidedialog")
    if Code.dgt:
        dgt = Code.dgt
        dgt._DGTDLL_HideDialog(ctypes.c_int(1))


def writeDebug(activar):
    if Code.dgt:
        dgt = Code.dgt
        dgt._DGTDLL_WriteDebug(activar)


def writePosition(cposicion):
    # prln("writePosition", cposicion)
    if Code.dgt:
        Code.dgt.allowHumanTB = False
        # log( "Enviado a la DGT" + cposicion )
        dgt = Code.dgt
        dgt._DGTDLL_WritePosition(cposicion.encode())


def writeClocks(wclock, bclock):
    # prln("writeclocks")
    if Code.dgt:
        if (Code.configuration.x_digital_board == "DGT") or (Code.configuration.x_digital_board == "DGT-gon"):
            # log( "WriteClocks: W-%s B-%s"%(str(wclock), str(bclock)) )
            dgt = Code.dgt
            dgt._DGTDLL_SetNRun(wclock.encode(), bclock.encode(), 0)


def _dgt2fen(datobyte):
    n = 0
    dato = datobyte.decode()
    ndato = len(dato)
    caja = [""] * 8
    ncaja = 0
    ntam = 0
    while True:
        if dato[n].isdigit():
            num = int(dato[n])
            if (n + 1 < ndato) and dato[n + 1].isdigit():
                num = num * 10 + int(dato[n + 1])
                n += 1
            while num:
                pte = 8 - ntam
                if num >= pte:
                    caja[ncaja] += str(pte)
                    ncaja += 1
                    ntam = 0
                    num -= pte
                else:
                    caja[ncaja] += str(num)
                    ntam += num
                    break

        else:
            caja[ncaja] += dato[n]
            ntam += 1
        if ntam == 8:
            ncaja += 1
            ntam = 0
        n += 1
        if n == ndato:
            break
    if ncaja != 8:
        caja[7] += str(8 - ntam)
    return "/".join(caja)


def _dgt2pv(datobyte):
    dato = datobyte.decode()
    # Coronacion
    if dato[0] in "Pp" and dato[3].lower() != "p":
        return dato[1:3] + dato[4:6] + dato[3].lower()

    return dato[1:3] + dato[4:6]


def icon_eboard():
    board = Code.configuration.x_digital_board
    if board == "DGT":
        return Iconos.DGT()
    elif board == "DGT-gon":
        return Iconos.DGTB()
    elif board == "Certabo":
        return Iconos.Certabo()
    elif board == "Millennium":
        return Iconos.Millenium()
    elif board == "Citrine":
        return Iconos.Novag()
    else:
        return Iconos.DGT()
