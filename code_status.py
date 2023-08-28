# encoding:utf-8
class code_status():
    def __init__(self):
        # no action
        self.success = 0

        # return
        self.success_elementActionRequired = 4001
        self.success_EmptyResult = 4002

        # data exist
        self.data_success = 3000  # TOKEN
        self.data_downloadable = 3001  # PAHT

        # msg needed
        self.msg_show = 1000
        self.msg_inputIncorrect = 1001
        self.msg_inputChangeRequired = 1002
        self.msg_success = 1003
        self.msg_operationFailed = 1100
        self.msg_dbOperationFailed = 1101

        # redirect needed
        self.msg_redirect_tokenRequired = 2000
        self.msg_redirect_tokenOutdate = 2001
        self.msg_redirect_noAccess = 2100