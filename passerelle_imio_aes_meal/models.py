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

import ast
import csv
import datetime
import json
import six
import time

from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import ugettext_lazy as _
from passerelle.base.models import BaseResource
from passerelle.compat import json_loads
from passerelle.utils.api import endpoint


class ImioAesMeal(BaseResource):

    category = _("Datasources manager")
    meal_file = models.FileField(
        _("AES Meal file"),
        upload_to="aes_meal",
        help_text=_("Supported file formats: csv, json"),
    )

    # [fruit,...]
    ignore_types = models.CharField(
        _("Types to ignore"), default="", max_length=128, blank=True
    )
    # An nothing type item can be select.
    nothing = models.BooleanField(
        default=True, verbose_name=_('Authorize to select "nothing" item')
    )
    # , help_text='If "Yes" Use with "one_choice_by_date" set on Additional css class property field')
    # Personal labels
    personal_labels = models.TextField(
        default="{}",
        verbose_name="Personalize labels",
        blank=True,
        help_text='Personal labels: define like a dictionary : {"fruit":"new label fruit","repas":"repas chaud",...}',
    )

    multi_select = models.BooleanField(
        default=True, verbose_name=_("Allows to select multiple items")
    )

    class Meta:
        verbose_name = _("Aes meal importer and serve in wcs")

    datas = {}

    @classmethod
    def get_verbose_name(cls):
        return cls._meta.verbose_name

    @classmethod
    def get_icon_class(cls):
        return ""

    def save(self, *args, **kwargs):
        kwargs.pop("cache", False)
        result = super(ImioAesMeal, self).save(*args, **kwargs)
        return result

    def _detect_dialect_options(self):
        content = self.get_content_without_bom()
        dialect = csv.Sniffer().sniff(content)
        self.dialect_options = {
            k: v for k, v in vars(dialect).items() if not k.startswith("_")
        }

    @property
    def dialect_options(self):
        """turn dict items into string
        """
        file_type = self.meal_file.name.split(".")[-1]
        if file_type in ("ods", "xls", "xlsx"):
            return None
        # Set dialect_options if None
        if self._dialect_options is None:
            self._detect_dialect_options()
        self.save(cache=False)

        options = {}
        for k, v in self._dialect_options.items():
            if isinstance(v, six.text_type):
                v = force_str(v.encode("ascii"))
            options[force_str(k.encode("ascii"))] = v

        return options

    @dialect_options.setter
    def dialect_options(self, value):
        self._dialect_options = value

    def get_content_without_bom(self):
        self.meal_file.seek(0)
        content = self.meal_file.read()
        return force_str(content.decode("utf-8-sig", "ignore").encode("utf-8"))

    def get_rows(self):
        file_type = self.meal_file.name.split(".")[-1]
        if file_type == "csv":
            content = self.get_content_without_bom()
            self.dialect_options = {'doublequote': False, 'quoting': 0, 'lineterminator': '\r\n',
                                    'skipinitialspace': False, 'quotechar': '"', 'delimiter': '|'}
            reader = csv.reader(content.splitlines(), **self.dialect_options)
            rows = list(reader)
        return rows

    def iddate(self, currdate):
        # All those lines a commented for history
        # I don't know why they exist, possibly for Tournai's usecases.
        # But now, they mess up Chaudfontaine.
        # Since the dates are already in the CSV, I don't see the utility of recalculating those dates

        #month = currdate.split("/")[1]
        #year = currdate.split("/")[2]
        #if month != "12":
        #    hack_month = "{:02d}".format(datetime.date.today().month + 1)
        #    currdate = currdate.replace("/" + month + "/", "/" + hack_month + "/")
        #else:
        #    hack_year = "{:02d}".format(datetime.date.today().year + 1)
        #    currdate = currdate.replace(year, hack_year)
        #    currdate = currdate.replace("/" + month + "/", "/01/")
        return currdate.replace("/", "-")

    @endpoint(
        perm="can_access",
        methods=["get"],
        description="True if csv file dates records are for the next month",
    )
    def are_meals_up_to_date(self, request, **kwargs):
        result = False
        # check only on the first date. Maybe stronger if we check on all records?
        first_date_record = self.get_rows()[0][0]
        try:
            date_object = time.strptime(first_date_record, "%d/%m/%Y")
        except Exception:
            return result
        if date_object.tm_year < datetime.date.today().year:
            return result
        if date_object.tm_year > datetime.date.today().year + 1:
            return result
        if date_object.tm_year == datetime.date.today().year:
            if date_object.tm_mon == datetime.date.today().month + 1:
                result = True
        if date_object.tm_year == datetime.date.today().year + 1:
            if date_object.tm_mon == 1 and datetime.date.today().month == 12:
                result = True
        return result

    #    @endpoint(perm='can_access', methods=['get'])
    #    def json_current_month(self, request, **kwargs):
    #        datas = self.json(request).get('data')
    #        datas = json.dumps(datas).replace('month','{:02d}'.format(datetime.date.today().month + 1))
    #        return json_loads(datas)

    def json_and_ignore(self):
        meals = []
        for meal in self.datas.get("data"):
            if meal.get("type").upper() not in self.ignore_types.upper():
                meals.append(meal)
        self.datas["data"] = meals
        return self.datas

    # {"potage":"Potage - tartine",
    #       "repas":"Repas chaud"}
    def json_add_types_and_labels(self):
        pl = ast.literal_eval(self.personal_labels)
        meals = []
        for meal in self.datas.get("data"):
            if meal.get("type") in pl:
                meal["text"] = "[{}];{}".format(
                    pl.get(meal.get("type")), meal.get("text")
                )
            meals.append(meal)
        self.datas["data"] = meals
        return self.datas

    @endpoint(
        serializer_type="json-api",
        perm="can_access",
        description="Ensure than citizen selected at least one item per day when nothing mode is set up",
        parameters={
            "lst_meals": {
                "description": "list of selected meals",
                "example_value": "'_04-11-2019_potage', '_05-11-2019_potage', '_19-11-2019_potage'",
            }
        },
    )
    def zero_if_meals_selected_for_each_day(self, request=None, **kwargs):
        lst_meals = request.GET["lst_meals"].split(",")
        lst_valid_dates = []
        if self.nothing is True:
            # This is the use-case one choice with "nothing" choice per day.
            all_meals = self.get_rows()
            for m in all_meals:
                if len(m[4]) == 0:
                    meal_date = m[0]
                    lst_valid_dates.append(meal_date)
            nb_valid_meals = len(set(lst_valid_dates))
            return len(lst_meals) - nb_valid_meals
        else:
            # This is the use-case multi-select checkbox per day.
            return 0

    def has_multi_select(self):
        multi_select = (
            "mult" if self.multi_select is True and self.nothing is False else ""
        )
        return multi_select

    @endpoint(perm="can_access", methods=["get"])
    def get(self, request=None, test=False):
        if request.body:
            params = json_loads(request.body)
            test = params.get("test")
        if test is True:
            self.datas = self.test_generating_menu()
        else:
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
        try:
            for r in rows:
                num_col = 0
                for col in r:
                    iddate = self.iddate(r[0])
                    is_day_off = False if len(r[4]) == 0 else True
                    if (
                        self.nothing is True
                        and nothing_already_add is False
                        and is_day_off is False
                    ):
                        # add a "nothing" choice checkbox.
                        meals.append(
                            {
                                "id": "_{}_{}".format(iddate, "nothing"),
                                "text": "Rien",
                                "type": "nothing",
                            }
                        )
                        nothing_already_add = True
                    if num_col == 4 and is_day_off is True:
                        # It's a day off!
                        meals.append(
                            {
                                "id": "{}_{}_{}".format(
                                    self.has_multi_select(), iddate, "exception"
                                ),
                                "text": "{}".format(r[4]),
                                "type": "exception",
                            }
                        )
                    elif len(r[4]) == 0:
                        if num_col == 1:
                            meals.append(
                                {
                                    "id": "{}_{}_{}".format(
                                        self.has_multi_select(), iddate, "potage"
                                    ),
                                    "text": "{}".format(r[1]),
                                    "type": "potage",
                                }
                            )
                        if num_col == 2:
                            meals.append(
                                {
                                    "id": "{}_{}_{}".format(
                                        self.has_multi_select(), iddate, "repas"
                                    ),
                                    "text": "{}".format(r[2]),
                                    "type": "repas",
                                }
                            )
                        if num_col == 3:
                            meals.append(
                                {
                                    "id": "{}_{}_{}".format(
                                        self.has_multi_select(), iddate, "fruit"
                                    ),
                                    "text": "{}".format(r[3]),
                                    "type": "fruit",
                                }
                            )
                    num_col = num_col + 1
                nothing_already_add = False
            return {"data": meals}
        except Exception as e:
            raise e

    @endpoint(
        name="test",
        perm="can_access",
        methods=["get"],
        description="test : Meals menu is always up to date but it's always the same food.",
    )
    def test_generating_menu(self, request=None):
        lst_meals = [
                            {
                                "text": "Potage cresson",
                                "type": "potage",
                                "id": "{}_03-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Lasagne bolognaise;pur boeuf ",
                                "type": "repas",
                                "id": "{}_03-month-year_repas".format(self.has_multi_select()),
                            },
                            {
                                "text": "Fruit",
                                "type": "fruit",
                                "id": "{}_03-month-year_fruit".format(self.has_multi_select()),
                            },
                            {
                                "text": "Potage chou-fleu",
                                "type": "potage",
                                "id": "{}_04-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Couscous poulet;Bouillon de légumes;Semoule",
                                "type": "repas",
                                "id": "{}_04-month-year_repas".format(self.has_multi_select()),
                            },
                            {
                                "text": "Yaourt sucré",
                                "type": "fruit",
                                "id": "{}_04-month-year_fruit".format(self.has_multi_select()),
                            },
                            {
                                "text": "Potage cerfeuil",
                                "type": "potage",
                                "id": "{}_01-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Carbonnades de boeuf;Carottes;Frites",
                                "type": "repas",
                                "id": "{}_01-month-year_repas".format(self.has_multi_select()),
                            },
                            {
                                "text": "Fruit",
                                "type": "fruit",
                                "id": "{}_01-month-year_fruit".format(self.has_multi_select()),
                            },
                            {
                                "text": "Potage champignons",
                                "type": "potage",
                                "id": "{}_05-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Filet de sole;Haricots verts ",
                                "type": "repas",
                                "id": "{}_05-month-year_repas".format(self.has_multi_select()),
                            },
                            {
                                "text": "Biscuit",
                                "type": "fruit",
                                "id": "{}_05-month-year_fruit".format(self.has_multi_select()),
                            },
                            {
                                "text": "Soupe à l'oignon",
                                "type": "potage",
                                "id": "{}_02-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Pain de veau sce brune;Compote de pommes;Purée",
                                "type": "repas",
                                "id": "{}_02-month-year_repas".format(self.has_multi_select()),
                            },
                            {
                                "text": "Mimolette",
                                "type": "fruit",
                                "id": "{}_02-month-year_fruit".format(self.has_multi_select()),
                            },
                            {
                                "text": "Potage julienne",
                                "type": "potage",
                                "id": "{}_10-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Pilaf aigre doux;(RIZ, lentilles);Salade",
                                "type": "repas",
                                "id": "{}_10-month-year_repas".format(self.has_multi_select()),
                            },
                            {
                                "text": "Yaourt nature bio & sucrette",
                                "type": "fruit",
                                "id": "{}_10-month-year_fruit".format(self.has_multi_select()),
                            },
                            {
                                "text": "Potage carotte curry",
                                "type": "potage",
                                "id": "{}_11-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Salade de pâtes mixtes au jambon (dinde);maïs bio;tomate et petits pois",
                                "type": "repas",
                                "id": "{}_11-month-year_repas".format(self.has_multi_select()),
                            },
                            {"text": "Fruit", "type": "fruit", "id": "_11-month-year_fruit"},
                            {
                                "text": "Potage courgette",
                                "type": "potage",
                                "id": "{}_12-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Emincé de dinde, jus aux herbes;Brocoli;Pomme de terre",
                                "type": "repas",
                                "id": "{}_12-month-year_repas".format(self.has_multi_select()),
                            },
                            {
                                "text": "Fruit",
                                "type": "fruit",
                                "id": "{}_12-month-year_fruit".format(self.has_multi_select()),
                            },
                            {
                                "text": "Potage tomate",
                                "type": "potage",
                                "id": "{}_08-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Pain hamburger pur boeuf;laitue;Frites",
                                "type": "repas",
                                "id": "{}_08-month-year_repas".format(self.has_multi_select()),
                            },
                            {"text": "Pop corn", "type": "fruit", "id": "_08-month-year_fruit"},
                            {
                                "text": "Potage navet",
                                "type": "potage",
                                "id": "{}_09-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Filet de saumon sce citron;Epinards à la crème;Purée maison",
                                "type": "repas",
                                "id": "{}_09-month-year_repas".format(self.has_multi_select()),
                            },
                            {"text": "Fruit", "type": "fruit", "id": "_09-month-year_fruit"},
                            {
                                "text": "Potage poireau",
                                "type": "potage",
                                "id": "{}_18-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Poisson meunière;Ratatouille niçoise;Ebly",
                                "type": "repas",
                                "id": "{}_18-month-year_repas".format(self.has_multi_select()),
                            },
                            {
                                "text": "Fruit",
                                "type": "fruit",
                                "id": "{}_18-month-year_fruit".format(self.has_multi_select()),
                            },
                            {
                                "text": "Potage potiron",
                                "type": "potage",
                                "id": "{}_17-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Emincé de boeuf;Gratin de chou-fleur et de pdt",
                                "type": "repas",
                                "id": "{}_17-month-year_repas".format(self.has_multi_select()),
                            },
                            {
                                "text": "Biscuit",
                                "type": "fruit",
                                "id": "{}_17-month-year_fruit".format(self.has_multi_select()),
                            },
                            {
                                "text": "Potage carotte curry",
                                "type": "potage",
                                "id": "{}_19-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Epigramme d'agneau jus au thym;Flageolets à l'ail;Purée maison",
                                "type": "repas",
                                "id": "{}_19-month-year_repas".format(self.has_multi_select()),
                            },
                            {
                                "text": "Crème dessert",
                                "type": "fruit",
                                "id": "{}_19-month-year_fruit".format(self.has_multi_select()),
                            },
                            {
                                "text": "Minestrone",
                                "type": "potage",
                                "id": "{}_15-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Omelette;Salade vinaigrette;Frites et mayonnaise",
                                "type": "repas",
                                "id": "{}_15-month-year_repas".format(self.has_multi_select()),
                            },
                            {
                                "text": "Yaourt aux fruits",
                                "type": "fruit",
                                "id": "{}_15-month-year_fruit".format(self.has_multi_select()),
                            },
                            {
                                "text": "Potage haricots verts",
                                "type": "potage",
                                "id": "{}_16-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Macaroni;carbonara de dinde aux blancs de poireaux",
                                "type": "repas",
                                "id": "{}_16-month-year_repas".format(self.has_multi_select()),
                            },
                            {
                                "text": "Fruit",
                                "type": "fruit",
                                "id": "{}_16-month-year_fruit".format(self.has_multi_select()),
                            },
                            {
                                "text": "Potage tomate boulettes",
                                "type": "potage",
                                "id": "{}_24-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Sauté de porc aux oignons;Quinoa bio aux petits légumes",
                                "type": "repas",
                                "id": "{}_24-month-year_repas".format(self.has_multi_select()),
                            },
                            {
                                "text": "Fruit",
                                "type": "fruit",
                                "id": "{}_24-month-year_fruit".format(self.has_multi_select()),
                            },
                            {
                                "text": "Potage vert pré",
                                "type": "potage",
                                "id": "{}_25-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Vol-au-vent aux champignons;Purée maison",
                                "type": "repas",
                                "id": "{}_25-month-year_repas".format(self.has_multi_select()),
                            },
                            {
                                "text": "Biscuit",
                                "type": "fruit",
                                "id": "{}_25-month-year_fruit".format(self.has_multi_select()),
                            },
                            {
                                "text": "Potage Céleri",
                                "type": "potage",
                                "id": "{}_26-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Oiseau sans tête;chou-rouge aux pommes;Pomme de terre",
                                "type": "repas",
                                "id": "{}_26-month-year_repas".format(self.has_multi_select()),
                            },
                            {
                                "text": "Yaourt aromatisé",
                                "type": "fruit",
                                "id": "{}_26-month-year_fruit".format(self.has_multi_select()),
                            },
                            {
                                "text": "CONGE EXCEPTIONNELLE",
                                "type": "exception",
                                "id": "{}_22-month-year_exception".format(
                                    self.has_multi_select()
                                ),
                            },
                            {
                                "text": "Potage brocoli",
                                "type": "potage",
                                "id": "{}_23-month-year_potage".format(self.has_multi_select()),
                            },
                            {
                                "text": "Dos de lieu;Courgettes à la tomate;Pâtes grecques",
                                "type": "repas",
                                "id": "{}_23-month-year_repas".format(self.has_multi_select()),
                            },
                            {
                                "text": "Fruit",
                                "type": "fruit",
                                "id": "{}_23-month-year_fruit".format(self.has_multi_select()),
                            },
                        ]
        if self.nothing is True:
            current_tmp_date = ""
            lst_tmp = []
            for meal in lst_meals:
                str_tmp_date = meal.get("id").split("_")[1]
                if str_tmp_date != current_tmp_date and meal.get("type") != "exception":
                    lst_tmp.append(
                        {
                            "id": "_{}_{}".format(str_tmp_date, "nothing"),
                            "text": "Rien",
                            "type": "nothing",
                        }
                    )
                current_tmp_date = meal.get("id").split("_")[1]
            lst_meals = lst_meals+ lst_tmp
        result = json_loads(
            json.dumps(lst_meals).replace("month", "{:02d}".format(datetime.date.today().month + 1)).replace("year", str(datetime.date.today().year))
        )
        return result
