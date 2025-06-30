"""Programa SMS Creado por la empresa TextLabel de UPIITA IPN
    23/06/2024
"""
from PySide6.QtWidgets import QMainWindow, QDialog, QMessageBox, QGraphicsView, QGraphicsScene, QVBoxLayout,QTimeEdit
from PySide6.QtGui import QColor, QPixmap, QFont, QPen, QBrush,QMovie
from PySide6.QtCore import Qt,Slot,QTimer
from SMS_ui import *
from Chat_ui import *
from Login_ui import *
from Menu_ui import *
from Personal_Chat_ui import *
from Create_gruop_ui import *
from On_Off_ui import *
from PySide6.QtCore import QThread, Signal
import sys
import socket
import chess
from gato.gato_online import GatoOnline
from gato.gato_dialog_ui import Ui_Dialog
import os 
import serial
from alimentador import AlimentadorApp
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
import logging
logging.basicConfig(level=logging.DEBUG)

#Variables globales
Photos = ["Icons/cat.jpg", "Icons/Makoto.jpg", "Icons/Aigis.jpg", "Icons/MikuKitty.jpg","Icons/importantPhoto.jpg"]
Group_Photos=["Icons_group/gato_arabe.jpg","Icons_group\gato_riendo.jpg","Icons_group\me_perdonas.jpg","Icons_group/server_omero.jpeg"]

class ThreadSocket(QThread):
    """
    Crea la conexión con el servidor
    Métodos:
    run: Deja conectar al usuario en caso de que el servidor se halle conectado, en caso 
        contrario, aparecerá un mensaje de "¡¡disconneceted!!". En caso de que haya algún problema
        se imprimirá el mensaje de "¡¡error!!"
    stop: Cuando el programa es cerrardo, la conexión entre usuario-servidor finaliza.
    """
    signal_message = Signal(str) 
    def __init__(self, name):
           """Inicializa el socket y conecta al servidor.
        Args:
            name (str): Nombre del usuario para registrar en el servidor."""
        super().__init__()
        self.connected = False
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server.connect(("18.119.164.44", 4004))
            self.connected = True
            self.server.send(bytes(f"<name>{name}", 'utf-8'))
        except Exception as e:
            print(f"Error al conectar: {e}")
            self.connected = False

    def run(self):
        """Escucha mensajes entrantes del servidor continuamente.
        Emite señal signal_message con cada mensaje recibido."""

        try:
            while self.connected:
                message = self.server.recv(BUFFER_SIZE)
                if message:
                    self.signal_message.emit(message.decode("utf-8"))
                else:
                    self.signal_message.emit("<!!disconnected!!>")
                    break
        except Exception as e:
            self.signal_message.emit(f"<!!error!!> {e}")
        finally:
            self.server.close()
            self.connected = False

    def stop(self):
        """Detiene el hilo y cierra la conexión limpiamente."""
        self.connected = False
        self.wait()

class MainWindow(QMainWindow, Ui_SMS):
    """
    Ventana principal de la aplicación
    Hereda de:
    QMainWindow: Ventana principal de Pyside6.
    Ui_SMS: Clase generada desde Qt Designer que contiene la interfaz
    Métodos:
    __init__: Inicializa la ventana y configura los widgets.
    Continue: Oculta la ventana actual y muestra la de login.
    """
    def __init__(self, *args, **kwargs):
        """Configura la interfaz principal con botón de inicio."""
        QMainWindow.__init__(self, *args, **kwargs)
        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())
        self.pushButton.clicked.connect(self.Continue)
        self.setWindowTitle("SMS - Desconectado")
    
    def Continue(self):
        """Oculta esta ventana y muestra el login."""
        self.hide()
        login = LoginWindow(self)
        login.show()       
    
