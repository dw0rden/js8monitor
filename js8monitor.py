import tkinter
import tkinter.messagebox
import customtkinter
from time import time
import sqlite3
import re
from js8net import *
import pyglet
import configparser
import winsound




customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

##########################################################################
""" DHW TODO
1)-done- Monitor is the default state
2)-done- write to DB always 
3)-done- Highlight active state
4) No- just set alarm and color --Filter monitor based on callsign and HB
5) test, test, test
6) document , thanks sources, submit change to js8net.py (Started)
7) create repository and make available
8)-done- set alarm on callsign1
9)-done- set alarm on callsign2
10) Maybe Color Code alarmed line in text box (See #4)
11) filter on Callsign1/2 add switch -- No seems redundant
12) QRZ data on selected callsign
13) Maybe some way to add transmitted text ?
14) well when xmitting on js8 we seem to lose connection to the main program
15) control params from a startup file
Startup params
config.ini
window appearance mode
-- done port and server for tcpip
-- done database name
sound if any
colors for text etc
"""


#############################################################
######## DB data for use by DB and realtime
#############################################################
class myData(object):
    js8port = ''
    js8host = ''
    db_file = ''
    alarm_sound = ''
    cqcolor = ''
    matchcolor = ''
    mycallsign = ""
    version = 'Beta 0.1.1'
    removeHB = True
    removeHBhist = False
    callsign1 = ""
    callsign2 = ""
    spantime = 86400 # 24hrs, 72 hrs, 1 week, 1 month  in ticks
    monitor = True
    alarm = False


class configfile():
    def __init__(self):
        config = configparser.ConfigParser()
        config.read_file(open(r'config.ini'))
        myData.js8port = config.get('IPCONFIG', 'js8port')
        myData.js8host = config.get('IPCONFIG', 'js8host')
        myData.db_file = config.get('DB', 'db_file')
        myData.alarm_sound = config.get('SOUND', 'alarm_file')
        myData.cqcolor = config.get('GENERAL','cqcolor')
        myData.matchcolor = config.get('GENERAL','matchcolor')
        #myData.version = config.get('GENERAL', 'version')

class Que():
    def __init__(self):
        print("Initialized test\n")
        ev=event()
        js8host = myData.js8host
        js8port = myData.js8port
        print("Connecting to JS8Call...")
        try:
            start_net(js8host, js8port)
            print("Connected.")
            myData.mycallsign=get_callsign()
            time.sleep(1)
        except :
            print("Network Connection Error\n")

    def getdata(self):
        #print("Checking the Queue\n")
        while (not (rx_queue.empty())):
            with rx_lock:
                self.rx = rx_queue.get()
                #print("Type: " + rx['type'] + "\n")
                #print(str(rx) + "\n")
                if self.rx['type'] == "RX.DIRECTED" :
                    print("Type: ", self.rx['type'])
                    print("FROM:   ", self.rx['params']['FROM'])
                    print("TO:     ", self.rx['params']['TO'])
                    if ('rxerror' in list(self.rx.keys())):
                        print("RX ERR: ", self.rx['rxerror'])
                    print("CMD:    ", self.rx['params']['CMD'])
                    print("GRID:   ", self.rx['params']['GRID'])
                    print("SPEED:  ", self.rx['params']['SPEED'])
                    print("SNR:    ", self.rx['params']['SNR'])
                    print("TDRIFT: ", str(int(self.rx['params']['TDRIFT'] * 1000)))
                    print("DIAL:   ", self.rx['params']['DIAL'])
                    print("OFFSET: ", self.rx['params']['OFFSET'])
                    print("FREQ:   ", self.rx['params']['FREQ'])
                    print("EXTRA:  ", self.rx['params']['EXTRA'])
                    print("TEXT:   ", self.rx['params']['TEXT'])
                    print("TIME: ", str((self.rx['time'])))
                    print()

                    y = self.rx['params']['FROM'] + "\t| " + self.rx['params']['TO'] + "\t| " + self.rx['params']['CMD'] + "\t| " + self.rx['params']['GRID']  + "\t| " + str(self.rx['params']['SNR'])+  "\t| " + self.rx['params']['TEXT'] +  "\t| " + time.asctime(time.localtime(self.rx['time'])) + "\n---------------------------------------------------------------------------------------------------------------------------------\n"
                    if myData.monitor == True:
                        if myData.callsign1 == self.rx['params']['FROM'] or myData.callsign2 == self.rx['params']['TO']:
                            app.sound_alarm()
                            textag=myData.matchcolor
                        elif 'CQ' in self.rx['params']['CMD']:
                            textag=myData.cqcolor
                        else:
                            textag="none"
                            # do something here to set print color for this line.

                    if myData.removeHB == False :
                        app.pushtotextbox(y,textag)
                    if myData.removeHB == True and "HEARTBEAT" not in self.rx['params']['CMD']:
                        app.pushtotextbox(y,textag)

                    if myData.removeHBhist == False :
                        mT.create_entry(self.rx)
                    if myData.removeHBhist == True and "HEARTBEAT" not in self.rx['params']['CMD']:
                        mT.create_entry(self.rx)


