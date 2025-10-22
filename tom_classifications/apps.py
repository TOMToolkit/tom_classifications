from django.apps import AppConfig


class TomClassificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tom_classifications'

    def target_detail_tabs(self):
        """
        Integration point for adding tabs to the target detail page.

        This method should return a list of dictionaries that include a `partial` key pointing to the path of the html
        target_detail_tab partial.
        The `context` key should point to the dot separated string path to the templatetag
        that will return a dictionary containing new context for the accompanying partial.
        The `label` key will represent the label string to put in the tab and use as a tab reference id.
        This partial will be displayed within the tab on the target detail page.

        """
        return [{'partial': f'{self.name}/partials/classification_tab.html',
                 'label': 'Classification',
                 # 'context': f'{self.name}.templatetags.classification_plots'
                }]