class LoginWindow(QDialog, Ui_Login):
    """
    Ventana de registro del usuario para la aplicación SMS
    Hereda de:
    QDialog:  Clase base de PySide6 para cuadros de diálogo.
    Ui_Login: Clase generada por Qt Designer que contiene el layout de la interfaz de login.
    Métodos:
    __init__(parent=None): Inicializa la ventana, establece el diseño y conecta los botones.
    Continuar(): Valida el nombre de usuario y abre la ventana del menú principal.
    ChangePhototoWard: Muestra la siguiente imagen guardada para el registro del usuario
    ChangePhototobackward: Muestra la anterior imagen guardada para el registro del usuario
    """
    def __init__(self, parent=None):
        """Prepara campos de nombre y selector de avatar."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("SMS - Login")
        self.setFixedSize(self.width(), self.height())
        self.current_index = 0
        self.adelante.clicked.connect(self.ChangePhototoward)
        self.atras.clicked.connect(self.ChangePhototobackward)
        self.SaveLogin.clicked.connect(self.Continuar)

    def Continuar(self):
        """Valida el nombre ingresado y abre el menú principal."""
        name = self.txtNameUsuario.text()
        photoIndex = self.current_index
        if name != "":
            self.hide()
            self.menu = MenuWindow(self, name, photoIndex)
            self.menu.show()
            self.txtNameUsuario.clear()
        else:
            self.txtNameUsuario.setPlaceholderText("Ingrese un nombre de usuario")
      
    def ChangePhototoward(self):
        """Cambia al siguiente avatar disponible."""
        new_index = (self.current_index + 1) % len(Photos)
        self.photo.setPixmap(QPixmap(Photos[new_index]))
        self.current_index = new_index

    def ChangePhototobackward(self):
        """Cambia al avatar anterior."""
        new_index = (self.current_index - 1) % len(Photos)
        self.photo.setPixmap(QPixmap(Photos[new_index]))
        self.current_index = new_index

class MenuWindow(QDialog, Ui_Menu):
    """
    Ventana del menú principal de la aplicación SMS.
    Esta interfaz permite al usuario acceder a diferentes funcionalidades del sistema como
    chats, control de dispositivos IoT (ESP32), el alimentador automático de mascotas,
    y el juego Gato en línea.

    Hereda de:
        QDialog: Clase base de PySide6 para cuadros de diálogo.
        Ui_Menu: Clase generada por Qt Designer que contiene el diseño de la interfaz del menú principal.

    Métodos:
        __init__(parent=None, user=None, photoIndex=None): Inicializa la ventana, configura señales y conexiones.
        ForoClicked(): Abre la ventana del chat global (foro).
        PersonalChatClicked(): Abre la ventana de chat personal y creación de grupos.
        IoTClicked(): Abre la interfaz para control de dispositivos IoT (ESP32).
        gatoClicked(): Inicia el juego en línea de Gato.
        abrir_alimentador(): Abre la interfaz del alimentador automático.
        handle_global_message(mensaje): Procesa mensajes especiales del servidor, como invitaciones a juegos.
        ExitProgram(): Cierra la conexión al servidor y termina la aplicación.    
    """
    def __init__(self, parent=None, user=None, photoIndex=None):
        """Configura el menú con avatar y nombre del usuario."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("SMS - Menú")
        self.setFixedSize(self.width(), self.height())
        self.NameUser=user
        self.photoI=photoIndex
        self.img.setPixmap(QPixmap(Photos[photoIndex]))
        self.NameUsuario.setText(user)
        self.coneccion = ThreadSocket(user)
        self.coneccion.start()
        self.Foro.clicked.connect(self.ForoClicked)
        self.PersonalChat.clicked.connect(self.PersonalChatClicked)
        self.IoT.clicked.connect(self.IoTClicked)
        #self.Games.clicked.connect(self.GameClicked)
        self.Exit.clicked.connect(self.ExitProgram)
        self.btn_gato.clicked.connect(self.gatoClicked)
        self.btn_alimentador.clicked.connect(self.abrir_alimentador)
        self.coneccion.signal_message.connect(self.handle_global_message)

    def ForoClicked(self):
         """Abre el chat público (foro)."""
        self.hide()
        self.chat = ForoWindow(self, self.NameUser, self.photoI, self.coneccion)
        self.chat.show()

    def PersonalChatClicked(self):
        """Abre la ventana de chats privados."""
        self.hide()
        self.personalChat = PersonalChatWindow(self, self.NameUser, self.coneccion)
        self.personalChat.show()
        
    def IoTClicked(self):
        """Muestra los controles para dispositivos IoT en este caso el coche."""
        self.hide()
        self.IoT = ESP32Activities(self,self.NameUser,self.coneccion)
        self.IoT.show()    

    def ExitProgram(self):
        """Cierra la conexión y termina la aplicación."""
        self.coneccion.server.close()
        self.coneccion.stop()
        sys.exit(0)
        
    #def GameClicked(self):
        #self.hide()
        #self.chess_dialog = ChessInitialGame(self, self.NameUser, self.coneccion)
        #self.chess_dialog.show()
        
    def gatoClicked(self):
        """Inicia el juego del Gato en línea."""
        self.hide()
        self.gato_dialog = GatoInitialGame(self, self.NameUser, self.coneccion)
        self.gato_dialog.show()
        
    def abrir_alimentador(self):
        """Abre el control del alimentador automático."""
        self.alimentador = AlimentadorApp(self.coneccion, self)
        self.alimentador.show()
        
    def handle_global_message(self, mensaje):
        """Procesa mensajes globales del servidor.
        Args:
            mensaje (str): Mensaje recibido con formato específico."""
        if mensaje.startswith("<gato_accept>"):
            rival = mensaje.replace("<gato_accept>", "").strip()

            # Asegurar que no se abren varias ventanas
            if hasattr(self, 'gato_game') and self.gato_game is not None:
                self.gato_game.close()

            print(f"[GATO] {self.NameUser} es jugador X contra {rival}")
            self.gato_game = GatoOnline(self.coneccion, jugador=self.NameUser, oponente=rival, soy_X=True)
            self.gato_game.show()

