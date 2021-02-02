import xml.etree.ElementTree as ET
import sys, os, jinja2
import time

path = os.path.abspath("")
datapath = os.path.abspath("") + "\\data.xml"
tpath = os.path.abspath("") + "\\template.py"

class AutoClaim():
    def __init__(self, xmlpath  = os.path.abspath("")+"\\data.xml", ctype = False, isEvent = False):
        self.path = os.path.abspath("")
        self.xmlpath = xmlpath
        self.ctype = ctype
        self.isEvent = isEvent

    def getdata(self, dataname, ctype, isEvent):
        suf = ""
        if '1min' in dataname:
            suf = '1min'
        elif '15s' in dataname:
            suf = '15s'
        name = dataname.split('.')[-1] + suf
        if name == "return":
            name = name + "1"
        if ctype == False:
            return f"self.{name} = dr.GetData('{dataname}')"
        else:
            if isEvent == False:
                return name, f"{name}(sdc(\"{dataname}\")),", f"Smart_Sptr& {name};"
            else:
                return name, f"{name}(sdc.event(\"{dataname}\")),", f"Event_Sptr& {name};"

    def to_script(self, dataname, ctype = False,
                  template_name = "template.py",
                  path = os.path.abspath(""),
                  write_path = os.path.abspath("")+ "\\" + "claim" + time.strftime('%Y%m%d-%H%M%S', time.localtime(time.time())) + ".py"):
        if ctype == True:
            wptmp = list(write_path)
            wptmp = "".join(wptmp[:-3]) + ".cc"
            write_path = wptmp
            template_name = "template.cc"
        file_loader = jinja2.FileSystemLoader(path)
        env = jinja2.Environment(loader=file_loader)
        temp = env.get_template(template_name)
        output = temp.render(dataname = dataname)
        with open(write_path , "w") as f:
            f.write(output)

    def parse_xml(self, xmlpath, ctype, isEvent ):
        tree = ET.parse(xmlpath)
        root = tree.getroot()
        dataname = []
        for stockdata in root.findall("Data"):
            for data in stockdata.findall("name"):
                dataname.append(self.getdata(data.text, ctype, isEvent))
        return dataname

    def test_redundant(self):
        pass

    def main(self, template_name = "template.py",  path = os.path.abspath("")):
        dir_claim = os.path.abspath("") + "\\" + "claim"
        if not os.path.exists(dir_claim):
            os.makedirs(dir_claim)
        ctype = self.ctype
        write_path = os.path.abspath("") + "\\" + "claim\\" + time.strftime('%Y%m%d-%H%M%S', time.localtime(time.time())) + ".py"
        dataname = self.parse_xml(xmlpath=self.xmlpath, ctype=self.ctype, isEvent=self.isEvent)
        self.to_script(dataname, ctype = self.ctype, template_name = template_name,
                  path = path,
                  write_path = write_path)

if __name__ == "__main__":
    """"""
    at = AutoClaim(ctype=False, isEvent=True)
    at.main()
