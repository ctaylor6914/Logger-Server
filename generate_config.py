import configparser

config_file = configparser.ConfigParser()                   #create object

config_file.add_section("IPSettings")                     #add selection

config_file.set("IPSettings", "ipAddress", "127.0.0.1")     #add settings
config_file.set("IPSettings", "port", "30000")


config_file["Log"] = {   #add log section
    "filePath":"",
    "fileName":"",
    "logLevel":""
}               


with open(r"configuration.ini", 'w') as configfileobj:      #save config File
    config_file.write(configfileobj)
    configfileobj.flush()
    configfileobj.close()