class ForoWindow(QDialog, Ui_Chat):
    """
    Ventana de chat global (foro) de la aplicación SMS.
    Esta clase representa una interfaz donde todos los usuarios conectados pueden comunicarse
    mediante mensajes públicos. Cada mensaje enviado se transmite al servidor y es reenviado
    a todos los clientes conectados.

    Hereda de:
        QDialog: Clase base para cuadros de diálogo en PySide6.
        Ui_Chat: Interfaz gráfica generada desde Qt Designer para el chat global (foro)

    Métodos:
        __init__(parent, user, photoIndex, conneccion): Inicializa la interfaz del foro, configura los elementos gráficos y los eventos.
        mensaje_saliente(): Obtiene el texto del campo de entrada y lo envía al servidor para su difusión.
        mensage_entrante(mensaje): Recibe y muestra mensajes enviados al foro por otros usuarios conectados.
        ReturnToMenu(): Cierra la ventana del foro y retorna a la ventana del menú principal.
    """
    def __init__(self, parent=MenuWindow, user=None, photoIndex=None, conneccion = None ):
         """Configura el chat con nombre y avatar del usuario."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(f"SMS - Conectado: {user}")
        self.setFixedSize(self.width(), self.height())
        self.NameUser = user
        self.NameUsuario.setText(user)
        self.ImgUsuario.setPixmap(QPixmap(Photos[photoIndex]))
        self.textEdit.setReadOnly(True)
        self.textEdit.setPlaceholderText("Esperando mensajes...")
        self.lineEdit.setPlaceholderText("Escribe un mensaje...")
        self.pushButton.clicked.connect(self.mensaje_saliente)
        self.Salir.clicked.connect(self.ReturnToMenu)
        self.coneccion = conneccion
        self.coneccion.signal_message.connect(self.mensage_entrante)
        self.coneccion.start()       
        
    def mensaje_saliente(self):
        """Envía mensaje al servidor con formato <all>."""
        # Enviar mensaje al servidor
        str = self.lineEdit.text()
        if str != "":
            self.coneccion.server.send(bytes(f"{str}", 'utf-8'))
            self.lineEdit.clear()
            self.textEdit.setPlainText(self.textEdit.toPlainText() + "<Tú> " + str + '\n')

    def mensage_entrante(self, mensaje):
         """Muestra mensajes recibidos con formato <all>."""
        if mensaje.startswith('<all>'):
            text=mensaje.removeprefix('<all>')
            # Mostrar mensaje entrante en el QTextEdit
            self.textEdit.setPlainText(self.textEdit.toPlainText() + text)
            self.textEdit.verticalScrollBar().setValue(self.textEdit.verticalScrollBar().maximum())

    def ReturnToMenu(self):
         """Regresa al menú principal."""
        # Detener el hilo y cerrar la conexión
        self.close()
        self.parent().show()

class PersonalChatWindow(QDialog, Ui_PersonalChat):
    """
    Ventana de chats personales y administración de grupos en la aplicación SMS.
    Esta interfaz permite al usuario visualizar los usuarios conectados, iniciar chats privados,
    gestionar grupos existentes y crear nuevos grupos para mensajería grupal.

    Hereda de:
        QDialog: Clase base para cuadros de diálogo en PySide6.
        Ui_PersonalChat: Interfaz gráfica generada por Qt Designer para la sección de chat personal.

    Métodos:
        __init__(parent, user, conneccion): Inicializa la ventana, configura los estilos y conecta eventos.
        mensaje_getList_of_clients(): Solicita al servidor la lista de clientes actualmente conectados.
        List_of_clients(mensaje): Procesa y muestra los usuarios conectados o muestra un mensaje si no hay ninguno.
        ItemClicked(item): Abre una ventana de chat personal o de grupo según el elemento seleccionado.
        groupclicked(): Abre la interfaz de creación de grupo si hay usuarios disponibles.
        CreateGroup(mensaje): Agrega un grupo recibido del servidor a la lista de usuarios con su nombre e imagen.
        return_to_menu(): Cierra esta ventana y regresa al menú principal.
    """
    def __init__(self, parent=MenuWindow, user=None, conneccion=None):
        """Muestra usuarios conectados y grupos disponibles."""
        super().__init__(parent)
        self.nameUser = user
        self.setupUi(self)
        self.setWindowTitle(f"SMS - Conectado: {user}")
        self.setFixedSize(self.width(), self.height())
        self.UserList.setGeometry(QRect(0, 10, 231, 391))
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setItalic(True)
        self.UserList.setFont(font)
        self.UserList.setIconSize(QSize(38, 38))
        self.coneccion = conneccion
        self.mensaje_getList_of_clients()
        self.coneccion.signal_message.connect(self.List_of_clients)
        self.UserList.itemClicked.connect(self.ItemClicked)
        self.coneccion.signal_message.connect(self.CreateGroup)
        self.Group.clicked.connect(self.groupclicked)
        self.exitButton.clicked.connect(self.return_to_menu)
        self.coneccion.start()

    def mensaje_getList_of_clients(self):
        """Solicita lista de usuarios al servidor."""
        # Enviar solicitud al servidor para obtener la lista de clientes
        self.coneccion.server.send(bytes("<get_clients>", 'utf-8'))
    
    def List_of_clients(self, mensaje):
         """Actualiza la lista de contactos conectados."""
        if mensaje.startswith('<get_clients>'):
            msg = mensaje.removeprefix('<get_clients>')
            if msg == self.nameUser:
                self.UserList.clear()
                self.UserList.addItem("No hay clientes conectados")
                self.flag_no_group=1
            else:
                clientes = [c.strip() for c in msg.split(",")]
                clientes.remove(self.nameUser)
                self.flag_no_group=0
                if clientes != None:
                    #Saca la lista de clientes cuando hay de uno en el servidor
                    self.UserList.clear()
                    self.UserList.addItem("Clientes conectados:")
                    for i, client in enumerate(clientes):
                        item = QListWidgetItem(client)
                        item.setIcon(QIcon(Photos[i % len(Photos)]))
                        self.UserList.addItem(item)
                else:
                    #Muestra que no hay clientes conectados
                    self.UserList.clear()
                    self.UserList.addItem("No hay clientes conectados")     

    def ItemClicked(self, item):
        """Abre chat al seleccionar un contacto/grupo."""
        self.select_name = item.text()
        if self.select_name.startswith('Grupo: '):
            name = self.select_name.removeprefix('Grupo: ')
            self.chat = GroupChat(self, self.Integrants, name ,self.GroupIndex, self.coneccion)
            self.hide()
            self.chat.show()
        else:
            self.index = self.UserList.row(item)-1
            self.chat = Chat(self, self.select_name, self.index, self.coneccion)
            self.hide()
            self.chat.show()
    
    def groupclicked(self):
         """Abre ventana para crear nuevo grupo."""
        if self.flag_no_group == 1 :
            QMessageBox.warning(self, "Error", "No hay usuarios conectados")
        else:
            self.group_window = GroupWindow(self, self.nameUser, self.coneccion)
            self.group_window.show()
        
    def CreateGroup(self, mensaje):
        """Procesa datos de nuevos grupos recibidos."""
        if mensaje.startswith('<group>'):
            # <group>Nombre del grupo,index de imagen<Integrants>Nombre1,Nombre2,Nombre3
            # Da el nombre del grupo y el index del icono
            name_group = mensaje.split('<group>')[1].split("<Integrants>")[0].strip().split(',')
            # Da los nombres de los integrantes del grupo en un string separados por ','
            self.Integrants = mensaje.split("<Integrants>")[1].strip().split(',')
            #Borra al mismo usuario de la lista
            if self.nameUser in self.Integrants:
                self.Integrants.remove(self.nameUser)
            # Separamos el nombre y el index
            self.GroupIndex=int(name_group[1])
            Group_name="Grupo: " + str(name_group[0])
            item = QListWidgetItem(Group_name)
            item.setIcon(QIcon(Group_Photos[self.GroupIndex]))
            self.UserList.addItem(item)    
    
    def return_to_menu(self):
        """Regresa al menú principal."""
        self.close()
        self.parent().show()

class GroupWindow(QDialog, Ui_Creacion_de_Grupo):
    """
    Ventana para la creación de grupos de chat en la aplicación SMS.
    Esta interfaz permite al usuario seleccionar contactos conectados, asignarles un nombre de grupo,
    elegir una imagen representativa y confirmar la creación del grupo, que será comunicado al servidor.

    Hereda de:
        QDialog: Clase base de PySide6 para cuadros de diálogo.
        Ui_Creacion_de_Grupo: Interfaz generada por Qt Designer para la creación de grupos.

    Métodos:
        __init__(parent, user, conneccion): Inicializa la ventana, solicita usuarios y conecta eventos.
        mensaje_getList_of_clients(): Envía una solicitud al servidor para obtener usuarios conectados.
        mostrar_usuarios(mensaje): Procesa y muestra la lista de usuarios conectados (excluyendo al propio).
        SelectedUser(item): Agrega un usuario seleccionado a la lista del nuevo grupo.
        DeleteUser(): Elimina manualmente a un usuario de la lista del grupo.
        confirmar(): Envía al servidor la creación del grupo, incluyendo nombre, imagen e integrantes.
        Prev(): Cambia a la imagen anterior de grupo disponible.
        Next(): Cambia a la siguiente imagen de grupo disponible.
        cancelar(): Cierra la ventana sin crear el grupo y regresa a la ventana anterior.
    """

    def __init__(self, parent=PersonalChatWindow, user=None, conneccion=None):
        """Prepara interfaz con lista de usuarios."""
        super().__init__(parent)
        self.nameUser=user
        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())
        font = QFont()
        font.setPointSize(12)
        self.current_index = 0
        self.UsersSelected=[]
        font.setBold(True)
        font.setItalic(True)
        self.SelectedUsersList.setReadOnly(True)
        self.coneccion = conneccion
        self.mensaje_getList_of_clients()
        self.coneccion.signal_message.connect(self.mostrar_usuarios)
        self.UsersConectedList.itemClicked.connect(self.SelectedUser)
        self.DeleteButton.clicked.connect(self.DeleteUser)
        self.confirm.clicked.connect(self.confirmar)
        self.Cancel.clicked.connect(self.cancelar)
        self.previmage.clicked.connect(self.Prev)
        self.nextimage.clicked.connect(self.Next)
        self.coneccion.start()

    def mensaje_getList_of_clients(self):
        # Enviar solicitud al servidor para obtener la lista de clientes
        self.coneccion.server.send(bytes("<get_clients>", 'utf-8'))

    def mostrar_usuarios(self, mensaje):
        """Muestra usuarios disponibles para agregar."""
        if mensaje.startswith("<get_clients>"):
            msg = mensaje.removeprefix("<get_clients>")
            clientes = [c.strip() for c in msg.split(",")]
            clientes.remove(self.nameUser)
            #Saca la lista de clientes cuando hay mas de uno en el servidor
            self.UsersConectedList.clear()
            for i, client in enumerate(clientes):
                item = QListWidgetItem(client)
                self.UsersConectedList.addItem(item)
    
    def SelectedUser(self,item):
         """Agrega usuario seleccionado al grupo."""
        self.select_name = item.text()
        if self.select_name == "No hay clientes conectados":
            self.SelectedUsersList.setText(self.select_name)
        else:
            self.UsersSelected.append(self.nameUser)
            self.UsersSelected.append(self.select_name)
            text = f"-->{self.select_name}\n"
            self.SelectedUsersList.setText(self.SelectedUsersList.toPlainText() + text)

    def DeleteUser(self):
        """Elimina usuario de la lista del grupo."""
        name = self.DeleteUserText.text()
        self.UsersSelected.remove(name)
        self.DeleteUserText.clear()

    def confirmar(self):
        """Envía datos del grupo al servidor."""
        name = f'{self.NameGroup.text()},{self.current_index}'
        self.NameGroup.clear()
        if name != "":
            UsersNames = ','.join(self.UsersSelected)
            # <group>Nombre del grupo<Integrants>Nombre1,Nombre2,Nombre3
            text_to_send=f"<group>{name}<Integrants>{UsersNames}"
            self.coneccion.server.send(bytes(text_to_send,'utf-8'))
            self.close()
            self.parent().show()
        else:
            self.NameGroup.setPlaceholderText("Ingrese un nombre")

    def Prev(self):
        """Muestra imagen anterior para el grupo."""
        new_index = (self.current_index + 1) % len(Group_Photos)
        self.Img_g.setPixmap(QPixmap(Group_Photos[new_index]))
        self.current_index = new_index

    def Next(self):
        """Muestra siguiente imagen para el grupo."""
        new_index = (self.current_index + 1) % len(Group_Photos)
        self.Img_g.setPixmap(QPixmap(Group_Photos[new_index]))
        self.current_index = new_index

    def cancelar(self):
         """Cierra sin crear el grupo."""
        self.close()
        self.parent().show()

class Chat(QDialog,Ui_Chat):
    """
    Ventana de chat personal entre dos usuarios dentro de la aplicación SMS.
    Permite enviar y recibir mensajes de texto entre usuarios conectados mediante una conexión cliente-servidor.

    Hereda de:
        QDialog: Clase base para cuadros de diálogo en PySide6.
        Ui_Chat: Interfaz gráfica generada por Qt Designer para la ventana de chat personal.

    Métodos:
        __init__(parent, user, photoIndex, conneccion): Inicializa la ventana de chat con el usuario seleccionado.
        ReturnToContacts(): Regresa a la ventana de contactos ocultando la ventana de chat actual.
        mensaje_saliente(): Envía un mensaje de texto al usuario conectado a través del servidor.
        mensage_entrante(mensaje): Recibe y muestra mensajes entrantes desde el servidor.
    """
    def __init__(self, parent=PersonalChatWindow, user=None, photoIndex=None, conneccion = None ):
        """Configura chat con nombre y avatar del contacto."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(f"Chat - Conectado: {user}")
        self.setFixedSize(self.width(), self.height())
        self.NameUser = user
        self.NameUsuario.setText(user)
        self.ImgUsuario.setPixmap(QPixmap(Photos[photoIndex]))
        self.textEdit.setReadOnly(True)
        self.textEdit.setPlaceholderText("Esperando mensajes...")
        self.lineEdit.setPlaceholderText("Escribe un mensaje...")
        self.pushButton.clicked.connect(self.mensaje_saliente)
        self.Salir.clicked.connect(self.ReturnToContacts)
        self.coneccion = conneccion
        self.coneccion.signal_message.connect(self.mensage_entrante)
        self.coneccion.start()
     
    def ReturnToContacts(self):
        """Regresa a la lista de contactos."""
        self.hide()
        self.parent().show()   
        
    def mensaje_saliente(self):
        """Envía mensaje privado con formato <only_to>."""
        # Enviar mensaje al servidor
        # <only_to>Nombre del cliente<text> - Envía un mensaje solo a un cliente específico
        str = self.lineEdit.text()
        self.lineEdit.clear()
        if str != "":
            self.coneccion.server.send(bytes(f"<only_to>{self.NameUser}<text>{str}", 'utf-8'))
            self.textEdit.setPlainText(self.textEdit.toPlainText() + "<Tú> " + str + '\n')
    
    def mensage_entrante(self, mensaje):
         """Muestra mensajes privados recibidos."""
        if mensaje.startswith('<only_to>'):
            text = mensaje.removeprefix('<only_to>')
        # Mostrar mensaje entrante en el QTextEdit
            self.textEdit.setPlainText(self.textEdit.toPlainText() + text)
            self.textEdit.verticalScrollBar().setValue(self.textEdit.verticalScrollBar().maximum())

