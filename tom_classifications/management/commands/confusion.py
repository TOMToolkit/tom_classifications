from django.core.management.base import BaseCommand
from tom_targets.models import TargetList
import json
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
from os import path
from django.conf import settings

class Command(BaseCommand):

    def handle(self, *args, **options):
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
        

        # alerce_series = pd.Series([1,0,0,1], name='ALeRCE')
        # fink_series = pd.Series([1,0,0,0], name='Fink')
        # df_confusion = pd.crosstab(alerce_series, fink_series)
        # self.confusion_plot(df_confusion)
        self.small_fink_lasair()
        return 'Success!'
    
    def small_con(self, x, y):
        targets = TargetList.objects.get(name='Alerce + Fink + Lasair').targets.all()
        print(len(targets))
        cap = 0
        skip = 0
        sources = ['ALeRCE Stamp', 'Lasair', 'Fink']#this is the order that the choices are arranged, make sure this is consistent with the assignment below
        big_choices = [[], [], []]
        for t in targets:
            tcs = t.targetclassification_set.all()#looks at all the associated target classifications and assesses the how many there are
            if cap < 500000:
                #these lines pick the classification with the highest probability form each broker
                stamp_set = tcs.filter(level='lc_classifier').order_by('mjd', '-probability')
                if not stamp_set.exists():
                    stamp_set = tcs.filter(level='stamp_classifier_1.0.4').order_by('mjd', '-probability')
                if not stamp_set.exists():
                    stamp_set = tcs.filter(level='stamp_classifier_1.0.0').order_by('mjd', '-probability')
                if not stamp_set.exists():
                    skip += 1
                    continue
                stamp_tc = stamp_set[0]
                # print(stamp_tc.as_dict())
                stamp_choice = self.alerce_codes[stamp_tc.classification]
                try:
                    las_choice = self.las_codes[tcs.filter(source='Lasair').order_by('mjd', '-probability')[0].classification]
                except:
                    skip+=1
                    continue
                fink_choice = self.fink_codes[tcs.filter(source='Fink').order_by('mjd', '-probability')[0].classification]
                if fink_choice == '?':
                    skip+=1
                    continue
                catch_list = ['SN*', 'CV*', 'AGN', 'V*', '~Alert']
                choices = [stamp_choice, las_choice, fink_choice]
                
                for i in range(len(choices)):
                    while not choices[i] in catch_list:
                        choices[i] = self.parents_dict[choices[i]]
                    big_choices[i].append(choices[i])
                cap += 1
        print(cap, skip)
        las_series = pd.Series(big_choices[1],  name='Lasair')
        alerce_series = pd.Series(big_choices[0], name='ALeRCE')
        fink_series = pd.Series(big_choices[2], name='Fink')
        big_series = [alerce_series, las_series, fink_series]
        df_confusion = pd.crosstab(big_series[x], big_series[y])
        self.confusion_plot(df_confusion)
    
    def large_con(self, max=99999999, tf = 1):
        targets = TargetList.objects.get(name='ALeRCE + Fink').targets.all()
        print(len(targets))
        cap = 0
        skip=0
        too_few=0
        sources = ['ALeRCE Stamp', 'Fink']#this is the order that the choices are arranged, make sure this is consistent with the assignment below
        big_choices = [[], [], []]
        for t in targets:
            tcs = t.targetclassification_set.all()#looks at all the associated target classifications and assesses the how many there are
            if cap < max:
                if t.targetextra_set.get(key='alerce_ndet').typed_value('number') < tf:
                    too_few +=1
                    continue
                #these lines pick the classification with the highest probability form each broker
                stamp_set = tcs.filter(level='lc_classifier').order_by('mjd', '-probability')
                if not stamp_set.exists():
                    stamp_set = tcs.filter(level='stamp_classifier_1.0.4').order_by('mjd', '-probability')
                if not stamp_set.exists():
                    stamp_set = tcs.filter(level='stamp_classifier_1.0.0').order_by('mjd', '-probability')
                if not stamp_set.exists():
                    skip += 1
                    continue
                stamp_choice = self.alerce_codes[stamp_set[0].classification]
                if not tcs.filter(source='Fink').exists():
                    skip += 1
                    continue
                fink_choice = self.fink_codes[tcs.filter(source='Fink').order_by('mjd', '-probability')[0].classification]
                if fink_choice == '?':
                    skip += 1
                    continue
                catch_list = ['SN*', 'CV*', 'AGN', 'QSO', 'LP*', 'Ce*', 'RR*', 'dS*', 'Pu*', 'EB*', 'Y*O', 'V*', '?', '~Alert']
                choices = [stamp_choice, fink_choice]
                
                for i in range(len(choices)):
                    while not choices[i] in catch_list:
                        choices[i] = self.parents_dict[choices[i]]
                    big_choices[i].append(choices[i])
                cap += 1
        print('The plot uses', cap)
        print(too_few, 'had too few data points')
        print(skip, 'were stopped for data reasons')
        alerce_series = pd.Series(big_choices[0], name='ALeRCE')
        fink_series = pd.Series(big_choices[1], name='Fink')
        df_confusion = pd.crosstab(alerce_series, fink_series)
        self.confusion_plot(df_confusion, tf)

    def small_alerce_lasair(self, max=99999999):
        targets = TargetList.objects.get(name='ALeRCE + Lasair').targets.all()
        print(len(targets))
        cap = 0
        alskip = 0
        lasskip = 0
        sources = ['ALeRCE Stamp', 'Lasair']#this is the order that the choices are arranged, make sure this is consistent with the assignment below
        big_choices = [[], []]
        for t in targets:
            tcs = t.targetclassification_set.all()#looks at all the associated target classifications and assesses the how many there are
            if cap < max:
                #these lines pick the classification with the highest probability form each broker
                stamp_set = tcs.filter(level='lc_classifier').order_by('mjd', '-probability')
                if not stamp_set.exists():
                    stamp_set = tcs.filter(level='stamp_classifier_1.0.4').order_by('mjd', '-probability')
                if not stamp_set.exists():
                    stamp_set = tcs.filter(level='stamp_classifier_1.0.0').order_by('mjd', '-probability')
                if not stamp_set.exists():
                    alskip += 1
                    continue
                stamp_tc = stamp_set[0]
                # print(stamp_tc.as_dict())
                stamp_choice = self.alerce_codes[stamp_tc.classification]
                try:
                    las_choice = self.las_codes[tcs.filter(source='Lasair').order_by('mjd', '-probability')[0].classification]
                except:
                    lasskip+=1
                    continue

                catch_list = ['SN*', 'CV*', 'AGN', 'V*', '~Alert']
                choices = [stamp_choice, las_choice]
                
                for i in range(len(choices)):
                    while not choices[i] in catch_list:
                        choices[i] = self.parents_dict[choices[i]]
                    big_choices[i].append(choices[i])
                cap += 1
        print(cap, alskip, lasskip)
        alerce_series = pd.Series(big_choices[0], name='ALeRCE')
        las_series = pd.Series(big_choices[1],  name='Lasair')
        df_confusion = pd.crosstab(las_series, alerce_series)
        self.confusion_plot(df_confusion)

    def small_fink_lasair(self, max=99999999):
            targets = TargetList.objects.get(name='Lasair + Fink').targets.all()
            print(len(targets))
            cap = 0
            lasskip = 0
            finskip = 0
            sources = ['Lasair', 'Fink']#this is the order that the choices are arranged, make sure this is consistent with the assignment below
            big_choices = [[], []]
            for t in targets:
                tcs = t.targetclassification_set.all()#looks at all the associated target classifications and assesses the how many there are
                if cap < max:
                    #these lines pick the classification with the highest probability form each broker
                    try:
                        las_choice = self.las_codes[tcs.filter(source='Lasair').order_by('mjd', '-probability')[0].classification]
                    except:
                        lasskip+=1
                        continue
                    try:
                        fink_choice = self.fink_codes[tcs.filter(source='Fink').order_by('mjd', '-probability')[0].classification]
                        if fink_choice == '?':
                            finskip+=1
                            continue
                    except:
                        finskip+=1
                        continue
                    catch_list = ['SN*', 'CV*', 'AGN', 'V*', '~Alert']
                    choices = [las_choice, fink_choice]
                    
                    for i in range(len(choices)):
                        while not choices[i] in catch_list:
                            choices[i] = self.parents_dict[choices[i]]
                        big_choices[i].append(choices[i])
                    cap += 1
            print(cap, lasskip, finskip)
            las_series = pd.Series(big_choices[0],  name='Lasair')
            fink_series = pd.Series(big_choices[1], name='Fink')
            df_confusion = pd.crosstab(las_series, fink_series)
            self.confusion_plot(df_confusion)

    def confusion_plot(self, df_confusion,tf=1):
        cols = list(df_confusion.columns)
        rows = list(df_confusion.index)
        for c in cols:#these loops add any missing data columns and rows to make it a square matrix
            if not c in rows:
                df_confusion.loc[c] = 0
        for r in rows:
            if not r in cols:
                df_confusion[r] = 0
        df_confusion = df_confusion.sort_index()
        df_confusion = df_confusion.sort_index(axis=1)
        print(df_confusion)
        fig, ax = plt.subplots()
        plt.suptitle('Classification Reliability')
        # plt.title(f'Targets with at least {tf} detections')
        fig.set_size_inches(8, 6)
        ax.matshow(df_confusion, cmap='Blues', norm=matplotlib.colors.LogNorm())
        tick_marks = np.arange(len(df_confusion.columns))

        xtick_labels = list(df_confusion.columns)
        for i,v in enumerate(xtick_labels):#these two loops pop out the '~Alert' label and swap it with 'Other', not part of the heirarchy, just for display
            if v == '~Alert':
                xtick_labels.pop(i)
                xtick_labels.insert(i,'Other')
        ytick_labels = list(df_confusion.index)
        for i,v in enumerate(ytick_labels):
            if v == '~Alert':
                ytick_labels.pop(i)
                ytick_labels.insert(i,'Other')
        ax.set_xticks(tick_marks, xtick_labels, rotation=45)
        ax.set_yticks(tick_marks, ytick_labels)
        #plt.tight_layout()
        ax.set_ylabel(df_confusion.index.name)
        ax.set_xlabel(df_confusion.columns.name)
        ax.tick_params(axis="x", bottom=True, top=False, labelbottom=True, labeltop=False)
        for (i, j), z in np.ndenumerate(df_confusion):
            ax.text(j, i, z, ha='center', va='center')
        fig.tight_layout()
        plt.show()

