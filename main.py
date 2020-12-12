import sys
from PyQt5.QtCore import QUrl, QSize
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineScript, QWebEnginePage, QWebEngineProfile
from PyQt5.QtWidgets import QToolBar, QAction, QLineEdit, QProgressBar, QLabel, QMainWindow, QTabWidget, QStatusBar, QApplication

class WebProfile(QWebEngineProfile):
    def __init__(self, *args, **kwargs):
        super(WebProfile, self).__init__(*args, **kwargs)
        self.setHttpUserAgent("Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0")
        self.setPersistentCookiesPolicy(0)
        
class BrowserTab(QMainWindow):
    def __init__(self, parent):
        super(BrowserTab, self).__init__(parent)
        self._tabIndex = -1
        self.mainWindow = self.parent()

        self.webView = QWebEngineView(self)
        self.page = QWebEnginePage(self.mainWindow.profile, self)
        self.webView.setPage(self.page)
        self.webView.load(QUrl("about:blank"))
        self.setCentralWidget(self.webView)

        self.navigation_bar = QToolBar('Navigation')
        self.navigation_bar.setIconSize(QSize(24, 24))
        self.navigation_bar.setMovable(False)
        self.addToolBar(self.navigation_bar)

        self.back_button = QAction(QIcon('Assets/back.png'), 'back', self)
        self.next_button = QAction(QIcon('Assets/forward.png'), 'forward', self)
        self.refresh_button = QAction(QIcon('Assets/refresh.png'), 'reload', self)
        self.home_button = QAction(QIcon('Assets/home.png'), 'home', self)
        self.enter_button = QAction(QIcon('Assets/enter.png'), 'go', self)
        self.add_button = QAction(QIcon('Assets/new.png'), 'new', self)
        self.ssl_icon = QLabel(self)
        self.ssl_status = QLabel(self)
        self.url_text_bar = QLineEdit(self)
        self.url_text_bar.setMinimumWidth(300)
        self.set_button = QAction(QIcon('Assets/setting.png'), 'setting', self)

        self.navigation_bar.addAction(self.back_button)
        self.navigation_bar.addAction(self.next_button)
        self.navigation_bar.addAction(self.refresh_button)
        self.navigation_bar.addAction(self.home_button)
        self.navigation_bar.addAction(self.add_button)
        self.navigation_bar.addSeparator()
        self.navigation_bar.addWidget(self.ssl_icon)
        self.navigation_bar.addWidget(self.ssl_status)
        self.navigation_bar.addWidget(self.url_text_bar)
        self.navigation_bar.addAction(self.enter_button)

        self.trigger()
        self.IsLoading = False

    def setTabIndex(self, index):
        self._tabIndex = index

    def trigger(self):
        self.back_button.triggered.connect(self.webView.back)
        self.next_button.triggered.connect(self.webView.forward)
        self.refresh_button.triggered.connect(self.onRefresh)
        self.home_button.triggered.connect(self.navigateHome)
        self.enter_button.triggered.connect(self.navigateUrl)
        self.url_text_bar.returnPressed.connect(self.navigateUrl)

        self.webView.iconChanged.connect(lambda x: self.mainWindow.tabs.setTabIcon(self._tabIndex, self.webView.icon()))
        self.webView.urlChanged.connect(self.urlChanged)
        self.webView.loadProgress.connect(self.onLoading)

        self.add_button.triggered.connect(lambda x: self.mainWindow.AddNewTab(BrowserTab(self.mainWindow)))
        self.webView.titleChanged.connect(self.onWebViewTitleChange)
        self.webView.createWindow = self.webViewCreateWindow # kết nối hàm tạo tab mới khi click vào 
                                                             # hình ảnh hoặc 1 đường dẫn bất kỳ.

    def webViewCreateWindow(self, *args):
        tab = BrowserTab(self.mainWindow)
        self.mainWindow.AddNewTab(tab)
        return tab.webView

    def onWebViewTitleChange(self, title):
        self.mainWindow.setWindowTitle(title)
        self.mainWindow.tabs.setTabToolTip(self._tabIndex, title)
        if len(title) >= 10:
            title = title[:10] + "..."
        self.mainWindow.tabs.setTabText(self._tabIndex, title)

    def navigateUrl(self):
        s = QUrl(self.url_text_bar.text())
        if s.scheme() == '':
            s.setScheme('http')
        self.webView.load(s)

    def navigateHome(self):
        s = QUrl("about:blank")
        self.webView.load(s)

    # Xác định xem link đó là https hay http
    def urlChanged(self, s):
        prec = s.scheme()
        if prec == 'http':
            self.ssl_icon.setPixmap(QPixmap("Assets/unsafe.png").scaledToHeight(24))
            self.ssl_status.setText(" unsafe ")
            self.ssl_status.setStyleSheet("color:red;")
        elif prec == 'https':
            self.ssl_icon.setPixmap(QPixmap("Assets/safe.png").scaledToHeight(24))
            self.ssl_status.setText(" safe ")
            self.ssl_status.setStyleSheet("color:green;")
        self.url_text_bar.setText(s.toString())
        self.url_text_bar.setCursorPosition(0)

    def onLoading(self, p):
        if p < 100 and self.IsLoading == False:
            self.refresh_button.setIcon(QIcon('Assets/stop.png'))
            self.IsLoading = True
        elif p == 100 and self.IsLoading:
            self.refresh_button.setIcon(QIcon('Assets/refresh.png'))
            self.IsLoading = False

    def onRefresh(self):
        if self.IsLoading:
            self.webView.stop()
        else:
            self.webView.reload()

    def close(self):
        self.webView.close()
        super(BrowserTab, self).close()

class MainWindow(QMainWindow):
    """docstring for MainWindow"""
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.tabs = QTabWidget(tabsClosable=True, movable=True)
        self.tabs.setTabShape(0)
        self.resize(800, 600)
        # self.showMaximized()
        self.setCentralWidget(self.tabs)
        self.tabs.tabCloseRequested.connect(self.CloseCurrentTab)
        self.tabs.currentChanged.connect(lambda i: self.setWindowTitle(self.tabs.tabText(i)))

        # Tạo trình duyệt ẩn danh. Xóa comment dòng sau.
        # self.profile = WebProfile(self)
         
        self.profile = QWebEngineProfile(self)

        # Tạo tab mặc định khi lần đầu chạy trình duyệt
        self.init_tab = BrowserTab(self)
        self.init_tab.webView.load(QUrl("https://www.google.com"))
        self.AddNewTab(self.init_tab)

    def AddNewTab(self, tab):
        i = self.tabs.addTab(tab, "")
        tab.setTabIndex(i)
        self.tabs.setCurrentIndex(i)
        self.tabs.setTabIcon(i,QIcon('Assets/main.png'))
        
    def CloseCurrentTab(self, tabIndex):
        if self.tabs.count() > 1:
            self.tabs.widget(tabIndex).close()
            self.tabs.removeTab(tabIndex)
        else:
            self.close()

def main():
    app = QApplication(sys.argv)
    MainWindow().show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()  