class GroupChat(QDialog, Ui_Chat):
    """
    Ventana de chat grupal dentro de la aplicación SMS.
    Permite la comunicación simultánea entre múltiples usuarios conectados mediante el envío de mensajes a un grupo.
    Hereda de:
        QDialog: Clase base para cuadros de diálogo en PySide6.
        Ui_Chat: Interfaz gráfica generada por Qt Designer, reutilizada para el entorno de chat grupal.
    Métodos:
        __init__(parent, Integrants, user, photoIndex, conneccion): Inicializa la ventana del chat grupal con los integrantes del grupo.
        ReturnToContacts(): Regresa a la ventana de contactos, ocultando la actual.
        mensaje_saliente(): Envía un mensaje a todos los integrantes del grupo.
        mensage_entrante(mensaje): Muestra mensajes recibidos que provienen del grupo.
    """

    def __init__(self, parent=PersonalChatWindow, Integrants=None ,user=None, photoIndex=None, conneccion = None ):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(f"Grupo - Conectado: {user}")
        self.setFixedSize(self.width(), self.height())
        self.NameUser = user
        self.Integrants = Integrants
        self.NameUsuario.setText(user)
        self.ImgUsuario.setPixmap(QPixmap(Group_Photos[photoIndex]))
        self.textEdit.setReadOnly(True)
        self.textEdit.setPlaceholderText("Esperando mensajes...")
        self.lineEdit.setPlaceholderText("Escribe un mensaje...")
        self.pushButton.clicked.connect(self.mensaje_saliente)
        self.Salir.clicked.connect(self.ReturnToContacts)
        self.coneccion = conneccion
        self.coneccion.signal_message.connect(self.mensage_entrante)
        self.coneccion.start()
     
    def ReturnToContacts(self):
        self.hide()
        self.parent().show()   
        
    def mensaje_saliente(self):
         """Envía mensaje a todos los miembros del grupo."""
        # Enviar mensaje al servidor
        # <some_people>Nombre del cliente<text> - Envía un mensaje solo a un cliente específico
        str = self.lineEdit.text()
        self.lineEdit.clear()
        if str != "":
            for names in self.Integrants:
                self.coneccion.server.send(bytes(f"<some_people>{names}<text>{str}", 'utf-8'))
                self.textEdit.setPlainText(self.textEdit.toPlainText() + "<Tú> " + str + '\n')
    
    def mensage_entrante(self, mensaje):
        """Muestra mensajes grupales recibidos."""
        if mensaje.startswith('<some_people>'):
            text=mensaje.removeprefix('<some_people>')
            # Mostrar mensaje entrante en el QTextEdit
            self.textEdit.setPlainText(self.textEdit.toPlainText() + text)
            self.textEdit.verticalScrollBar().setValue(self.textEdit.verticalScrollBar().maximum())
                         
