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



class ImioAesMeal(BaseResource):

    category = _('Datasources manager')
    meal_file = models.FileField(_('AES Meal file'), upload_to='aes_meal',
        help_text=_('Supported file formats: csv, json'))
    
    class Meta:
        verbose_name = _('Aes meal importer and serve in wcs')

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
        return currdate.replace('/','-')

    @endpoint(perm='can_access', methods=['get'])
    def json(self, request, **kwargs):
        meals = []
        rows = self.get_rows()
        num_col = 0
        try:            
            for r in rows:
                num_col = 0
                for col in r:
                    iddate = self.iddate(r[0])
                    if num_col == 4 and len(r[4]) > 1:
                        meals.append(
                                {"id":"_{}_{}".format(iddate,'exception'),
                             "text":"{}".format(r[4]),
                             "type":"exception"})
                    elif len(r[4]) == 0:
                        if num_col == 1:
                            meals.append(
                                {"id":"_{}_{}".format(iddate,'potage'),
                                "text":"{}".format(r[1]),
                                "type":"potage"})
                        if num_col == 2:
                            meals.append(
                                {"id":"_{}_{}".format(iddate,'repas'),
                                "text":"{}".format(r[2]),
                                "type":"repas"})
                        if num_col == 3:
                            meals.append(
                                {"id":"_{}_{}".format(iddate,'fruit'),
                                "text":"{}".format(r[3]),
                                "type":"fruit"})
                    num_col = num_col + 1
            return {'data':meals}
        except Exception as e:
            import ipdb;ipdb.set_trace()

