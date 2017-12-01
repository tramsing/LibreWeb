# This is a part of LibreWeb project


def dir_as_string(argument):
    string = ""
    for i in dir(argument):
        string = string + i + " -- "
    return string


def get_save_dir(ctx):
    '''Returns the save file directory, if don't
       exists, it will be created'''
    from settings import save_dir_name
    import unohelper
    import os
    _path = ctx.ServiceManager.createInstance("com.sun.star.util.PathSubstitution")
    user_dir = _path.getSubstituteVariableValue("$(user)")
    user_dir = unohelper.fileUrlToSystemPath(user_dir)
    save_dir = os.path.join(user_dir, save_dir_name)
    if save_dir_name not in os.listdir(user_dir):
        os.mkdir(save_dir)
    return save_dir


def get_local_data(ctx):
    '''Returns the save file '''
    from settings import save_file_name
    import os.path
    return os.path.join(get_save_dir(ctx), save_file_name)


def get_settings_file(ctx, msg_box):
    '''Returns the settings file'''
    from settings import settings_file
    import os.path
    file_url = os.path.join(get_save_dir(ctx), settings_file)
    if not os.path.isfile(file_url):
        try:
            from savemodule import LibreWebPickle
            file = LibreWebPickle(file_url)
            file.save({})
        except OSError as error:
            if error.errno == 13:
                msg_box.show("You have no rights to create settings file",
                             "Attention, 2")
    return file_url


def open_url(url, message_box, default_decoding="utf-8"):
    '''Function that try to open,read and decode a web site
     '''
    import urllib.error
    import urllib.request
    try:
        result = urllib.request.urlopen(url).read().decode(default_decoding)
        return result
    except UnicodeDecodeError:
        message_box.show("Site is not utf-8 encoded", "Error", 2)

    except ValueError as error:
        message_box.show("Invalid URL", "Attention", 2)

    except urllib.error.URLError:
        message_box.show("Site not reachable or internet connection is missing",
                         "Attention", 2)

    except Exception as error:
        str_error = ""
        for i in error.args:
            str_error = str_error + "\n" + str(i)
            message_box.show(str_error, "Attention", 2)


def start_service(smgr, document, message_box, *args):
    try:
        from docsave import read_file, check_save_file
        from parsermodule import LibreWebParser

        if check_save_file(document):
            stored_data = read_file(smgr, document)
        else:
            message_box.show("This document has no saved data, \n please select Set data from menu.", "Attention", 1)
            return

        sheets = document.Sheets.ElementNames
        stored_sheets = list(stored_data.keys())
        for sheet_name in stored_sheets:
            if sheet_name in sheets:
                sheet = document.Sheets.getByName(sheet_name)
                url_list = list(stored_data[sheet_name].keys())
                for url in url_list:
                    result = open_url(url, message_box)
                    if result:
                        tag_list = list(stored_data[sheet_name][url].keys())
                        for tag in tag_list:
                            my_parser = LibreWebParser(tag)
                            my_parser.feed(result)
                            if my_parser.collectedData:
                                cell_list = list(stored_data[sheet_name][url][tag].keys())
                                for cell in cell_list:
                                    cell_items = stored_data[sheet_name][url][tag][cell]
                                    cell_data = my_parser.collectedData[cell_items[0]]
                                    if cell_items[1] == "String":
                                        sheet.getCellRangeByName(cell).setString(cell_data)
                                    elif cell_items[1] == "Value":
                                        try:
                                            sheet.getCellRangeByName(cell).setValue(cell_data)
                                        except:
                                            sheet.getCellRangeByName(cell).setString(cell_data)

        message_box.show("Operation completed.", "Message", 1)

    except:
        message_box.show("Error on start_service", "Attention", 2)


def get_cur_version(ctx):
    '''A function that return a string with current extension version'''
    ext = ctx.ServiceManager.createInstance(
        "com.sun.star.comp.deployment.PackageInformationProvider"
    )
    for i in ext.ExtensionList:
        if "com.libreweb.web" in i[0]:
            return i[1]


def get_help_file(smgr, desktop, ext_id, help_name):
    '''Open help file'''
    ext = smgr.createInstance(
        "com.sun.star.comp.deployment.PackageInformationProvider"
    )
    ext_url = ext.getPackageLocation(ext_id)
    help_url = "{}/{}".format(ext_url, help_name)
    desktop.loadComponentFromURL(help_url, "_blanc", 0, [])


def get_online_version():
    '''A function that looks for an update on different sites,
        like extensions site and github
        returns a tuple with 2 args,arg[0] = version nr'
        arg[1] = update's web site'''
    from parsermodule import LibreWebParser
    from settings import update_source as sites
    import urllib.request
    try:
        for arg in sites:
            result = urllib.request.urlopen(arg[0]).read().decode()
            parser = LibreWebParser(arg[1])
            parser.feed(result)
            for elem in parser.collectedData:
                if "LibreWeb" and ".oxt" in elem:
                    return (elem[-9:-4], arg[0])
    except:
        pass


def verify_update(ctx, msg_box):
    '''Function that asks for download if a new version is
       available,if positive answer opens a web page with new version.'''
    from messagebox import BUTTONS_OK_CANCEL, OK, QUERYBOX

    online_version = get_online_version()
    cur_version = get_cur_version(ctx)
    if online_version and online_version[0] > cur_version:
        if msg_box.show(
                "Would you like to download it?",
                                "Version " + online_version[0] + " is available", QUERYBOX, BUTTONS_OK_CANCEL) == OK:
            import webbrowser
            webbrowser.open(online_version[1])
            return True
        else:
            return True


# version 1.0.7
'''
def do_update(ctx, msg_box):
    
    from datetime import date
    from savemodule import LibreWebPickle
    from settings import last_update_key, check_update_period
    file_url = get_settings_file(ctx, msg_box)
    file = LibreWebPickle(file_url)
    file_read = file.read()
    today = date.today()
    if last_update_key not in file.read().keys():
        _verify_update(ctx, msg_box)
        file_read[last_update_key] = today
        file.save(file_read)
    else:
        delta = today - file_read[last_update_key]
        if delta.days >= check_update_period:
            _verify_update(ctx, msg_box)
            file_read[last_update_key] = today
            file.save(file_read)
'''


def send_mail(ctx, subject, message):
    from settings import send_to
    email_instance = ctx.ServiceManager.createInstance("com.sun.star.system.SimpleSystemMail")
    email_client = email_instance.querySimpleMailClient()
    mail = email_client.createSimpleMailMessage()
    mail.Recipient = send_to
    mail.Body = message
    mail.Subject = subject
    email_client.sendSimpleMailMessage(mail, 0)
