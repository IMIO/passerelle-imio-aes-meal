# -*- coding: utf-8 -*-


# passerelle-imio-aes-meal - passerelle connector for aes meal management
# Copyright (C) 2016  Entr'ouvert / Imio
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import csv
import decimal

from django.db import models
from django.core.validators import RegexValidator
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from passerelle.base.models import BaseResource
from passerelle.utils.api import endpoint

import ast
import datetime
import json

class ImioAesMeal(BaseResource):

    category = _('Datasources manager')
    meal_file = models.FileField(_('AES Meal file'), upload_to='aes_meal',
        help_text=_('Supported file formats: csv, json'))

    # [fruit,...]
    ignore_types =  models.CharField(_('Types to ignore'), default='', max_length=128, blank=True)
    # An nothing type item can be select.
    nothing = models.BooleanField(default=True,
            verbose_name=_('Authorize to select "nothing" item'))
            #, help_text='If "Yes" Use with "one_choice_by_date" set on Additional css class property field')
    #Personal labels
    personal_labels = models.TextField(default="{}", verbose_name='Personalize labels', blank=True, help_text='Personal labels: define like a dictionary : {"fruit":"new label fruit","repas":"repas chaud",...}')

    multi_select = models.BooleanField(default=True,
            verbose_name=_('Allows to select multiple items'))
    class Meta:
        verbose_name = _('Aes meal importer and serve in wcs')

    datas = {}
    @classmethod
    def get_verbose_name(cls):
        return cls._meta.verbose_name

    @classmethod
    def get_icon_class(cls):
        return ''

    def save(self, *args, **kwargs):
        result = super(ImioAesMeal, self).save(*args, **kwargs)
        return result

    def get_content_without_bom(self):
        self.meal_file.seek(0)
        content = self.meal_file.read()
        return content.decode('utf-8-sig', 'ignore').encode('utf-8')

    def get_rows(self):
        file_type = self.meal_file.name.split('.')[-1]
        if file_type == 'csv':
            content = self.get_content_without_bom()
            reader = csv.reader(content.splitlines(), delimiter='|')
            rows = list(reader)
        return rows

    def iddate(self, currdate):
        month = currdate.split('/')[1]
        hack_month = '{:02d}'.format(datetime.date.today().month + 1)
        currdate = currdate.replace('/' +month+ '/', '/' +hack_month+ '/')
        return currdate.replace('/','-')

    @endpoint(perm='can_access', methods=['get'])
    def json_current_month(self, request, **kwargs):
        datas = self.json(request).get('data')
        datas = json.dumps(datas).replace('month','{:02d}'.format(datetime.date.today().month + 1))
        return json.loads(datas)


    def json_and_ignore(self):
        meals = []
        datas = self.json().get('data')
        for meal in self.datas.get('data'):
            if meal.get('type').upper() not in self.ignore_types.upper():
                meals.append(meal)
        self.datas['data'] = meals
        return self.datas


    # {"potage":"Potage - tartine",
    #       "repas":"Repas chaud"}
    def json_add_types_and_labels(self):
        pl = ast.literal_eval(self.personal_labels)
        meals = []
        for meal in self.datas.get('data'):
            if meal.get('type') in pl:
                meal['text'] = '[{}];{}'.format(pl.get(meal.get('type')), meal.get('text'))
            meals.append(meal)
        self.datas['data'] = meals
        return self.datas

    @endpoint(serializer_type='json-api', perm='can_access', description='Ensure than citizen selected at least one item per day when nothing mode is set up',
            parameters={'lst_meals':{'description':'list of selected meals', 'example_value':"'_04-11-2019_potage', '_05-11-2019_potage', '_19-11-2019_potage'"}})
    def zero_if_meals_selected_for_each_day(self, request=None, **kwargs):
        lst_meals = request.GET['lst_meals'].split(',')
        lst_valid_dates = []
        if self.nothing is True:
            all_meals = self.get()['data']
            for m in all_meals:
                if m.get('type') != 'exception':
                    meal_date = m.get('id').split('_')[1]
                    lst_valid_dates.append(meal_date)
            nb_valid_meals = len(set(lst_valid_dates))
            return len(lst_meals) - nb_valid_meals
        else:
            return 0

    @endpoint(perm='can_access', methods=['get'])
    def get(self, request=None, **kwargs):
        self.datas = self.json()
        if self.personal_labels:
            self.datas = self.json_add_types_and_labels()
        if len(self.ignore_types) > 0:
            self.datas = self.json_and_ignore()
        return self.datas

    def json(self):
        meals = []
        rows = self.get_rows()
        num_col = 0
        nothing_already_add = False
        multi_select = 'mult' if self.multi_select is True and self.nothing is False else ''
        try:
            for r in rows:
                num_col = 0
                for col in r:
                    iddate = self.iddate(r[0])
                    is_day_off = False if len(r[4]) == 0 else True
                    if self.nothing is True and nothing_already_add is False and is_day_off is False:
                        # add a "nothing" choice checkbox.
                        meals.append( {"id":"_{}_{}".format(iddate, 'nothing'),
                            "text":"Rien",
                            "type":"nothing"})
                        nothing_already_add = True
                    if num_col == 4 and is_day_off is True:
                        # It's a day off!
                        meals.append(
                                {"id":"{}_{}_{}".format(multi_select, iddate, 'exception'),
                             "text":"{}".format(r[4]),
                             "type":"exception"})
                    elif len(r[4]) == 0:
                        if num_col == 1:
                            meals.append(
                                {"id":"{}_{}_{}".format(multi_select, iddate, 'potage'),
                                "text":"{}".format(r[1]),
                                "type":"potage"})
                        if num_col == 2:
                            meals.append(
                                {"id":"{}_{}_{}".format(multi_select, iddate, 'repas'),
                                "text":"{}".format(r[2]),
                                "type":"repas"})
                        if num_col == 3:
                            meals.append(
                                {"id":"{}_{}_{}".format(multi_select, iddate, 'fruit'),
                                "text":"{}".format(r[3]),
                                "type":"fruit"})
                    num_col = num_col + 1
                nothing_already_add = False
            # self.datas = {'data':meals}
            return {'data':meals}
        except Exception as e:
            raise e
