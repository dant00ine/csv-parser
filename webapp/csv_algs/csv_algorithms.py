import csv
import re
import os
# import chardet
import datetime
# import logging
# logger = logging.getLogger('django')

from django.core.files.storage import FileSystemStorage
from django.conf import settings

from .csv_exceptions import ColumnCount, MatchingColumn, AcceptableFormat

class CSVAlgs(object):

    mobileCodes = ['0570', '0800', '0910', '0990']
    regex1 = '0[2-9]0'
    regex1 = re.compile(regex1)
    regex2 = '01\d0'
    regex2 = re.compile(regex2)

    _ACCEPTED_ENCODINGS = ['utf-8', 'shift_jis', 'shiftjisx0213']

    _mailMagaDictionary = None
    _smsDictionary = None
    _ngSet = None
    _ngSetProcessedSemaphore = False



    # *** PUBLIC METHODS *** #
    # -- This class is intended to be interfaced with through the following functions -- #
    # -- constructor accepts two or three CSV files; output files are then called -- #
    def __init__(self, mailMagaCSV, ngCSV, eccubeCSV=None):
        self._eccubeCSV = eccubeCSV
        self._mailMagaCSV = mailMagaCSV
        self._ngCSV = ngCSV

    def retrieveMailMagaOutput(self):
        thisFormat = self._acceptableFormat(self._mailMagaCSV)
        self._validateEccubeData(self._mailMagaCSV, thisFormat, 5, '会員id')
        self._mailMagaDictionary = self._csvToMap(self._mailMagaCSV, thisFormat)
        if self._smsDictionary is not None:
            self._mailMagaDictionary = self._verifyPresentInSms(
                                            smsDict=self._smsDictionary, 
                                            mailList=self._mailMagaDictionary)
        return self._genMailOutputFile( self._mailMagaDictionary )

    def retrieveSMSOutput(self):
        self._processNGCSV()
        if (self._eccubeCSV == None):
            return None
        thisFormat = self._acceptableFormat(self._eccubeCSV)
        self._validateEccubeData(self._eccubeCSV, thisFormat, 5, '会員ID')
        self._smsDictionary = self._csvToMap(self._eccubeCSV, thisFormat, True)
        return self._genSmsOutputFile( self._smsDictionary)



    # *** VALIDATION HELPERS *** #
    # -- Accepted formats: shift_jis, shiftjisx0213, utf-8 -- #
    # -- if CSV fails to compile in these formats, an encoding error should be raise -- #
    def _validateEccubeData(self, filepath, _encoding, columns, firstColumn):
        with open(filepath, encoding=_encoding) as csvfile:
            csv_data = csv.reader(csvfile)
            firstRow = next(csv_data)
            if len(firstRow) != columns:
                raise ColumnCount(columns, len(firstRow))
            if firstRow[0] != firstColumn:
                raise MatchingColumn(filepath, firstRow[0], firstColumn)

    def _acceptableFormat(self, filepath):
        for _encoding in self._ACCEPTED_ENCODINGS:
            if self._canDecode(filepath, _encoding): return _encoding
        raise AcceptableFormat(
            os.path.basename(
                filepath), self._ACCEPTED_ENCODINGS)
        
    def _canDecode(self, filepath, _encoding):
        try:
            # TODO this is where we can tell if it's a CSV or not
            csvfile = open(filepath, encoding=_encoding)
            csv_data = csv.reader(csvfile)
            for row in csv_data:
                # TODO this is a hack solution
                # text should be output to file and then delted
                print(', '.join(row))
        except UnicodeDecodeError:
            return False
        return True

    # REMOVED (but still cool, so comment is left)
    # def _detectEncoding(self, csvFilePath):
    #     detector = chardet.UniversalDetector()
    #     with open(csvFilePath, 'rb') as csvfile:
    #         for line in csvfile:
    #             detector.feed(line)
    #             if detector.done: break
    #         detector.close()
    #         return detector.result['encoding']



    # *** OUTPUT FUNCTIONS *** #
    # -- CREATES FILES ON THE SYSTEM -- #
    # -- Turn in-memory data structures into CSV for output -- #
    def _processNGCSV(self):
        thisFormat = self._acceptableFormat(self._ngCSV)
        self._validateEccubeData(self._ngCSV, thisFormat, 1, 'Email Address')
        self._ngSet = self._csvToSet(self._ngCSV, thisFormat)

    def _genSmsOutputFile(self, smsDict):
        filename = self._genFileName('SMSOutput')
        with open(filename, 'w+') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow( ['電話番号','会員ID','TEL1','TEL2','TEL3','(ラベル無し)','(ラベル無し)','(ラベル無し)','(ラベル無し)','(ラベル無し)','(ラベル無し)','(ラベル無し)','(ラベル無し)','(ラベル無し)','(ラベル無し)','(ラベル無し)',] )
            for key, value in smsDict.items():
                phoneNumber = value[2] + value[3] + value[4]
                writer.writerow( [phoneNumber, value[0]] + value[2:5] + [''] * 12 )
            return filename

    def _genMailOutputFile(self, okMailMaga):
        filename = self._genFileName('mailMagaOutput')
        with open(filename, 'w+') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            # writer.writerow( [ '会員id','e-mail','お名前(姓)','お名前(名)','購入回数' ] )
            for key, value in okMailMaga.items():
                writer.writerow( value[0:5] )
            return filename



    # *** CONVERSION FUNCTIONS *** #
    # -- Turn CSV into in-memory data structures -- #
    # -- logic for mungeing data found here. Munge munge munge! -- #
    def _csvToSet(self, filepath, encoding='shift_jis'):
        with open(filepath, encoding=encoding) as csvfile:
            eccube_data = csv.reader(csvfile)
            newSet = set()
            for row in eccube_data:
                newSet.add(row[0])
            return newSet

    def _csvToMap(self, filepath, fileEncoding, removeMobile=False):
        with open(filepath, encoding=fileEncoding) as csvfile:
            eccube_data = csv.reader(csvfile)
            newDict = dict()
            for row in eccube_data:
                if (removeMobile and self._checkForMobile(row[2])):
                    continue
                if (row[1] not in self._ngSet):
                    newDict[row[1]] = row
            return newDict



    # *** UTILITY FUNCTIONS *** #
    # -- Used during various stages for small tasks -- #
    def _checkForMobile(self, areaCode):
        if (CSVAlgs.regex1.match(areaCode) is not None):
            return False
        if (CSVAlgs.regex2.match(areaCode) is not None):
            return False
        if (areaCode in CSVAlgs.mobileCodes):
            return False
        return True

    def _verifyPresentInSms(self, smsDict, mailList):
        returnList = dict()
        for key, value in mailList.items():
            if (key in smsDict):
                returnList[key] = value
        return returnList

    def _genFileName(self, fileName):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S%Y-%m-%d')
        return settings.MEDIA_ROOT + fileName + timestamp + '.csv'