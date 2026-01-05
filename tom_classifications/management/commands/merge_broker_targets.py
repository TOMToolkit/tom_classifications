from django.core.management.base import BaseCommand
from tom_targets.models import Target, TargetList
from tom_alerts.brokers.mars import MARSBroker
from tom_antares.antares import ANTARESBroker
from tom_alerts.brokers.alerce import ALeRCEBroker
from tom_fink.fink import FinkBroker
from tom_alerts.brokers.lasair import LasairBroker
from merge_methods import *
import time, json, logging
from astropy.time import Time
from tom_classifications.models import TargetClassification

class Command(BaseCommand):

    help = 'This command calls two brokers, gets the alerts for a day and merges the alerts via Targets and TargetExtras'

    def add_arguments(self, parser):
        parser.add_argument('--ztf', help='Download data for a single target')

    def handle(self, *args, **options):
        
        st = time.time()

        # WATCH OUT!!! this line deletes all targets at the beginning of the script
        # are you sure this is what you want to do?
        # Target.objects.all().delete()
        mjd__lt = Time.now().mjd #maximum date
        mjd__gt = mjd__lt - 1 #minimum date
        
        FORMAT = '%(asctime)s %(message)s'
        logging.basicConfig(format = FORMAT, filename='/home/bmills/bmillsWork/tom_test/mytom/stream_merge.log', level=logging.INFO, force=True)
        logging.info(f'Stream Merge: mjd {mjd__gt} to {mjd__lt}')

        # mars_alert_list = self.get_mars(mjd__gt, mjd__lt)
        # merge_mars(mars_alert_list)

        # #start an antares broker and geth the alerts
        # antares_alert_list = self.get_antares(mjd__gt, mjd__lt)
        # merge_antares(antares_alert_list)

        # fink broker
        fink_alert_list = self.get_fink(mjd__gt, mjd__lt)
        # merge_fink(fink_alert_list)

        # # lasair broker
        # lasair_alert_list = self.get_lasair(mjd__gt, mjd__lt)
        # merge_lasair(lasair_alert_list)

        # #alerce broker
        # alerce_alert_list = self.get_alerce(mjd__gt, mjd__lt)
        # merge_alerce(alerce_alert_list)

        # print(len(Target.objects.all()), ' targets registered')


        # print(len(TargetList.objects.get(name = 'Duplicates').targets.all()), ' duplicates')
        # print(len(TargetList.objects.get(name = 'Triplicates').targets.all()), ' triplicates')
        

        #Timing report
        et = time.time()
        # print(round(et - st, 4), 'sec total')
        logging.info(f'There are now {len(Target.objects.all())} targets registered')
        return

    def get_mars(self, mjd__gt, mjd__lt):#no idea how to change length of output. might have to do with pagination
        # print('Getting MARS alerts')
        start_time = time.time()
        mars_broker = MARSBroker()
        mars_alerts = mars_broker.fetch_alerts({'jd__gt': mjd__gt+2400000, 'jd__lt': mjd__lt+2400000})
        # mars_alerts = mars_broker.fetch_alerts({'objectId': options['ztf']})
        mars_alert_list = list(mars_alerts)
        # print(f'Got {len(mars_alert_list)} MARS alerts')

        logging.info('MARS took {} sec to gather {} alerts'.format(time.time() - start_time, len(mars_alert_list)))
        return mars_alert_list

    def get_antares(self, mjd__gt, mjd__lt): #if you want to change the length of the outout you have to go to antares.py
        # print('Getting ANTARES alerts')
        t = time.time()
        antares_broker = ANTARESBroker()
        antares_alerts = antares_broker.fetch_alerts({'mjd__gt': mjd__gt, 'mjd__lt': mjd__lt, 'max_alerts': 50})
        #antares_alerts = antares_broker.fetch_alerts({'ztfid': options['ztf']})
        antares_alert_list = list(antares_alerts)
        # print(f'Got {len(antares_alert_list)} ANTARES alerts')

        logging.info('ANTARES took {} sec to gather {} alerts'.format(time.time() - t, len(antares_alert_list)))
        return antares_alert_list

    def get_fink(self, mjd__gt, mjd__lt):
        st = time.time()
        fink_broker = FinkBroker()
        fink_alert_list_big = []

        dur = mjd__lt-mjd__gt
        offset = 0
        i = 0
        while offset < dur:# and len(fink_alert_list_big) < 50: #this line keeps fink from running all 25000, comment out before and
            t = Time(mjd__gt + offset,format = 'mjd')
            window = 3
            if offset + window/24 > dur:
                window = dur - offset
            query = {
                'objectId': '', 
                'conesearch': '', 
                'datesearch': f'{t.iso}, {window*60}',
                'classsearch': '', 
                'classsearchdate': '', 
                'ssosearch': ''
            }
            offset += 3/24

            fink_alerts = fink_broker.fetch_alerts(query)

            fink_alert_list = list(fink_alerts)
            for a in fink_alert_list:
                fink_alert_list_big.append(a)
            i+=1

        logging.info(f'Fink took {time.time() - st } sec to gather {len(fink_alert_list_big)} alerts')
        return fink_alert_list_big

    def get_alerce(self, mjd__gt, mjd__lt):
        # print('Getting ALeRCE alerts')
        t = time.time()
        alerce_broker = ALeRCEBroker()
        query = {
            'stamp_classifier': '',
            'lc_classifier': '',
            'ra': '',
            'dec': '',
            'radius': '',
            'lastmjd__gt': mjd__gt,
            'lastmjd__lt': mjd__lt,
            'max_pages':5, #this line supresses a longer output
            'page_size': 5000
        }
        alerce_alerts = alerce_broker.fetch_alerts(query)
        alerce_alert_list = list(alerce_alerts)
        # print(json.dumps(alerce_alert_list[0], indent=3))
        # print(f'Got {len(alerce_alert_list)} ALeRCE alerts')

        logging.info('Alerce took {} sec to gather {} alerts'.format(time.time() - t, len(alerce_alert_list)))
        return alerce_alert_list
    
    def get_lasair(self, mjd__gt, mjd__lt):
        start_time = time.time()
        lasair_broker = LasairBroker()
        lasair_alerts = lasair_broker.fetch_alerts({'mjd__gt': mjd__gt, 'mjd__lt': mjd__lt, 'max_alerts': 50000})
        lasair_alert_list = list(lasair_alerts)

        logging.info('Lasair took {} sec to gather {} alerts'.format(time.time() - start_time, len(lasair_alert_list)))
        return lasair_alert_list

    def temp_func(self):
        
        return 'Success!'
