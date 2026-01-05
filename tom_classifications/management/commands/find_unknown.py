from django.core.management.base import BaseCommand
from tom_targets.models import Target
import logging
from tom_classifications.models import TargetClassification
import numpy as np

class Command(BaseCommand):

    help = 'This command generates the unique classification codes of the target classification objects in the database. Make sure these are represented in the broker codes dictionaries'

    def add_arguments(self, parser):
        parser.add_argument('--ztf', help='Download data for a single target')

    def handle(self, *args, **options):
        FORMAT = '%(asctime)s %(message)s'
        print('test')
        logging.basicConfig(format = FORMAT, filename='/home/bmills/bmillsWork/tom_test/mytom/find_unknown.log', level=logging.INFO, force=True)
        
        self.classification_printout()


    def count_tcs(self):
        '''This method goes though all the targets and sees hoe many target classifications it has
        It prints out a list showing how many classifications a target might have, and how many 
        targets have that may classifications. '''
        targets = list(Target.objects.all())
        lengths = []
        counts = []
        names = []
        for t in targets:
            tcs = TargetClassification.objects.filter(target = t)
            l = len(tcs)
            try:
                i = lengths.index(l)
                counts[i] += 1
                names[i].append(t.name)
            except:
                lengths.append(l)
                counts.append(1)
                names.append([t.name])

        
        order = np.argsort(lengths)
        for i in order:
            print(lengths[i], counts[i])

        print(names[-1][0])
        return lengths, counts, names
    
    def classification_printout(self):
        '''This method goes through all target classifications and generates a printout with the unique classifications and how many appear in the database
        also it is formatted like a dictionary in case you need to copy and paste it somewhere.'''
        tcs = TargetClassification.objects.all()
        total = len(tcs)
        classifications = []
        counts = []
        for tc in tcs:
            text = tc.source + ' ' + tc.classification
            if not text in classifications:
                classifications.append(text)
                counts.append(1)
            else:
                counts[classifications.index(text)] +=1
        for i in range(len(classifications)):
            print("'" + classifications[i] + "': " +  "'" + str(counts[i]) + "'")
        print(len(classifications))
        print(f'there are {total} total classifications')