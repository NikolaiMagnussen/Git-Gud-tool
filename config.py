import configparser

# On 'config.ini' file
#
# [DEFAULT]
# KEY = Your API KEY
#

_config_parser = configparser.ConfigParser()
_config_parser.read('config.ini')
_key = _config_parser['DEFAULT']['KEY']


GIT_GUD_CONFIG = {
    'key': _key,

    'owners': {
        "GitHub_User_Name1",
        "GitHub_User_Name2",
        "GitHub_User_Name3"
    },

    'grading_file': "GRADING.md",

    'passed': 'Result: PASS',

    'failed': 'Result: FAIL',

    'commit_msg': 'Graded project, see the {}-file in the root directory',

}