#############################################################
######## DB class
#############################################################
class mydb(object):

    def __init__(self):
        self.list = None
        self.conn = None
        e=""
        db_file = myData.db_file
        try:
            self.conn = sqlite3.connect(db_file, check_same_thread=False)
        except sqlite3.Error as e:
            print(e)

        sql_create_data_table = """CREATE TABLE IF NOT EXISTS js8data(
                                            id integer PRIMARY KEY,
                                            XMIT text NOT NULL,
                                            RCV text,
                                            RX_ERR text,
                                            CMD  text,
                                            GRID text,
                                            SPEED text,
                                            SNR text,
                                            DIAL text,
                                            OFFSET text,
                                            EXTRA text,
                                            TEXT text,
                                            TIME int
                                        );"""
        try:
            c = self.conn.cursor()
            c.execute(sql_create_data_table)
        except sqlite3.Error as e:
            print(e)


        # Type:  RX.DIRECTED
        # FROM:    WE4SEL
        # TO:      K1OEV
        # RX ERR:  False
        # CMD:      SNR
        # GRID:
        # SPEED:   0
        # SNR:     -16
        # TDRIFT:  -2099
        # DIAL:    7078000
        # OFFSET:  2042
        # EXTRA:   -02
        # TEXT:    WE4SEL: K1OEV SNR -02 ♢


    def create_entry(self, rx):
        XMIT = rx['params']['FROM']
        RCV = rx['params']['TO']
        RX_ERR = rx['rxerror']
        CMD = rx['params']['CMD']
        GRID = rx['params']['GRID']
        SPEED = rx['params']['SPEED']
        SNR = rx['params']['SNR']
        DIAL = rx['params']['DIAL']
        OFFSET = rx['params']['OFFSET']
        FREQ = rx['params']['FREQ']
        EXTRA = rx['params']['EXTRA']
        TEXT = rx['params']['TEXT']
        TIME = rx['time']

        sql = ''' INSERT INTO js8data(XMIT,RCV,RX_ERR,CMD,GRID,SPEED,SNR,DIAL,OFFSET,EXTRA,TEXT,TIME)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?) '''
        c = self.conn.cursor()
        c.execute(sql, (XMIT, RCV, RX_ERR, CMD, GRID, SPEED, SNR, DIAL, OFFSET, EXTRA, TEXT, TIME))
        self.conn.commit()

    # Python3 code to remove whitespace
    def remove(self,string):
        pattern = re.compile(r'\s+')
        return re.sub(pattern, '', string)

    def read_from_db(self):
        print (myData.callsign1 + "\n")
        #print ("SpanTime = " + str(self.spantime))
        e=""
        querytime = time.time() - myData.spantime
        db_query = "select * from js8data where time >= '" + str(querytime) + "' "
        no_hb = "and RCV !='@HB' and CMD not like '%HEARTBEAT%' "
        sortcallsigns = "and XMIT=='' and RCV=='' "
        # remove heartbeats
        if myData.removeHB  :
            db_query += no_hb 
        # sort on call signs
        # clean up callsigns first
        myData.callsign1=self.remove(myData.callsign1)
        myData.callsign2=self.remove(myData.callsign2)

        myData.callsign1 = "%" + myData.callsign1 + "%"
        myData.callsign2 = "%" + myData.callsign2 + "%"    
        db_query += " and XMIT like'" + myData.callsign1 +"' and RCV like'" + myData.callsign2 + "'" 
            
        print ("\n\n******** " + db_query + " *******\n\n")      
        if self.conn is not None:
            try:
                info=""
                c = self.conn.cursor()
                c.execute(db_query)
                data = c.fetchall()
                #print(data)
                for row in data:
                    info += str(row[1]) + "\t| " + str(row[2]) + "\t| "  
                    info += str(row[4]) + "\t| " + str(row[5]) + "\t| " + str(row[7]) + "\t| "
                    info += str(row[8]) + "\t| "  + str(row[11]) + "\t| " + time.asctime( time.localtime(row[12]) )  
                    info += "\n"
                    info += "-----------------------------------------------------------------------------------\n"
                    #print(info)
                return(info)
            except sqlite3.Error as e:
                print(e) 

