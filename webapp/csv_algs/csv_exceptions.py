# a small collection of custom error messages 
# pertaining to the CSV_Algorithms library

class ColumnCount(Exception):
    def __init__(self, expected, found):
        self.message = f'''
        Mail Maga CSV did not have correct
        column count. 
        Expected: {expected}, Found: {found}
        '''

class MatchingColumn(Exception):
    def __init__(self, fileName, offendingColumn, correctColumn):
        self.message = f'''
        Expected {fileName} to posses column {correctColumn}
        but instead found {offendingColumn}. Please make sure
        that you have uploaded the correct CSV.
        '''

class AcceptableFormat(Exception):
    def __init__(self, fileName, acceptedEncodings):
        self.message = f'''
        The uploaded file {fileName} does not conform to any 
        of the accepted file encodings {acceptedEncodings}
        '''