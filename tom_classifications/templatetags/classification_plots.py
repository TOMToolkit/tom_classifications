import json
import logging
from os import path

from django import template
from django.conf import settings

from tom_classifications import __version__

from plotly import offline
from plotly import graph_objs as go

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

register = template.Library()


@register.inclusion_tag('tom_classifications/partials/classification_tab.html')
def get_context(request_context):
    context = {
        'version': __version__
    }
    return context


@register.inclusion_tag('tom_classifications/partials/classif_sun.html')
def classif_sun(target, width=700, height=700, background=None, label_color=None, grid=True):
    tcs = target.targetclassification_set.all()

    alerce_lc_tcs = tcs.filter(level='lc_classifier')
    alerce_stamp_tcs= tcs.filter(level='stamp_classifier_1.0.4')
    if len(alerce_stamp_tcs) == 0:
        alerce_stamp_tcs = tcs.filter(level='stamp_classifier_1.0.0')
    lasair_tcs = tcs.filter(source='Lasair')
    fink_tcs = tcs.filter(source='Fink')

    with open(path.join(settings.MEDIA_ROOT,'broker_codes.txt')) as json_file:#this loads the parentage dictionary that I made
        big_codes_dict = json.load(json_file)
    las_codes = big_codes_dict['las_codes']
    alst_codes = big_codes_dict['alerce_stamp_codes']
    allc_codes = big_codes_dict['alerce_lc_codes']
    fink_codes = big_codes_dict['fink_codes']

    codes = []
    if lasair_tcs:
        tc = lasair_tcs[len(lasair_tcs)-1]
        l_code = las_codes.get(tc.classification)
        codes.append( (l_code, 'Lasair', tc.probability) )

    # deals with alerce stamp
    for tc in alerce_stamp_tcs:
        codes.append( (alst_codes.get(tc.classification), 'Alerce stamp', tc.probability))

    #does alerce lc
    for tc in alerce_lc_tcs:
        codes.append( (allc_codes.get(tc.classification), 'Alerce LC', tc.probability))

    #deals with fink
    with open(path.join(settings.MEDIA_ROOT,'SIMBAD_otypes_labels.txt')) as f:
        for line in f:
            [_, code, old, new] = line.split('|')
            fink_codes[old.strip()] = code.strip()
            fink_codes[new.strip()] = code.strip()
    candidate = False
    for tc in fink_tcs:
        if tc.probability > 0.1 and 'candidate' in tc.classification or 'Candidate' in tc.classification:
            candidate = True
        codes.append( (fink_codes[tc.classification], 'Fink', tc.probability))

    with open(path.join(settings.MEDIA_ROOT,'variability.txt')) as json_file:
        parents_dict = json.load(json_file)

    labels = ['~Alert']
    parents = ['']
    values = [None]
    colors = [0]
    for code in codes:
        code_walker = code[0]
        confidence = code[2] #this is not statistical confidence more like a relative feeling
        if confidence < 0.01:
            continue
        lineage = [(code_walker, confidence)]
        while code_walker and code_walker != '~Alert':#this loop builds the lineage
            code_walker = parents_dict[code_walker]
            lineage.append( (code_walker, confidence) )
        lineage.append(('',-1))
        for l in lineage:
            if not l[0]:
                break
            if l[0] == '~Alert':
                continue
            if l[0] in labels:
                colors[labels.index(l[0])] += l[1]
            else:
                labels.append(l[0])
                parents.append(parents_dict[l[0]])
                values.append(1)
                colors.append(l[1])

    fig =go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=colors,
        marker=dict(
            colors=colors,
            colorscale='Greens',
            colorbar=dict(
                tick0=0,
                len=0.25
                )),
    ))

    fig.update_layout(
        title={
            'text': target.name,
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        margin = dict(t=100, l=0, r=0, b=0),
        height=800,
        width=800,)

    plot_out = offline.plot(
        fig, output_type='div', show_link=False
    )

    return {'plot': plot_out}

@register.inclusion_tag('tom_classifications/partials/classif_scatter.html')
def classif_scatter(target, width=700, height=700, background=None, label_color=None, grid=True):
    tcs = target.targetclassification_set.all()
    alerce_lc_tcs = tcs.filter(level='lc_classifier')
    alerce_stamp_tcs= tcs.filter(level='stamp_classifier_1.0.4')
    if len(alerce_stamp_tcs) == 0:
        alerce_stamp_tcs = tcs.filter(level='stamp_classifier_1.0.0')
    lasair_tcs = tcs.filter(source='Lasair')
    fink_tcs = tcs.filter(source='Fink')

    with open(path.join(settings.MEDIA_ROOT,'variability.txt')) as json_file:
        parents_dict = json.load(json_file)

    fig = go.Figure(go.Barpolar(
        r=[1,1,1,1,1,1,1],
        theta=['AGN', 'SNII', 'RR*', 'Y*O','ast', 'Other'],
        width=[3, 5, 5, 7, 1, 3],
        marker_color=["#E4FF87", '#709BFF', '#B6FFB4', '#FFAA70', '#F242F5','#424142'],
        opacity=0.15,
        hovertext=['AGN Types', 'Supernovae', 'Pulsating', 'Stellar Variability', 'Asteroid', 'Other Variability'],
        hoverinfo='text',
        
        showlegend=False
    ))
    fig.add_trace(go.Barpolar(
        r=[.1,.1,.1,.1,.1,.1],
        theta=['AGN', 'SNII', 'RR*', 'Y*O','ast', 'Other'],
        width=[3, 5, 5, 7, 1, 3],
        marker_color=["#E4FF87", '#709BFF', '#B6FFB4', '#FFAA70', '#F242F5','#424142'],
        opacity=0.8,
        hovertext=['AGN Types', 'Supernovae', 'Pulsating', 'Stellar Variability', 'Asteroid', 'Other Variability'],
        hoverinfo='text',
        name='Groupings',
        base=[1,1,1,1,1,1],
    ))
    objs = ['SNIa', 'SNIbc', 'SNII', 'SLSN', 'SN*', 'QSO', 'AGN', 'G*', 'LP*', 'Ce*', 'RR*', 'dS*', 'Pu*', 'EB*', 'CV*', '**',  'Y*O', 'Er*', 'Ro*', 'V*', 'ast', 'grv', 'Other', '~Alert']

    with open(path.join(settings.MEDIA_ROOT,'broker_codes.txt')) as json_file:#this loads the parentage dictionary that I made
        big_codes_dict = json.load(json_file)
    las_codes = big_codes_dict['las_codes']
    alst_codes = big_codes_dict['alerce_stamp_codes']
    allc_codes = big_codes_dict['alerce_lc_codes']
    fink_codes = big_codes_dict['fink_codes']
    #delas with lasair
    if lasair_tcs:
        tc = lasair_tcs[len(lasair_tcs)-1]
        code_walker = las_codes[tc.classification]
        while not code_walker in objs:
            code_walker = parents_dict[code_walker]
        l_code = code_walker
        l_prob = tc.probability
        fig.add_trace(go.Barpolar(
            name="Lasair",
            r=[l_prob],
            theta=[l_code],
            width=[1],
            marker= dict(line_width=2, line_color='green', color='rgba(0,0,0,0)',),
            base=0,
            hovertext=['Lasair: ' + tc.classification],
            hoverinfo='text',
        ))

    # deals with alerce stamp
    alst_list = []
    alst_probs = []
    for tc in alerce_stamp_tcs:
        code_walker = alst_codes[tc.classification]
        while not code_walker in objs:
            code_walker = parents_dict[code_walker]
        alst_list.append(code_walker)
        alst_probs.append(tc.probability)

    fig.add_trace(go.Barpolar(#alerce stamp bar chart
        name='ALeRCE Stamp',
        r=alst_probs,
        theta=alst_list,
        width=[1,1,1,1,1],
        marker_color='#BB8FCE',
        marker_line_color="black",
        marker_line_width=2,
        opacity=0.8,
        base=0,
        ))

    #does alerce lc
    alerce_lc_cats = []
    alerce_lc_probs = []
    for tc in alerce_lc_tcs:
        code_walker = allc_codes[tc.classification]
        while not code_walker in objs:
            code_walker = parents_dict[code_walker]
        alerce_lc_cats.append(code_walker)
        alerce_lc_probs.append(tc.probability)

    lc_out = []
    lc_out_p = []
    for o in objs:#this reorders the list to make the output nicer
        try:
            i = alerce_lc_cats.index(o)
            lc_out.append(alerce_lc_cats[i])
            lc_out_p.append(alerce_lc_probs[i])
        except:
            pass
    fig.add_trace(go.Scatterpolar(
        name='ALeRCE LC',
        r=lc_out_p,
        theta=lc_out,
        line=dict(color='#8E44AD', width=2),
        opacity=0.8,
        fill = 'toself'))

    #deals with fink,
    with open(path.join(settings.MEDIA_ROOT,'SIMBAD_otypes_labels.txt')) as f:
        for line in f:
            [_, code, old, new] = line.split('|')
            fink_codes[old.strip()] = code.strip()
            fink_codes[new.strip()] = code.strip()

    #deals with fink,
    if fink_tcs:
        fink_cats = []
        fink_probs = []
        offset = 0
        for tc in fink_tcs:
            if tc.probability < 0.01:
                fink_cats.append('~Alert')
                fink_probs.append(0)
                continue
            candidate = 'Candidate' in tc.classification or 'candidate' in tc.classification
            if candidate:
                fig.add_annotation(x=1,y=.98,text='This is a candidate target',showarrow=False)
            code_walker = fink_codes[tc.classification]
            while not code_walker in objs:
                code_walker = parents_dict[code_walker]
            if not code_walker == fink_codes[tc.classification]:
                offset += 0.05
                fig.add_annotation(x=1,y=1.1-offset,
                text='Fink actually thinks this is ' + tc.classification,
                showarrow=False,)
            fink_cats.append(code_walker)
            fink_probs.append(tc.probability)
        fig.add_trace(go.Scatterpolar(
            name='Fink',
            r=fink_probs,
            theta=fink_cats,
            line=dict(color='#EB984E', width=2),
            opacity=0.8,
            marker_size=10))
    fig.update_layout(
        template=None,
        height=800,
        width=800,
        polar = dict(
            # radialaxis = dict(showticklabels=False, ticks=''),
            angularaxis = dict(
                categoryarray=objs,
                categoryorder='array',
                showticklabels=True,
                )))
    plot_out = offline.plot(
        fig, output_type='div', show_link=False
    )

    return {'plot': plot_out}