#######################################################################

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("js8monitor " + myData.version + " : " + myData.mycallsign)
        self.geometry(f"{1100}x{580}")
        self.count = 0
        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((2), weight=0)
        self.grid_rowconfigure((0,1), weight=1)
        self.grid_rowconfigure((4,5),weight=1 )
        ##############################################################################
        # create left sidebar frame with widgets
        ################ SIDEBAR #####################################################
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")
        self.sidebar_frame.grid_columnconfigure((2, 3), weight=0)
        self.sidebar_frame.grid_rowconfigure((3), weight=1)
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="js8Monitor", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        # set monitor button
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, border_width=2,border_color='yellow', text="Monitor" , command=self.sidebar_button_event_monitor)
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        # set historical button
        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, border_width=2, text="Historical" , command=self.sidebar_button_event_historical)
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
                                                               #command=self.change_scaling_event)
        #self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))
        ###################################################################
        ### End SIDEBAR
        ###################################################################
        

        #####################################################################
        # create textbox
        #####################################################################
        self.textbox = customtkinter.CTkTextbox(self, width=250) #, text_color="white"
        self.textbox.grid(row=0, column=1, padx=(20, 20), pady=(20, 0), sticky="nsew")
        self.textbox.grid(rowspan=5)
        self.textbox.tag_config("red", foreground="red")
        self.textbox.tag_config("green", foreground="green")
        self.textbox.tag_config("yellow", foreground="yellow")
        self.textbox.tag_config("blue", foreground="blue")
        self.textbox.tag_add("red", '0.0', '0.5')
        self.textbox.tag_add("green", '0.0', '0.5')
        self.textbox.tag_add("yellow", '0.0', '0.5')
        self.textbox.tag_add("blue", '0.0', '0.5')
        self.textbox.tag_add("none", '0.0', '0.5')


        ####################################################################
        # create sort frame
        ####################################################################
        self.sort_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.sort_frame.grid(row=5, column=1, columnspan=2, padx=(20, 20), pady=(5, 0), sticky="nsew")
        self.sort_frame.grid_columnconfigure(3, weight=0)
        self.sort_frame.grid_rowconfigure((2,3,4,5), weight=1)
        self.sort_frame.grid_rowconfigure((1),weight=10)
        
        self.remove_hb = customtkinter.CTkSwitch(master=self.sort_frame,state="on",text="Remove HB, Mon" ,command= self.remove_hb_cmd)
        self.remove_hb.grid(row=0, column=1, pady=(10,10), padx=20, sticky="n")      
        
        self.remove_hbhistorical = customtkinter.CTkSwitch(master=self.sort_frame,state="on",text="Remove HB, db " ,command= self.remove_hb_hist)
        self.remove_hbhistorical.grid(row=1, column=1, pady=(10,10), padx=20, sticky="n")

        self.combobox_1 = customtkinter.CTkComboBox(master=self.sort_frame, values=["24 Hours", "72 Hours", "1 Week", "1 Month"],command=self.readcombobox)
        self.combobox_1.grid(row=0, column=2, padx=20, pady=(10,20))
                
        self.callsign1 = customtkinter.CTkEntry(master=self.sort_frame)#,textvariable = self.call1_var
        self.callsign1.grid(row=0, column=3, pady=(10,10), padx=20, sticky="n")
        self.callsign1.bind('<KeyRelease>', self.dataevent)
        
        self.callsign2 = customtkinter.CTkEntry(master=self.sort_frame)#,textvariable = self.call2_var
        self.callsign2.grid(row=0, column=4, pady=(10,10), padx=20, sticky="n")
        self.callsign2.bind('<KeyRelease>', self.dataevent)

        self.alarm = customtkinter.CTkSwitch(master=self.sort_frame, state="on", text="Alarm", command=self.alarm_cmd)
        self.alarm.grid(row=1, column=3, pady=(10, 10), padx=20, sticky="n")

        self.remove_hb.select()
        self.appearance_mode_optionemenu.set("Dark")

    #####################################################################
    ########### Dialog
    #####################################################################
    def open_input_dialog_event(self):
        dialog = customtkinter.CTkInputDialog(text="Type in a number:", title="CTkInputDialog")
        print("CTkInputDialog:", dialog.get_input())

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def pushtotextbox(self, y, textag):
        self.count = self.count + 1
        y = str(self.count) + ": "+ y
        self.textbox.insert('1.0', y, textag)

    def sidebar_button_event_monitor(self):
        #self.textbox.insert("0.0",text="Monitoring" )
        myData.monitor = True
        get_callsign()
        #if get_callsign():
        self.sidebar_button_1.configure(border_color='yellow')
        self.sidebar_button_2.configure(border_color='blue')
        self.textbox.delete("0.0",'end')
        #else:
        #    self.textbox.delete("0.0", 'end')
        #    self.textbox.insert("0.0", text="TCPIP Failure !")
        #print("sidebar_button click")

    def sidebar_button_event_historical(self):
        myData.monitor = False
        self.sidebar_button_1.configure(border_color='blue')
        self.sidebar_button_2.configure(border_color='yellow')

        self.textbox.delete('1.0',"end" )
        self.textbox.insert("0.0",text=mydb().read_from_db())
        #print("sidebar_button click")

    def alarm_cmd(self):
        val = self.alarm.get()
        if val == 1:
            myData.alarm = True
        else:
            myData.alarm = False

    def sound_alarm(self):
        winsound.PlaySound(myData.alarm_sound, winsound.SND_FILENAME)

    def remove_hb_cmd(self):
        val = self.remove_hb.get()
        if val==1:
            myData.removeHB = True       
        else:
            myData.removeHB = False
        #self.sidebar_button_event_historical()
        #print(str(val) + "\n")

    def remove_hb_hist(self):
        val = self.remove_hbhistorical.get()
        if val==1:
            myData.removeHBhist = True
        else:
            myData.removeHBhist = False
        #self.sidebar_button_event_historical()
        #print(str(val) + "\n")
        
    def readcombobox(self, val):
        if val=="24 Hours" :
            myData.spantime = 86400
        elif val=="72 Hours":
            myData.spantime = 259200
        elif val=="1 Week" : 
            myData.spantime = 604800
        elif val=="1 Month" :
            myData.spantime = 2592000
        else:
            myData.spantime = 86400
        #print ("spantime = " + str(mydb.spantime) + "\n")
        
    def dataevent(self,Event):
        print (Event)
        c1=self.callsign1.get()
        c2=self.callsign2.get()
        c1 = c1.upper()
        c2 = c2.upper()
        self.callsign1.delete(0,20)
        self.callsign1.insert(0,c1)
        self.callsign2.delete(0,20)
        self.callsign2.insert(0,c2)
        myData.callsign1=self.callsign1.get()
        myData.callsign2=self.callsign2.get()
        #print ( "callsign1 :",c1, "callsign2 :",c2 ,"\n")

if __name__ == "__main__":
    cf = configfile()
    tt = Que()
    ev += tt.getdata

    mT = mydb()
    app = App()
    app.mainloop()

