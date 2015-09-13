# -*- coding: utf-8 -*-
"""
/***************************************************************************
 rejestr
                                 A QGIS plugin
 Rejestr
                              -------------------
        begin                : 2015-09-13
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Tomasz Hak
        email                : tomplamka@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from qgis.utils import *
import psycopg2
from datetime import *
import sys
import os
import pdb
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from Rejestr_dialog import rejestrDialog
import os.path


class rejestr:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'rejestr_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = rejestrDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Rejestr')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'rejestr')
        self.toolbar.setObjectName(u'rejestr')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('rejestr', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/rejestr/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Rejestr'),
            callback=self.run,
            parent=self.iface.mainWindow())
            
        self.dlg.nazwaAdresataLineEdit.clear()
        self.dlg.imieLineEdit.clear()
        self.dlg.nazwiskoLineEdit.clear()
        self.dlg.ulicaLineEdit.clear()
        self.dlg.nrBudynkuLineEdit.clear()
        self.dlg.miejscowoscLineEdit.clear()
        self.dlg.kodLineEdit.clear()
        self.dlg.dataZlozeniaWnioskuLineEdit.clear()
        self.dlg.znakSprawyLineEdit.clear()
        
        self.dlg.rejonComboBox.addItem(u'Knurów')
        self.dlg.rejonComboBox.addItem(u'Krywałd')
        self.dlg.rejonComboBox.addItem(u'Szczygłowice')
        
        self.dlg.rodzajDokumentuLineEdit.clear()
        self.dlg.celWydaniaDokumentuLineEdit.clear()
        self.dlg.oplataLineEdit.clear()
        self.dlg.pobranaOplataSkarowaLineEdit.clear()
        self.dlg.numeryDzialekLineEdit.clear()
        self.dlg.dokumentyPlanistyczneLineEdit.clear()
        self.dlg.zalDoWnioskuLineEdit.clear()


        self.dlg.btnRejestruj.clicked.connect(self.wniosek)
        self.dlg.btnClearForm.clicked.connect(self.clearForm)


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Rejestr'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        
    def wniosek(self):
        newlineNameAdr = self.dlg.nazwaAdresataLineEdit.text()
        newlineImie_2 = self.dlg.imieLineEdit.text()
        newlineNazwisko_2 = self.dlg.nazwiskoLineEdit.text()
        newlineUlica = self.dlg.ulicaLineEdit.text()
        newlineNrBud = self.dlg.nrBudynkuLineEdit.text()
        newlineMiejscowosc = self.dlg.miejscowoscLineEdit.text()
        newlineKod = self.dlg.kodLineEdit.text()
        
        dataDatePicker = self.dlg.dataZlozeniaWnioskuLineEdit.text()
        #if not dataDatePicker:
        #    iface.messageBar().pushMessage('Puste pole', u'Proszę wypełnić datę wniosku', level=QgsMessageBar.CRITICAL, duration=10)
        #else:            
        #vartemp = dataDatePicker.toPyDate()
        day,month,year = dataDatePicker.split('-')
        newlineDataWniosku = (datetime(int(year),int(month),int(day)))
        #newlineDataWniosku = date(dataDatePicker)
        
        newlineZnakSpr = self.dlg.znakSprawyLineEdit.text()
        newcbRejon = self.dlg.rejonComboBox.currentText()
        newlineRodzDok = self.dlg.rodzajDokumentuLineEdit.text()
        newlineCelDok = self.dlg.celWydaniaDokumentuLineEdit.text()
        newlineOplata = self.dlg.oplataLineEdit.text()
        newlinePobOplSkarb = self.dlg.pobranaOplataSkarowaLineEdit.text()
        newlineNumDzialek = self.dlg.numeryDzialekLineEdit.text()
        newlineDokPlan = self.dlg.dokumentyPlanistyczneLineEdit.text()
        newlineZalWniosek = self.dlg.zalDoWnioskuLineEdit.text()
        
        dataRejestracji = datetime.now()

        
        #newlineID = QtGui.QLineEdit(self)
        #validatorInt = QtGui.QIntValidator()
        #newlineID.setValidator(validatorInt)
        
        con = None

        try:
             
            con = psycopg2.connect(database='netgis_knurow', user='netgis_knurow', password='n4feqeTR', host='178.216.202.213')
            cur = con.cursor()
            
            cur.execute("select Id from rejestr order by id desc limit 1")
            con.commit()
            dataId = cur.fetchone()[0]
            
            newlineId = (dataId + 1)
            
            if all([not newlineNameAdr, not newlineImie_2, not newlineNazwisko_2, not newlineUlica, not newlineNrBud, not newlineMiejscowosc, not newlineKod, not newlineDataWniosku, not newlineZnakSpr, not newcbRejon, not newlineRodzDok, not newlineCelDok, not newlineOplata, not newlinePobOplSkarb, not newlineNumDzialek, not newlineDokPlan, not newlineZalWniosek]):
                iface.messageBar().pushMessage('Puste pole', u'Proszę wypełnić wszystkie pola formularza', level=QgsMessageBar.CRITICAL, duration=10)
            else:
            
                query = "INSERT INTO rejestr (id, nameadr, imie, nazwisko, ulica, nrbud, miejscowosc, kod, datawniosku, znakspr, rejon, rodzdok, celdok, oplata, poboplskarb, numdzialek, dokplan, zalwniosek, datenow) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                data = (newlineId, newlineNameAdr, newlineImie_2, newlineNazwisko_2, newlineUlica, newlineNrBud, newlineMiejscowosc, newlineKod, newlineDataWniosku, newlineZnakSpr, newcbRejon, newlineRodzDok, newlineCelDok, newlineOplata, newlinePobOplSkarb, newlineNumDzialek, newlineDokPlan, newlineZalWniosek, dataRejestracji)
                #query = "INSERT INTO test (id, nameadr) VALUES(%s, %s);"
                #data = (newlineId, newlineNameAdr)

                cur.execute(query, data)
                
                
                
                con.commit()
                
    #            self.dlg.lineNameAdr.clear()
    #            self.dlg.lineImie_2.clear()
    #            self.dlg.lineNazwisko_2.clear()
    #            self.dlg.lineUlica.clear()
    #            self.dlg.lineNrBud.clear()
    #            self.dlg.lineMiejscowosc.clear()
    #            self.dlg.lineKod.clear()
    #            self.dlg.lineZnakSpr.clear()
    #            self.dlg.lineRodzDok.clear()
    #            self.dlg.lineCelDok.clear()
    #            self.dlg.lineOplata.clear()
    #            self.dlg.linePobOplSkarb.clear()
    #            self.dlg.lineNumDzialek.clear()
    #            self.dlg.lineDokPlan.clear()
    #            self.dlg.lineZalWniosek.clear()
                
                iface.messageBar().pushMessage('Sukces', u'Dane zostały zapisane', level=QgsMessageBar.SUCCESS, duration=5)

        except psycopg2.DatabaseError, e:
            if con:
                con.rollback()

            iface.messageBar().pushMessage(u'Błąd', u'Problem z połączeniem do bazy', level=QgsMessageBar.CRITICAL, duration=5)
            sys.exit(1)
            
            
        finally:
            
            if con:
                con.close()
                
            else:
                iface.messageBar().pushMessage(u'Błąd', u'Dane nie zostały zapisane', level=QgsMessageBar.CRITICAL, duration=5)
                
    def clearForm(self):
        self.dlg.nazwaAdresataLineEdit.clear()
        self.dlg.imieLineEdit.clear()
        self.dlg.nazwiskoLineEdit.clear()
        self.dlg.ulicaLineEdit.clear()
        self.dlg.nrBudynkuLineEdit.clear()
        self.dlg.miejscowoscLineEdit.clear()
        self.dlg.kodLineEdit.clear()
        self.dlg.dataZlozeniaWnioskuLineEdit.clear()
        self.dlg.znakSprawyLineEdit.clear()
        
        self.dlg.rodzajDokumentuLineEdit.clear()
        self.dlg.celWydaniaDokumentuLineEdit.clear()
        self.dlg.oplataLineEdit.clear()
        self.dlg.pobranaOplataSkarowaLineEdit.clear()
        self.dlg.numeryDzialekLineEdit.clear()
        self.dlg.dokumentyPlanistyczneLineEdit.clear()
        self.dlg.zalDoWnioskuLineEdit.clear()


    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
