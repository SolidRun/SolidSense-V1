#-------------------------------------------------------------------------------
# Name:        PppService
# Purpose:    Provisionning of the PppService
#
# Author:      Laurent
#
# Created:     27/11/2019
# Copyright:   (c) Laurent Carré Sterwen Technologies 2019
# Licence:     Eclipse Public License 1.0
#-------------------------------------------------------------------------------
import os, sys, inspect
# cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0], "../modem_gps")))
sys.path.insert(0, '/opt/SolidSense/modem_gps')

import json
import logging
import stat

from SolidSenseService import *
try:
    from QuectelAT_Service import *
except ImportError :
    pass

from provisioning_utils import *

loclog=logging.getLogger('SolidSense-provisioning')


class PppService(NetworkService):

    def __init__(self,kura_config,def_dict):
        NetworkService.__init__(self,kura_config,def_dict)



    def configuration(self):
        modem=self._kura_config.get_service('modem_gps')
        if modem == None:
            self._state=state_DISABLED
            loclog.error("Ppp Service => No supporting modem service")
            self._valid = False
        else:
            self._valid = modem.valid()
            if not self._valid :
                loclog.error('Ppp Service => No valid modem')

        if not self._valid :
            return
        if self._state == state_DISABLED :
            return
        NetworkService.configuration(self)
        kura_id=self._kura_config.get_variable('MODEM_KURAID')
        # check that we have an APN
        apn=self.variableValue("APN")
        if apn == None or len(apn) < 2 :
            loclog.error("Invalid APN - ppp not configured -APN="+str(apn))
            return
        #
        #  generations of the files
        #
        #  peer file
        peersdir=self._kura_config.output_dir('/etc/ppp/peers')
        peer=os.path.join(peersdir,kura_id)
        self._kura_config.gen_from_template(self,'ppp','peer.tmpl',peer)
        # chat
        outdir=self._kura_config.output_dir('/etc/ppp/scripts')
        # check if the scripts dir is existing
        if not os.path.exists(outdir) :
            os.mkdir(outdir)

        outfile=os.path.join(outdir,'chat_'+kura_id)
        self._kura_config.gen_from_template(self,'ppp','chat.tmpl',outfile)
        # disconnect
        outfile=os.path.join(outdir,'disconnect_'+kura_id)
        self._kura_config.gen_from_template(self,'ppp','disconnect.tmpl',outfile)
        if isWindows():
            return
        # generate the link
        port=os.path.join(peersdir,self._name)
        try:
            res=os.lstat(port)
            os.remove(port)
        except IOError :
            pass

        os.symlink(peer,port)

        #
        #  /etc/ppp/options file
        #
        outfile='/etc/ppp/options'
        fd=open(outfile,'w')
        loclog.info("Generating "+outfile)
        fd.write('lock\n')
        if self.asParameter('mtu') :
            mtu=self.parameterValue('mtu')
            try:
                if mtu > 300 and mtu < 2500 :
                    loclog.debug("mtu "+str(mtu))
                    line="mtu %d\n" % mtu
                    fd.write(line)
                else:
                    loclog.error("MTU size incorrect falling to default")
            except (TypeError,ValueError) :
                loclog.error("Wrong MTU, shall be integer")
        fd.close()

        #
        #   create entry in secret files
        #
        def add_secret_entry(file):
            filename=os.path.join('/etc/ppp',file)
            try:
                fd=open(filename,'a')
            except IOError as err:
                servlog.error(str(err))
                return
            line="%s\t*\t%s\t*\t#%s\n"%(user,passwd,model)
            fd.write(line)
            fd.close()


        if self.asVariable('APN_AUTH') :
            auth=self.variableValue('APN_AUTH')
            gen_pap=False
            gen_chap=False
            if auth == 'AUTO' or auth == 'PAP':
                gen_pap= True
            if auth == 'AUTO' or auth == 'PAP':
                gen_chap=True
            if not(gen_pap or gen_chap ):
                return
            user=self.variableValue('APN_USER')
            if user == None : user=""
            passwd=self.variableValue('APN_PASSWORD')
            if passwd == None : passwd = ""
            model=self.variableValue('MODEM_MODEL')
            if gen_chap :
               add_secret_entry('chap-secrets')
            if gen_pap :
                add_secret_entry('pap-secrets')



class ModemGps(SolidSenseService):

    def __init__(self,kura_config,def_dict):
        SolidSenseService.__init__(self,kura_config,def_dict)
        if isWindows():
            kura_config.set_variable('MODEM_MODEL',"EC25")
            self._state='active'
            self._valid=True
            kura_config.set_variable('MODEM_KURAID',"EC25_2-1.2")
        else:

            if QuectelModem.chekModemPresence() :
                self._valid=False
                return

            tty1=self.parameterValue('modem_ctrl')
            if not os.path.exists(tty1) :
                loclog.error('Modem service => TTY control file not existing:'+tty1)
                self._valid=False
                return
            mode=os.stat(tty1).st_mode
            if stat.S_ISCHR(mode) == 0 :
                loclog.error('Modem service => Invalid TTY control file:'+tty1)
                self._valid=False
                return
            # Now some basic checks on the modem
            try:
                modem = QuectelModem(tty1)
            except ModemException as err:
                loclog.error('Modem Service => Error during modem access:'+str(err))
                self._valid=False
                return
            except ImportError :
                loclog.error('Modem Service => Missing Quectel AT module')
                self._valid=False
                return
            #
            #  now get the parameters
            #

            modem_kura_id=modem.model()+"_"+mdm_usb['dev_path']

            kura_config.set_variable('MODEM_MFG',modem.manufacturer())
            kura_config.set_variable('MODEM_MODEL',modem.model())
            kura_config.set_variable('MODEM_IMEI',modem.IMEI())
            kura_config.set_variable('MODEM_SIM_IN',modem.SIM_Present())
            kura_config.set_variable('MODEM_KURAID',modem_kura_id)
            self._valid= True
            if self._state == state_AUTO :
                self._state = state_ACTIVE




    def valid(self):
        return self._valid


    def configuration(self):
        if self._state == state_ACTIVE and self._valid :
            self._parameters['start_gps_service']= True
        else:
            self._parameters['start_gps_service']= False
        self._system_serv=self._parameters.get('system')
        try:
            del self._parameters['system']
        except KeyError :
            pass
        outdir=self._kura_config.output_dir('/data/solidsense/modem_gps')
        param=os.path.join(outdir,'parameters.json')
        checkCreateDir(outdir)
        try:
            fd=open(param,'w')
        except IOError as err:
            loclog.error("ModemGps "+param+ " "+str(err))
            return
        json.dump(self._parameters,fd,indent=1)
        fd.close()

    def startService(self):
        if self._state == state_ACTIVE :
            servlog.info('Systemd activation for: '+self._name)
            systemCtl('enable',self._system_serv)
            systemCtl('start',self._system_serv)


def main():
    pass

if __name__ == '__main__':
    main()
