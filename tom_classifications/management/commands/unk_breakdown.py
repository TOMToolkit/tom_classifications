from django.core.management.base import BaseCommand
from tom_targets.models import Target, TargetList
from tom_alerts.brokers.mars import MARSBroker
from tom_antares.antares import ANTARESBroker
from tom_alerts.brokers.alerce import ALeRCEBroker
from tom_fink.fink import FinkBroker
from tom_alerts.brokers.lasair import LasairBroker
from merge_methods import *
import time, json, logging, requests
from astropy.time import Time
from tom_classifications.models import TargetClassification
from dateutil.parser import parse
from urllib.parse import urlencode
from plotly import offline
from plotly.subplots import make_subplots
from plotly import graph_objs as go

class Command(BaseCommand):

    help = 'This is a playground function so I can quickly test things out'
    
    def add_arguments(self, parser):
        parser.add_argument('--ztf', help='Download data for a single target')

    def handle(self, *args, **options):
        with open('/home/bmills/bmillsWork/tom_test/mytom/broker_codes.txt') as json_file:#this loads the parentage dictionary that I made
            big_codes_dict = json.load(json_file)
        self.alerce_codes = big_codes_dict['alerce_stamp_codes']
        self.alerce_codes.update(big_codes_dict['alerce_lc_codes'])
        self.las_codes = big_codes_dict['las_codes']
        self.fink_codes = big_codes_dict['fink_codes']

        with open('/home/bmills/bmillsWork/tom_test/mytom/SIMBAD_otypes_labels.txt') as f:#this uses a file downloaded for simbad to deal with old codes
            for line in f:
                [_, code, old, new] = line.split('|')
                self.fink_codes[old.strip()] = code.strip()
                self.fink_codes[new.strip()] = code.strip()
        with open('/home/bmills/bmillsWork/tom_test/mytom/variability.txt') as json_file:#this loads the parentage dictionary that I made
            self.parents_dict = json.load(json_file)

        alfin = TargetList.objects.get(name = 'ALeRCE + Fink').targets.all()
        lasfin = TargetList.objects.get(name = 'Lasair + Fink').targets.all()
        lasfin_len = len(lasfin)
        alfin_len = len(alfin)

        alfin_f_unk = 0
        alfin_a_unk = 0
        alfin_a_bog = 0
        alfin_f_abi = 0
        alfin_f_503 = 0

        skip = 0
        for j, t in enumerate(alfin):
            tcs = t.targetclassification_set.all()
            try:
                fink_choice = self.fink_codes[tcs.filter(source='Fink').order_by('mjd', '-probability')[0].classification]
            except:
                skip += 1
                continue
            alerce_tcs = tcs.filter(source='ALeRCE')
            check_unk = len(alerce_tcs) == 1 and alerce_tcs[0].classification == 'Unknown'
            if check_unk:
                stamp_choice = '?'
                use_lc = False
            else:
                stamp_set = alerce_tcs.filter(level='lc_classifier').order_by('mjd', '-probability')
                use_lc = True
                if not stamp_set.exists():
                    use_lc=False
                    stamp_set = alerce_tcs.filter(level='stamp_classifier_1.0.4').order_by('mjd', '-probability')
                if not stamp_set.exists():
                    stamp_set = alerce_tcs.filter(level='stamp_classifier_1.0.0').order_by('mjd', '-probability')
                if not stamp_set.exists():
                    skip += 1
                    continue
                stamp_tc = stamp_set[0]
                stamp_choice = self.alerce_codes[stamp_tc.classification]

            choices = [stamp_choice, fink_choice]
            if stamp_choice == '?':
                alfin_a_unk += 1
            elif stamp_choice == 'bog':
                alfin_a_bog += 1
            if fink_choice == '?':
                alfin_f_unk += 1
            elif fink_choice == 'abi':
                alfin_f_abi += 1
            elif fink_choice == '503':
                alfin_f_503 += 1
            printProgressBar(j + 1, alfin_len, prefix = 'Alerce + Fink:', suffix = 'Complete', length = 50)

        print('alfin_f_unk', alfin_f_unk)
        print('alfin_a_unk', alfin_a_unk)
        print('alfin_a_bog', alfin_a_bog)
        print('alfin_f_abi', alfin_f_abi)
        print('alfin_f_503', alfin_f_503)

        lasfin_f_unk = 0
        lasfin_f_abi = 0
        lasfin_f_503 = 0
        lasfin_l_orp = 0
        skip = 0
        

        for j, t in enumerate(lasfin):
            tcs = t.targetclassification_set.all()
            try:
                las_choice = self.las_codes[tcs.filter(source='Lasair').order_by('mjd', '-probability')[0].classification]
                fink_choice = self.fink_codes[tcs.filter(source='Fink').order_by('mjd', '-probability')[0].classification]
            except:
                skip+=1
                continue
            if fink_choice == '?':
                lasfin_f_unk += 1
            elif fink_choice == 'abi':
                lasfin_f_abi += 1
            elif fink_choice == '503':
                lasfin_f_503 += 1
            if las_choice == 'ORPHAN':
                lasfin_l_orp += 1

            printProgressBar(j + 1, lasfin_len, prefix = 'Lasair + Fink:', suffix = 'Complete', length = 50)
        print('lasfin_f_unk', lasfin_f_unk)
        print('lasfin_l_orp', lasfin_l_orp)
        print('lasfin_f_abi', lasfin_f_abi)
        print('lasfin_f_503', lasfin_f_503)

        broker_pairs=['Alerce + Fink', 'Lasair + Fink']

        fig = go.Figure(data=[
            go.Bar(name='ALeRCE Unk', x=broker_pairs, y=[alfin_a_unk,0],),
            go.Bar(name='ALeRCE Bogus', x=broker_pairs, y=[alfin_a_bog,0], ),
            go.Bar(name='Fink Unk', x=broker_pairs, y=[alfin_f_unk, lasfin_f_unk], ),
            go.Bar(name='Fink Abi', x=broker_pairs, y=[alfin_f_abi, lasfin_f_abi],),
            go.Bar(name='Fink 503', x=broker_pairs, y=[alfin_f_503, lasfin_f_503],),
            go.Bar(name='Lasair Orphan', x=broker_pairs, y=[0, lasfin_l_orp], ),
        ])
        # Change the bar mode
        fig.update_layout(barmode='stack', title_text='Other Classifications',yaxis_title='Number of Classifications')
        fig.show()