class ESP32Activities(QDialog, Ui_On_Off):
    """
    Ventana de control remoto para la placa ESP32 dentro de la aplicación SMS.
    Permite enviar comandos al hardware conectado para controlar LEDs, dirección de movimiento y claxon.

    Hereda de:
        QDialog: Clase base para cuadros de diálogo en PySide6.
        Ui_On_Off: Interfaz gráfica generada por Qt Designer para el panel de control del ESP32.
    
    Métodos:
        __init__(parent, user, conneccion): Inicializa la interfaz, conecta botones con sus funciones y establece la comunicación.
        ReturnToMenu(): Cierra la ventana actual y retorna al menú principal.
        ChargeOn(): Envía el comando para encender los LEDs.
        ChargeOff(): Envía el comando para apagar los LEDs.
        Forward(): Envía el comando para avanzar.
        Backward(): Envía el comando para retroceder.
        Leftward(): Envía el comando para girar a la izquierda.
        Rightward(): Envía el comando para girar a la derecha.
        Pitar(): Envía el comando para activar el claxon.
    """
    def __init__(self, parent=MenuWindow, user=None, conneccion = None ):
        """Configura interfaz de controles IoT."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(f"ESP32 - Conectado: {user}")
        self.setFixedSize(self.width(), self.height())
        self.NameUser = user
        self.coneccion = conneccion
        self.OnButton.clicked.connect(self.ChargeOn)
        self.OffButton.clicked.connect(self.ChargeOff)
        self.ForwardButton.clicked.connect(self.Forward)
        self.BackwardButton.clicked.connect(self.Backward)
        self.RightwardButton.clicked.connect(self.Rightward)
        self.LeftwardButton.clicked.connect(self.Leftward)
        #self.StopButton.clicked.connect(self.Stop)
        self.Claxon.clicked.connect(self.Pitar)
        self.coneccion.start()
        self.return_to_menu.clicked.connect(self.ReturnToMenu)
        
    def ReturnToMenu(self):
        self.close()
        self.parent().show()
        
    def ChargeOn(self):
        """Envía comando 'LEDS_ON' al ESP32."""
        self.coneccion.server.send(bytes("<conection_ESP32>ESP32<text>LEDS_ON", 'utf-8'))
    
    def ChargeOff(self):
        self.coneccion.server.send(bytes("<conection_ESP32>ESP32<text>LEDS_OFF", 'utf-8'))
        
    def Forward(self):
        """Envía comando 'Forward' para movimiento."""
        self.coneccion.server.send(bytes("<conection_ESP32>ESP32<text>Forward", 'utf-8'))
        
    def Backward(self):
        self.coneccion.server.send(bytes("<conection_ESP32>ESP32<text>Backward", 'utf-8'))
        
    def Leftward(self):
        self.coneccion.server.send(bytes("<conection_ESP32>ESP32<text>Leftward",'utf-8'))
    
    def Rightward(self):
        self.coneccion.server.send(bytes("<conection_ESP32>ESP32<text>Rightward",'utf-8'))
    
    #def Stop(self):
        #self.coneccion.server.send(bytes("<conection_ESP32>ESP32<text>Stop", 'utf-8'))
    
    def Pitar(self):
        """Envía comando 'Claxon' al ESP32."""
        self.coneccion.server.send(bytes("<conection_ESP32>ESP32<text>Claxon",'utf-8'))
            
class GatoInitialGame(QDialog, Ui_PersonalChat):
    """
    Ventana de inicio para el modo multijugador del juego "Gato" dentro de la aplicación SMS.
    Permite al usuario visualizar los clientes conectados, enviar invitaciones para jugar y gestionar el inicio del juego en línea.

    Hereda de:
        QDialog: Clase base para cuadros de diálogo en PySide6.
        Ui_PersonalChat: Interfaz gráfica reutilizada para mostrar la lista de usuarios conectados y controles de navegación.

    Métodos:
        __init__(parent, user, conneccion): Inicializa la ventana, configura la lista de usuarios y conecta señales.
        mensaje_getList_of_clients(): Solicita al servidor la lista de clientes conectados.
        List_of_clients(mensaje): Muestra la lista de usuarios disponibles para invitar al juego.
        ItemClicked(item): Envía una invitación al usuario seleccionado.
        handle_incoming_message(mensaje): Maneja invitaciones entrantes, aceptación y jugadas del juego Gato.
        ask_invitation(rival): Muestra un cuadro de diálogo para aceptar o rechazar una invitación a jugar.
        start_gato_game(user, rival, is_X): Inicia la partida de Gato con el rival especificado.
        returnToMenu(): Cierra la ventana actual y regresa al menú principal.
    """
    def __init__(self, parent=MenuWindow, user=None, conneccion=None):
         """Muestra lista de usuarios para invitar."""
        super().__init__(parent)
        self.nameUser = user
        self.setupUi(self)
        self.setWindowTitle(f"SMS - Gato en línea - {user}")
        self.setFixedSize(self.width(), self.height())
        self.UserList.setGeometry(QRect(0, 10, 231, 391))
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setItalic(True)
        self.UserList.setFont(font)
        self.UserList.setIconSize(QSize(38, 38))
        self.coneccion = conneccion
        self.mensaje_getList_of_clients()
        self.coneccion.signal_message.connect(self.List_of_clients)
        self.coneccion.signal_message.connect(self.handle_incoming_message)
        self.UserList.itemClicked.connect(self.ItemClicked)
        self.exitButton.clicked.connect(self.returnToMenu)

    def mensaje_getList_of_clients(self):
        self.coneccion.server.send(bytes("<get_clients>", 'utf-8'))

    def List_of_clients(self, mensaje):
        if mensaje.startswith('<get_clients>'):
            msg = mensaje.removeprefix('<get_clients>')
            if msg == self.nameUser:
                self.UserList.clear()
                self.UserList.addItem("No hay clientes conectados")
                self.flag_no_group = 1
            else:
                clientes = [c.strip() for c in msg.split(",")]
                if self.nameUser in clientes:
                    clientes.remove(self.nameUser)
                self.flag_no_group = 0
                if clientes:
                    self.UserList.clear()
                    self.UserList.addItem("Clientes conectados:")
                    for client in clientes:
                        self.UserList.addItem(client)
                else:
                    self.UserList.clear()
                    self.UserList.addItem("No hay clientes conectados")

    def ItemClicked(self, item):
        """Envía invitación al usuario seleccionado."""
        text = item.text()
        if text in ["Clientes conectados:", "No hay clientes conectados"]:
            return
        self.select_name = text.strip()
        if self.select_name != self.nameUser:
            self.coneccion.server.send(
                bytes(f"<gato_invite>{self.select_name}<from>{self.nameUser}", "utf-8")
            )
            QMessageBox.information(self, "Invitación enviada", f"Invitación enviada a {self.select_name}. Espera la respuesta.")

    def handle_incoming_message(self, mensaje):
        if mensaje.startswith("<gato_invite>"):
            try:
                parts = mensaje.replace("<gato_invite>", "").split("<from>")
                to_user = parts[0].strip()
                from_user = parts[1].strip()
                if to_user == self.nameUser:
                    self.ask_invitation(from_user)
            except Exception:
                pass
        elif mensaje.startswith("<gato_accept>"):
            rival = mensaje.replace("<gato_accept>", "").strip()
            self.start_gato_game(self.nameUser, rival, is_X=True)
            
        elif mensaje.startswith("<jugar>"):
            parts = mensaje.replace("<jugar>", "").split("<text>")
            jugador = parts[0].strip()
            movimiento = parts[1].strip()
            fila, columna = map(int, movimiento.split(","))
            if hasattr(self, 'partida'):
                self.partida.marcar_jugada_remota(fila, columna)

    def ask_invitation(self, rival):
        reply = QMessageBox.question(
            self,
            "Invitación a jugar Gato",
            f"{rival} quiere jugar Gato contigo. ¿Aceptar?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.coneccion.server.send(
                bytes(f"<gato_accept>{rival}", "utf-8")
            )
            print(f"[GATO] {self.nameUser} aceptó reto. Es jugador O contra {rival}")
            self.start_gato_game(self.nameUser, rival, is_X=False)

    def start_gato_game(self, user, rival, is_X):
        """Inicia partida con configuración de jugadores."""
        self.partida = GatoOnline(self.coneccion, jugador=user, oponente=rival, soy_X=is_X)
        self.hide()
        self.partida.show()

    def returnToMenu(self):
        self.close()
        self.parent().show()
    
class AlimentadorApp(QDialog):
    """
    Ventana principal para el control de un alimentador automático conectado a un ESP32.
    Esta interfaz permite gestionar la alimentación manual y programada de una mascota a través de comandos enviados
    por puerto serial o simulación. Incluye soporte para visualización animada mediante GIFs, programación de horarios,
    estado del sistema, y control del motor de alimentación.

    Hereda de:
        QDialog: Clase base para cuadros de diálogo en PySide6.

    Métodos:
        __init__(conneccion, parent): Inicializa la ventana principal, carga la interfaz y configura los componentes.
        cargar_interfaz_ui(): Intenta cargar la interfaz desde un archivo .ui generado por Qt Designer.
        cargar_gifs(): Carga y asigna los GIFs de animaciones (comiendo, esperando, feliz).
        crear_interfaz_manual(): Construye manualmente una interfaz alternativa si falla la carga desde .ui.
        enviar_comando_serial(comando): Envía un comando por puerto serial al ESP32.
        iniciar_alimentacion_manual(): Inicia la alimentación manual de la mascota.
        timer_comiendo_timeout(): Maneja el fin de la alimentación mostrando la animación de "feliz".
        timer_feliz_timeout(): Restablece la animación a "esperando" luego del estado "feliz".
        detener_alimentacion(): Detiene la alimentación y cambia el estado visual.
        encender_motor(): Activa el motor del alimentador (encendido manual).
        apagar_motor(): Apaga el motor y muestra el estado visual de espera.
        actualizar_estado(mensaje): Actualiza el texto de estado mostrado al usuario.
        procesar_mensaje(mensaje): Procesa mensajes recibidos desde el ESP32.
        closeEvent(event): Cierra la conexión serial de forma segura al cerrar la ventana.
        iniciar_lectura_serial(): Inicia un temporizador para leer datos seriales.
        leer_serial(): Lee datos del puerto serial y los procesa.
        mostrar_gif_feliz(): Cambia la animación a "gato feliz" y actualiza el estado.
        iniciar_alimentacion_programada(): Inicia la alimentación según un horario programado.
        mostrar_animacion(estado): Cambia la animación según el estado recibido.
        mostrar_panel_programacion(): Muestra u oculta el panel de horarios programados.
        verificar_horarios(): Verifica si la hora actual coincide con un horario programado.
        agregar_horario(): Agrega un nuevo horario a la lista de alimentación.
        eliminar_horario(): Elimina uno o más horarios seleccionados.
    """    
    def __init__(self, conneccion, parent=None):
        """Configura interfaz con temporizadores y GIFs."""
        super().__init__(parent)

        # Variables estado
        self.alimentacion_activa = False
        self.es_programado = False
    
        # Guardar conexión
        self.coneccion = conneccion
        self.coneccion.signal_message.connect(self.procesar_mensaje)
        self.timer_horarios = QTimer(self)
        self.timer_horarios.timeout.connect(self.verificar_horarios)
        self.timer_horarios.start(60000)

        # Temporizadores
        self.timer_comiendo = QTimer(self)
        self.timer_comiendo.setSingleShot(True)
        self.timer_comiendo.timeout.connect(self.timer_comiendo_timeout)
        self.timer_feliz = QTimer(self)
        self.timer_feliz.setSingleShot(True)
        self.timer_feliz.timeout.connect(self.timer_feliz_timeout)

        # Cargar interfaz
        if not self.cargar_interfaz_ui():
            self.crear_interfaz_manual()

        self.cargar_gifs()
        self.configurar_serial()
        self.setWindowTitle("Control de Alimentador")
        self.resize(700, 600)
        self.show()
        self.iniciar_lectura_serial()
        
    def cargar_interfaz_ui(self):
        try:
            ui_file_path = os.path.join(os.path.dirname(__file__), "alimentador.ui")
            loader = QUiLoader()
            ui_file = QFile(ui_file_path)
        
            if not ui_file.open(QFile.ReadOnly):
                print(f"No se pudo abrir UI: {ui_file.errorString()}")
                return False
            
            self.ui_widget = loader.load(ui_file, None)  
            ui_file.close()
            layout = QVBoxLayout(self)
            layout.addWidget(self.ui_widget)
            
            # Buscar y asignar widgets
            self.btn_alimentar = self.ui_widget.findChild(QPushButton, "btn_alimentar")
            self.btn_programar = self.ui_widget.findChild(QPushButton, "btn_programar")
            self.btn_detener = self.ui_widget.findChild(QPushButton, "btn_detener")
            self.btn_encender = self.ui_widget.findChild(QPushButton, "btn_encender")
            self.btn_reintentar = self.ui_widget.findChild(QPushButton, "btn_reintentar")
            self.status_label = self.ui_widget.findChild(QLabel, "status_label")
            self.lbl_animacion = self.ui_widget.findChild(QLabel, "lbl_animacion")
            
            if not os.path.exists(ui_file_path):
                print(f"Archivo UI no encontrado: {ui_file_path}")
                return False
                    
            if not self.ui_widget:
                print("Error al cargar el archivo UI")
                return False
            
            self.setLayout(layout)

            self.btn_apagar = self.ui_widget.findChild(QPushButton, "btn_apagar")
            self.status_label = self.ui_widget.findChild(QLabel, "status_label")

            self.btn_detener = self.ui_widget.findChild(QPushButton, "btn_detener")

            if self.btn_programar:
                self.btn_programar.clicked.connect(self.mostrar_panel_programacion)
                
            if self.btn_detener:
                self.btn_detener.clicked.connect(self.detener_alimentacion)
            
            btn_agregar = self.ui_widget.findChild(QPushButton, "btn_agregar_horario")
            btn_eliminar = self.ui_widget.findChild(QPushButton, "btn_eliminar")

            if btn_agregar:
                btn_agregar.clicked.connect(self.agregar_horario)
            if btn_eliminar:
                btn_eliminar.clicked.connect(self.eliminar_horario)


            # Conectar señales
            if self.btn_alimentar:
                self.btn_alimentar.clicked.connect(self.iniciar_alimentacion_manual)
            if self.btn_reintentar:
                self.btn_reintentar.clicked.connect(self.configurar_serial)
            if self.btn_encender:
                self.btn_encender.clicked.connect(self.encender_motor)
            if self.btn_apagar:
                self.btn_apagar.clicked.connect(self.apagar_motor)
                
            frame = self.ui_widget.findChild(QWidget, "frame_programacion")
            if frame:
                frame.setVisible(False)  # Ocultar al inicio
            return True

        except Exception as e:
            print(f"Error cargando UI: {e}")
            return False

    def cargar_gifs(self):
        if not self.lbl_animacion:
            print("No hay QLabel para animación. Saltando carga de GIFs.")
            return

        base_path = os.path.dirname(__file__)
        
        self.gif_comiendo = QMovie(os.path.join(base_path, "comiendo.gif"))
        self.gif_esperando = QMovie(os.path.join(base_path, "esperando_comida.gif"))
        self.gif_feliz = QMovie(os.path.join(base_path, "gato_feliz.gif"))

        # Verifica si se cargaron correctamente
        print("GIFs cargados:")
        print("  comiendo:", self.gif_comiendo.isValid())
        print("  esperando:", self.gif_esperando.isValid())
        print("  feliz:", self.gif_feliz.isValid())

        # Tamaño fijo al QLabel (opcional)
        self.lbl_animacion.setFixedSize(300, 200)
        self.lbl_animacion.setScaledContents(True)

        # Mostrar por defecto el de esperando
        self.lbl_animacion.setMovie(self.gif_esperando)
        self.gif_esperando.start()


    def crear_interfaz_manual(self):
        print("Creando interfaz manual...")
        layout = QVBoxLayout()
        self.btn_encender = QPushButton("Encender Motor")
        self.btn_apagar = QPushButton("Apagar Motor")
        self.btn_alimentar = QPushButton("Alimentar Ahora")
        self.status_label = QLabel("Estado: Desconectado")
        self.status_label.setStyleSheet("font-size: 16px; color: #333;")
        layout.addWidget(self.btn_encender)
        layout.addWidget(self.btn_apagar)
        layout.addWidget(self.btn_alimentar)
        layout.addWidget(self.status_label)
        self.setLayout(layout)
        self.btn_encender.clicked.connect(self.encender_motor)
        self.btn_apagar.clicked.connect(self.apagar_motor)
        self.btn_alimentar.clicked.connect(self.iniciar_alimentacion_manual)

    def enviar_comando_serial(self, comando):
        if self.esp_conectado and self.esp and self.esp.is_open:
            try:
                self.esp.write(f"{comando}\n".encode())
                return True
            except serial.SerialException as e:
                print(f"Error al enviar comando: {e}")
                self.esp_conectado = False
                self.actualizar_estado("Desconectado del ESP32")
                return False
        else:
            print("No conectado al ESP32, comando no enviado.")
        return False


    def iniciar_alimentacion_manual(self):
        """Activa alimentación inmediata."""
        if self.alimentacion_activa:
            print("Alimentación ya está activa")
            return
        print("Iniciando alimentación manual")
        self.alimentacion_activa = True
        self.es_programado = False
        self.enviar_comando_serial("ALIMENTAR")  # CORREGIDO
        self.mostrar_animacion("comiendo")
        self.timer_comiendo.start(10000)

    def timer_comiendo_timeout(self):
        # Termina alimentación
        print("Alimentación terminada, mostrando feliz")
        self.mostrar_animacion("feliz")
        self.timer_feliz.start(10000)  # Mostrar feliz por 10 segundos

    def timer_feliz_timeout(self):
        print("Fin animación feliz, volviendo a esperando")
        self.alimentacion_activa = False
        self.mostrar_animacion("esperando")

    def detener_alimentacion(self):
        if not self.alimentacion_activa:
            print("No hay alimentación activa")
            return
        print("Deteniendo alimentación")
        self.alimentacion_activa = False
        self.timer_comiendo.stop()
        self.timer_feliz.stop()
        if self.esp and self.esp.is_open:
            self.esp.write(b'STOP\n')  # Apagar motor y LED en ESP32
        self.mostrar_animacion("feliz")  # Gato feliz 5 segundos
        self.timer_feliz.start(5000)     # Luego a esperando

    def encender_motor(self):
        if hasattr(self, 'lbl_animacion') and self.lbl_animacion:
            self.lbl_animacion.setMovie(self.gif_feliz)
            self.gif_feliz.start()        
        if not self.enviar_comando_serial('ON'):
            print("Simulación: Motor encendido")
        self.actualizar_estado("Motor encendido")

    def apagar_motor(self):
        # Si hay conexión, envía comando para apagar motor
        if not self.enviar_comando_serial('OFF'):
            print("Simulación: Motor apagado")
        self.actualizar_estado("Motor apagado")
        # Cambiar GIF a esperando
        if self.lbl_animacion and self.gif_esperando:
            self.lbl_animacion.setMovie(self.gif_esperando)
            self.gif_esperando.start()
        # Si hay botón de alimentar, habilitarlo (si lo habías deshabilitado)
        if hasattr(self, 'btn_alimentar') and self.btn_alimentar:
            self.btn_alimentar.setEnabled(True)

    def actualizar_estado(self, mensaje):
        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.setText(f"Estado: {mensaje}")
    @Slot(str)
    def procesar_mensaje(self, mensaje):
        print(f"[Alimentador] Recibido: {mensaje}")
        if "Alimentación completada" in mensaje:
            self.actualizar_estado("Alimentación completada")
            if self.lbl_animacion and self.gif_feliz:
                self.lbl_animacion.setMovie(self.gif_feliz)
                self.gif_feliz.start()
        elif "Recibido comando ALIMENTAR" in mensaje:
            self.actualizar_estado("Alimentando...")
            if self.lbl_animacion and self.gif_comiendo:
                self.lbl_animacion.setMovie(self.gif_comiendo)
                self.gif_comiendo.start()

    def closeEvent(self, event):
        if hasattr(self, 'esp') and self.esp and self.esp.is_open:
            self.esp.close()
        event.accept()
        
    def iniciar_lectura_serial(self):
        self.timer_serial = QTimer(self)
        self.timer_serial.timeout.connect(self.leer_serial)
        self.timer_serial.start(300)
            
    def leer_serial(self):
        try:
            if self.esp and self.esp.is_open and self.esp.in_waiting > 0:
                mensaje = self.esp.readline().decode(errors='ignore').strip()
                print(f"[ESP32] {mensaje}")
                self.procesar_mensaje(mensaje)
        except serial.SerialException as e:
            print(f"Error serial: {e}")
            # Cierra y marca desconectado para evitar futuros errores
            try:
                if self.esp and self.esp.is_open:
                    self.esp.close()
            except Exception:
                pass
            self.esp_conectado = False
            self.actualizar_estado("Desconectado del ESP32")
        except Exception as e:
            print(f"Error inesperado leyendo serial: {e}")
    def mostrar_gif_feliz(self):
        if self.lbl_animacion and self.gif_feliz:
            self.lbl_animacion.setMovie(self.gif_feliz)
            self.gif_feliz.start()
        self.actualizar_estado("Alimentación completada")
        
    def iniciar_alimentacion_programada(self):
        if self.alimentacion_activa:
            return
        self.alimentacion_activa = True
        self.es_programado = True
        self.enviar_comando_serial("ALIMENTAR")
        self.mostrar_animacion("comiendo")
        self.timer_comiendo.start(10000)
        
    def mostrar_animacion(self, estado):
         """Cambia GIF según estado (comiendo/esperando/feliz)."""
        if estado == "comiendo":
            self.lbl_animacion.setMovie(self.gif_comiendo)
            self.gif_comiendo.start()
        elif estado == "esperando":
            self.lbl_animacion.setMovie(self.gif_esperando)
            self.gif_esperando.start()
        elif estado == "feliz":
            self.lbl_animacion.setMovie(self.gif_feliz)
            self.gif_feliz.start()
            
    def mostrar_panel_programacion(self):
        visible = self.ui_widget.findChild(QWidget, "frame_programacion").isVisible()
        self.ui_widget.findChild(QWidget, "frame_programacion").setVisible(not visible)
        
    def verificar_horarios(self):
        """Compara hora actual con horarios programados."""
        hora_actual = QTime.currentTime().toString("hh:mm ap")
        lista = self.ui_widget.findChild(QListWidget, "list_horarios")
        for i in range(lista.count()):
            if lista.item(i).text() == hora_actual:
                self.iniciar_alimentacion_programada()
                break       
    def agregar_horario(self):
         """Añade nuevo horario programado."""
        time_edit = self.ui_widget.findChild(QTimeEdit, "time_edit")
        list_horarios = self.ui_widget.findChild(QListWidget, "list_horarios")
        hora = time_edit.time().toString("hh:mm ap")
        if not any(list_horarios.item(i).text() == hora for i in range(list_horarios.count())):
            list_horarios.addItem(hora)
            
    def eliminar_horario(self):
        list_horarios = self.ui_widget.findChild(QListWidget, "list_horarios")
        if not list_horarios:
            print("No se encontró la lista de horarios")
            return
        selected_items = list_horarios.selectedItems()
        if not selected_items:
            print("No hay horarios seleccionados para eliminar")
            return
        for item in selected_items:
            row = list_horarios.row(item)
            list_horarios.takeItem(row)
            print(f"Horario eliminado: {item.text()}")
                    
if __name__ == "__main__":
    BUFFER_SIZE = 1024  # Usamos un número pequeño para tener una respuesta rápida
    connected = False
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    
