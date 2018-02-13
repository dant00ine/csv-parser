# DJANGO LIBRARIES
from django.test import LiveServerTestCase
from django.conf import settings

# SELENIUM LIBRARIES
from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# PYTHON LIBRARIES
import time, os, stat, glob, codecs, csv

class UploadFiles(LiveServerTestCase):

    _testFilesPath = settings.TEST_FILES_PATH
    _fileDownloadPath = settings.DOWNLOAD_DIRECTORY
    _logDirectory = settings.LOG_DIRECTORY
    _logName = settings.LOG_NAME

    _defaultFilesDict = {
        "eccube": f"{_testFilesPath}/eccube.csv",
        "mailMaga": f"{_testFilesPath}/mail_list_allow.csv",
        "noMail": f"{_testFilesPath}/mail_list_deny.csv",
    }

    def setUp(self):
        options = Options()
        options.set_headless()
        # options.add_experimental_option("profile.default_content_settings.popups", 0)
        # options.add_experimental_option("profile.default_content_setting_values.automatic_downloads", 2)
        self.selenium = webdriver.Chrome(chrome_options=options)
        self._enable_download_in_headless_chrome(self.selenium, self._fileDownloadPath)
        super(UploadFiles, self).setUp()

    def tearDown(self):
        self.selenium.quit()
        super(UploadFiles, self).tearDown()

    def _enable_download_in_headless_chrome(self, driver, download_dir):
        driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
        
        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
        command_result = driver.execute("send_command", params)
        # result contains sessionId, status, and value


    # --- DOWNLOAD FILE HELPER FUNCTIONS ------ #
    # --- PRIVATE TO TESTING MODULE ----------- #
    def _loadPageAndUploadFiles(self, files=_defaultFilesDict):
        self.selenium.get("http://localhost:8000/")
        if 'eccube' in files:
            uploadElement = self.selenium.find_element_by_css_selector("#eccube-csv")
            uploadElement.send_keys(files['eccube'])
        if 'mailMaga' in files:
            uploadElement = self.selenium.find_element_by_css_selector("#mail-maga-csv")
            uploadElement.send_keys(files['mailMaga'])
        if 'noMail' in files:
            uploadElement = self.selenium.find_element_by_css_selector("#no-mail-csv")
            uploadElement.send_keys(files['noMail'])
        self.selenium.find_element_by_css_selector(".box__button").click()
        time.sleep(2)
    
    def _didDownloadFiles(self):
        recent_time = time.time()
        list_of_files = glob.glob(self._fileDownloadPath + '/*.csv')
        list_of_files.sort(key=os.path.getctime, reverse=True)
        timeDelta1 = abs(os.path.getmtime(list_of_files[0]) - recent_time)
        if timeDelta1 < 1.5: #and timeDelta2 < 0.5:
            return True
        return False

    def _composeFilePaths(self, names=[]):
        returnDict = {}
        for name in names:
            returnDict[name] = self._defaultFilesDict[name]
        return returnDict



    # --- LOGGER TESTING HELPER FUNCTIONS ----- #
    # --- PRIVATE TO TESTING MODULE ----------- #

    def _findMostRecentFile(self, directory, partial_file_name):
        files = os.listdir(directory)
        files = filter(lambda x: x.find(partial_file_name) > -1, files)
        name_n_timestamp = dict([(x, os.stat(directory+x).st_mtime) for x in files])
        return max(name_n_timestamp, key=lambda k: name_n_timestamp.get(k))

    def _getLogRef(self):
        try:
            return self._findMostRecentFile(self._logDirectory, self._logName)
        except:
            return os.getcwd() + '/webapp/logfile.log'

    def _tail(self,  f, lines=5 ): #reads last n lines of a file
        total_lines_wanted = lines

        BLOCK_SIZE = 1024
        f.seek(0, 2)
        block_end_byte = f.tell()
        lines_to_go = total_lines_wanted
        block_number = -1
        blocks = [] # blocks of size BLOCK_SIZE, in reverse order starting
                    # from the end of the file
        while lines_to_go > 0 and block_end_byte > 0:
            if (block_end_byte - BLOCK_SIZE > 0):
                # read the last block we haven't yet read
                f.seek(block_number*BLOCK_SIZE, 2)
                blocks.append(f.read(BLOCK_SIZE))
            else:
                # file too small, start from begining
                f.seek(0,0)
                # only read what was not read
                blocks.append(f.read(block_end_byte))
            lines_found = blocks[-1].count(b'\n')
            lines_to_go -= lines_found
            block_end_byte -= BLOCK_SIZE
            block_number -= 1
        strings = list(map(lambda x: x.decode('utf-8'), blocks))
        all_read_text = ''.join(reversed(strings))
        return '\n'.join(all_read_text.splitlines()[-total_lines_wanted:])



    # --- TEST CASES ------ #
    # --------------------- #
    def test_uploadCorrectFiles(self):
        self._loadPageAndUploadFiles()
        assert self._didDownloadFiles()

    def test_noEccubeCsv(self):
        self._loadPageAndUploadFiles(self._composeFilePaths(['mailMaga', 'noMail']))
        assert self._didDownloadFiles()
        
    def test_noMailMagaList(self):
        self._loadPageAndUploadFiles(self._composeFilePaths(['eccube', 'noMail']))
        assert "ERROR" in self.selenium.page_source
        assert "2 files needed" in self.selenium.page_source
        assert not self._didDownloadFiles()

    def test_noNoMailList(self):
        self._loadPageAndUploadFiles(self._composeFilePaths(['eccube', 'mailMaga']))
        assert "ERROR" in self.selenium.page_source
        assert "2 files needed" in self.selenium.page_source
        assert not self._didDownloadFiles()

    def test_columnCount(self):
        self._loadPageAndUploadFiles({
            "mailMaga": "/Users/funglr-dan/CODE/csv_sample/mail_list_deny.csv",
            "noMail": "/Users/funglr-dan/CODE/csv_sample/mail_list_allow.csv",
        })
        assert "ERROR" in self.selenium.page_source
        assert "CSV did not have correct" in self.selenium.page_source

    def test_wrongMojiCodes(self):
        self._loadPageAndUploadFiles({
            "mailMaga": "/Users/funglr-dan/CODE/csv_sample/russian.csv",
            "noMail": "/Users/funglr-dan/CODE/csv_sample/russian.csv",
        })
        assert "ERROR" in self.selenium.page_source
        assert "accepted file encodings" in self.selenium.page_source   

    def test_outputFileUTF(self):
        list_of_files = glob.glob(self._fileDownloadPath + '/*.csv')
        list_of_files.sort(key=os.path.getctime, reverse=True)
        newestFile = list_of_files[0]
        newDict = dict()
        with open(newestFile, encoding="utf-8") as csvoutput:
            data = csv.reader(csvoutput)
            for row in data:
                newDict[row[0]] = row

    def test_filePermissionsError(self):
        csv_dir = os.path.dirname(os.getcwd()) + '/webapp/webapp/csvs'
        os.chmod(csv_dir, 0o000) # NG file permissions
        self._loadPageAndUploadFiles() #upload correct files
        os.chmod(csv_dir, 0o755) # revert to original permissions
        assert "ERROR" in self.selenium.page_source

    def test_loggingErrors(self):
        # since last test should result in error...
        # not super pretty but I'm pressed for time
        log = self._getLogRef()
        lines = self._tail(open(log, 'rb'))
        assert "ERROR" in lines

    def test_loggingUploads(self):
        self._loadPageAndUploadFiles() #upload correct files
        log = self._getLogRef() # get reference to log file
        lines = self._tail(open(log, 'rb')) # find most recent lines
        assert "successfully output" in lines
         # check for presence of upload success msg

    def test_filesErased(self):
        pass
