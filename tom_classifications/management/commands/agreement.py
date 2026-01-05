from django.core.management.base import BaseCommand
from tom_targets.models import TargetList
import json
from plotly import graph_objs as go
from os import path
from django.conf import settings

class Command(BaseCommand):

    help = 'This command runs over all the targets in duplicate lists of classifying brokers, and for each one, using the heirarchy, decides if the brokers agree or not using the '
    
    def add_arguments(self, parser):
        parser.add_argument('--ztf', help='Download data for a single target')

    def handle(self, *args, **options):
        '''
        This method requires that the TargetLists of three pairs of brokers be populated and named according to lines 35-37

        '''
        with open(path.join(settings.MEDIA_ROOT,'broker_codes.txt')) as json_file:#this loads the parentage dictionary that I made
            big_codes_dict = json.load(json_file)
        self.alerce_codes = big_codes_dict['alerce_stamp_codes']
        self.alerce_codes.update(big_codes_dict['alerce_lc_codes'])
        self.las_codes = big_codes_dict['las_codes']
        self.fink_codes = big_codes_dict['fink_codes']

        with open(path.join(settings.MEDIA_ROOT,'SIMBAD_otypes_labels.txt')) as f:#this uses a file downloaded for simbad to deal with old codes
            for line in f:
                [_, code, old, new] = line.split('|')
                self.fink_codes[old.strip()] = code.strip()
                self.fink_codes[new.strip()] = code.strip()
        with open(path.join(settings.MEDIA_ROOT,'variability.txt') )as json_file:#this loads the parentage dictionary that I made
            self.parents_dict = json.load(json_file)

        alfin = TargetList.objects.get(name = 'ALeRCE + Fink').targets.all()
        lasfin = TargetList.objects.get(name = 'Lasair + Fink').targets.all()
        allas = TargetList.objects.get(name = 'ALeRCE + Lasair').targets.all()
        alfin_len = len(alfin)
        lasfin_len = len(lasfin)
        allas_len = len(allas)

        allas_agree = 0
        allas_disag = 0
        allas_unk = 0
        skip = 0
        for j, t in enumerate(allas):
            tcs = t.targetclassification_set.all()
            try:
                las_choice = self.las_codes[tcs.filter(source='Lasair').order_by('mjd', '-probability')[0].classification]
            except:
                skip+=1
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
            catch_list = ['SN*', 'CV*', 'AGN', 'V*', '?', '~Alert']
            choices = [las_choice, stamp_choice]
            if '?' in choices or 'err' in choices:
                allas_unk += 1
                continue
            for i in range(len(choices)):
                while not choices[i] in catch_list:
                    choices[i] = self.parents_dict[choices[i]]
            
            if choices[0] == '~Alert' and choices[1] == '~Alert':
                allas_disag += 1
            elif choices[0] == choices[1]:
                allas_agree += 1
            else:
                allas_disag += 1
            self.printProgressBar(j + 1, allas_len, prefix = 'Alerce + Lasair:', suffix = 'Complete', length = 50)
            
        print('allas', allas_agree, allas_disag, allas_unk, skip)

        lasfin_agree = 0
        lasfin_disag = 0
        lasfin_unk = 0
        skip = 0
        for j, t in enumerate(lasfin):
            tcs = t.targetclassification_set.all()
            try:
                las_choice = self.las_codes[tcs.filter(source='Lasair').order_by('mjd', '-probability')[0].classification]
                fink_choice = self.fink_codes[tcs.filter(source='Fink').order_by('mjd', '-probability')[0].classification]
            except:
                skip+=1
                continue

            catch_list = ['SN*', 'CV*', 'AGN', 'V*', '?', '~Alert']
            choices = [las_choice, fink_choice]
            if '?' in choices or 'err' in choices:
                lasfin_unk += 1
                continue
            for i in range(len(choices)):
                while not choices[i] in catch_list:
                    choices[i] = self.parents_dict[choices[i]]
            if choices[0] == '~Alert' and choices[1] == '~Alert':
                lasfin_disag += 1
            elif choices[0] == choices[1]:
                lasfin_agree += 1
            else:
                lasfin_disag += 1
            self.printProgressBar(j + 1, lasfin_len, prefix = 'Lasair + Fink:', suffix = 'Complete', length = 50)
            
        print('lasfin', lasfin_agree, lasfin_disag, lasfin_unk, skip)

        alfin_agree = 0
        alfin_disag = 0
        alfin_unk = 0
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

            if use_lc:
                catch_list = ['SN*', 'CV*', 'AGN', 'QSO', 'LP*', 'Ce*', 'RR*', 'dS*', 'Pu*', 'EB*', 'Y*O', 'V*', '?', 'SSO', '~Alert']
            else:
                catch_list = ['SN*', 'AGN', 'V*', '?', 'SSO', '~Alert']
            choices = [stamp_choice, fink_choice]
            if '?' in choices or 'err' in choices:
                alfin_unk += 1
                continue
            for i in range(len(choices)):
                while not choices[i] in catch_list:
                    choices[i] = self.parents_dict[choices[i]]
            if choices[0] == '~Alert' and choices[1] == '~Alert':
                alfin_disag += 1
            elif choices[0] == choices[1]:
                alfin_agree += 1
            else:
                alfin_disag += 1
            self.printProgressBar(j + 1, alfin_len, prefix = 'Alerce + Fink:', suffix = 'Complete', length = 50)
        print('alfin', alfin_agree, alfin_disag, alfin_unk, skip)

        broker_pairs=['Alerce + Fink', 'Lasair + Fink', 'ALeRCE + Lasair']

        # fig = go.Figure(data=[
        #     go.Bar(name='Agree', x=broker_pairs, y=[alfin_agree/alfin_len, lasfin_agree/lasfin_len, allas_agree/allas_len], marker_color='lightgreen'),
        #     go.Bar(name='Disagree', x=broker_pairs, y=[alfin_disag/alfin_len, lasfin_disag/lasfin_len, allas_disag/allas_len], marker_color='tomato'),
        #     go.Bar(name='Unknown/Bogus', x=broker_pairs, y=[alfin_unk/alfin_len, lasfin_unk/lasfin_len, allas_unk/allas_len], marker_color='lightgray')
        # ])
        fig = go.Figure(data=[
            go.Bar(name='Agree', x=broker_pairs, y=[alfin_agree, lasfin_agree, allas_agree], marker_color='lightgreen'),
            go.Bar(name='Disagree', x=broker_pairs, y=[alfin_disag, lasfin_disag, allas_disag], marker_color='tomato'),
            go.Bar(name='Unknown/Bogus', x=broker_pairs, y=[alfin_unk, lasfin_unk, allas_unk], marker_color='lightgray')
        ])
        # Change the bar mode
        fig.update_layout(barmode='stack', title_text='Broker Agreement',yaxis_title='Classification Agreement')
        fig.show()

    def printProgressBar(self, iteration, total, prefix = '', suffix = 'Complete', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
        # Print New Line on Complete
        if iteration == total: 
            print()




